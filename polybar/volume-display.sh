#!/bin/bash

# Script para exibir volume no polybar (atualização contínua)

# Função para obter volume
get_volume() {
    pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\d+(?=%)' | head -1
}

# Função para obter status mute
get_mute() {
    pactl get-sink-mute @DEFAULT_SINK@ | grep -q 'yes' && echo "yes" || echo "no"
}

# Monitorar mudanças no pulseaudio
pactl subscribe | grep --line-buffered "sink" | while read -r line; do
    volume=$(get_volume)
    muted=$(get_mute)

    if [ "$muted" = "yes" ]; then
        echo " 0%"
    else
        echo " $volume%"
    fi
done &

# Primeira execução
volume=$(get_volume)
muted=$(get_mute)

if [ "$muted" = "yes" ]; then
    echo " 0%"
else
    echo " $volume%"
fi

# Manter script rodando
wait
