#!/usr/bin/env bash
# Toggle da sidebar do workmux somente na janela tmux atual.
# Usa o comando interno `workmux _sidebar-run` (pode mudar em updates do workmux).
set -euo pipefail

window="${1:?uso: $0 <window_id>}"
width="${WORKMUX_SIDEBAR_WIDTH:-35}"

existing=$(tmux list-panes -t "$window" -F '#{pane_id} #{@wm_local_sidebar}' | awk '$2 == 1 { print $1; exit }')

if [[ -n "$existing" ]]; then
  tmux kill-pane -t "$existing"
else
  pane=$(tmux split-window -t "$window" -fhbd -l "$width" -P -F '#{pane_id}' "workmux _sidebar-run")
  tmux set-option -p -t "$pane" @wm_local_sidebar 1
fi
