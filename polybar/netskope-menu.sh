#!/bin/bash

# Netskope Menu Script for Polybar
# Uses rofi to display menu options and D-Bus to trigger actions

THEME="$HOME/.config/rofi/themes/netskope_menu.rasi"

# D-Bus configuration
DBUS_DEST="netskope-client.stagentapp"
DBUS_PATH="/org/ayatana/NotificationItem/com_netskope_stagentui/Menu"
DBUS_INTERFACE="com.canonical.dbusmenu"

# Function to send D-Bus event to Netskope menu
send_dbus_event() {
    local item_id=$1
    dbus-send --session --dest="$DBUS_DEST" --type=method_call \
        "$DBUS_PATH" "$DBUS_INTERFACE.Event" \
        int32:"$item_id" string:"clicked" variant:int32:0 uint32:$(date +%s)
}

# Get current status from nsclient
get_status() {
    if ! command -v nsclient &>/dev/null; then
        echo "Disconnected"
        return
    fi

    local output
    output=$(nsclient show-config 2>&1)

    if [ $? -ne 0 ] || [ -z "$output" ]; then
        echo "Disconnected"
        return
    fi

    if echo "$output" | grep -q "Private Access: Connected"; then
        echo "Connected"
    else
        echo "Disconnected"
    fi
}

# Menu options with icons
STATUS=$(get_status)
declare -a options=(
    "  Status: $STATUS"
    "  Re-authenticate"
    "  Configuration"
    "  View Blocked Events"
    "  Save Logs"
    "  Advanced Debugging"
    "  About"
)

# Show rofi menu
chosen=$(printf '%s\n' "${options[@]}" | rofi -dmenu -i -p " Netskope" -theme "$THEME")

# Handle selection
case "$chosen" in
    *"Re-authenticate"*)
        send_dbus_event 4
        ;;
    *"Configuration"*)
        send_dbus_event 7
        ;;
    *"View Blocked Events"*)
        send_dbus_event 11
        ;;
    *"Save Logs"*)
        send_dbus_event 9
        ;;
    *"Advanced Debugging"*)
        send_dbus_event 10
        ;;
    *"About"*)
        send_dbus_event 14
        ;;
esac
