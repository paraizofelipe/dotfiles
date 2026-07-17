#!/bin/bash

# Script para monitorar notificações do deadd-notification-center
# e mudar a cor do ícone no polybar
#
# O deadd não expõe facilmente o contador de notificações,
# então usamos dbus-monitor para detectar quando notificações são enviadas/fechadas

# Ícone (Font Awesome bell)
ICON="  "

# Cores (Gruvbox)
COLOR_NO_NOTIF="#ebdbb2" # branco (foreground)
COLOR_HAS_NOTIF="#fabd2f"

# Arquivo de estado para rastrear notificações
STATE_FILE="/tmp/deadd-notification-count-$USER"

# Inicializa o arquivo de estado se não existir
if [ ! -f "$STATE_FILE" ]; then
    echo "0" >"$STATE_FILE"
fi

# Função para incrementar contador
increment_count() {
    count=$(cat "$STATE_FILE" 2>/dev/null || echo "0")
    count=$((count + 1))
    echo "$count" >"$STATE_FILE"
}

# Função para resetar contador (quando o centro é aberto)
reset_count() {
    echo "0" >"$STATE_FILE"
}

# Função para exibir o status atual
display_status() {
    count=$(cat "$STATE_FILE" 2>/dev/null || echo "0")

    if [ "$count" -gt 0 ]; then
        # Tem notificações não lidas - ícone amarelo e underline amarelo
        # echo "%{F$COLOR_HAS_NOTIF}%{u$COLOR_HAS_NOTIF}%{+u}$ICON $count%{-u}%{F-}"
        echo "%{F$COLOR_HAS_NOTIF}%{u$COLOR_HAS_NOTIF}%{+u}$ICON%{F-}"
    else
        # Sem notificações não lidas - ícone padrão sem underline
        echo "$ICON"
    fi
}

# Monitora notificações via dbus-monitor em background
(
    dbus-monitor "interface='org.freedesktop.Notifications',member='Notify'" 2>/dev/null |
        while read -r line; do
            if echo "$line" | grep -q "method call"; then
                increment_count
            fi
        done
) &

MONITOR_PID=$!

# Cleanup ao sair
trap "kill $MONITOR_PID 2>/dev/null; exit" EXIT INT TERM

# Loop principal - atualiza display
while true; do
    display_status
    sleep 2
done
