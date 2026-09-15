#!/usr/bin/env python3

import json
import subprocess

AUDIO_SOURCE = "Audio/Source"
VIDEO_SOURCE = "Video/Source"
VIDEO_STREAM = "Stream/Input/Video"

MICROPHONE_VARIABLE = "privacy_active_microphone"
WEBCAM_VARIABLE = "privacy_active_webcam"
SCREENCAST_VARIABLE = "privacy_active_screencast"

CAMERA_ROLE = "Camera"


def get_node_info(obj):
    if obj.get("type") != "PipeWire:Interface:Node":
        return None

    info = obj.get("info", {})
    props = info.get("props", {})

    name = props.get("node.name")
    media_class = props.get("media.class")

    if not isinstance(name, str):
        return None

    if media_class not in (AUDIO_SOURCE, VIDEO_SOURCE, VIDEO_STREAM):
        return None

    return {
        "name": name,
        "media_class": media_class,
        "media_role": props.get("media.role"),
        "state": info.get("state"),
    }


def set_ironbar_variable(name, value):
    subprocess.run(
        ["ironbar", "var", "set", name, "true" if value else "false"],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def update_variables(nodes):
    microphone_active = any(
        node["media_class"] == AUDIO_SOURCE and node["state"] == "running"
        for node in nodes.values()
    )

    webcam_active = any(
        node["media_class"] == VIDEO_SOURCE
        and node["media_role"] == CAMERA_ROLE
        and node["state"] == "running"
        for node in nodes.values()
    )

    screencast_active = not webcam_active and any(
        node["media_class"] == VIDEO_STREAM and node["state"] == "running"
        for node in nodes.values()
    )

    set_ironbar_variable(MICROPHONE_VARIABLE, microphone_active)
    set_ironbar_variable(WEBCAM_VARIABLE, webcam_active)
    set_ironbar_variable(SCREENCAST_VARIABLE, screencast_active)


def main():
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

            id_ = obj.get("id")

            node = get_node_info(obj)

            if id_ is None:
                continue

            if node:
                nodes[id_] = node
                changed = True
            elif id_ in nodes:
                nodes.pop(id_)
                changed = True

        if changed:
            update_variables(nodes)


if __name__ == "__main__":
    main()
