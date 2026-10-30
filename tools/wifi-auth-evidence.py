#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Verify native supplicant handshake evidence without requesting secret APIs.

NetworkManager may use D-Bus without creating a wpa_cli control socket. Parse
only the caller's current-boot journal, after this trial's monotonic cutoff.
RSN-only profile enforcement and live station authorization are checked by caller.
"""
import json
import re

MAC=r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})'
KEY=re.compile(r'^wlan0: WPA: Key negotiation completed with '+MAC+r' \[PTK=CCMP GTK=CCMP\]$')
CONNECTED=re.compile(r'^wlan0: CTRL-EVENT-CONNECTED - Connection to '+MAC+r' completed(?: |$)')


def verify_ccmp_handshake(journal_jsonl, since_monotonic_seconds, *, rsn_only):
    if not rsn_only or since_monotonic_seconds<0:
        raise ValueError('Require enforced RSN-only profile and valid trial cutoff')
    rows=[]
    for line in journal_jsonl.splitlines():
        if not line.strip():
            continue
        obj=json.loads(line)
        stamp=int(obj.get('__MONOTONIC_TIMESTAMP',0))/1_000_000
        message=obj.get('MESSAGE','')
        if stamp>=since_monotonic_seconds and isinstance(message,str):
            rows.append((stamp,message))
    rows.sort(key=lambda row:row[0])
    keys={};latest=None
    for stamp,message in rows:
        key=KEY.match(message)
        if key:
            keys[key[1].lower()]=stamp
        event=CONNECTED.match(message)
        if event:
            peer=event[1].lower()
            latest={'stamp':stamp,'matching_ccmp_key':peer in keys and keys[peer]<=stamp}
        if message.startswith('wlan0: CTRL-EVENT-DISCONNECTED'):
            latest=None
            keys.clear()
    if not latest or not latest['matching_ccmp_key']:
        raise ValueError('No fresh connected event with matching CCMP pairwise/group negotiation')
    return {'handshake_verified':True,'pairwise_cipher':'CCMP','group_cipher':'CCMP',
            'protocol':'WPA2/RSN (enforced live profile)',
            'source':'current-boot native supplicant journal after trial monotonic cutoff',
            'connected_event_monotonic_seconds':latest['stamp'],
            'secret_properties_read':False,'wpa_cli_socket_required':False}
