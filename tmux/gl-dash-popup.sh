#!/usr/bin/env bash
# Popup persistente do gl-dash: roda o gl-dash numa sessão tmux dedicada e só
# reanexa nas próximas aberturas (o prefix + d dentro do popup apenas desanexa).
set -euo pipefail

SESSION="gl-dash"

if ! tmux has-session -t "=$SESSION" 2>/dev/null; then
  # O servidor tmux não tem o env do zsh: importa só GITLAB_HOST/TOKEN do
  # ~/.use.env (o arquivo inteiro executa comandos e imprime tokens). O eval
  # roda dentro da sessão para o token não aparecer no argv do tmux.
  # O set-option vai na mesma sequência: `set-option -t =gl-dash` falha no
  # tmux 3.7 ("no such session") e, com set -e, abortava antes do attach.
  tmux new-session -d -s "$SESSION" -c "$PWD" \
    'eval "$(grep -E "^export GITLAB_(HOST|TOKEN)=" ~/.use.env)" && exec gl-dash' \; \
    set-option status off
fi

# Sem TMUX no env: dentro do popup ele aponta para o cliente pai e o attach recusaria.
exec env -u TMUX tmux attach-session -t "=$SESSION"
