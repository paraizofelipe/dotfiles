"""Claude Code: limites de 5h/semanal pelo endpoint OAuth de uso."""
import os
import time
import urllib.error

from .. import common

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
LIMITS = (
    ("five_hour", "session", "5h", common.SESSION_WINDOW),
    ("seven_day", "weekly", "Semanal", common.WEEKLY_WINDOW),
)


def parse_usage(payload):
    limits = []
    for key, limit_id, label, window in LIMITS:
        win = payload.get(key) or {}
        if win:
            limits.append(common.make_limit(
                limit_id, label, win.get("utilization"), win.get("resets_at"), window))
    return limits + parse_scoped_limits(payload.get("limits"))


def _scope_name(scope):
    data = scope if isinstance(scope, dict) else {}
    model = data.get("model")
    model = model if isinstance(model, dict) else {}
    surface = data.get("surface")
    if isinstance(surface, dict):
        surface = surface.get("display_name")
    return model.get("display_name") or model.get("id") or surface or None


def parse_scoped_limits(items):
    """Limites semanais por modelo/superfície (ex.: Fable) da lista `limits`.
    Formato não documentado: qualquer item inesperado é ignorado."""
    scoped = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or item.get("kind") != "weekly_scoped":
            continue
        if not isinstance(item.get("percent"), (int, float)):
            continue
        name = _scope_name(item.get("scope"))
        slug = "".join(c if c.isalnum() else "-" for c in (name or "scoped").lower()).strip("-")
        scoped.append(common.make_limit(
            f"weekly_{slug}", name or "Escopo", item["percent"], item.get("resets_at"),
            common.WEEKLY_WINDOW))
    return scoped


def read_credentials(home):
    """OAuth do CLI ou None. Só leitura: o refresh do token é feito pelo próprio CLI."""
    creds = common.read_json(os.path.join(home, ".credentials.json"))
    oauth = (creds or {}).get("claudeAiOauth") or {}
    return oauth if oauth.get("accessToken") else None


def collect(account, now=None, fetch=common.http_get_json):
    now = time.time() if now is None else now
    oauth = read_credentials(account["home"])
    if oauth is None:
        return {"status": common.SIGNIN_REQUIRED, "error": "credenciais não encontradas"}
    result = {"plan": oauth.get("subscriptionType")}
    expires = common.to_epoch(oauth.get("expiresAt"))
    if expires is not None and expires < now:
        return {**result, "status": common.SIGNIN_REQUIRED, "error": "sessão expirada"}
    try:
        payload = fetch(USAGE_URL, {
            "Authorization": f"Bearer {oauth['accessToken']}",
            "anthropic-beta": "oauth-2025-04-20",
        })
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return {**result, "status": common.SIGNIN_REQUIRED, "error": "sessão expirada"}
        return {**result, "status": common.ERROR, "error": f"HTTP {exc.code}"}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {**result, "status": common.OFFLINE, "error": "sem conexão"}
    return {**result, "status": common.OK, "error": None, "limits": parse_usage(payload)}
