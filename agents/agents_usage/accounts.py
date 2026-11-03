"""Registro de contas por provider.

A conta "main" é o login que já existe em ~/.claude ou ~/.codex e nunca é
movida nem apagada. Contas extras vivem em <data_dir>/accounts/<provider>/<id>/
e são selecionadas via CLAUDE_CONFIG_DIR / CODEX_HOME pelos shims em
agents/shims, que leem o ponteiro <data_dir>/active-<provider>.
Histórico, settings, skills e plugins são symlinks para a conta main; só as
credenciais são próprias de cada conta.
"""
import os
import re
import shutil

from . import common

MULTI_ACCOUNT_PROVIDERS = ("claude", "codex")
MAIN_HOMES = {
    "claude": os.path.join(common.HOME, ".claude"),
    "codex": os.path.join(common.HOME, ".codex"),
}
HOME_ENV = {"claude": "CLAUDE_CONFIG_DIR", "codex": "CODEX_HOME"}
SHARED_ENTRIES = {
    "claude": ("projects", "history.jsonl", "settings.json", "CLAUDE.md", "RTK.md", "agents",
               "commands", "skills", "plugins", "hooks", "rules", "themes", "plans", "todos",
               "file-history", "statusline-command.sh", "file-suggestion.sh"),
    "codex": ("config.toml", "AGENTS.md", "sessions", "history.jsonl", "session_index.jsonl",
              "prompts", "skills", "plugins", "memories", "hooks.json"),
}
# Com CLAUDE_CONFIG_DIR o Claude lê os MCP servers de <dir>/.claude.json em vez de ~/.claude.json.
CLAUDE_MAIN_STATE = os.path.join(common.HOME, ".claude.json")
DEFAULT_THRESHOLD = 95


class AccountError(Exception):
    pass


def registry_file(data_dir=None):
    return os.path.join(data_dir or common.DATA_DIR, "accounts.json")


def pointer_file(provider, data_dir=None):
    return os.path.join(data_dir or common.DATA_DIR, f"active-{provider}")


def accounts_root(provider, data_dir=None):
    return os.path.join(data_dir or common.DATA_DIR, "accounts", provider)


def _main_account(provider):
    return {"id": "main", "label": "Main", "home": MAIN_HOMES[provider]}


def load_registry(path=None):
    data = common.read_json(path or registry_file(), {}) or {}
    data.setdefault("default_provider", "claude")
    for provider in MULTI_ACCOUNT_PROVIDERS:
        entry = data.get(provider) or {}
        entry.setdefault("active", "main")
        entry.setdefault("mode", "notify")
        entry.setdefault("threshold", DEFAULT_THRESHOLD)
        accs = entry.setdefault("accounts", [])
        if not any(a.get("id") == "main" for a in accs):
            accs.insert(0, _main_account(provider))
        data[provider] = entry
    return data


def save_registry(registry, data_dir=None):
    common.write_json_atomic(registry_file(data_dir), registry)


def accounts_for(provider, registry=None):
    registry = registry or load_registry()
    entry = registry[provider]
    active = entry.get("active", "main")
    return [{**acc, "provider": provider, "active": acc["id"] == active}
            for acc in entry["accounts"]]


def find_account(registry, provider, ref):
    """Por id, label (case-insensitive) ou posição 1-based."""
    accs = registry[provider]["accounts"]
    ref = str(ref).strip()
    if ref.isdigit() and 1 <= int(ref) <= len(accs):
        return accs[int(ref) - 1]
    for acc in accs:
        if ref.lower() in (acc["id"], acc.get("label", "").lower()):
            return acc
    raise AccountError(f"conta '{ref}' não encontrada em {provider}")


def slugify(label):
    slug = re.sub(r"[^a-z0-9]+", "-", label.strip().lower()).strip("-")
    if not slug:
        raise AccountError("nome de conta inválido")
    return slug


