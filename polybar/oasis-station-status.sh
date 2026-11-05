#!/bin/bash

# Ícone do polybar para a Station do oasis-notify.
#
# Fica amarelo quando chegaram notificações desde a última vez que a Station
# foi aberta (ou fechada) pelo `oasis-notify station`. O total vem do próprio
# daemon (`station list --count`); o dbus-monitor só avisa quando recontar:
# Notify (nova notificação), Toggle/Clear da Station (o List não, senão a
# própria recontagem dispararia outra) e troca de dono
# do nome (daemon reiniciado). O timeout do read cobre o botão Clear da
# própria Station, que não passa pelo D-Bus.

OASIS="$HOME/.local/bin/oasis-notify"

# Ícone (Font Awesome bell)
ICON="  "

# Cores (Gruvbox)
COLOR_HAS_NOTIF="#fabd2f"

# Segundos entre recontagens sem eventos
REFRESH=5

seen=0

count_station() {
    local count
    count=$(timeout 2s "$OASIS" station list --count 2>/dev/null)
    # Falha não é "zero": zerar o seen faria notificações já vistas acenderem de novo
    [[ "$count" =~ ^[0-9]+$ ]] && echo "$count"
}

display_status() {
    local count=$1
    # A Station encolheu (Clear ou daemon reiniciado): tudo já foi visto
    ((count < seen)) && seen=$count
    if ((count > seen)); then
        echo "%{F$COLOR_HAS_NOTIF}%{u$COLOR_HAS_NOTIF}%{+u}$ICON%{-u}%{F-}"
    else
        echo "$ICON"
    fi
}

coproc MONITOR {
    exec dbus-monitor \
        "type='method_call',interface='org.freedesktop.Notifications',member='Notify'" \
        "type='method_call',interface='local.oasis.Station',member='Toggle'" \
        "type='method_call',interface='local.oasis.Station',member='Clear'" \
        "type='signal',interface='org.freedesktop.DBus',member='NameOwnerChanged',arg0='org.freedesktop.Notifications'" \
        2>/dev/null
}
trap 'kill "$MONITOR_PID" 2>/dev/null; exit' EXIT INT TERM

seen=$(count_station) || seen=0
display_status "$seen"
last=$seen

while true; do
    toggled=0
    # Junta a rajada de linhas de um evento numa única recontagem
    if read -r -t "$REFRESH" line <&"${MONITOR[0]}"; then
        [[ "$line" == *"member=Toggle"* ]] && toggled=1
        while read -r -t 0.2 line <&"${MONITOR[0]}"; do
            [[ "$line" == *"member=Toggle"* ]] && toggled=1
        done
    elif [[ -z "${MONITOR_PID:-}" ]] || ! kill -0 "$MONITOR_PID" 2>/dev/null; then
        exit 1 # dbus-monitor morreu; o polybar reinicia o módulo
    fi
    count=$(count_station) || count=$last # consulta falhou: mantém a última contagem válida
    last=$count
    ((toggled)) && seen=$count
    display_status "$count"
done
