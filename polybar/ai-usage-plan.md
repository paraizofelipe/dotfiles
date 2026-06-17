# Módulo de utilização de IA na polybar — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar um módulo na polybar (à direita do `vial`) com ícone de cérebro colorido pela utilização de IA, que ao clicar abre um modal no canto superior esquerdo com as barras de consumo de Claude Code, Codex e OpenRouter.

**Architecture:** Um único script Python standalone (`polybar/ai-usage.py`, só stdlib) com três subcomandos — `poll` (polybar, a cada 5 min, atualiza cache e imprime o ícone), `show` (toggle do modal tkinter lendo o cache) e `fetch` (atualiza o cache). Coletores por provider (Claude via API OAuth, Codex via logs locais, OpenRouter via API de créditos) devolvem um esquema normalizado renderizado de forma uniforme no modal.

**Tech Stack:** Python 3.13 + stdlib apenas (`urllib`, `json`, `glob`, `tkinter`, `datetime`, `signal`). Polybar `custom/script`. Tema Gruvbox.

## Global Constraints

- **Zero dependências externas** — apenas stdlib do Python 3. Nenhum `pip install`, nenhum `eww`/`rofi`/`yad`/`zenity`.
- **`tkinter` importado de forma preguiçosa** (dentro de `run_modal`), para que os testes e os subcomandos `poll`/`fetch` não precisem de `$DISPLAY`.
- **Degradação independente por provider** — falha de um provider nunca derruba a barra nem os demais cards.
- **A barra nunca quebra** — `poll` sempre imprime o ícone de cérebro, mesmo em erro.
- **Cor de severidade** (única fonte de verdade): `< 50%` verde `#b8bb26`, `50–80%` amarelo `#fabd2f`, `> 80%` vermelho `#fb4934`.
- **Ícone de cérebro:** `` (nf-fa-brain / Font Awesome 5 Solid, já carregado na barra).
- **Caminhos:** cache `/tmp/polybar-ai-usage-$USER.json`; pidfile do modal `/tmp/polybar-ai-usage-modal-$USER.pid`.
- **Não alterar `install.sh` nem `start.sh`** — `~/.config/polybar` já é symlink para `polybar/`.
- **Commits:** autor é o usuário; **não** adicionar `Co-Authored-By`.

## File Structure

- **Create:** `polybar/ai-usage.py` — script único. Responsabilidades em blocos: config/constantes → helpers puros → parsers puros → coletores de IO → cache/fetch → poll → modal → dispatch.
- **Create:** `polybar/test_ai_usage.py` — testes `unittest` (stdlib) das funções puras, com os payloads reais capturados como fixtures.
- **Modify:** `polybar/config-3monitor.ini` — adicionar `[module/ai-usage]` e inserir `ai-usage` no `modules-right` da `mainbar-i3`.

---

### Task 1: Helpers puros (cores, formatação, tempo relativo)

**Files:**
- Create: `polybar/ai-usage.py`
- Test: `polybar/test_ai_usage.py`

**Interfaces:**
- Produces:
  - `severity_color(percent: float) -> str` — devolve `#b8bb26`/`#fabd2f`/`#fb4934`.
  - `human_int(n) -> str` — `1500 -> "1.5k"`, `999 -> "999"`, `None -> "0"`.
  - `relative_reset(value, now: datetime | None = None) -> str` — aceita ISO8601 (str) ou epoch (int/float); devolve `"reset em Xh Ym"` / `"reset em Xd Yh"` / `"reset em Xm"` / `"reset agora"` / `""` (se inválido).
  - Constantes de cor: `GREEN`, `YELLOW`, `RED`, `BG`, `BG_ALT`, `FG`, `FG_DIM`, `BRAIN`.

- [ ] **Step 1: Escrever os testes que falham**

Criar `polybar/test_ai_usage.py`:

