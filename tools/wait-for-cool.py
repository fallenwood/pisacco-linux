#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Wait without arming hardware; retain the services' own thermal checks."""
from pathlib import Path
import time

STARTUP_LIMIT_MC = 65000


def temperatures():
    values = {
        p.parent.name: int(p.read_text())
        for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')
    }
    if not values or not all(-10000 <= value <= 150000 for value in values.values()):
        raise RuntimeError('Invalid/missing thermal telemetry')
    return values


def wait_for_cool():
    deadline = time.monotonic() + 300
    consecutive = 0
    print('Waiting for three samples strictly below 65C; hardware not armed', flush=True)
    while time.monotonic() < deadline:
        values = temperatures()
        consecutive = consecutive + 1 if max(values.values()) < STARTUP_LIMIT_MC else 0
        if consecutive == 3:
            print('Startup temperature below 65C confirmed', flush=True)
            return
        time.sleep(1)
    raise TimeoutError('Startup temperature did not settle below 65C within 300s')


if __name__ == '__main__':
    wait_for_cool()
