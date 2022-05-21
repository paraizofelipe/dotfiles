#!/bin/bash

# Battery 0: Discharging, 99%, 09:19:48 remaining
# Battery 0: Unknown, 99%


BAT=$(upower -i $(upower -e | grep BAT) | grep --color=never -E "state|to\ full|to\ empty|percentage")

CHARGE=$(echo "$BAT" | grep percentage | cut -d : -f 2)
STATE=$(echo "$BAT" | grep state | cut -d : -f 2)
TIME=$(echo "$BAT" | grep time | cut -d : -f 2)
ICON=""

if [ $STATE == "discharging" ]; then
    [ ${CHARGE%?} -lt 100 -a ${CHARGE%?} -ge 90 ] && ICON=" "
    [ ${CHARGE%?} -lt 90 -a ${CHARGE%?} -ge 70 ] && ICON=" "
    [ ${CHARGE%?} -lt 70 -a ${CHARGE%?} -ge 50 ] && ICON=" "
    [ ${CHARGE%?} -lt 50 -a ${CHARGE%?} -ge 30 ] && ICON=" "
    [ ${CHARGE%?} -lt 30 -a ${CHARGE%?} -ge 10 ] && ICON=" "
fi

[ $STATE == "fully-charged" ] && ICON="" && TIME="00:00" && CHARGE='100%'

# Full and short texts
echo "$ICON $CHARGE - ($TIME)"
echo "$ICON $CHARGE"

# Set urgent flag below 5% or use orange below 20%
[ ${CHARGE%?} -le 5 ] && exit 33
[ ${CHARGE%?} -le 65 ] && echo "#FFEA00"
[ ${CHARGE%?} -le 20 ] && echo "#FF8000"

exit 0
