#!/usr/bin/env python3
"""Módulo polybar de utilização de IA (Claude Code, Codex, OpenRouter).

Standalone — apenas a stdlib do Python 3. Subcomandos: poll | fetch | show.
"""
import glob
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# ---------------------------------------------------------------- Config
USER = os.environ.get("USER", "user")
CACHE = f"/tmp/polybar-ai-usage-{USER}.json"
PIDFILE = f"/tmp/polybar-ai-usage-modal-{USER}.pid"
HTTP_TIMEOUT = 8
ROBOT = "\uf544"  # nf-fa-robot / Font Awesome 5 Solid (U+F544)
# Família que contém o glifo do robô no modal (Hack Nerd Font não cobre U+F544).
# weight=bold seleciona a face Solid-900, que é a que tem o ícone.
ICON_FONT = "Font Awesome 5 Free"
MONITOR_NAME = "DP-1"  # monitor da mainbar-i3: o modal abre nele
MODAL_MARGIN_X = 8     # px a partir da borda esquerda do monitor
MODAL_MARGIN_Y = 30    # px a partir do topo (logo abaixo da barra)

# Gruvbox
BG = "#32302f"
BG_ALT = "#1d2021"
FG = "#ebdbb2"
FG_DIM = "#a89984"
GREEN = "#b8bb26"
YELLOW = "#fabd2f"
RED = "#fb4934"

CLAUDE_CREDENTIALS = os.path.expanduser("~/.claude/.credentials.json")
CLAUDE_PROJECTS = os.path.expanduser("~/.claude/projects")
CODEX_AUTH = os.path.expanduser("~/.codex/auth.json")
CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
# A polybar não herda o env do shell interativo (~/.zshrc); por isso lemos
# variáveis sensíveis também destes arquivos de env, se necessário.
ENV_FILES = [os.path.expanduser("~/.use.env"), os.path.expanduser("~/.user.env")]
# Providers que NÃO contam para a cor do ícone (ex.: OpenRouter é saldo de
# créditos, não janela de rate-limit — não deve deixar o cérebro vermelho).
COLOR_EXCLUDED_PROVIDERS = {"OpenRouter"}


# ---------------------------------------------------------------- Helpers
def severity_color(percent):
    if percent < 50:
        return GREEN
    if percent <= 80:
        return YELLOW
    return RED


