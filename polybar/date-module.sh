#!/bin/bash

# Script para exibir data e hora no polybar
while true; do
    DATE=$(date '+%d %B %Y')
    TIME=$(date '+%H:%M:%S')
    echo " $DATE  $TIME"
    sleep 1
done
