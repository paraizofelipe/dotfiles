#!/bin/bash
# Script para menu de energia com rofi
# Exibe opções para suspender, reiniciar e desligar o sistema

# Opções do menu com ícones Font Awesome
shutdown="  Desligar"
reboot="  Reiniciar"
suspend="  Suspender"

# Exibe o menu rofi
chosen=$(echo -e "$suspend\n$reboot\n$shutdown" | rofi -dmenu -i -p "  Energia" -theme ~/.config/rofi/themes/power_menu.rasi)

# Executa a ação escolhida
case $chosen in
$shutdown)
    systemctl poweroff
    ;;
$reboot)
    systemctl reboot
    ;;
$suspend)
    systemctl suspend
    ;;
esac
