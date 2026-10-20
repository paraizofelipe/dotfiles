#!/usr/bin/env bash
# prefix + w: lista (fzf) TODAS as worktrees do diretório `[worktrees]` do herdr
# e abre a escolhida no herdr: foca o workspace se já estiver aberta; senão abre
# agrupada sob o workspace pai do repo; sem pai aberto, cria um workspace.
set -euo pipefail

config="${HERDR_CONFIG_PATH:-$HOME/.config/herdr/config.toml}"

fail() {
  printf '\n%s\n\n[Enter para fechar]' "$1"
  read -r _
  exit 1
}

# directory = "..." da seção [worktrees] (padrão do herdr: ~/.herdr/worktrees)
root="$(sed -n '/^\[worktrees\]/,/^\[/{s/^directory *= *"\(.*\)"/\1/p}' "$config" 2>/dev/null | head -n 1)"
root="${root:-~/.herdr/worktrees}"
root="${root/#\~/$HOME}"

workspaces="$(herdr workspace list 2>/dev/null)" || fail "herdr indisponível — o servidor está rodando?"

# Linhas: estado, repo, branch, path. Worktree linkada = diretório com `.git` arquivo.
list_worktrees() {
  local gitfile dir common repo branch state
  while IFS= read -r gitfile; do
    dir="${gitfile%/.git}"
    common="$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || continue
    repo="$(basename "$(dirname "$common")")"
    branch="$(git -C "$dir" branch --show-current 2>/dev/null)"
    state="○"
    if jq -e --arg p "$dir" 'any(.result.workspaces[]; .worktree.checkout_path? == $p)' \
        <<<"$workspaces" >/dev/null; then
      state="●"
    fi
    printf '%s\t%s\t%s\t%s\n' "$state" "$repo" "${branch:-(detached)}" "$dir"
  done < <(find "$root" -mindepth 2 -maxdepth 4 -name .git -type f 2>/dev/null | sort)
}

# A última coluna é o path (worktrees sem espaços no path).
selected="$(list_worktrees | column -t -s $'\t' \
  | fzf --reverse --prompt "worktree> " --header "● aberta no herdr  ○ fechada  ($root)")" || exit 0
path="${selected##* }"

open_id="$(jq -r --arg p "$path" \
  'first(.result.workspaces[] | select(.worktree.checkout_path? == $p) | .workspace_id) // empty' \
  <<<"$workspaces")"
if [[ -n "$open_id" ]]; then
  herdr workspace focus "$open_id" >/dev/null || fail "falha ao focar o workspace $open_id"
  exit 0
fi

# O `worktree open` exige o workspace pai do repo; usa-o se estiver aberto.
repo_key="$(git -C "$path" rev-parse --path-format=absolute --git-common-dir)"
parent_id="$(jq -r --arg k "$repo_key" \
  'first(.result.workspaces[] | select(.worktree.repo_key? == $k and (.worktree.is_linked_worktree | not)) | .workspace_id) // empty' \
  <<<"$workspaces")"
if [[ -n "$parent_id" ]]; then
  herdr worktree open --workspace "$parent_id" --path "$path" --focus >/dev/null \
    || fail "falha ao abrir a worktree $path"
  exit 0
fi

herdr workspace create --cwd "$path" --focus >/dev/null || fail "falha ao criar workspace em $path"
