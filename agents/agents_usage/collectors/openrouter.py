"""OpenRouter: saldo pré-pago pelo endpoint /credits."""
import urllib.error

from .. import common

CREDITS_URL = "https://openrouter.ai/api/v1/credits"


def parse_credits(payload):
    data = payload.get("data") or {}
    total = float(data.get("total_credits") or 0)
    used = float(data.get("total_usage") or 0)
    return {"remaining": round(total - used, 4), "total": total, "currency": "USD"}


def collect(account, now=None, fetch=common.http_get_json, key=None):
    key = key or common.env_var("OPENROUTER_API_KEY")
    if not key:
        return {"status": common.NOT_CONFIGURED, "error": "sem OPENROUTER_API_KEY"}
    try:
        payload = fetch(CREDITS_URL, {"Authorization": f"Bearer {key}"})
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return {"status": common.SIGNIN_REQUIRED, "error": "chave inválida"}
        return {"status": common.ERROR, "error": f"HTTP {exc.code}"}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"status": common.OFFLINE, "error": "sem conexão"}
    return {"status": common.OK, "error": None, "plan": "prepaid",
            "balance": parse_credits(payload)}
