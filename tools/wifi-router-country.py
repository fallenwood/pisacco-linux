#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bind a reviewed router country to selected-BSS evidence and signed regdb rules."""
import re


def require(ok, message):
    if not ok:
        raise ValueError(message)


def country_code(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Z]{2}', value) is not None,
            'Require a real two-letter router country')
    return value


def frequency(value):
    number = float(value)
    require(number > 0 and number.is_integer(), 'Require an integral Picasso channel frequency')
    return int(number)


def kernel_rules(reference, country):
    country_code(country)
    require(reference.startswith('global\ncountry ' + country + ':') and '\nphy#' not in reference,
            'Require isolated observed router-country kernel/regdb reference')
    rules = []
    for line in reference.splitlines():
        if not line.lstrip().startswith('('):
            continue
        match = re.fullmatch(
            r'\s*\(([\d.]+) - ([\d.]+) @ ([\d.]+)\), \(N/A, ([\d.]+)\), \([^)]*\)(.*)',
            line)
        require(match is not None, 'Unsupported kernel regulatory rule')
        start, end, width, power = map(float, match.groups()[:4])
        flags = match[5]
        require(start < end and width > 0 and 0 < power <= 60,
                'Malformed router-country kernel rule')
        require('NO-OFDM' not in flags, 'Unsupported OFDM restriction in router-country reference')
        rules.append((start, end, width, power, 'DFS' in flags,
                      'NO-OUTDOOR' in flags, 'NO-IR' in flags or 'PASSIVE-SCAN' in flags))
    require(len(rules) >= 4, 'Incomplete router-country kernel rules')
    return rules


def link_identity(text, allowed_ssids):
    if text.strip() == 'Not connected.':
        return None
    bssid = re.search(r'^Connected to ((?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})\b', text)
    ssids = re.findall(r'^\s*SSID: (.+)$', text, re.M)
    frequencies = re.findall(r'^\s*freq: (\d+(?:\.\d+)?)$', text, re.M)
    require(bssid is not None and len(ssids) == len(frequencies) == 1,
            'Incomplete selected AP identity')
    require(ssids[0] in allowed_ssids, 'Unapproved router SSID')
    return {'bssid': bssid[1].lower(), 'ssid': ssids[0], 'frequency_mhz': frequency(frequencies[0])}


def country_from_records(records, identity):
    selected = []
    for record in records:
        header = re.match(r'((?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})\b', record)
        if header and header[1].lower() == identity['bssid']:
            selected.append(record)
    require(len(selected) == 1, 'Selected AP missing or ambiguous in cached BSS evidence')
    ssids = re.findall(r'^\s*SSID: ?(.*)$', selected[0], re.M)
    require(bool(ssids) and all(ssid in (identity['ssid'], '') for ssid in ssids),
            'Selected cached AP SSID mismatch')
    frequencies = re.findall(r'^\s*freq: (\d+(?:\.\d+)?)$', selected[0], re.M)
    require(len(frequencies) == 1 and frequency(frequencies[0]) == identity['frequency_mhz'],
            'Selected AP frequency changed')
    countries = re.findall(r'^\s*Country: ([A-Z]{2})(?:\s|$)', selected[0], re.M)
    require(bool(countries) and len(set(countries)) == 1, 'Selected AP Country IE missing or ambiguous')
    return country_code(countries[0])


def validate_policy(policy, reference):
    require(isinstance(policy, dict) and policy.get('mode') == 'reviewed_router_country_ie'
            and policy.get('router_country_legitimate') is True,
            'Explicit legitimate router-country policy required')
    country = country_code(policy.get('country'))
    kernel_rules(reference, country)
    return country
