#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import time

ID_FILE = f"/tmp/state-notification-id-{os.getuid()}"


def run(*args):
    return subprocess.run(
        args,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def parse_action(value):
    if value == "toggle":
        return value

    # Absolute volume: 0..100
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        volume = float(value)

        if not 0 <= volume <= 100:
            raise argparse.ArgumentTypeError(
                "absolute volume must be between 0 and 100"
            )

        return value

    # Relative volume: e.g. 2+, 2-, 2.5+, 10-
    if re.fullmatch(r"\d+(?:\.\d+)?[+-]", value):
        return value

    raise argparse.ArgumentTypeError("must be a volume such as 50, 2+, 2-, or toggle")


def get_volume():
    output = run("wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@")

    match = re.search(
        r"Volume:\s+([0-9.]+)(?:\s+(\[MUTED\]))?",
        output,
    )

    if not match:
        raise RuntimeError(f"Could not parse wpctl output: {output!r}")

    volume = round(float(match.group(1)) * 100)
    muted = match.group(2) == "[MUTED]"

    return volume, muted


def get_device_name():
    output = run("wpctl", "inspect", "@DEFAULT_AUDIO_SINK@")

    for line in output.splitlines():
        match = re.search(
            r'(?:node|card|device|media)\.description\s*=\s*"([^"]*)"',
            line,
        )

        if match:
            return match.group(1)

    return ""


def adjust_volume(action):
    if action == "toggle":
        subprocess.run(
            [
                "wpctl",
                "set-mute",
                "@DEFAULT_AUDIO_SINK@",
                "toggle",
            ],
            check=True,
        )
        return

    if action[-1:] in "+-":
        # Relative adjustment.
        amount = action[:-1]
        direction = action[-1]

        subprocess.run(
            [
                "wpctl",
                "set-volume",
                "@DEFAULT_AUDIO_SINK@",
                f"{amount}%{direction}",
            ],
            check=True,
        )
    else:
        # Absolute volume.
        subprocess.run(
            [
                "wpctl",
                "set-volume",
                "@DEFAULT_AUDIO_SINK@",
                f"{action}%",
            ],
            check=True,
        )


def show_notification():
    # Give PipeWire a moment to register the change.
    time.sleep(0.05)

    volume, muted = get_volume()
    device_name = get_device_name()

    if muted:
        summary = "Muted"
        body = f"{device_name} (volume: {volume}%)"
        icon = "audio-volume-muted"
    else:
        if volume == 0:
            icon = "audio-volume-muted"
        elif volume < 33:
            icon = "audio-volume-low"
        elif volume < 90:
            icon = "audio-volume-medium"
        else:
            icon = "audio-volume-high"

        summary = f"Volume: {volume}%"
        body = device_name

    replace_id = None

    try:
        with open(ID_FILE) as f:
            replace_id = f.read().strip() or None
    except FileNotFoundError:
        pass

    command = [
        "notify-send",
        "--print-id",
        "-u",
        "low",
        "-e",
        "-t",
        "2000",
        "-i",
        icon,
        "-h",
        f"int:value:{volume}",
        "-h",
        "string:synchronous:volume-change",
    ]

    if replace_id:
        command.extend(["--replace-id", replace_id])

    command.extend([summary, body])

    result = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )

    with open(ID_FILE, "w") as f:
        f.write(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Set or adjust the default audio sink volume and show a notification."
        )
    )

    parser.add_argument(
        "action",
        nargs="?",
        type=parse_action,
        metavar="VOLUME",
        help=(
            "absolute volume (0-100), relative adjustment (e.g. 2+, 2-), or toggle mute"
        ),
    )

    args = parser.parse_args()

    if args.action is not None:
        adjust_volume(args.action)

    show_notification()


if __name__ == "__main__":
    main()
