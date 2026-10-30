#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Strict 20MHz CN/verified-intersection audit against observed kernel CN rules.
No regdb/BDF/calibration/power modifications. NO-OUTDOOR and DFS retained.
"""
import re


def cn_rules(reference):
    if not reference.startswith('global\ncountry CN:') or '\nphy#' in reference:
        raise ValueError('Require isolated observed CN kernel/regdb reference')
    rules=[]
    for line in reference.splitlines():
        match=re.search(r'\(([\d.]+) - ([\d.]+) @ ([\d.]+)\), \(N/A, ([\d.]+)\)',line)
        if match:
            a,b,width,power=map(float,match.groups())
            if not (a<b and width>=20 and 0<power<=60):raise ValueError('Malformed CN rule')
            rules.append((a,b,width,power,'DFS' in line,'NO-OUTDOOR' in line,'NO-IR' in line))
    if len(rules)<4:raise ValueError('Incomplete CN rules')
    return rules


def audit(reference,effective,phy):
    rules=cn_rules(reference)
    if not effective.startswith(('global\ncountry CN:','global\ncountry 98:')):
        header=' / '.join(effective.splitlines()[:2])
        raise ValueError('Neither CN nor verified intersection candidate: '+header)
    count=0
    for line in phy.splitlines():
        frequency=re.match(r'\s*\*\s+(\d+(?:\.\d+)?)\s+MHz\s+\[\d+\]',line)
        if not frequency or 'disabled' in line:continue
        match=re.match(r'\s*\*\s+([\d.]+)\s+MHz\s+\[\d+\]\s+\(([-\d.]+) dBm\)(.*)',line)
        if not match:raise ValueError('Unknown enabled CN channel representation')
        freq,power=float(match[1]),float(match[2]);flags=match[3]
        indoor=any(value in flags for value in ('indoor only','indoor-only','no outdoor'))
        choices=[v for v in rules if v[0]<=freq-10 and freq+10<=v[1] and v[2]>=20 and power<=v[3]+0.001
            and (not v[4] or 'radar detection' in flags) and (not v[5] or indoor) and (not v[6] or 'no IR' in flags)]
        if not choices:raise ValueError(f'Enabled {freq:g} MHz / {power:g} dBm exceeds observed CN20MHz rules or lacks DFS/indoor/IR restriction')
        count+=1
    if not count:raise ValueError('No auditable enabled CN channels')
    return {'country_requested':'CN','effective_global_domain':'98-intersection' if effective.startswith('global\ncountry 98:') else 'CN',
        'enabled_20mhz_channels_verified':count,'channel_eirp_dfs_indoor_ir_subset_of_observed_CN_rules':True,
        'does_not_certify_RF_emissions_hardware_or_charging':True}
