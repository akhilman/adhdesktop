#!/usr/bin/env python3

import json
import subprocess
import sys


def get_sinks():
    output = subprocess.run(
        ["pw-dump"],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    objects = json.loads(output)

    sinks = []

    for obj in objects:
        props = obj.get("info", {}).get("props", {})

        if props.get("media.class") != "Audio/Sink":
            continue

        if props.get("node.virtual") is True:
            continue

        sink_id = obj.get("id")
        name = props.get("node.description")
        if "bluez" in props.get("device.api", ""):
            icon = "bluetooth-active"
        elif props.get("device.bus") == "usb":
            icon = "drive-removable-media-usb"
        elif props.get("device.icon-name") == "audio-card-analog":
            icon = "audio-card"
        else:
            icon = props.get("device.icon-name", "")

        if not isinstance(sink_id, int):
            continue

        if not name:
            continue

        sinks.append((sink_id, name, icon))

    return sinks


def select_sink(sinks):
    # fuzzel dmenu input:
    #
    #   ID<TAB>NAME<NUL>icon<TAB>ICON
    #
    # fuzzel's --with-nth=2 hides the ID from the displayed text.
    data = "".join(
        f"{sink_id}\t{name}\0icon\x1f{icon}\n" for sink_id, name, icon in sinks
    )

    result = subprocess.run(
        [
            "fuzzel",
            "--dmenu",
            "--with-nth=2",
            "--prompt=Audio output: ",
        ],
        input=data,
        stdout=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        return None

    selection = result.stdout.strip()

    if not selection:
        return None

    # The first field is the sink ID.
    try:
        return int(selection.split("\t", 1)[0])
    except (ValueError, IndexError):
        return None


def main():
    sinks = get_sinks()

    if not sinks:
        print("No audio outputs found.", file=sys.stderr)
        return 1

    sink_id = select_sink(sinks)

    if sink_id is None:
        return 0

    subprocess.run(
        ["wpctl", "set-default", str(sink_id)],
        check=True,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
