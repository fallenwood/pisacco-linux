#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exact user-authorized order; never substitute SSIDs or rely on NM priority.

Each startup tries primary once, then fallback once. Never leave a successful
fallback merely to probe the known weak primary. Crash/thermal/identity failures
are fatal, NOT reasons to connect another SSID.
"""
from pathlib import Path
import hashlib
import stat

TARGETS=(('Chaldea','a',20),('Chaldea-2.4G','bg',25))
CAP_KHZ=1094400
START_MC=40000
ABORT_MC=45000


def network_policy(cfg):
    enabled=cfg.get('ipv6_auto',False)
    if type(enabled) is not bool:
        raise ValueError('IPv6 opt-in must be boolean')
    return {'ipv6_method':'auto' if enabled else 'disabled',
            'profile_suffix':'-ipv6' if enabled else ''}


def profile_name(cfg,ssid):
    if ssid not in {target[0] for target in TARGETS}:
        raise ValueError('Unapproved network profile target')
    return 'picasso-auto-'+ssid+network_policy(cfg)['profile_suffix']


def derive_both(passphrase):
    raw=passphrase.encode('utf-8')
    if not 8<=len(raw)<=63 or any(c in passphrase for c in '\r\n\0'):
        raise ValueError('Require shared 8–63 UTF-8 byte passphrase; a raw PSK cannot be shared between different SSIDs')
    return {ssid:hashlib.pbkdf2_hmac('sha1',raw,ssid.encode('ascii'),4096,32).hex() for ssid,_,_ in TARGETS}


def private_file(path,minimum=1,maximum=16384):
    p=Path(path);s=p.lstat()
    if not (stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and
            stat.S_IMODE(s.st_mode)==0o600 and minimum<=s.st_size<=maximum):
        raise ValueError('Unsafe private file metadata')
    return p


def attempt_order(activate,validate,disconnect):
    """Only an ordinary activation failure permits fallback; validation raises.

    Callbacks must propagate thermal/DSP/identity/regulatory exceptions. The
    activate callback returns False only for a normal bounded nmcli failure.
    """
    attempts=[]
    for ssid,band,seconds in TARGETS:
        attempts.append(ssid)
        if activate(ssid,band,seconds):
            validate(ssid)
            return {'ssid':ssid,'attempt_order':attempts,'fallback_used':len(attempts)==2}
        disconnect(ssid)
    raise RuntimeError('Both authorized SSIDs failed bounded activation')
