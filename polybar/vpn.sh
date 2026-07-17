#!/bin/bash

if [[ $(ip a | grep -E -o "tun0:|pptp0:") ]]; then echo ""; else echo ""; fi
