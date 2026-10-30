#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Pure screen-idle state machine. Screen-off is NOT system suspend."""
POWER=116
VOLUME_UP=115
VOLUME_DOWN=114
WAKE_KEYS=frozenset((POWER,VOLUME_UP,VOLUME_DOWN))


class ScreenPolicy:
    def __init__(self,idle_seconds=60,now=0):
        if not 5<=idle_seconds<=3600:raise ValueError('Idle timeout outside 5..3600s')
        self.idle_seconds=idle_seconds;self.deadline=now+idle_seconds;self.on=True;self.held=set()

    def key(self,code,value,now):
        if code not in WAKE_KEYS or value not in (0,1,2):return None
        if value==0:self.held.discard(code);return None
        if value==2 or code in self.held:return None
        self.held.add(code)
        if not self.on:
            self.on=True;self.deadline=now+self.idle_seconds;return 'on'
        if code==POWER:
            self.on=False;return 'off'
        self.deadline=now+self.idle_seconds
        return None

    def tick(self,now):
        if self.on and now>=self.deadline:
            self.on=False;return 'off'
        return None
