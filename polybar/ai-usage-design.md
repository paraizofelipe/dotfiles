# Módulo de utilização de IA na polybar — Design

- **Data:** 2026-06-17
- **Repositório:** dotfiles (`polybar/`)
- **Barra alvo:** `mainbar-i3` (monitor `DP-1`), arquivo `polybar/config-3monitor.ini`

## Objetivo

Adicionar um módulo na polybar, à direita do `module/vial`, que mostra um ícone de
cérebro () colorido pela utilização de IA. Ao clicar, abre um modal no canto
superior esquerdo da tela (logo abaixo da barra) com as barras de consumo dos
providers **Claude Code**, **Codex** e **OpenRouter**, incluindo a utilização atual,
o limite semanal, horários de reset e dados da última request. O card **MIA
(Luizalabs)** entrou depois, com o consumo do mês no gateway LiteLLM corporativo. O modal tem botão de
refresh.

## Princípios

- **Standalone / zero dependências externas.** Apenas a stdlib do Python 3
  (`urllib`, `json`, `tkinter`, `datetime`, `os`, `sys`). Nenhum `pip install`,
  nenhum `eww`/`rofi`/`yad`/`zenity`. `tkinter` 8.6 e o Python 3.13 já estão
  disponíveis no ambiente.
- **Degradação independente por provider.** Falha de um provider (rede, token
  expirado, ausência de logs) nunca quebra a barra nem os demais cards.
- **A barra nunca quebra.** O subcomando `poll` sempre imprime o ícone de cérebro,
  mesmo em erro.

## Arquitetura

### Arquivo único: `polybar/ai-usage.py`

Script Python executável (`#!/usr/bin/env python3`). Como `~/.config/polybar` é um
symlink para o diretório `polybar/` do repositório, o script fica automaticamente
disponível em `~/.config/polybar/ai-usage.py` — **sem alteração em `install.sh` nem
em `start.sh`**.

Três subcomandos:

| Subcomando | Quem chama | O que faz |
|---|---|---|
| `poll` | polybar (`interval = 300`) | Atualiza o cache de todos os providers e imprime o label da barra (ícone de cérebro colorido pela pior utilização). |
| `show` | `click-left` do módulo | Toggle do modal. Se já estiver aberto, fecha; senão lê o cache e abre o modal. |
| `fetch` | botão Refresh do modal e `poll` | Apenas atualiza o cache (sem UI). |

### Cache

