#!/bin/bash

# Script para exibir controle de volume visual com rofi
# Tema Gruvbox

# Obter volume atual
get_volume() {
    pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\d+(?=%)' | head -1
}

# Obter status mute
get_mute() {
    pactl get-sink-mute @DEFAULT_SINK@ | grep -q 'yes' && echo "yes" || echo "no"
}

# Criar barra de volume visual
create_volume_bar() {
    local volume=$1
    local bar_length=20
    local filled=$((volume * bar_length / 100))
    local empty=$((bar_length - filled))

    # Cores Gruvbox
    local bar=""

    # Criar barra preenchida
    for ((i=0; i<filled; i++)); do
        bar+="█"
    done

    # Criar barra vazia
    for ((i=0; i<empty; i++)); do
        bar+="░"
    done

    echo "$bar"
}

# Obter ícone baseado no volume
get_icon() {
    local volume=$1
    local muted=$2

    if [ "$muted" = "yes" ]; then
        echo ""
    elif [ "$volume" -eq 0 ]; then
        echo ""
    elif [ "$volume" -lt 33 ]; then
        echo ""
    elif [ "$volume" -lt 66 ]; then
        echo ""
    else
        echo ""
    fi
}

# Ajustar volume
adjust_volume() {
    case $1 in
        "+")
            pactl set-sink-volume @DEFAULT_SINK@ +5%
            ;;
        "-")
            pactl set-sink-volume @DEFAULT_SINK@ -5%
            ;;
        "mute")
            pactl set-sink-mute @DEFAULT_SINK@ toggle
            ;;
    esac
}

# Menu principal
show_volume_menu() {
    local volume=$(get_volume)
    local muted=$(get_mute)
    local icon=$(get_icon $volume $muted)
    local bar=$(create_volume_bar $volume)

    # Opções do menu
    local options=""
    options+="$icon  Volume: $volume%\n"
    options+="$bar\n"
    options+="\n"
    options+="  Aumentar (+5%)\n"
    options+="  Diminuir (-5%)\n"

    if [ "$muted" = "yes" ]; then
        options+="  Desmutar"
    else
        options+="  Mutar"
    fi

    # Exibir menu com rofi
    echo -e "$options" | rofi -dmenu \
        -i \
        -p "Volume Control" \
        -theme-str 'window {width: 400px;}' \
        -theme-str 'listview {lines: 6;}' \
        -theme-str 'element-text {horizontal-align: 0.5;}' \
        -theme-str 'inputbar {children: [prompt];}' \
        -theme-str '* {background-color: #282828; foreground-color: #ebdbb2; border-color: #d3869b;}' \
        -theme-str 'element selected {background-color: #d3869b; text-color: #282828;}' \
        -no-custom \
        -format 's' | {

        read -r choice

        case "$choice" in
            *"Aumentar"*)
                adjust_volume "+"
                show_volume_menu
                ;;
            *"Diminuir"*)
                adjust_volume "-"
                show_volume_menu
                ;;
            *"Mutar"*|*"Desmutar"*)
                adjust_volume "mute"
                show_volume_menu
                ;;
        esac
    }
}

# Executar menu
show_volume_menu
