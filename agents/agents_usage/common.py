"""Helpers compartilhados: caminhos, HTTP, env, escrita atômica e ritmo de uso."""
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
STATE_DIR = os.path.join(
    os.environ.get("XDG_STATE_HOME", os.path.join(HOME, ".local", "state")), "agents")
DATA_DIR = os.path.join(
    os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share")), "agents")
USAGE_FILE = os.path.join(STATE_DIR, "usage.json")
TOKENS_CACHE_FILE = os.path.join(STATE_DIR, "tokens-cache.json")

HTTP_TIMEOUT = 8
USER_AGENT = "agents-usage"
# A polybar/systemd não herdam o env do shell interativo; variáveis sensíveis
# também são procuradas nestes arquivos.
ENV_FILES = [os.path.join(HOME, ".use.env"), os.path.join(HOME, ".user.env")]

SESSION_WINDOW = 5 * 3600
WEEKLY_WINDOW = 7 * 24 * 3600

# Status de um registro de conta
OK = "ok"
SIGNIN_REQUIRED = "signin_required"
OFFLINE = "offline"
ERROR = "error"
NOT_CONFIGURED = "not_configured"


def http_get_json(url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def write_json_atomic(path, data, mode=0o600):
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def extract_env_value(text, name):
    """Valor de `NAME=valor` (ou `export NAME=valor`), sem aspas externas.
    A última atribuição vence, como ao fazer `source` do arquivo."""
    matches = re.findall(rf"^\s*(?:export\s+)?{re.escape(name)}=(.*)$", text, re.M)
    if not matches:
        return None
    return matches[-1].strip().strip('"').strip("'")


def env_var(name, env_files=None):
    val = os.environ.get(name)
    if val:
        return val
    for path in ENV_FILES if env_files is None else env_files:
        try:
            with open(path, encoding="utf-8") as f:
                found = extract_env_value(f.read(), name)
        except OSError:
            continue
        if found:
            return found
    return None


def to_epoch(value):
    """ISO 8601 ou epoch (s/ms) -> epoch em segundos (float). None se inválido."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value) / 1000 if value > 1e12 else float(value)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def make_limit(limit_id, label, percent, resets_at, window_seconds):
    return {
        "id": limit_id,
        "label": label,
        "percent": max(0.0, float(percent or 0)),
        "resets_at": to_epoch(resets_at),
        "window_seconds": window_seconds,
    }


def pace(limit, now=None):
    """Razão uso/tempo decorrido da janela: >1 = consumindo mais rápido que o
    ritmo que esgota exatamente no reset. None sem dados de janela."""
    now = time.time() if now is None else now
    resets_at, window = limit.get("resets_at"), limit.get("window_seconds")
    if not resets_at or not window:
        return None
    elapsed = window - max(0.0, resets_at - now)
    elapsed_frac = min(1.0, max(0.0, elapsed / window))
    if elapsed_frac < 0.05:  # início da janela: ritmo ainda não significa nada
        return None
    return (limit["percent"] / 100) / elapsed_frac


def severity(limit, now=None):
    """'low' | 'medium' | 'high' por percentual absoluto e ritmo."""
    percent = limit.get("percent", 0)
    ratio = pace(limit, now)
    if percent >= 90 or (ratio is not None and ratio >= 1.25 and percent >= 50):
        return "high"
    if percent >= 70 or (ratio is not None and ratio >= 1.0 and percent >= 25):
        return "medium"
    return "low"
