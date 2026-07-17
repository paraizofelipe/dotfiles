#!/bin/bash

# Netskope Details Display Script
# This script forces a cache refresh and displays the current Netskope status
# It keeps the terminal open until the user presses a key

# Gruvbox colors for terminal output
COLOR_RESET="\e[0m"
COLOR_BLUE="\e[38;5;109m"    # Gruvbox blue
COLOR_RED="\e[38;5;167m"     # Gruvbox red
COLOR_GREEN="\e[38;5;142m"   # Gruvbox green
COLOR_YELLOW="\e[38;5;214m"  # Gruvbox yellow
COLOR_GRAY="\e[38;5;245m"    # Gruvbox gray

# Cache file location
CACHE_FILE="/tmp/netskope_status_cache_$USER"

echo -e "${COLOR_YELLOW}╔════════════════════════════════════════════════════╗${COLOR_RESET}"
echo -e "${COLOR_YELLOW}║        NETSKOPE STATUS - REFRESHING CACHE         ║${COLOR_RESET}"
echo -e "${COLOR_YELLOW}╚════════════════════════════════════════════════════╝${COLOR_RESET}"
echo ""

# Force cache refresh by removing the old cache file
if [ -f "$CACHE_FILE" ]; then
    rm -f "$CACHE_FILE"
    echo -e "${COLOR_GRAY}Cache anterior removido...${COLOR_RESET}"
fi

echo -e "${COLOR_BLUE}Consultando status do Netskope...${COLOR_RESET}"
echo ""

# Check if nsclient command exists
if ! command -v nsclient &>/dev/null; then
    echo -e "${COLOR_RED}✗ Erro: Comando 'nsclient' não encontrado!${COLOR_RESET}"
    echo ""
    echo -e "${COLOR_GRAY}Pressione qualquer tecla para fechar...${COLOR_RESET}"
    read -n 1 -s -r
    exit 1
fi

# Get Netskope configuration
output=$(nsclient show-config 2>&1)
exit_code=$?

# Display the full output
echo -e "${COLOR_YELLOW}════════════════════════════════════════════════════${COLOR_RESET}"
echo "$output"
echo -e "${COLOR_YELLOW}════════════════════════════════════════════════════${COLOR_RESET}"
echo ""

# Determine and display status
if [ $exit_code -ne 0 ] || [ -z "$output" ]; then
    echo -e "${COLOR_RED}✗ STATUS: DESCONECTADO${COLOR_RESET}"
    status="disconnected"
elif echo "$output" | grep -q "Private Access: Connected"; then
    if echo "$output" | grep -qi "configuration is up-to-date"; then
        echo -e "${COLOR_BLUE}✓ STATUS: CONECTADO E ATUALIZADO${COLOR_RESET}"
        status="connected_updated"
    else
        echo -e "${COLOR_GREEN}⚠ STATUS: CONECTADO (configuração desatualizada)${COLOR_RESET}"
        status="connected_outdated"
    fi
else
    echo -e "${COLOR_RED}✗ STATUS: DESCONECTADO${COLOR_RESET}"
    status="disconnected"
fi

# Update cache with new status
echo "$status" > "$CACHE_FILE"
echo ""
echo -e "${COLOR_GRAY}Cache atualizado em: $(date '+%d/%m/%Y %H:%M:%S')${COLOR_RESET}"

# Wait for user input before closing
echo ""
echo -e "${COLOR_YELLOW}╔════════════════════════════════════════════════════╗${COLOR_RESET}"
echo -e "${COLOR_YELLOW}║  Pressione qualquer tecla para fechar...          ║${COLOR_RESET}"
echo -e "${COLOR_YELLOW}╚════════════════════════════════════════════════════╝${COLOR_RESET}"
read -n 1 -s -r

# Force polybar to update by sending a signal (optional)
# This will make the polybar module refresh immediately after closing
polybar-msg action netskope hook 0 2>/dev/null || true