```python
import unittest
from datetime import datetime, timezone

import ai_usage  # noqa: importado por nome de módulo (ver Step 3)


class TestHelpers(unittest.TestCase):
    def test_severity_color_green(self):
        self.assertEqual(ai_usage.severity_color(0), ai_usage.GREEN)
        self.assertEqual(ai_usage.severity_color(49.9), ai_usage.GREEN)

    def test_severity_color_yellow(self):
        self.assertEqual(ai_usage.severity_color(50), ai_usage.YELLOW)
        self.assertEqual(ai_usage.severity_color(80), ai_usage.YELLOW)

    def test_severity_color_red(self):
        self.assertEqual(ai_usage.severity_color(80.1), ai_usage.RED)
        self.assertEqual(ai_usage.severity_color(100), ai_usage.RED)

    def test_human_int(self):
        self.assertEqual(ai_usage.human_int(999), "999")
        self.assertEqual(ai_usage.human_int(1500), "1.5k")
        self.assertEqual(ai_usage.human_int(0), "0")
        self.assertEqual(ai_usage.human_int(None), "0")

    def test_relative_reset_hours_minutes(self):
        now = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(
            ai_usage.relative_reset("2026-06-17T15:30:00+00:00", now), "reset em 3h 30m")

    def test_relative_reset_days(self):
        now = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        epoch = datetime(2026, 6, 18, 13, 0, 0, tzinfo=timezone.utc).timestamp()
        self.assertEqual(ai_usage.relative_reset(epoch, now), "reset em 1d 1h")

    def test_relative_reset_past(self):
        now = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(
            ai_usage.relative_reset("2026-06-17T11:00:00+00:00", now), "reset agora")

    def test_relative_reset_invalid(self):
        self.assertEqual(ai_usage.relative_reset(None), "")
        self.assertEqual(ai_usage.relative_reset("not-a-date"), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar os testes e ver falhar**

Run: `cd polybar && python3 -m unittest test_ai_usage -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'ai_usage'`.

- [ ] **Step 3: Criar o script com os helpers**

> Nota: o arquivo no disco é `ai-usage.py`, mas o teste o importa como `ai_usage`. Resolver criando o módulo importável. A forma mais simples e sem deps: criar o arquivo como `polybar/ai-usage.py` e, no teste, importar via `importlib`. **Substituir** o `import ai_usage` do Step 1 pelo bloco abaixo no topo de `test_ai_usage.py`:

```python
import importlib.util
import os
import unittest
from datetime import datetime, timezone

_spec = importlib.util.spec_from_file_location(
    "ai_usage", os.path.join(os.path.dirname(__file__), "ai-usage.py"))
ai_usage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ai_usage)
```

Criar `polybar/ai-usage.py`:

```python
#!/usr/bin/env python3
"""Módulo polybar de utilização de IA (Claude Code, Codex, OpenRouter).

Standalone — apenas a stdlib do Python 3. Subcomandos: poll | fetch | show.
"""
import glob
import json
import os
import signal
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
BRAIN = ""  # nf-fa-brain / Font Awesome 5 Solid

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
CODEX_SESSIONS = os.path.expanduser("~/.codex/sessions")


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


