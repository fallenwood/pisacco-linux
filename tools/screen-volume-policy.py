#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""User-selected volume-UP-only screen policy, never system suspend."""

class VolumePolicy:
    def __init__(self,now=0,held=False):
        self.on=True;self.deadline=now+15;self.held=held

    def key(self,code,value,now):
        if code!=115:return None
        if value==0:self.held=False;return None
        if value!=1 or self.held:return None
        self.held=True;self.deadline=now+15
        if not self.on:self.on=True;return 'on'
        return None

    def tick(self,now):
        if self.on and now>=self.deadline:self.on=False;return 'off'
        return None
