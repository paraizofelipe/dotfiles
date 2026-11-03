"""`agents usage-update`: coleta todas as contas e grava USAGE_FILE atomicamente."""
import time

from . import accounts, common, tokens
from .collectors import claude, codex, openrouter

COLLECTORS = {"claude": claude.collect, "codex": codex.collect, "openrouter": openrouter.collect}
PROVIDER_NAMES = {"claude": "Claude Code", "codex": "Codex", "openrouter": "OpenRouter"}


def all_accounts(registry):
    found = []
    for provider in accounts.MULTI_ACCOUNT_PROVIDERS:
        found.extend(accounts.accounts_for(provider, registry))
    found.append({"provider": "openrouter", "id": "main", "label": "Main", "active": True})
    return found


def build_record(account, result, previous, now):
    record = {
        "provider": account["provider"],
        "provider_name": PROVIDER_NAMES[account["provider"]],
        "account": account["id"],
        "label": account.get("label", account["id"]),
        "active": account.get("active", False),
        "status": result.get("status", common.ERROR),
        "error": result.get("error"),
        "plan": result.get("plan"),
        "limits": result.get("limits") or [],
        "balance": result.get("balance"),
        "updated_at": now,
        "stale": False,
    }
    # Offline/erro transitório: mantém os últimos números bons em vez de zerar a barra.
    if record["status"] in (common.OFFLINE, common.ERROR) and previous:
        if previous.get("limits") or previous.get("balance"):
            record.update(limits=previous.get("limits") or [], balance=previous.get("balance"),
                          plan=record["plan"] or previous.get("plan"),
                          updated_at=previous.get("updated_at", now), stale=True)
    return record


def run(now=None, registry=None, collectors=None, usage_file=None, token_collector=None):
    now = time.time() if now is None else now
    registry = registry or accounts.load_registry()
    collectors = collectors or COLLECTORS
    usage_file = usage_file or common.USAGE_FILE
    previous = {(r["provider"], r["account"]): r
                for r in (common.read_json(usage_file, {}) or {}).get("accounts", [])}
    records = []
    for account in all_accounts(registry):
        key = (account["provider"], account["id"])
        try:
            result = collectors[account["provider"]](account, now=now)
        except Exception as exc:  # fronteira de resiliência: uma conta nunca derruba as outras
            result = {"status": common.ERROR, "error": f"erro interno: {exc}"}
        records.append(build_record(account, result, previous.get(key), now))
    homes = {p: [a["home"] for a in accounts.accounts_for(p, registry)]
             for p in accounts.MULTI_ACCOUNT_PROVIDERS}
    try:
        token_stats = (token_collector or tokens.collect_tokens)(homes, now=now)
    except Exception as exc:
        token_stats = {"error": f"erro ao ler transcrições: {exc}"}
    data = {"updated_at": now, "accounts": records, "tokens": token_stats}
    common.write_json_atomic(usage_file, data)
    return data
