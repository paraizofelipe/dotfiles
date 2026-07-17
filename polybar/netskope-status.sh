#!/bin/bash

# Netskope Status Script for Polybar
# Colors: Blue (connected & updated), Red (disconnected), Green (connected & outdated)
# Cache duration: 10 minutes

# Gruvbox colors
COLOR_BLUE="#83a598"  # Connected and updated
COLOR_RED="#fb4934"   # Disconnected
COLOR_GREEN="#b8bb26" # Connected but outdated

# Shield icon (Font Awesome)
ICON=""

# Cache configuration
CACHE_FILE="/tmp/netskope_status_cache_$USER"
CACHE_DURATION=600 # 10 minutes in seconds

# Function to get cached status or refresh if needed
get_netskope_status() {
    local current_time=$(date +%s)
    local cache_valid=false

    # Check if cache exists and is still valid
    if [ -f "$CACHE_FILE" ]; then
        local cache_time=$(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null)
        local time_diff=$((current_time - cache_time))

        if [ $time_diff -lt $CACHE_DURATION ]; then
            cache_valid=true
        fi
    fi

    # Return cached status if valid
    if [ "$cache_valid" = true ]; then
        cat "$CACHE_FILE"
        return
    fi

    # Refresh cache
    local status=$(check_netskope_status)
    echo "$status" >"$CACHE_FILE"
    echo "$status"
}

# Function to check actual Netskope status
check_netskope_status() {
    # Check if nsclient command exists
    if ! command -v nsclient &>/dev/null; then
        echo "disconnected"
        return
    fi

    # Get Netskope configuration, suppressing all errors completely
    local output
    output=$(nsclient show-config 2>&1)
    local exit_code=$?

    # Check if command failed or output is empty
    if [ $exit_code -ne 0 ] || [ -z "$output" ]; then
        echo "disconnected"
        return
    fi

    # Check if Private Access is Connected
    if echo "$output" | grep -q "Private Access: Connected"; then
        # Check if configuration is up-to-date
        if echo "$output" | grep -qi "configuration is up-to-date"; then
            echo "connected_updated"
        else
            echo "connected_outdated"
        fi
    else
        echo "disconnected"
    fi
}

# Main logic
main() {
    # Capture status, ensuring only the last line if multiple lines are returned
    local status=$(get_netskope_status | tail -n 1)

    case "$status" in
    "connected_updated")
        # Connected and up-to-date - BLUE
        echo "%{F$COLOR_BLUE}$ICON%{F-}"
        ;;
    "connected_outdated")
        # Connected but outdated - GREEN
        echo "%{F$COLOR_GREEN}$ICON%{F-}"
        ;;
    "disconnected" | *)
        # Disconnected or unknown - RED
        echo "%{F$COLOR_RED}$ICON%{F-}"
        ;;
    esac
}

# Execute main and ensure only one line is output
main 2>/dev/null