def relative_reset(value, now=None):
    dt = _to_datetime(value)
    if dt is None:
        return ""
    now = now or datetime.now(timezone.utc)
    secs = int((dt - now).total_seconds())
    if secs <= 0:
        return "reset agora"
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    if days > 0:
        return f"reset em {days}d {hours}h"
    if hours > 0:
        return f"reset em {hours}h {mins}m"
    return f"reset em {mins}m"


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
```

> `cmd_poll`, `cmd_fetch` e `cmd_show` ainda não existem — serão adicionados nas próximas tasks. Como `main()` só roda sob `__main__`, importar o módulo nos testes não dispara o dispatch.

- [ ] **Step 4: Rodar os testes e ver passar**

Run: `cd polybar && python3 -m unittest test_ai_usage -v`
Expected: PASS (8 testes).

- [ ] **Step 5: Commit**

```bash
cd /home/paraizo/projects/dotfiles
git add polybar/ai-usage.py polybar/test_ai_usage.py
git commit -m "feat(polybar): helpers puros do módulo de utilização de IA"
```

---

### Task 2: Parsers puros dos providers

**Files:**
- Modify: `polybar/ai-usage.py` (adicionar funções após os helpers)
- Test: `polybar/test_ai_usage.py` (adicionar classe de teste)

**Interfaces:**
- Consumes: `human_int` (Task 1).
- Produces (todas devolvem o esquema normalizado `{"ok": bool, "error": str|None, "bars": list, "info": list}`; cada barra é `{"label": str, "percent": float, "resets_at": str|int|None}`):
  - `parse_claude_usage(payload: dict) -> dict`
  - `parse_codex_token_count(tc: dict) -> dict`
  - `parse_openrouter_credits(payload: dict) -> dict`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar ao final de `polybar/test_ai_usage.py` (antes do `if __name__`):

```python
class TestParsers(unittest.TestCase):
    CLAUDE = {
        "five_hour": {"utilization": 22.0, "resets_at": "2026-06-17T23:00:00+00:00"},
        "seven_day": {"utilization": 7.0, "resets_at": "2026-06-23T02:00:00+00:00"},
    }
    CODEX = {
        "type": "token_count",
        "info": {"last_token_usage": {"total_tokens": 21668}},
        "rate_limits": {
            "primary": {"used_percent": 2, "window_minutes": 300, "resets_at": 1774974811},
            "secondary": {"used_percent": 24, "window_minutes": 10080, "resets_at": 1775221497},
            "plan_type": "plus",
        },
    }
    OPENROUTER = {"data": {"total_credits": 100, "total_usage": 84.74115602}}

    def test_parse_claude_usage(self):
        r = ai_usage.parse_claude_usage(self.CLAUDE)
        self.assertTrue(r["ok"])
        self.assertEqual([b["label"] for b in r["bars"]], ["Atual (5h)", "Semanal"])
        self.assertEqual(r["bars"][0]["percent"], 22.0)
        self.assertEqual(r["bars"][1]["percent"], 7.0)
        self.assertEqual(r["bars"][0]["resets_at"], "2026-06-17T23:00:00+00:00")

    def test_parse_codex_token_count(self):
        r = ai_usage.parse_codex_token_count(self.CODEX)
        self.assertTrue(r["ok"])
        self.assertEqual([b["label"] for b in r["bars"]], ["Atual (5h)", "Semanal"])
        self.assertEqual(r["bars"][0]["percent"], 2.0)
        self.assertEqual(r["bars"][1]["percent"], 24.0)
        self.assertEqual(r["bars"][1]["resets_at"], 1775221497)
        self.assertIn("Última request: 21.7k tokens", r["info"])
        self.assertIn("Plano: plus", r["info"])

    def test_parse_openrouter_credits(self):
        r = ai_usage.parse_openrouter_credits(self.OPENROUTER)
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["bars"]), 1)
        self.assertAlmostEqual(r["bars"][0]["percent"], 84.74115602, places=4)
        self.assertEqual(r["info"], ["Disponível: 15.26 de 100"])
```

- [ ] **Step 2: Rodar os testes e ver falhar**

Run: `cd polybar && python3 -m unittest test_ai_usage -v`
Expected: FAIL com `AttributeError: module 'ai_usage' has no attribute 'parse_claude_usage'`.

- [ ] **Step 3: Implementar os parsers**

Adicionar em `polybar/ai-usage.py`, logo após `relative_reset` (antes de `def main`):

```python
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


def parse_codex_token_count(tc):
    rate = tc.get("rate_limits") or {}
    bars = []
    for key, label in (("primary", "Atual (5h)"), ("secondary", "Semanal")):
        win = rate.get(key)
        if win:
            bars.append({
                "label": label,
                "percent": float(win.get("used_percent") or 0),
                "resets_at": win.get("resets_at"),
            })
    info = []
    last = ((tc.get("info") or {}).get("last_token_usage") or {}).get("total_tokens")
    if last is not None:
        info.append(f"Última request: {human_int(last)} tokens")
    plan = rate.get("plan_type")
    if plan:
        info.append(f"Plano: {plan}")
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
        "info": [f"Disponível: {available:.2f} de {total:.0f}"],
    }
