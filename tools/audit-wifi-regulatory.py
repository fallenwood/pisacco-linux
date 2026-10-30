#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Conservative 20-MHz channel/power/DFS check against observed SG regdb rules.

'98' is Linux regdom_intersect(), not a country to fabricate or bypass.
Accept a stricter EEPROM intersection only after checking enabled channels.
No database, BDF, calibration, or kernel regulatory flags are changed.
"""
import re


def sg_rules(reference):
    if not reference.startswith('global\ncountry SG:') or '\nphy#' in reference:
        raise ValueError('Require original isolated SG kernel/regdb reference')
    rules=[]
    for line in reference.splitlines():
        m=re.search(r'\((\d+) - (\d+) @ (\d+)\), \(N/A, ([\d.]+)\)',line)
        if m:
            a,b,bw,power=map(float,m.groups())
            rules.append((a,b,bw,power,'DFS' in line))
    if len(rules)<5:raise ValueError('Incomplete SG rules')
    return rules


def audit(reference,effective,phy):
    rules=sg_rules(reference)
    if not effective.startswith(('global\ncountry SG:','global\ncountry 98:')):
        raise ValueError('Neither SG nor verified intersection candidate')
    count=0
    for line in phy.splitlines():
        m=re.match(r'\s*\*\s+(\d+(?:\.\d+)?)\s+MHz\s+\[\d+\]\s+\(([-\d.]+) dBm\)(.*)',line)
        if not m:continue
        freq,power=float(m[1]),float(m[2]);flags=m[3]
        if 'disabled' in flags:continue
        choices=[v for v in rules if v[0]<=freq-10 and freq+10<=v[1] and v[2]>=20 and power<=v[3]+0.001 and (not v[4] or 'radar detection' in flags)]
        if not choices:raise ValueError(f'Enabled {freq:g} MHz / {power:g} dBm exceeds observed SG 20-MHz rules or lacks DFS')
        count+=1
    if not count:raise ValueError('No auditable enabled channels')
    return {'country_requested':'SG','effective_global_domain':'98-intersection' if 'country 98:' in effective.split('phy#')[0] else 'SG','enabled_20mhz_channels_verified':count,'channel_eirp_dfs_subset_of_observed_sg_rules':True,'does_not_certify_wide_channel_modes_rf_emissions_or_charging':True}