- Caminho: `/tmp/polybar-ai-usage-$USER.json`.
- Conteúdo: `{ "updated_at": <epoch>, "providers": { "<nome>": <normalizado|erro> } }`.
- O modal lê **somente** o cache (resposta instantânea e mostra o "último estado
  consultado"). O `poll` (5 min) e o botão Refresh são os únicos que tocam a rede.

### Esquema normalizado por provider

Cada coletor devolve um dicionário uniforme para o modal renderizar de forma
homogênea:

```python
{
  "ok": bool,
  "error": str | None,          # mensagem curta quando ok = False
  "bars": [                      # 0..N barras de consumo
    { "label": str,             # ex.: "Atual (5h)", "Semanal"
      "percent": float,         # 0..100
      "resets_at": str | None } # ISO8601 ou None
  ],
  "info": [ str, ... ]           # linhas extras (última request, créditos, plano)
}
```

### Coletores

**1. Claude Code** — `GET https://api.anthropic.com/api/oauth/usage`
- Headers: `Authorization: Bearer <accessToken>` (lido de
  `~/.claude/.credentials.json` → `claudeAiOauth.accessToken`) e
  `anthropic-beta: oauth-2025-04-20`.
- Barras: `five_hour.utilization` (label "Atual (5h)") + `five_hour.resets_at`;
  `seven_day.utilization` (label "Semanal") + `seven_day.resets_at`.
- `info`: tokens da última request lidos do JSONL local mais recente em
  `~/.claude/projects/*/*.jsonl` (última mensagem `type == "assistant"` com
  `message.usage`: input/output/cache).
- Erros: HTTP 401 → `error = "token expirado — rode o Claude Code"`. Outros erros de
  rede → `error` genérico.

**2. Codex** — leitura local (sem rede)
- Lê o `~/.codex/sessions/<ano>/<mês>/<dia>/rollout-*.jsonl` mais recente e pega o
  **último** evento `type == "token_count"`.
- Barras: `rate_limits.primary.used_percent` (label "Atual" — `window_minutes` ~300 =
  5h) + `primary.resets_at`; `rate_limits.secondary.used_percent` (label "Semanal" —
  `window_minutes` ~10080) + `secondary.resets_at`.
- `info`: `last_token_usage.total_tokens` e `plan_type`.
- `resets_at` vem como epoch (segundos) → converter para ISO/relativo.
- Erro: sem arquivos de sessão → `error = "sem dados locais do Codex"`.

**3. MIA (Luizalabs)** — `GET {base_url}/key/info` + `GET {base_url}/user/daily/activity`
- Gateway LiteLLM corporativo. Virtual key e `base_url` vêm de
  `~/.mia/credentials.json` (CLI `mia`); com `expires_at` vencido, `mia status`
  revalida a sessão e reescreve o arquivo antes das chamadas.
- Header: `Authorization: Bearer <litellm_key>`.
- Barras: o gateway hoje não publica teto — `max_budget` vem nulo na key, no
  usuário e no time, e os endpoints de budget exigem papel de admin. Sem
  denominador não há percentual honesto, então a barra usa **teto local**:
  `MIA_MONTHLY_BUDGET` (env, lida também dos `ENV_FILES` como a chave do
  OpenRouter) sobre o gasto do mês, com reset na virada do mês (label
  "Budget (mês)"). Se a key passar a ter `max_budget`, ela tem **precedência** por
  ser a fonte de verdade (label "Budget (<budget_duration>)", reset em
  `budget_reset_at`). Sem teto e sem `/user/daily/activity`, nenhuma barra — o card
  vive de `info` em vez de exibir 0% falso.
- `info`: gasto e tokens/requests do mês corrente
  (`/user/daily/activity?start_date=<1º do mês>&end_date=<hoje>` → `metadata`) e o
  tempo restante da sessão (`info.expires` do `/key/info`).
- Erros: HTTP 401/403 → `"sessão expirada — rode `mia auth`"`; sem credenciais →
  `"credenciais do MIA não encontradas — rode `mia auth`"`. Falha só no
  `/user/daily/activity` degrada para o card sem as linhas de consumo.

**4. OpenRouter** — `GET https://openrouter.ai/api/v1/credits`
- Header: `Authorization: Bearer $OPENROUTER_API_KEY` (env).
- Resposta: `{ data: { total_credits, total_usage } }`.
- `info`: "Créditos disponíveis: {total_credits - total_usage:.2f}".
- Barras: uma barra de % usado = `total_usage / total_credits * 100` (label
  "Créditos", sem `resets_at`).
- Erro: sem `OPENROUTER_API_KEY` → `error = "sem OPENROUTER_API_KEY"`.

### Modal (tkinter)

- Janela borderless (`overrideredirect(True)`), tema Gruvbox (mesmas cores do
  polybar: bg `#32302f`, fg `#ebdbb2`).
- Posição: canto superior esquerdo, logo abaixo da barra. Geometria `+8+30`
  (a barra tem ~20pt de altura no topo; gap pequeno).
- Um card por provider: ícone + nome; para cada barra, uma barra horizontal
  (`Canvas` com retângulos) colorida por severidade, o `%` e "reset em Xh Ym"
  (tempo relativo a partir de `resets_at`); linhas de `info`.
- Provider com `ok = False`: card mostra o ícone + a mensagem de `error` (sem barras).
- Rodapé: "atualizado há X min" (a partir de `updated_at`) + **botão Refresh**
  (chama `fetch` e redesenha) + fechar no `Esc` / segundo clique no cérebro.
- Toggle via pidfile (`/tmp/polybar-ai-usage-modal-$USER.pid`), no mesmo padrão do
  `calendar.sh` (segundo clique fecha).

### Severidade / cores

| Faixa | Cor (Gruvbox) |
|---|---|
| < 50% | verde `#b8bb26` |
| 50–80% | amarelo `#fabd2f` |
| > 80% | vermelho `#fb4934` |

- O ícone de cérebro na barra usa a cor da **pior** utilização entre os providers
  ativos. (O Codex também expõe `severity`; usamos a faixa de % como fonte única de
  verdade para manter consistência entre providers.)

## Módulo polybar (`config-3monitor.ini`)

```ini
[module/ai-usage]
type = custom/script
exec = ~/.config/polybar/ai-usage.py poll
interval = 300
format = <label>
label = %output%
click-left = ~/.config/polybar/ai-usage.py show
cursor-click = pointer
```

Inserção em `[bar/mainbar-i3]`, `modules-right`, imediatamente após `vial`:

```
modules-right = pulseaudio xkeyboard vial ai-usage wlan bluetooth opendeck netskope power
```

## Tratamento de erros (resumo)

| Situação | Comportamento |
|---|---|
| Token OAuth do Claude expirado (401) | Card Claude: "token expirado — rode o Claude Code". Barra segue normal. |
| Sem `OPENROUTER_API_KEY` | Card OpenRouter: "sem OPENROUTER_API_KEY". |
| Sem logs do Codex | Card Codex: "sem dados locais do Codex". |
| Sessão MIA expirada (401/403) | Card MIA: "sessão expirada — rode `mia auth`". |
| Erro de rede no `fetch` | Mantém o último valor do cache + indica que está desatualizado. |
| Qualquer erro no `poll` | Ainda imprime o ícone de cérebro (cor neutra/foreground). |

## Testes

- Funções de **parsing/normalização** são puras e testadas com `unittest` (stdlib)
  usando os payloads reais já capturados (oauth/usage, token_count do Codex,
  credits do OpenRouter).
- Formatação de **tempo relativo** ("reset em Xh Ym") testada com timestamps fixos.
- Modal (tkinter) e chamadas de rede: verificação manual (`ai-usage.py poll`,
  `ai-usage.py show`, botão Refresh) e reload do polybar (`~/.config/polybar/start.sh`).

## Fora de escopo (YAGNI)

- Refresh automático do token OAuth do Claude (apenas aviso no card quando expira).
- Histórico ou gráficos temporais — somente estado atual + última request.
- Configuração externa (arquivo `.ini` próprio); constantes ficam no topo do script
  para manter o caráter standalone.
