#!/bin/bash

# Script para controle de volume com slider usando YAD
# Tema Gruvbox

# Cores Gruvbox
BG="#282828"
FG="#ebdbb2"
PURPLE="#d3869b"

# Obter volume atual
get_volume() {
    pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\d+(?=%)' | head -1
}

# Obter status mute
is_muted() {
    pactl get-sink-mute @DEFAULT_SINK@ | grep -q 'yes' && echo 1 || echo 0
}

CURRENT_VOLUME=$(get_volume)
MUTED=$(is_muted)

# Criar slider com YAD
NEW_VOLUME=$(yad --scale \
    --title="Controle de Volume" \
    --text="Ajuste o volume:" \
    --value=$CURRENT_VOLUME \
    --min-value=0 \
    --max-value=100 \
    --step=1 \
    --print-partial \
    --hide-value \
    --width=350 \
    --height=100 \
    --center \
    --on-top \
    --skip-taskbar \
    --undecorated \
    --no-buttons \
    --close-on-unfocus \
    --borders=20 \
    --color="$BG" \
    2>/dev/null | while read -r value; do
        # Atualizar volume em tempo real
        pactl set-sink-volume @DEFAULT_SINK@ "${value}%"
        pactl set-sink-mute @DEFAULT_SINK@ 0
    done
)
