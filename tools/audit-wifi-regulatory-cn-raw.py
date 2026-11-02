#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""CN audit using actual authenticated split nl80211 attributes, NOT iw flags.
The caller pins the existing strict CN rules parser/reference/collector. Legacy
iw text is used only for complete inventory cross-check, never indoor evidence.
"""
import math
import re


def require(ok,message):
    if not ok:raise ValueError(message)


def audit(reference,effective,report,expected_index,expected_name,legacy_info,parse_rules,expected_country='CN'):
    rules=parse_rules(reference)
    require(isinstance(expected_country,str) and re.fullmatch(r'[A-Z]{2}',expected_country) is not None,'Invalid reviewed country')
    require(effective.startswith(('global\ncountry '+expected_country+':','global\ncountry 98:')),'Neither '+expected_country+' nor verified intersection candidate')
    require(report.get('source')=='read_only_raw_nl80211_split_GET_WIPHY','Wrong raw evidence source')
    require(report.get('kernel_release')=='6.18.58-picasso-lts-wifi2','Unpinned raw kernel')
    require(report.get('split_requested') is True and report.get('complete_dump') is True,'Incomplete split dump')
    require(type(report.get('protocol_features')) is int and report['protocol_features']&1,'Split support absent')
    phys=report.get('phys');require(type(phys) is list and len(phys)==1,'Require exactly one requested PHY')
    phy=phys[0];require(type(phy.get('index')) is int and phy['index']==expected_index and phy.get('name')==expected_name,'Wrong PHY identity')
    channels=phy.get('channels');require(type(channels) is list and bool(channels),'No actual channel evidence')
    inventory=set()
    for line in legacy_info.splitlines():
        match=re.match(r'\s*\*\s+(\d+(?:\.\d+)?)\s+MHz\s+\[\d+\]',line)
        if match:
            frequency=float(match[1]);require(frequency not in inventory,'Duplicate iw inventory frequency');inventory.add(frequency)
    observed=set();enabled=0;indoor=[];non20=[]
    for ch in channels:
        frequency=ch.get('frequency_mhz');require(type(frequency) in (int,float) and math.isfinite(frequency),'Invalid raw frequency')
        require(frequency not in observed,'Duplicate raw frequency');observed.add(frequency)
        require(type(ch.get('band_index')) is int and ch['band_index'] in (0,1),'Unexpected Picasso band')
        attrs=ch.get('observed_attribute_ids');require(type(attrs) is list and all(type(x) is int for x in attrs) and len(attrs)==len(set(attrs)) and 1 in attrs,'Raw attribute provenance absent')
        for name,attribute in (('disabled',2),('no_ir',3),('radar',5),('indoor_only',14),('no_20mhz',16)):
            require(type(ch.get(name)) is bool and ch[name]==(attribute in attrs),'Flag/provenance mismatch: '+name)
        if ch['disabled']:continue
        power=ch.get('max_tx_power_mbm');require(type(power) is int and 0<=power<=10000 and 6 in attrs,'Actual power absent')
        require(expected_country!='CN' or not ch['no_20mhz'],'Enabled channel not auditable in20MHz mode')
        # NO_20MHZ excludes a channel from this mode, not from narrower regdb auditing.
        width=(5 if 17 in attrs else 10) if ch['no_20mhz'] else 20
        matches=[rule for rule in rules if rule[0]<=frequency-width/2 and frequency+width/2<=rule[1] and rule[2]>=width and power<=rule[3]*100+.1
            and (not rule[4] or ch['radar']) and (not rule[5] or ch['indoor_only']) and (not rule[6] or ch['no_ir'])]
        require(bool(matches),f'Actual raw {frequency:g} MHz/{power}mBm exceeds {expected_country} rules or lacks DFS/INDOOR_ONLY/no-IR')
        if ch['indoor_only']:indoor.append(frequency)
        if ch['no_20mhz']:
            non20.append(frequency);continue
        enabled+=1
    require(observed==inventory,'Raw and iw complete channel inventory differ')
    require(enabled>0,'No eligible actual 20MHz channels')
    return {'country_requested':expected_country,'effective_global_domain':'98-intersection' if effective.startswith('global\ncountry 98:') else expected_country,
        'evidence_source':'authenticated_complete_raw_nl80211_split_same_PHY','PHY_index':expected_index,'PHY_name':expected_name,
        'total_channel_inventory_cross_checked':len(observed),'enabled_20mhz_channels_verified':enabled,
        'actual_INDOOR_ONLY_frequencies_mhz':indoor,        ('actual_CN_EIRP_DFS_NO_OUTDOOR_IR_subset_verified' if expected_country=='CN' else 'actual_regdb_EIRP_DFS_NO_OUTDOOR_IR_subset_verified'):True,
        'iw_indoor_text_not_used':True,'does_not_prove_physical_indoor_location_RF_emissions_or_charging_safety':True,
        **({'enabled_non20_channels_excluded':non20} if expected_country!='CN' else {})}
