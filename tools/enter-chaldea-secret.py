#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Local interactive credential entry only; never start radio or log a PSK.

Allowlisted SSIDs Chaldea / Chaldea-2.4G, WPA2-PSK. Derive a PMK for the
selected SSID; the same passphrase normally gives different PMKs across SSIDs.
Store it in a distinct root-only phone tmpfs file for nmcli passwd-file.
The bounded connection test must unlink it
in finally; reboot also removes it. No persistent connection-secret storage.
"""
import argparse
import getpass
import hashlib
import os
from pathlib import Path
import re
import stat
import sys

DEST=Path('/run/picasso-chaldea.passwd')
SSID=b'Chaldea'
TARGETS={'Chaldea':Path('/run/picasso-chaldea.passwd'),
         'Chaldea-2.4G':Path('/run/picasso-chaldea-2g.passwd')}


def configure_target(name):
    global SSID,DEST
    if name not in TARGETS:raise ValueError('SSID is not an authorized local-entry target')
    SSID=name.encode('ascii')
    DEST=TARGETS[name]


def psk_value(secret):
    if re.fullmatch(r'[0-9a-fA-F]{64}',secret):return secret.lower()
    raw=secret.encode('utf-8')
    if not 8<=len(raw)<=63 or any(c in secret for c in '\n\r\0'):
        raise ValueError('WPA2 passphrase must be 8–63 UTF-8 bytes, or a 64-hex PSK')
    return hashlib.pbkdf2_hmac('sha1',raw,SSID,4096,32).hex()


def save(secret):
    parent=DEST.parent.stat()
    if parent.st_uid!=0 or parent.st_mode&0o022:raise ValueError('Unsafe runtime directory')
    data=('802-11-wireless-security.psk:'+psk_value(secret)+'\n').encode('ascii')
    fd=os.open(DEST,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        s=os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1:raise ValueError('Unsafe credential file')
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'wb',closefd=False) as f:f.write(data);f.flush();os.fsync(fd)
    finally:os.close(fd)


def main():
    if os.geteuid()!=0 or os.uname().release!='6.18.58-picasso-lts-wifi2' or not sys.stdin.isatty() or not sys.stderr.isatty():
        raise SystemExit('Run only in the pinned interactive SSH terminal on native wifi2; no stdin/chat/argv password input')
    parser=argparse.ArgumentParser(description='Interactive only; no password arguments or stdin')
    parser.add_argument('--ssid',choices=tuple(TARGETS),default='Chaldea')
    configure_target(parser.parse_args().ssid)
    if DEST.exists() or DEST.is_symlink():raise SystemExit('A pending credential already exists; do not overwrite it')
    one=getpass.getpass(SSID.decode('ascii')+' WPA2 password (not echoed): ')
    two=getpass.getpass('Repeat password: ')
    if one!=two:raise SystemExit('Passwords differ; nothing stored')
    try:save(one)
    except ValueError as e:raise SystemExit(str(e))
    print('Credential entered into root-only phone /run; no connection started. Reply 已录入. Test cleanup/reboot removes it.')


if __name__=='__main__':main()
