#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Parse iw BSS *record boundaries*, never headings such as 'BSS Load:'.

Only retain records for the explicitly authorized SSID. This parser does not
establish association, frame transmission, firmware ABI or regulatory compliance.
"""
import re


def bss_records(text):
    return re.split(r'(?m)^BSS ', text)[1:]


def active_2g_frequencies(phy):
    """Use auditable enabled IR-capable PHY channels, never one cached AP channel.

    This is not a regulatory audit: the caller must first verify the actual PHY
    against the user's SG reference. Do not remove no-IR/disabled restrictions.
    """
    frequencies=[]
    for line in phy.splitlines():
        match=re.match(r'\s*\*\s+(\d+(?:\.\d+)?)\s+MHz\s+\[\d+\](.*)',line)
        if not match:
            continue
        freq=float(match[1]);flags=match[2].lower()
        if 'disabled' in flags or 'no ir' in flags:
            continue
        if 2412<=freq<=2472 and freq.is_integer() and (int(freq)-2407)%5==0:
            if int(freq) not in frequencies:
                frequencies.append(int(freq))
    if not frequencies:
        raise ValueError('No enabled IR-capable 2.4GHz channels in audited PHY')
    return frequencies


def target_bss_records(text, ssid):
    if not ssid or any(c in ssid for c in '\n\r\0'):
        raise ValueError('Expected one nonempty SSID without control delimiters')
    expected = 'SSID: ' + ssid
    return [record for record in bss_records(text)
            if any(line.strip() == expected for line in record.splitlines())]
