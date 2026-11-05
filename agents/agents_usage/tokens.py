"""Tokens por dia e por modelo a partir das transcrições locais dos CLIs.

Cada arquivo é parseado uma vez e cacheado por (mtime, size), porque
~/.claude/projects passa fácil de centenas de MB.
Entrada normalizada: [chave_dedupe, epoch, modelo, input, output, cache].
"""
import glob
import json
import os
import time
from datetime import datetime

from . import common

LOOKBACK_DAYS = 7
SKIP_MODELS = {"<synthetic>"}


def parse_claude_lines(lines):
    """Uma entrada por message.id: o CLI regrava a mesma mensagem em várias
    linhas durante o streaming, com o usage final na última."""
    found = {}
    for line in lines:
        if '"assistant"' not in line or '"usage"' not in line:
            continue
        try:
            obj = json.loads(line)
            msg = obj.get("message") or {}
            usage, model = msg.get("usage"), msg.get("model")
            ts = common.to_epoch(obj.get("timestamp"))
            if obj.get("type") != "assistant" or not usage or not ts or model in SKIP_MODELS:
                continue
            key = msg.get("id") or obj.get("requestId") or obj.get("uuid")
            found[key] = [key, ts, model or "unknown",
                          int(usage.get("input_tokens") or 0),
                          int(usage.get("output_tokens") or 0),
                          int(usage.get("cache_read_input_tokens") or 0)
                          + int(usage.get("cache_creation_input_tokens") or 0)]
        except (ValueError, TypeError, AttributeError):
            continue  # linha fora do formato esperado (JSONDecodeError é ValueError)
    return list(found.values())


def parse_codex_lines(lines, file_key):
    """Eventos token_count trazem o delta em last_token_usage; o Codex repete o
    evento quando só os rate limits mudam, então o total acumulado é a chave."""
    entries, model, last_total = [], "unknown", None
    for line in lines:
        if '"turn_context"' not in line and '"token_count"' not in line:
            continue
        try:
            obj = json.loads(line)
            payload = obj.get("payload") or {}
            if obj.get("type") == "turn_context":
                model = payload.get("model") or model
                continue
            if payload.get("type") != "token_count":
                continue
            info = payload.get("info") or {}
            last = info.get("last_token_usage")
            total = (info.get("total_token_usage") or {}).get("total_tokens")
            ts = common.to_epoch(obj.get("timestamp"))
            if not last or not ts or total == last_total:
                continue
            cached = int(last.get("cached_input_tokens") or 0)
            entry = [f"{file_key}:{len(entries)}", ts, model,
                     max(0, int(last.get("input_tokens") or 0) - cached),
                     int(last.get("output_tokens") or 0), cached]
        except (ValueError, TypeError, AttributeError):
            continue  # linha fora do formato esperado (JSONDecodeError é ValueError)
        last_total = total
        entries.append(entry)
    return entries


def claude_files(homes):
    return [p for h in homes
            for p in glob.glob(os.path.join(h, "projects", "**", "*.jsonl"), recursive=True)]


def codex_files(homes):
    return [p for h in homes
            for p in glob.glob(os.path.join(h, "sessions", "**", "*.jsonl"), recursive=True)]


def collect_entries(files, parser, cache, now, lookback_days=LOOKBACK_DAYS):
    """Entradas dos arquivos tocados na janela; atualiza `cache` in place."""
    cutoff = now - (lookback_days + 1) * 86400
    seen_real, entries = set(), []
    for path in files:
        real = os.path.realpath(path)  # contas podem compartilhar o histórico via symlink
        if real in seen_real:
            continue
        seen_real.add(real)
        try:
            st = os.stat(real)
        except OSError:
            continue
        if st.st_mtime < cutoff:
            continue
        hit = cache.get(real)
        if hit and hit["mtime"] == st.st_mtime and hit["size"] == st.st_size:
            entries.extend(hit["entries"])
            continue
        try:
            with open(real, encoding="utf-8", errors="replace") as f:
                parsed = parser(f, real)
        except OSError:
            continue
        cache[real] = {"mtime": st.st_mtime, "size": st.st_size, "entries": parsed}
        entries.extend(parsed)
    for stale in set(cache) - seen_real:
        del cache[stale]
    return entries


def aggregate(entries, now, lookback_days=LOOKBACK_DAYS):
    cutoff = now - lookback_days * 86400
    by_day, by_model, seen = {}, {}, set()
    week = {"input": 0, "output": 0, "cache": 0, "total": 0}
    for key, ts, model, inp, out, cache in entries:
        if key in seen or ts < cutoff or ts > now + 300:
            continue
        seen.add(key)
        total = inp + out + cache
        day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        by_day[day] = by_day.get(day, 0) + total
        by_model[model] = by_model.get(model, 0) + total
        week["input"] += inp
        week["output"] += out
        week["cache"] += cache
        week["total"] += total
    top = max(by_model, key=by_model.__getitem__) if by_model else None
    return {"by_day": dict(sorted(by_day.items())),
            "by_model": dict(sorted(by_model.items(), key=lambda kv: -kv[1])),
            "week": week, "top_model": top}


PARSERS = {
    "claude": (claude_files, lambda f, _key: parse_claude_lines(f)),
    "codex": (codex_files, parse_codex_lines),
}


def collect_tokens(homes_by_provider, now=None, cache_file=None):
    now = time.time() if now is None else now
    cache_file = cache_file or common.TOKENS_CACHE_FILE
    cache = common.read_json(cache_file, {}) or {}
    result = {}
    for provider, homes in homes_by_provider.items():
        list_files, parser = PARSERS[provider]
        bucket = cache.setdefault(provider, {})
        result[provider] = aggregate(collect_entries(list_files(homes), parser, bucket, now), now)
    common.write_json_atomic(cache_file, cache)
    return result
