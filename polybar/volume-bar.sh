#!/bin/bash

# Script simples para exibir barra de volume visual com rofi
# Tema Gruvbox

# Cores Gruvbox
BG="#282828"
FG="#ebdbb2"
PURPLE="#d3869b"
RED="#fb4934"

# Obter volume atual
VOLUME=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\d+(?=%)' | head -1)
MUTED=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -q 'yes' && echo "yes" || echo "no")

# Criar barra de volume visual (0-100)
create_bar() {
    local percent=$1
    local width=30
    local filled=$((percent * width / 100))

    # Criar barra
    local bar=""
    for ((i=0; i<width; i++)); do
        if [ $i -lt $filled ]; then
            bar+="█"
        else
            bar+="░"
        fi
    done

    echo "$bar"
}

# Obter ícone
if [ "$MUTED" = "yes" ]; then
    ICON=""
    COLOR=$RED
elif [ "$VOLUME" -eq 0 ]; then
    ICON=""
    COLOR=$FG
elif [ "$VOLUME" -lt 33 ]; then
    ICON=""
    COLOR=$FG
elif [ "$VOLUME" -lt 66 ]; then
    ICON=""
    COLOR=$FG
else
    ICON=""
    COLOR=$FG
fi

# Criar mensagem
BAR=$(create_bar $VOLUME)

if [ "$MUTED" = "yes" ]; then
    MESSAGE="$ICON  MUDO\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n$BAR\n0%"
else
    MESSAGE="$ICON  Volume: $VOLUME%\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n$BAR"
fi

# Exibir com rofi
echo -e "$MESSAGE" | rofi -dmenu \
    -p "" \
    -theme-str "window {width: 450px; height: 180px; location: north east; x-offset: -10px; y-offset: 30px;}" \
    -theme-str "mainbox {children: [message];}" \
    -theme-str "message {enabled: true; padding: 20px; border: 0px; background-color: $BG; text-color: $PURPLE;}" \
    -theme-str "textbox {horizontal-align: 0.5; vertical-align: 0.5; background-color: $BG; text-color: $FG;}" \
    -theme-str "element-text {font: 'Hack Nerd Font Mono 14'; background-color: $BG; text-color: $FG; horizontal-align: 0.5;}" \
    -theme-str "inputbar {enabled: false;}" \
    -theme-str "listview {enabled: false;}" \
    > /dev/null
