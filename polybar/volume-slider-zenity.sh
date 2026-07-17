#!/bin/bash

# Script para controle de volume com slider usando Zenity
# Tema Gruvbox

# Obter volume atual
get_volume() {
    pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\d+(?=%)' | head -1
}

CURRENT_VOLUME=$(get_volume)

# Criar slider com Zenity e capturar o novo valor
NEW_VOLUME=$(zenity --scale \
    --title="Volume Control" \
    --text="Ajuste o volume:" \
    --value=$CURRENT_VOLUME \
    --min-value=0 \
    --max-value=100 \
    --step=1 \
    --width=350 \
    --height=100 \
    2>/dev/null)

# Se o usuário escolheu um valor (não cancelou)
if [ $? -eq 0 ]; then
    # Atualizar volume
    pactl set-sink-volume @DEFAULT_SINK@ "${NEW_VOLUME}%"
    pactl set-sink-mute @DEFAULT_SINK@ 0
fi
