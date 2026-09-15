#!/usr/bin/env python3

import json
import math
import subprocess

DEFAULT_METADATA = "default"
DEFAULT_SINK = "default.audio.sink"

SINK = "Audio/Sink"

VOLUME_ICONS = ["󰕿", "󰖀", "󰕾"]
MUTE_ICON = "󰝟"


def get_default_sink(obj):
    if obj.get("type") != "PipeWire:Interface:Metadata":
        return None

    props = obj.get("props", {})

    if props.get("metadata.name") != DEFAULT_METADATA:
        return {}

    for metadata in obj.get("metadata", []):
        key = metadata.get("key")
        value = metadata.get("value")

        if key != DEFAULT_SINK:
            continue

        if not isinstance(value, dict):
            continue

        name = value.get("name")

        if not isinstance(name, str):
            continue

        return name

    return None


def get_node_info(obj):
    if obj.get("type") != "PipeWire:Interface:Node":
        return None

    info = obj.get("info", {})
    props = info.get("props", {})

    name = props.get("node.name")
    media_class = props.get("media.class")

    if not isinstance(name, str):
        return None

    if media_class != SINK:
        return None

    return {
        "name": name,
        "media_class": media_class,
        "state": info.get("state"),
        "params": info.get("params", {}),
    }


def get_volume(node):
    params = node.get("params", {})
    props = params.get("Props")

    if not isinstance(props, list):
        return None

    for param in props:
        if not isinstance(param, dict):
            continue

        volumes = param.get("channelVolumes")

        if not isinstance(volumes, list) or not volumes:
            continue

        volumes = [
            float(volume) for volume in volumes if isinstance(volume, (int, float))
        ]

        if not volumes:
            continue

        # PipeWire volume is linear; convert to the percentage
        # representation normally used by wpctl.
        linear = max(volumes)
        return round(math.pow(linear, 1 / 3) * 100)

    return None


def is_muted(node):
    params = node.get("params", {})
    props = params.get("Props")

    if not isinstance(props, list):
        return None

    for param in props:
        if not isinstance(param, dict):
            continue

        mute = param.get("mute")

        if not isinstance(mute, bool):
            continue

        return mute

    return None


def print_status(sink, nodes):

    node = nodes.get(sink)

    if not node:
        return

    volume = get_volume(node)

    if volume is None:
        return

    if is_muted(node):
        icon = MUTE_ICON
    else:
        icon = VOLUME_ICONS[min(math.floor(volume * 3 / 100), 2)]

    print(f"{icon} {volume}%", flush=True)


def main():
    default_sink = None
    nodes = {}

    process = subprocess.Popen(
        ["pw-dump", "-Rm"],
        stdout=subprocess.PIPE,
        text=True,
    )
    for line in process.stdout:
        line = line.strip()

        if not line:
            continue

        try:
            objects = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(objects, list):
            continue

        changed = False

        for obj in objects:
            if not isinstance(obj, dict):
                continue

            new_default = get_default_sink(obj)

            if new_default:
                default_sink = new_default
                changed = True
                continue

            node = get_node_info(obj)

            if node is None:
                continue

            nodes[node["name"]] = node

            if node["name"] == default_sink:
                changed = True

        if changed:
            print_status(default_sink, nodes)


if __name__ == "__main__":
    main()
