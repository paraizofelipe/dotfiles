#!/usr/bin/env bash
# BROWSER usado no login de contas extras: abre a URL num perfil temporário e
# isolado. Janelas anônimas compartilham a sessão entre si, então um login
# anterior ainda aberto poderia ser reaproveitado pela conta seguinte.
set -euo pipefail
url="${1:?uso: agents-private-browser <url>}"
profile=$(mktemp -d "${TMPDIR:-/tmp}/agents-login.XXXXXX")

launch() {
  # Em segundo plano: o CLI não espera o navegador fechar; o perfil some quando ele fecha.
  ( "$@"; rm -rf "$profile" ) >/dev/null 2>&1 &
  disown
  exit 0
}

chromium_like() { launch "$1" --user-data-dir="$profile" --no-first-run --incognito "$url"; }

default=$(xdg-settings get default-web-browser 2>/dev/null || true)
case "$default" in
  *firefox*) launch firefox --no-remote --profile "$profile" --private-window "$url" ;;
  *brave*) chromium_like brave-browser ;;
  *chromium*) chromium_like chromium ;;
  *chrome*) chromium_like google-chrome ;;
esac
for cmd in google-chrome chromium brave-browser; do
  command -v "$cmd" >/dev/null && chromium_like "$cmd"
done
command -v firefox >/dev/null && launch firefox --no-remote --profile "$profile" --private-window "$url"
rm -rf "$profile"
echo "Abra numa janela privada: $url" >&2
