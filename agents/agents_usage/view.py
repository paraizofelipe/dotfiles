"""View model do painel e do ícone da barra: transforma usage.json + registro
em textos e cores prontos. Sem Qt, para ser testável e reaproveitado pelo polybar."""
import time

from . import accounts, common

COLORS = {"low": "#b8bb26", "medium": "#fabd2f", "high": "#fb4934", "none": "#a89984"}
STATUS_TEXT = {
    common.OK: "",
    common.SIGNIN_REQUIRED: "Sign-in required",
    common.OFFLINE: "Sem conexão",
    common.ERROR: "Erro ao consultar",
    common.NOT_CONFIGURED: "Não configurado",
}
STALE_AFTER = 30 * 60
SEVERITY_ORDER = ("none", "low", "medium", "high")


def human_tokens(n):
    n = float(n or 0)
    for unit, size in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if abs(n) >= size:
            return f"{n / size:.1f}".replace(".", ",").removesuffix(",0") + unit
    return f"{n:.0f}"


def money(value, currency="USD"):
    if value is None:
        return "?"
    text = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"US$ {text}" if currency == "USD" else f"{text} créditos"


def duration(secs):
    secs = max(0, int(secs))
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def ago(ts, now):
    secs = now - ts
    if secs < 60:
        return "agora"
    return f"há {duration(secs)}"


def meter(limit, now):
    sev = common.severity(limit, now)
    ratio = common.pace(limit, now)
    reset = limit.get("resets_at")
    return {
        "id": limit["id"],
        "label": limit["label"],
        "percent": round(limit["percent"], 1),
        "fraction": min(1.0, limit["percent"] / 100),
        "percent_text": f"{limit['percent']:.0f}%",
        "reset_text": f"reseta em {duration(reset - now)}" if reset else "",
        "pace_text": (f"ritmo {ratio:.1f}× do ideal" if ratio is not None else "ritmo: início da janela"),
        "severity": sev,
        "color": COLORS[sev],
    }


def account_view(index, acc, record, now):
    record = record or {}
    status = record.get("status")
    limits = record.get("limits") or []
    balance = record.get("balance")
    balance_view = None
    if balance:
        total = balance.get("total")
        remaining = balance.get("remaining") or 0
        balance_view = {
            "text": (f"{money(remaining, balance.get('currency'))} de {money(total)}" if total
                     else money(remaining, balance.get("currency"))),
            # total desconhecido (créditos avulsos): barra cheia; total zero: barra vazia
            "fraction": (1.0 if total is None else
                         min(1.0, max(0.0, remaining / total)) if total else 0.0),
        }
    status_text = STATUS_TEXT.get(status, "Aguardando atualização") if status else "Aguardando atualização"
    if record.get("stale"):
        status_text = f"{status_text} · últimos dados {ago(record.get('updated_at', now), now)}"
    return {
        "id": acc["id"],
        "label": acc.get("label", acc["id"]),
        "index": index,
        "active": acc.get("active", False),
        "plan": (record.get("plan") or "").upper(),
        "status": status or "pending",
        "status_text": status_text,
        "needs_signin": status == common.SIGNIN_REQUIRED,
        "meters": [meter(lim, now) for lim in limits],
        "balance": balance_view,
    }


def ticker(token_stats, records, now=None):
    lines = []
    total = sum((s.get("week") or {}).get("total", 0) for s in token_stats.values() if isinstance(s, dict))
    if total:
        lines.append(f"{human_tokens(total)} tokens nos últimos 7 dias")
    tops = [(s.get("by_model") or {}) for s in token_stats.values() if isinstance(s, dict)]
    merged = {}
    for by_model in tops:
        for model, n in by_model.items():
            merged[model] = merged.get(model, 0) + n
    if merged:
        model = max(merged, key=merged.__getitem__)
        lines.append(f"Modelo mais usado: {model} ({human_tokens(merged[model])})")
    today = time.strftime("%Y-%m-%d", time.localtime(now))
    today_total = sum((s.get("by_day") or {}).get(today, 0) for s in token_stats.values() if isinstance(s, dict))
    if today_total:
        lines.append(f"Hoje: {human_tokens(today_total)} tokens")
    for name, stats in token_stats.items():
        if isinstance(stats, dict) and (stats.get("week") or {}).get("total"):
            lines.append(f"{name.title()}: {human_tokens(stats['week']['total'])} tokens na semana")
    balances = [r for r in records if r.get("balance")]
    for r in balances:
        lines.append(f"{r['provider_name']}: {money(r['balance']['remaining'], r['balance'].get('currency'))} restantes")
    return lines or ["Sem uso registrado nos últimos 7 dias"]


def worst(records, registry, now=None):
    """Pior meter entre as contas ativas: alimenta a cor do ícone da barra.
    Registros stale ficam de fora: o ritmo de um percentual congelado cai com o
    tempo e pintaria a barra com uma severidade que ninguém mediu."""
    best = {"percent": None, "severity": "none", "color": COLORS["none"], "provider": None}
    for r in records:
        if r["provider"] in accounts.MULTI_ACCOUNT_PROVIDERS:
            if r["account"] != registry[r["provider"]].get("active", "main"):
                continue
        if r.get("stale"):
            continue
        for lim in r.get("limits") or []:
            sev = common.severity(lim, now)
            if (SEVERITY_ORDER.index(sev) > SEVERITY_ORDER.index(best["severity"])
                    or (sev == best["severity"] and lim["percent"] > (best["percent"] or -1))):
                best = {"percent": lim["percent"], "severity": sev, "color": COLORS[sev],
                        "provider": r["provider"]}
    return best


def build(usage, registry, now=None):
    now = time.time() if now is None else now
    usage = usage or {}
    records = usage.get("accounts", [])
    by_key = {(r["provider"], r["account"]): r for r in records}
    providers = []
    for provider in accounts.MULTI_ACCOUNT_PROVIDERS:
        entry = registry[provider]
        accs = accounts.accounts_for(provider, registry)
        providers.append({
            "id": provider,
            "name": {"claude": "Claude Code", "codex": "Codex"}[provider],
            "multi": True,
            "mode": entry.get("mode", "notify"),
            "threshold": entry.get("threshold", accounts.DEFAULT_THRESHOLD),
            "accounts": [account_view(i, a, by_key.get((provider, a["id"])), now)
                         for i, a in enumerate(accs, 1)],
        })
    openrouter = by_key.get(("openrouter", "main"))
    if openrouter and openrouter.get("status") != common.NOT_CONFIGURED:
        providers.append({"id": "openrouter", "name": "OpenRouter", "multi": False, "mode": "",
                          "threshold": 0, "accounts": [account_view(
                              1, {"id": "main", "label": "Pré-pago", "active": True},
                              {**openrouter, "plan": None}, now)]})
    # Atalho de teclado global (1, 2, 3...) para as contas que podem virar ativas.
    key = 0
    for prov in providers:
        for acc in prov["accounts"]:
            if prov["multi"]:
                key += 1
            acc["key"] = key if prov["multi"] else 0
    updated = usage.get("updated_at")
    return {
        "updated_text": f"Atualizado {ago(updated, now)}" if updated else "Nunca atualizado",
        "outdated": bool(updated is None or now - updated > STALE_AFTER),
        "ticker": ticker(usage.get("tokens") or {}, records, now),
        "providers": providers,
        "worst": worst(records, registry, now),
    }
