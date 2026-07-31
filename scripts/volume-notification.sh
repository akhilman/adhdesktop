#!/bin/bash

# Script to create pop-up notification when volume changes.

# Create a delay so the change in volume can be registered:
sleep 0.05

# Get the volume and check if muted or not (STATE):
VOLUME=$(wpctl get-volume @DEFAULT_AUDIO_SINK@)
IS_MUTE=$(echo $VOLUME | awk '{print $3}')
VOLUME=$(echo $VOLUME | awk '{print $2 * 100}')

DEVICE_NAME=$(wpctl inspect @DEFAULT_AUDIO_SINK@ | grep -oP '(?<=(node|card|device|media)\.description = ").*(?=")' | head -n 1)

ID_FILE=/tmp/state-notification-id-$(id -u)

show_notification() {
        args=""
        if [ -f $ID_FILE ]; then
                id=$(cat $ID_FILE)
                if [ -n "$id" ]; then
                        args="$args --replace-id=$id"
                fi
        fi
        notify-send --print-id $args $@ "$summary" "$body" > $ID_FILE
}

# Have a different symbol for varying volume levels:
if [ x$IS_MUTE != x'[MUTED]' ]; then
        if [ "${VOLUME}" == "0" ]; then
                ICON=audio-volume-muted
        elif [ "${VOLUME}" -lt "33" ]; then
                ICON=audio-volume-low
        elif [ "${VOLUME}" -lt "90" ]; then
                ICON=audio-volume-medium
        else
                ICON=audio-volume-high
        fi

        summary="Volume: $VOLUME%" body="$DEVICE_NAME" \
        show_notification \
                -u low \
                -e \
                -t 2000 \
                -i ${ICON} \
                -h int:value:${VOLUME} \
                -h string:synchronous:volume-change

# If volume is muted, display the mute sybol:
else
        summary="Muted" body="$DEVICE_NAME (volume: $VOLUME%)"
        show_notification \
                -u low \
                -e \
                -t 2000 \
                -i audio-volume-muted \
                -h int:value:${VOLUME} \
                -h string:synchronous:volume-change
fi