def _link_shared(provider, home):
    main = MAIN_HOMES[provider]
    for name in SHARED_ENTRIES[provider]:
        src, dst = os.path.join(main, name), os.path.join(home, name)
        if os.path.lexists(src) and not os.path.lexists(dst):
            os.symlink(src, dst)


def _copy_claude_mcp(home, main_state=None):
    state = common.read_json(main_state or CLAUDE_MAIN_STATE, {}) or {}
    servers = state.get("mcpServers")
    if servers:
        common.write_json_atomic(os.path.join(home, ".claude.json"), {"mcpServers": servers})


def add_account(provider, label, data_dir=None, main_state=None):
    registry = load_registry(registry_file(data_dir))
    account_id = slugify(label)
    if any(a["id"] == account_id for a in registry[provider]["accounts"]):
        raise AccountError(f"já existe a conta '{account_id}' em {provider}")
    home = os.path.join(accounts_root(provider, data_dir), account_id)
    os.makedirs(home, mode=0o700)
    _link_shared(provider, home)
    if provider == "claude":
        _copy_claude_mcp(home, main_state)
    account = {"id": account_id, "label": label.strip(), "home": home}
    registry[provider]["accounts"].append(account)
    save_registry(registry, data_dir)
    return account


def _write_pointer(provider, account, data_dir=None):
    path = pointer_file(provider, data_dir)
    if account["id"] == "main":
        if os.path.lexists(path):
            os.remove(path)
        return
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(account["home"] + "\n")
    os.replace(tmp, path)


def use_account(provider, ref, data_dir=None):
    registry = load_registry(registry_file(data_dir))
    account = find_account(registry, provider, ref)
    registry[provider]["active"] = account["id"]
    save_registry(registry, data_dir)
    _write_pointer(provider, account, data_dir)
    return account


def rename_account(provider, ref, label, data_dir=None):
    registry = load_registry(registry_file(data_dir))
    account = find_account(registry, provider, ref)
    if not label.strip():
        raise AccountError("nome de conta inválido")
    account["label"] = label.strip()  # o id fica estável: é o que os comandos usam
    save_registry(registry, data_dir)
    return account


def remove_account(provider, ref, data_dir=None):
    registry = load_registry(registry_file(data_dir))
    account = find_account(registry, provider, ref)
    if account["id"] == "main":
        raise AccountError("a conta main não pode ser removida")
    root = os.path.realpath(accounts_root(provider, data_dir))
    home = os.path.realpath(account["home"])
    # Só apaga o que este módulo criou; rmtree não segue os symlinks do histórico compartilhado.
    if os.path.dirname(home) != root:
        raise AccountError(f"recusando apagar diretório fora de {root}: {home}")
    registry[provider]["accounts"].remove(account)
    if registry[provider]["active"] == account["id"]:
        registry[provider]["active"] = "main"
        _write_pointer(provider, _main_account(provider), data_dir)
    save_registry(registry, data_dir)
    if os.path.isdir(home):
        shutil.rmtree(home)
    return account


def set_mode(provider, mode, threshold=None, data_dir=None):
    if mode not in ("auto", "notify"):
        raise AccountError("modo deve ser 'auto' ou 'notify'")
    if threshold is not None and not 1 <= threshold <= 100:
        raise AccountError("threshold deve estar entre 1 e 100")
    registry = load_registry(registry_file(data_dir))
    registry[provider]["mode"] = mode
    if threshold is not None:
        registry[provider]["threshold"] = threshold
    save_registry(registry, data_dir)
    return registry[provider]


def login_command(provider, account, browser=None):
    """(argv, env) para autenticar a conta no CLI real. Contas extras usam um
    navegador privado para não reaproveitar a sessão já logada."""
    env = dict(os.environ)
    if account["id"] != "main":
        env[HOME_ENV[provider]] = account["home"]
        if browser:
            env["BROWSER"] = browser
    else:
        env.pop(HOME_ENV[provider], None)
    argv = ["claude", "auth", "login"] if provider == "claude" else ["codex", "login"]
    return argv, env
