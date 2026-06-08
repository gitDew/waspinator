#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Run with sudo"
    exit 1
fi

if [ $# -lt 2 ]; then
    echo "Usage: add-wifi <ssid> <password> [priority]"
    exit 1
fi

SSID="$1"
PSK="$2"
PRIORITY="${3:-5}"

nmcli con add type wifi ifname wlan0 con-name "$SSID" ssid "$SSID" \
    wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PSK"

nmcli con mod "$SSID" connection.autoconnect-priority "$PRIORITY"

echo "Added $SSID with priority $PRIORITY"

