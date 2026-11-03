"""Codex: limites de 5h/semanal pelo endpoint wham/usage do ChatGPT."""
import os
import urllib.error

from .. import common

USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
LIMITS = (
    ("primary_window", "session", "5h", common.SESSION_WINDOW),
    ("secondary_window", "weekly", "Semanal", common.WEEKLY_WINDOW),
)


def parse_usage(payload):
    rate = payload.get("rate_limit") or {}
    limits = []
    for key, limit_id, label, window in LIMITS:
        win = rate.get(key)
        if win:
            limits.append(common.make_limit(
                limit_id, label, win.get("used_percent"), win.get("reset_at"),
                win.get("limit_window_seconds") or window))
    balance = None
    credits = payload.get("credits") or {}
    raw = credits.get("balance")
    if not limits and credits.get("has_credits") and not credits.get("unlimited") and raw is not None:
        try:
            balance = {"remaining": float(raw), "total": None, "currency": "credits"}
        except (TypeError, ValueError):
            balance = None
    return {"plan": payload.get("plan_type"), "limits": limits, "balance": balance}


def collect(account, now=None, fetch=common.http_get_json):
    auth = common.read_json(os.path.join(account["home"], "auth.json"))
    tokens = (auth or {}).get("tokens") or {}
    if not tokens.get("access_token"):
        return {"status": common.SIGNIN_REQUIRED, "error": "credenciais não encontradas"}
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    if tokens.get("account_id"):
        headers["ChatGPT-Account-Id"] = tokens["account_id"]
    try:
        payload = fetch(USAGE_URL, headers)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return {"status": common.SIGNIN_REQUIRED, "error": "sessão expirada"}
        return {"status": common.ERROR, "error": f"HTTP {exc.code}"}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"status": common.OFFLINE, "error": "sem conexão"}
    return {"status": common.OK, "error": None, **parse_usage(payload)}
