#!/usr/bin/env python3
"""Bridge: show ironbar only while niri overview is open."""

import json
import subprocess

BAR_NAME = "main"


def main():
    proc = subprocess.Popen(
        ["niri", "msg", "--json", "event-stream"],
        stdout=subprocess.PIPE,
        text=True,
    )
    for line in proc.stdout:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if overview := event.get("OverviewOpenedOrClosed"):
            cmd = "show" if overview.get("is_open") else "hide"
            subprocess.run(
                ["ironbar", "bar", BAR_NAME, cmd],
                stdout=subprocess.DEVNULL,
                check=False,
            )


if __name__ == "__main__":
    main()
