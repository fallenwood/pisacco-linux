#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""KEY_POWER hold/release only. Never change hardware reset or cold-start logic.

Request orderly shutdown only on RELEASE after a 2..3 second hold, so the
button is not still held when the PMIC powers off. Longer holds are rejected,
not treated as proof that hardware forced-reset can be prevented.
"""

class PowerHoldPolicy:
    def __init__(self):self.pressed_at=None;self.requested=False

    def key(self,code,value,stamp):
        if code!=116 or self.requested:return None
        if value==1:
            if self.pressed_at is None:self.pressed_at=stamp
            return None
        if value!=0:return None
        start=self.pressed_at;self.pressed_at=None
        if start is None:return None
        duration=stamp-start
        if 2<=duration<=3:
            self.requested=True;return 'orderly_poweroff'
        return None
