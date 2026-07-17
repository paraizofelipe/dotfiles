#!/bin/bash

# Toggle gsimplecal - if running, kill it; if not, start it
if pgrep -x "gsimplecal" > /dev/null; then
    killall gsimplecal
else
    gsimplecal &
fi
