#!/bin/bash 

IFACE=$(ip a | grep -E -o "tun0:|pptp0:")
ICON=" "

[ $IFACE ] && ICON=""

echo "$ICON vpn"
echo "$ICON vpn"

[ ! $IFACE ] && echo "#454947"

exit 0
