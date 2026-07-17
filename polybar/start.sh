#!/bin/bash 

killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# if type "xrandr"; then
#   for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
#     MONITOR=$m polybar -c $HOME/.config/polybar/config.ini --reload mainbar-i3 &
#   done
# else
#   polybar -c config.ini --reload mainbar-i3 &
# fi
#

polybar -c $HOME/.config/polybar/config-3monitor.ini --reload mainbar-i3 &
polybar -c $HOME/.config/polybar/config-3monitor.ini --reload vertical-i3 &
polybar -c $HOME/.config/polybar/config-3monitor.ini --reload horizontal-i3 &

# polybar -c $HOME/.config/polybar/config-3monitor.ini --reload verical2-i3 &
