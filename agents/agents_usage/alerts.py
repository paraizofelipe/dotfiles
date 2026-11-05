"""Alertas de limite e troca de conta.

Quando a conta ativa passa do threshold (95% por padrão) em qualquer janela:
- modo "notify": notifica com a ação de trocar para a conta com mais folga;
- modo "auto": troca sozinho e avisa;
- todas as contas acima: avisa uma vez qual conta libera primeiro.
Cada alerta dispara uma vez por janela (chave inclui o reset), guardado em ALERTS_FILE.
"""
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime

from . import accounts, common

ALERTS_FILE = os.path.join(common.STATE_DIR, "alerts.json")
NEAR_MARGIN = 15          # pontos abaixo do threshold que ativam o polling rápido
FAST_INTERVAL = 3 * 60
NORMAL_INTERVAL = 15 * 60
ACTION_TIMEOUT = 10 * 60  # quanto tempo a notificação com ação fica escutando o clique


def peak(record, now=None):
    """Maior percentual entre os limites da conta, ou None sem dados utilizáveis.
    Janelas que já resetaram não contam: com dado stale o percentual é do ciclo anterior."""
    now = time.time() if now is None else now
    if not record or not record.get("limits"):
        return None
    if record.get("status") != common.OK and not record.get("stale"):
        return None
    live = [lim["percent"] for lim in record["limits"]
            if not lim.get("resets_at") or lim["resets_at"] > now]
    return max(live) if live else None


def frees_at(record, threshold):
    """Quando a conta volta a ficar abaixo do threshold: o reset mais tardio
    entre as janelas estouradas."""
    resets = [lim["resets_at"] for lim in record.get("limits", [])
              if lim["percent"] >= threshold and lim.get("resets_at")]
    return max(resets) if resets else None


def _clock(ts):
    if not ts:
        return "horário desconhecido"
    dt = datetime.fromtimestamp(ts)
    fmt = "%H:%M" if dt.date() == datetime.now().date() else "%d/%m %H:%M"
    return dt.strftime(fmt)


def decide(records, registry, now=None):
    """Lista de ações (puro, sem efeitos colaterais)."""
    now = time.time() if now is None else now
    actions = []
    for provider in accounts.MULTI_ACCOUNT_PROVIDERS:
        entry = registry[provider]
        threshold = entry.get("threshold", accounts.DEFAULT_THRESHOLD)
        mine = [r for r in records if r["provider"] == provider]
        active = next((r for r in mine if r["account"] == entry.get("active", "main")), None)
        active_peak = peak(active, now)
        if active is None or active_peak is None or active_peak < threshold:
            continue
        name = active["provider_name"]
        window_key = frees_at(active, threshold)
        # Só troca para conta com leitura atual: offline/erro podem estar sem login ou esgotadas.
        others = [(peak(r, now), r) for r in mine if r is not active and r.get("status") == common.OK]
        free = sorted(((p, r) for p, r in others if p is not None and p < threshold),
                      key=lambda pr: pr[0])
        if free:
            best = free[0][1]
            kind = "switch" if entry.get("mode") == "auto" else "suggest"
            title = (f"{name}: trocado para {best['label']}" if kind == "switch"
                     else f"{name}: {active['label']} passou de {threshold}%")
            body = (f"{active['label']} em {active_peak:.0f}%. {best['label']} está em {free[0][0]:.0f}%."
                    if kind == "switch" else
                    f"Em {active_peak:.0f}%. Clique para trocar para {best['label']} ({free[0][0]:.0f}%).")
            actions.append({"kind": kind, "provider": provider, "from": active["account"],
                            "to": best["account"], "to_label": best["label"],
                            "title": title, "body": body,
                            "key": f"{provider}:{active['account']}:{kind}:{window_key}"})
            continue
        candidates = [(frees_at(r, threshold), r) for r in mine if peak(r, now) is not None]
        candidates = [(t, r) for t, r in candidates if t]
        first = min(candidates, key=lambda tr: tr[0]) if candidates else None
        body = (f"{first[1]['label']} libera primeiro, às {_clock(first[0])}." if first and len(mine) > 1
                else f"Libera às {_clock(window_key)}.")
        actions.append({"kind": "exhausted", "provider": provider, "from": active["account"],
                        "to": None, "title": f"{name}: limite de {threshold}% atingido", "body": body,
                        "key": f"{provider}:exhausted:{first[0] if first else window_key}"})
    return actions


