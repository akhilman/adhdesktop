#!/usr/bin/env python3
"""
ironbar-mic-watch.py
Toggles a CSS class on an Ironbar volume module when any mic capture port is active.
Uses pw-mon (native PipeWire) — event-driven, no polling.
"""

import logging
import subprocess

MODULE_NAME = "volume"
CLASS_NAME = "recording"


def set_class(active: bool):
    cmd = [
        "ironbar",
        "style",
        "add-class" if active else "remove-class",
        MODULE_NAME,
        CLASS_NAME,
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    log = logging.getLogger(__name__)

    process = subprocess.Popen(
        ["pactl", "subscribe"],
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None

    active = set()

    for line in process.stdout:
        line = line.strip()

        if "Event 'new' on source-output #" in line:
            source_output = line.rsplit("#", 1)[1]
            if not active:
                log.info("MICROPHONE OPENED")
                set_class(True)
            active.add(source_output)

        elif "Event 'remove' on source-output #" in line:
            source_output = line.rsplit("#", 1)[1]
            active.discard(source_output)
            if not active:
                log.info("MICROPHONE CLOSED")
                set_class(False)


if __name__ == "__main__":
    main()