def human_int(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "0"
    if abs(n) >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def _to_datetime(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def seconds_until(value, now=None):
    """Segundos até `value` (ISO8601 ou epoch); negativo se já passou. None se
    a data for inválida ou ausente."""
    dt = _to_datetime(value)
    if dt is None:
        return None
    return int((dt - (now or datetime.now(timezone.utc))).total_seconds())


def humanize_delta(secs):
    """Duração curta em pt-BR: '2d 20h', '3h 30m' ou '12m'."""
    days, rem = divmod(max(int(secs), 0), 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def relative_reset(value, now=None):
    secs = seconds_until(value, now)
    if secs is None:
        return ""
    if secs <= 0:
        return "reset agora"
    return f"reset em {humanize_delta(secs)}"


def extract_env_value(text, name):
    """Valor de `NAME=valor` (ou `export NAME=valor`) num texto de env. As
    aspas externas são removidas. Retorna None se não encontrar."""
    match = re.search(rf"^\s*(?:export\s+)?{re.escape(name)}=(.*)$", text, re.M)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def env_var(name):
    """Valor da variável de ambiente; se ausente (ex.: processo sem o env do
    shell, como a polybar), procura em ENV_FILES."""
    val = os.environ.get(name)
    if val:
        return val
    for path in ENV_FILES:
        try:
            with open(path, encoding="utf-8") as f:
                found = extract_env_value(f.read(), name)
        except OSError:
            continue
        if found:
            return found
    return None


# ---------------------------------------------------------------- Parsers
def _err(msg):
    return {"ok": False, "error": msg, "bars": [], "info": []}


def parse_claude_usage(payload):
    bars = []
    for key, label in (("five_hour", "Atual (5h)"), ("seven_day", "Semanal")):
        win = payload.get(key) or {}
        if win:
            bars.append({
                "label": label,
                "percent": float(win.get("utilization") or 0),
                "resets_at": win.get("resets_at"),
            })
    return {"ok": True, "error": None, "bars": bars, "info": []}


def parse_codex_usage(payload):
    """Resposta de https://chatgpt.com/backend-api/wham/usage.

    `rate_limit.primary_window` (janela de 5h) e `secondary_window` (semanal)
    trazem `used_percent` + `reset_at` (epoch). Igual ao que o próprio Codex usa.
    """
    rate = payload.get("rate_limit") or {}
    bars = []
    for key, label in (("primary_window", "Atual (5h)"), ("secondary_window", "Semanal")):
        win = rate.get(key)
        if win:
            bars.append({
                "label": label,
                "percent": float(win.get("used_percent") or 0),
                "resets_at": win.get("reset_at"),
            })
    info = []
    plan = payload.get("plan_type")
    if plan:
        info.append(f"Plano: {plan}")
    # Sem janelas (ex.: conta só por créditos): mostra um estado honesto.
    if not bars:
        credits = payload.get("credits") or {}
        if credits.get("unlimited"):
            info.append("Uso ilimitado")
        elif credits.get("has_credits"):
            info.append(f"Créditos: {credits.get('balance', '?')}")
        else:
            info.append("Sem limites de janela")
    return {"ok": True, "error": None, "bars": bars, "info": info}


def parse_openrouter_credits(payload):
    data = payload.get("data") or {}
    total = float(data.get("total_credits") or 0)
    used = float(data.get("total_usage") or 0)
    available = total - used
    percent = (used / total * 100) if total else 0.0
    return {
        "ok": True,
        "error": None,
        "bars": [{"label": "Créditos usados", "percent": percent, "resets_at": None}],
        "info": [f"Disponível: ${available:.2f} de ${total:.2f}"],
    }


# ---------------------------------------------------------------- Coletores de IO
def _http_get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def claude_last_request_line():
    try:
        files = glob.glob(os.path.join(CLAUDE_PROJECTS, "*", "*.jsonl"))
        if not files:
            return None
        newest = max(files, key=os.path.getmtime)
        usage = None
        with open(newest, encoding="utf-8") as f:
            for line in f:
                if '"assistant"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                found = (obj.get("message") or {}).get("usage")
                if found:
                    usage = found
        if not usage:
            return None
        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        cache = (usage.get("cache_read_input_tokens", 0)
                 + usage.get("cache_creation_input_tokens", 0))
        return (f"Última request: {human_int(inp)} in / {human_int(out)} out "
                f"(+{human_int(cache)} cache)")
    except OSError:
        return None


def collect_claude():
    try:
        with open(CLAUDE_CREDENTIALS, encoding="utf-8") as f:
            token = json.load(f)["claudeAiOauth"]["accessToken"]
    except (OSError, KeyError, json.JSONDecodeError):
        return _err("credenciais do Claude não encontradas")
    try:
        payload = _http_get_json(
            "https://api.anthropic.com/api/oauth/usage",
            {"Authorization": f"Bearer {token}",
             "anthropic-beta": "oauth-2025-04-20",
             "User-Agent": "polybar-ai-usage"})
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return _err("token expirado — rode o Claude Code")
        return _err(f"erro HTTP {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError):
        return _err("sem conexão")
    result = parse_claude_usage(payload)
    line = claude_last_request_line()
    if line:
        result["info"].append(line)
    return result


def collect_codex():
    try:
        with open(CODEX_AUTH, encoding="utf-8") as f:
            tokens = json.load(f)["tokens"]
        token = tokens["access_token"]
    except (OSError, KeyError, json.JSONDecodeError):
        return _err("credenciais do Codex não encontradas")
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "codex-cli"}
    account_id = tokens.get("account_id")
    if account_id:
        headers["ChatGPT-Account-Id"] = account_id
    try:
        payload = _http_get_json(CODEX_USAGE_URL, headers)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return _err("token expirado — rode o codex")
        return _err(f"erro HTTP {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError):
        return _err("sem conexão")
    return parse_codex_usage(payload)


def collect_openrouter():
    key = env_var("OPENROUTER_API_KEY")
    if not key:
        return _err("sem OPENROUTER_API_KEY")
    try:
        payload = _http_get_json(
            "https://openrouter.ai/api/v1/credits",
            {"Authorization": f"Bearer {key}", "User-Agent": "polybar-ai-usage"})
    except urllib.error.HTTPError as exc:
        return _err(f"erro HTTP {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError):
        return _err("sem conexão")
    return parse_openrouter_credits(payload)


PROVIDERS = [
    ("Anthropic", collect_claude),
    ("OpenAI", collect_codex),
    ("OpenRouter", collect_openrouter),
]


def cmd_fetch():
    data = {"updated_at": time.time(), "providers": {}}
    for name, fn in PROVIDERS:
        try:
            data["providers"][name] = fn()
        except Exception as exc:  # fronteira de resiliência: 1 provider nunca derruba os outros
            data["providers"][name] = _err(f"erro: {exc}")
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, CACHE)
    return data


def read_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------- Poll
def worst_percent(data):
    worst = None
    for name, prov in data.get("providers", {}).items():
        if name in COLOR_EXCLUDED_PROVIDERS or not prov.get("ok"):
            continue
        for bar in prov.get("bars", []):
            pct = bar.get("percent", 0)
            if worst is None or pct > worst:
                worst = pct
    return worst


def cmd_poll():
    data = cmd_fetch()
    worst = worst_percent(data)
    color = FG if worst is None else severity_color(worst)
    sys.stdout.write(f"%{{F{color}}}{ROBOT}%{{F-}}\n")


# ---------------------------------------------------------------- Modal
def _notify(msg):
    """Aviso ao usuário (best-effort) quando o modal não pode abrir."""
    try:
        subprocess.run(["notify-send", "AI Usage", msg], check=False)
    except OSError:
        sys.stderr.write(msg + "\n")


def _reexec_with_tkinter():
    """Garante um interpretador com tkinter para o modal.

    A polybar roda o script com o python do sistema, que pode não ter tkinter.
    Se faltar, re-executa com um Python do pyenv que o tenha — sem precisar
    instalar nenhuma dependência (mantém o script standalone).
    """
    try:
        import tkinter  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get("AI_USAGE_REEXEC"):
        return  # evita loop; deixa o ImportError aparecer e ser tratado
    for py in sorted(glob.glob(os.path.expanduser("~/.pyenv/versions/*/bin/python3")),
                     reverse=True):
        try:
            subprocess.run([py, "-c", "import tkinter"], check=True,
                           capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            continue
        env = dict(os.environ, AI_USAGE_REEXEC="1")
        os.execve(py, [py, os.path.abspath(__file__), *sys.argv[1:]], env)


def cmd_show():
    _reexec_with_tkinter()  # troca para um Python com tkinter, se necessário
    # Toggle: se o modal já está aberto, fecha e sai.
    if os.path.exists(PIDFILE):
        try:
            pid = int(open(PIDFILE, encoding="utf-8").read().strip())
            os.kill(pid, signal.SIGTERM)
        except (ValueError, ProcessLookupError, OSError):
            pass
        try:
            os.remove(PIDFILE)
        except OSError:
            pass
        return
    data = read_cache() or cmd_fetch()
    with open(PIDFILE, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    try:
        run_modal(data)
    except ImportError:
        _notify("tkinter indisponível — instale python3-tk ou um Python (pyenv) com tkinter")
    finally:
        try:
            os.remove(PIDFILE)
        except OSError:
            pass


def parse_monitor_geometry(xrandr_output, name):
    """Extrai (x, y, w, h) do monitor `name` da saída de `xrandr --query`.

    Se `name` não for encontrado, cai para o monitor marcado como 'primary'.
    Retorna None se nada casar.
    """
    primary = None
    target = None
    for line in xrandr_output.splitlines():
        if " connected" not in line:
            continue
        match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
        if not match:
            continue
        w, h, x, y = (int(g) for g in match.groups())
        geo = (x, y, w, h)
        if line.split()[0] == name:
            target = geo
        if "primary" in line:
            primary = geo
    return target or primary


def target_monitor_geometry():
    """Geometria do monitor da barra (DP-1) via xrandr, ou None se indisponível."""
    try:
        out = subprocess.run(["xrandr", "--query"], capture_output=True,
                             text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return parse_monitor_geometry(out, MONITOR_NAME)


def right_aligned_x(mon_x, mon_w, win_w, margin):
    """X (canto superior esquerdo da janela) para ancorar pela borda direita
    do monitor, deixando `margin` px de folga."""
    return mon_x + mon_w - win_w - margin


def run_modal(data):
    import tkinter as tk

    state = {"data": data}
    root = tk.Tk()
    root.title("AI Usage")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg=BG)
    geo = target_monitor_geometry()

    def position():
        """Ancla o modal no canto superior DIREITO do monitor da barra (DP-1),
        na mesma altura (logo abaixo da polybar)."""
        root.update_idletasks()
        win_w = root.winfo_reqwidth()
        if geo:
            mon_x, mon_y, mon_w, _h = geo
            pos_x = right_aligned_x(mon_x, mon_w, win_w, MODAL_MARGIN_X)
            pos_y = mon_y + MODAL_MARGIN_Y
        else:
            pos_x = right_aligned_x(0, root.winfo_screenwidth(), win_w, MODAL_MARGIN_X)
            pos_y = MODAL_MARGIN_Y
        root.geometry(f"+{pos_x}+{pos_y}")

    root.bind("<Escape>", lambda _e: root.destroy())

    container = tk.Frame(root, bg=BG, padx=12, pady=10)
    container.pack(fill="both", expand=True)

    def draw_bar(parent, bar):
        pct = max(0.0, min(100.0, float(bar.get("percent", 0))))
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=1)
        top = f"  {bar.get('label', '')}: {pct:.0f}%"
        reset = relative_reset(bar.get("resets_at")) if bar.get("resets_at") else ""
        if reset:
            top += f"  ·  {reset}"
        tk.Label(row, text=top, bg=BG, fg=FG,
                 font=("Hack Nerd Font", 9), anchor="w").pack(fill="x")
        canvas = tk.Canvas(row, height=8, width=260, bg=BG_ALT, highlightthickness=0)
        canvas.pack(anchor="w", padx=(8, 0))
        canvas.create_rectangle(0, 0, 260 * pct / 100, 8,
                                fill=severity_color(pct), outline="")

    def render():
        for widget in container.winfo_children():
            widget.destroy()
        current = state["data"]
        header = tk.Frame(container, bg=BG)
        header.pack(anchor="w", pady=(0, 8))
        # ícone na fonte FA Solid (Hack Nerd Font não tem o glifo do robô)
        tk.Label(header, text=ROBOT, bg=BG, fg=FG,
                 font=(ICON_FONT, 12, "bold")).pack(side="left")
        tk.Label(header, text="  Utilização de IA", bg=BG, fg=FG,
                 font=("Hack Nerd Font", 12, "bold")).pack(side="left")
        for name, _fn in PROVIDERS:
            prov = current.get("providers", {}).get(name) or _err("sem dados")
            card = tk.Frame(container, bg=BG)
            card.pack(fill="x", pady=4)
            tk.Label(card, text=name, bg=BG, fg=FG_DIM,
                     font=("Hack Nerd Font", 10, "bold")).pack(anchor="w")
            if not prov.get("ok"):
                tk.Label(card, text=f"  {prov.get('error', 'erro')}", bg=BG, fg=RED,
                         font=("Hack Nerd Font", 9)).pack(anchor="w")
                continue
            for bar in prov.get("bars", []):
                draw_bar(card, bar)
            for line in prov.get("info", []):
                tk.Label(card, text=f"  {line}", bg=BG, fg=FG_DIM,
                         font=("Hack Nerd Font", 9)).pack(anchor="w")
        footer = tk.Frame(container, bg=BG)
        footer.pack(fill="x", pady=(8, 0))
        updated = current.get("updated_at")
        ago = ""
        if updated:
            mins = int((time.time() - updated) / 60)
            ago = "atualizado agora" if mins <= 0 else f"atualizado há {mins} min"
        tk.Label(footer, text=ago, bg=BG, fg=FG_DIM,
                 font=("Hack Nerd Font", 8)).pack(side="left")
        tk.Button(footer, text="↻ Refresh", command=refresh, bg=BG_ALT, fg=FG,
                  relief="flat", font=("Hack Nerd Font", 9),
                  activebackground=YELLOW, activeforeground=BG).pack(side="right")

    def refresh():
        state["data"] = cmd_fetch()
        render()
        position()

    render()
    position()
    root.mainloop()


# ---------------------------------------------------------------- Dispatch
def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "poll"
    if cmd == "poll":
        cmd_poll()
    elif cmd == "fetch":
        cmd_fetch()
    elif cmd == "show":
        cmd_show()
    else:
        sys.stderr.write("uso: ai-usage.py [poll|fetch|show]\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
