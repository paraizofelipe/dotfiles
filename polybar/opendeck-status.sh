#!/bin/sh

# Ícone para o OpenDeck (usando um ícone de deck/gamepad)
ICON=""

# Cores Gruvbox
COLOR_BLUE="#ebdbb2"
COLOR_RED="#fb4934"

# Verifica se o OpenDeck está em execução
# Procura por processos relacionados ao OpenDeck
if pgrep -f -i "opendeck" >/dev/null 2>&1; then
    # OpenDeck está em execução - azul
    echo "%{F$COLOR_BLUE}$ICON%{F-}"
else
    # OpenDeck não está em execução - vermelho
    echo "%{F$COLOR_RED}$ICON%{F-}"
fi
