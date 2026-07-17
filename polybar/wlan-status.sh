#!/bin/bash
# Script para mostrar status do WiFi no polybar

# Interface WiFi
INTERFACE="wlp0s20f3"

# Verifica se o WiFi está conectado
if nmcli -t -f DEVICE,STATE device | grep "^$INTERFACE:connected" >/dev/null 2>&1; then
    # Conectado - ícone aqua
    echo "%{F#8ec07c} %{F-}"
else
    # Desconectado - ícone vermelho
    echo "%{F#fb4934} %{F-}"
fi
