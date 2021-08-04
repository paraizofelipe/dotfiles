#!/bin/bash

# Battery 0: Discharging, 99%, 09:19:48 remaining
# Battery 0: Unknown, 99%


BAT=$(acpi -b)

CHARGE=$(echo $BAT | cut -d , -f 2)
TYPE=$(echo $BAT | cut -d , -f 1 | cut -d : -f 2)
TIME=$(echo $BAT | grep -E -o [0-9]{2}:[0-9]{2})
ICON=""

if [ $TYPE == "Discharging" ]; then
    [ ${CHARGE%?} -lt 100 -a ${CHARGE%?} -ge 90 ] && ICON=" "
    [ ${CHARGE%?} -lt 90 -a ${CHARGE%?} -ge 70 ] && ICON=" "
    [ ${CHARGE%?} -lt 70 -a ${CHARGE%?} -ge 50 ] && ICON=" "
    [ ${CHARGE%?} -lt 50 -a ${CHARGE%?} -ge 30 ] && ICON=" "
    [ ${CHARGE%?} -lt 30 -a ${CHARGE%?} -ge 10 ] && ICON=" "
fi

[ ${CHARGE%?} -eq 100 ] && ICON="" && TIME="00:00"

# Full and short texts
echo "$ICON $CHARGE - ($TIME)"
echo "$ICON $CHARGE"

# Set urgent flag below 5% or use orange below 20%
[ ${CHARGE%?} -le 5 ] && exit 33
[ ${CHARGE%?} -le 65 ] && echo "#FFEA00"
[ ${CHARGE%?} -le 20 ] && echo "#FF8000"

exit 0