```

- [ ] **Step 4: Rodar os testes e ver passar**

Run: `cd polybar && python3 -m unittest test_ai_usage -v`
Expected: PASS (11 testes).

- [ ] **Step 5: Commit**

```bash
cd /home/paraizo/projects/dotfiles
git add polybar/ai-usage.py polybar/test_ai_usage.py
git commit -m "feat(polybar): parsers normalizados dos providers de IA"
```

---

### Task 3: Coletores de IO, cache e `fetch`

**Files:**
- Modify: `polybar/ai-usage.py` (adicionar coletores + cache + `cmd_fetch`)

**Interfaces:**
- Consumes: `parse_claude_usage`, `parse_codex_token_count`, `parse_openrouter_credits`, `_err`, `human_int` (Tasks 1–2).
- Produces:
  - `collect_claude() -> dict`, `collect_codex() -> dict`, `collect_openrouter() -> dict` (esquema normalizado).
  - `PROVIDERS: list[tuple[str, callable]]` — ordem de exibição.
  - `cmd_fetch() -> dict` — `{"updated_at": float, "providers": {nome: normalizado}}`; grava em `CACHE`.
  - `read_cache() -> dict | None`.

> Estes tocam rede/arquivos e não têm teste unitário; a verificação é um smoke run real (Step 3).

- [ ] **Step 1: Implementar coletores, cache e fetch**

Adicionar em `polybar/ai-usage.py`, após os parsers (antes de `def main`):

```python
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
        files = glob.glob(os.path.join(CODEX_SESSIONS, "*", "*", "*", "rollout-*.jsonl"))
        if not files:
            return _err("sem dados locais do Codex")
        newest = max(files, key=os.path.getmtime)
        token_count = None
        with open(newest, encoding="utf-8") as f:
            for line in f:
                if '"token_count"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                obj = obj.get("payload", obj)
                if obj.get("type") == "token_count":
                    token_count = obj
        if token_count is None:
            return _err("sem uso registrado no Codex")
        return parse_codex_token_count(token_count)
    except OSError:
        return _err("erro ao ler logs do Codex")


def collect_openrouter():
    key = os.environ.get("OPENROUTER_API_KEY")
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
    ("Claude Code", collect_claude),
    ("Codex", collect_codex),
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
```

- [ ] **Step 2: Garantir que os testes existentes continuam passando**

Run: `cd polybar && python3 -m unittest test_ai_usage -v`
Expected: PASS (11 testes — nada quebrou).

- [ ] **Step 3: Smoke run real do fetch e inspeção do cache**

Run:
```bash
cd polybar && python3 ai-usage.py fetch && \
python3 -c "import json,os; d=json.load(open(f\"/tmp/polybar-ai-usage-{os.environ['USER']}.json\")); print(json.dumps(d['providers'], indent=2, ensure_ascii=False))"
```
Expected: JSON com as três chaves `Claude Code`, `Codex`, `OpenRouter`. Cada uma com `ok: true` e `bars`/`info` preenchidos (ou `ok: false` com `error` legível, se o provider estiver indisponível — isso é comportamento válido). Nenhuma exceção/traceback.

- [ ] **Step 4: Commit**

```bash
cd /home/paraizo/projects/dotfiles
git add polybar/ai-usage.py
git commit -m "feat(polybar): coletores de IO, cache e fetch dos providers de IA"
```

---

### Task 4: Subcomando `poll` (label da barra)

**Files:**
- Modify: `polybar/ai-usage.py` (adicionar `worst_percent` + `cmd_poll`)
- Test: `polybar/test_ai_usage.py` (teste de `worst_percent`)

**Interfaces:**
- Consumes: `cmd_fetch`, `severity_color`, `BRAIN`, `FG` (Tasks 1, 3).
- Produces:
  - `worst_percent(data: dict) -> float | None` — maior `percent` entre providers com `ok=True`; `None` se não houver nenhum.
  - `cmd_poll()` — imprime `%{F<cor>}<cérebro>%{F-}` no stdout.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao final de `polybar/test_ai_usage.py` (antes do `if __name__`):

```python
class TestPoll(unittest.TestCase):
    def test_worst_percent_picks_max_of_ok_providers(self):
        data = {"providers": {
            "A": {"ok": True, "bars": [{"percent": 10}, {"percent": 22}]},
            "B": {"ok": True, "bars": [{"percent": 84.7}]},
            "C": {"ok": False, "bars": [{"percent": 99}]},  # ignorado
        }}
        self.assertEqual(ai_usage.worst_percent(data), 84.7)

    def test_worst_percent_none_when_no_ok_bars(self):
        data = {"providers": {"A": {"ok": False, "bars": []}}}
        self.assertIsNone(ai_usage.worst_percent(data))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd polybar && python3 -m unittest test_ai_usage.TestPoll -v`
Expected: FAIL com `AttributeError: module 'ai_usage' has no attribute 'worst_percent'`.

- [ ] **Step 3: Implementar `worst_percent` e `cmd_poll`**

Adicionar em `polybar/ai-usage.py`, após `read_cache` (antes de `def main`):

```python
def worst_percent(data):
    worst = None
    for prov in data.get("providers", {}).values():
        if not prov.get("ok"):
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
    sys.stdout.write(f"%{{F{color}}}{BRAIN}%{{F-}}\n")
