#!/bin/bash 

IFACE=$(ip a | grep -E -o "tun0:|pptp0:")
ICON=" "

[ $IFACE ] && ICON=""

echo "$ICON vpn"
echo "$ICON vpn"

[ ! $IFACE ] && echo "#515754"

exit 0