def needs_fast_poll(records, registry, now=None):
    for provider in accounts.MULTI_ACCOUNT_PROVIDERS:
        entry = registry[provider]
        threshold = entry.get("threshold", accounts.DEFAULT_THRESHOLD)
        for r in records:
            if r["provider"] == provider and r["account"] == entry.get("active", "main"):
                p = peak(r, now)
                if p is not None and p >= threshold - NEAR_MARGIN:
                    return True
    return False


def next_interval(records, registry):
    return FAST_INTERVAL if needs_fast_poll(records, registry) else NORMAL_INTERVAL


# ------------------------------------------------------------------ efeitos
def notify(title, body, urgency="normal"):
    """True se a notificação foi entregue ao servidor de notificações."""
    try:
        return subprocess.run(["notify-send", "-a", "Agents", "-u", urgency, title, body],
                              check=False, timeout=5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def spawn_action_notification(action, agents_bin):
    """Processo destacado que mostra a notificação e troca a conta no clique,
    para o usage-update (rodando no systemd) não ficar bloqueado esperando."""
    subprocess.Popen(
        [sys.executable, agents_bin, "notify-switch", action["provider"], action["to"],
         action["title"], action["body"]],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)


def still_active(provider, account_id, mode=None, data_dir=None):
    """Relê o registro: o usuário pode ter trocado conta/modo durante a coleta."""
    entry = accounts.load_registry(accounts.registry_file(data_dir))[provider]
    return entry.get("active", "main") == account_id and (mode is None or entry.get("mode") == mode)


def apply(actions, agents_bin, alerts_file=None, data_dir=None, notifier=notify, spawner=None):
    """Executa as ações ainda não alertadas nesta janela. Retorna as executadas.
    Só marca como enviada a ação que de fato chegou ao usuário; o resto é
    recalculado na próxima coleta."""
    alerts_file = alerts_file or ALERTS_FILE
    spawner = spawner or spawn_action_notification
    sent = common.read_json(alerts_file, {}) or {}
    keys = {a["key"] for a in actions}
    done = []
    for action in actions:
        if action["key"] in sent:
            continue
        if action["kind"] == "switch":
            if not still_active(action["provider"], action["from"], "auto", data_dir):
                continue
            accounts.use_account(action["provider"], action["to"], data_dir=data_dir)
            notifier(action["title"], action["body"])  # a troca já valeu, mesmo sem o aviso
        elif action["kind"] == "suggest":
            spawner(action, agents_bin)
        elif not notifier(action["title"], action["body"], "critical"):
            continue
        sent[action["key"]] = time.time()
        done.append(action)
    # Esquece alertas que não se aplicam mais, para dispararem de novo na próxima vez.
    common.write_json_atomic(alerts_file, {k: v for k, v in sent.items() if k in keys})
    return done


# ------------------------------------------------------------------ notificação com ação (D-Bus)
DBUS_ARGS = ["--session", "--dest", "org.freedesktop.Notifications",
             "--object-path", "/org/freedesktop/Notifications"]
ACTION_RE = re.compile(r"ActionInvoked \(uint32 (\d+), '([^']*)'\)")
CLOSED_RE = re.compile(r"NotificationClosed \(uint32 (\d+),")


def _gvariant_str(text):
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def wait_for_action(title, body, action_label, timeout=ACTION_TIMEOUT):
    """Mostra a notificação com um botão e retorna True se ele foi clicado."""
    monitor = subprocess.Popen(["gdbus", "monitor", *DBUS_ARGS], stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True)
    # O for abaixo bloqueia esperando linhas; o timer encerra o monitor no prazo.
    timer = threading.Timer(timeout, monitor.kill)
    timer.daemon = True
    timer.start()
    try:
        out = subprocess.run(
            ["gdbus", "call", *DBUS_ARGS, "--method", "org.freedesktop.Notifications.Notify",
             "Agents", "0", "", title, body,
             f"['switch', {_gvariant_str(action_label)}, 'default', {_gvariant_str(action_label)}]",
             "{'urgency': <byte 2>}", "0"],
            capture_output=True, text=True, timeout=5, check=True).stdout
        match = re.search(r"uint32 (\d+)", out)
        if not match:
            return False
        nid = match.group(1)
        assert monitor.stdout is not None
        for line in monitor.stdout:
            act = ACTION_RE.search(line)
            if act and act.group(1) == nid:
                return act.group(2) in ("switch", "default")
            closed = CLOSED_RE.search(line)
            if closed and closed.group(1) == nid:
                return False
        return False
    except (OSError, subprocess.SubprocessError):
        return False
    finally:
        timer.cancel()
        monitor.kill()