```

- [ ] **Step 4: Rodar os testes e ver passar**

Run: `cd polybar && python3 -m unittest test_ai_usage -v`
Expected: PASS (13 testes).

- [ ] **Step 5: Smoke run real do poll**

Run: `cd polybar && python3 ai-usage.py poll | cat -v`
Expected: uma linha como `%{F#fabd2f}<cérebro>%{F-}` (a cor varia conforme a utilização atual; o glifo pode aparecer como caixa no terminal, é esperado).

- [ ] **Step 6: Commit**

```bash
cd /home/paraizo/projects/dotfiles
git add polybar/ai-usage.py polybar/test_ai_usage.py
git commit -m "feat(polybar): subcomando poll com ícone colorido por severidade"
```

---

### Task 5: Modal tkinter + toggle (`show`)

**Files:**
- Modify: `polybar/ai-usage.py` (adicionar `cmd_show` + `run_modal`)

**Interfaces:**
- Consumes: `read_cache`, `cmd_fetch`, `severity_color`, `relative_reset`, `PROVIDERS`, `_err`, constantes de cor, `BRAIN` (Tasks 1–4).
- Produces: `cmd_show()` (toggle via `PIDFILE`), `run_modal(data: dict)` (constrói e roda a UI).

> Verificação é manual (precisa de `$DISPLAY`). `tkinter` é importado **dentro** de `run_modal` para não exigir display nos demais subcomandos/testes.

- [ ] **Step 1: Implementar `cmd_show` e `run_modal`**

Adicionar em `polybar/ai-usage.py`, após `cmd_poll` (antes de `def main`):

```python
def cmd_show():
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
    finally:
        try:
            os.remove(PIDFILE)
        except OSError:
            pass


def run_modal(data):
    import tkinter as tk

    state = {"data": data}
    root = tk.Tk()
    root.title("AI Usage")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg=BG)
    root.geometry("+8+30")  # canto superior esquerdo, logo abaixo da barra
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
        tk.Label(container, text=f"{BRAIN}  Utilização de IA", bg=BG, fg=FG,
                 font=("Hack Nerd Font", 12, "bold")).pack(anchor="w", pady=(0, 8))
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

    render()
    root.mainloop()
```

- [ ] **Step 2: Garantir que os testes continuam passando**

Run: `cd polybar && python3 -m unittest test_ai_usage -v`
Expected: PASS (13 testes — importar o módulo não dispara `tkinter`).

- [ ] **Step 3: Verificação manual do modal**

Run: `cd polybar && python3 ai-usage.py show`
Expected: abre uma janela sem borda no canto superior esquerdo, com os três cards (barras coloridas, % e "reset em ..."), o rodapé "atualizado há X min" e o botão "↻ Refresh". Verificar:
- Clicar em **Refresh** re-consulta e redesenha (o "atualizado" volta a "agora").
- `Esc` fecha a janela.
- Rodar `python3 ai-usage.py show` de novo **com o modal aberto** fecha o modal (toggle via pidfile).

- [ ] **Step 4: Commit**

```bash
cd /home/paraizo/projects/dotfiles
git add polybar/ai-usage.py
git commit -m "feat(polybar): modal tkinter de utilização de IA com refresh e toggle"
```

---

### Task 6: Integração na polybar (`config-3monitor.ini`)

**Files:**
- Modify: `polybar/config-3monitor.ini` (linha 212 + novo bloco de módulo no fim do arquivo)

**Interfaces:**
- Consumes: `~/.config/polybar/ai-usage.py` (symlink já existente para `polybar/ai-usage.py`).

- [ ] **Step 1: Tornar o script executável**

Run: `cd polybar && chmod +x ai-usage.py && ls -l ai-usage.py`
Expected: permissões `-rwxr-xr-x`.

- [ ] **Step 2: Inserir `ai-usage` no `modules-right` da `mainbar-i3`**

Editar `polybar/config-3monitor.ini` — trocar a linha 212 (atenção ao **espaço duplo** após `pulseaudio`):

De:
```
modules-right = pulseaudio  xkeyboard vial wlan bluetooth opendeck netskope power
```
Para:
```
modules-right = pulseaudio  xkeyboard vial ai-usage wlan bluetooth opendeck netskope power
```

- [ ] **Step 3: Adicionar o bloco do módulo no fim do arquivo**

Acrescentar ao final de `polybar/config-3monitor.ini` (após o bloco `[module/opendeck]`):

```ini

#####################################################################################################

[module/ai-usage]
type = custom/script
exec = ~/.config/polybar/ai-usage.py poll
interval = 300
format = <label>
label = %output%
click-left = ~/.config/polybar/ai-usage.py show
cursor-click = pointer
```

- [ ] **Step 4: Validar a sintaxe do config e o caminho via symlink**

Run:
```bash
test -x ~/.config/polybar/ai-usage.py && echo "symlink+exec OK"
grep -n "ai-usage" ~/.config/polybar/config-3monitor.ini
```
Expected: `symlink+exec OK` e duas ocorrências de `ai-usage` (no `modules-right` e no bloco do módulo).

- [ ] **Step 5: Recarregar a polybar e verificar**

Run: `~/.config/polybar/start.sh`
Expected (verificação manual): o ícone de cérebro aparece na `mainbar-i3` (monitor DP-1) entre o `vial` e o `wlan`, colorido conforme a utilização. Clicar abre o modal; clicar de novo fecha.

- [ ] **Step 6: Commit**

```bash
cd /home/paraizo/projects/dotfiles
git add polybar/config-3monitor.ini polybar/ai-usage.py
git commit -m "feat(polybar): módulo ai-usage na barra mainbar-i3"
```

---

## Self-Review

**1. Spec coverage:**
- Módulo à direita do `vial` → Task 6, Step 2. ✓
- Ícone de cérebro colorido pela pior utilização → Task 4 (`cmd_poll` + `worst_percent`). ✓
- Compatível com OpenRouter / Claude Code / Codex → Tasks 2–3 (parsers + coletores). ✓
- Modal no canto superior esquerdo abaixo da barra → Task 5 (`geometry("+8+30")`, `overrideredirect`). ✓
- Script Python consulta API a cada 5 min → Task 6 (`interval = 300`) + Task 3 (`cmd_fetch`). ✓
- Clicar mostra o consumo da última request → Task 5 (modal lê cache) + Task 3 (`info` da última request por provider). ✓
- Botão de refresh → Task 5 (`refresh`). ✓
- Definido em `config-3monitor.ini` → Task 6. ✓
- Standalone, evitar dependências → Global Constraints (só stdlib). ✓
- Claude Code via endpoint OAuth → Task 3 (`collect_claude`). ✓
- OpenRouter mostra créditos disponíveis → Task 2 (`parse_openrouter_credits` → "Disponível: ..."). ✓
- Utilização atual + % + reset e semanal + % + reset (Claude/Codex) → Task 2 (`parse_claude_usage`/`parse_codex_token_count`) + Task 5 (`relative_reset` no modal). ✓

**2. Placeholder scan:** Sem TBD/TODO; todo passo que altera código mostra o código completo. ✓

**3. Type consistency:** Esquema normalizado `{"ok","error","bars","info"}` idêntico em todos os parsers/coletores; `bars` sempre `{"label","percent","resets_at"}`; `cmd_fetch` produz `{"updated_at","providers"}` consumido igual em `worst_percent`, `read_cache` e `run_modal`. Nomes de funções consistentes entre tasks. ✓
