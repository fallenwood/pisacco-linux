#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Own-ROM power wiring + exact wifi2 baseline extension audit. Offline only."""
import hashlib
import struct
from fdt import nodes,fixed_regions

BASE_SHA='62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388'
VENDOR_SHA='f75e1bf1af964147ee929b97a6b857516a4591b7bc096fe31e73d9ed8b8dc6f6'
PREFIX='/soc@0/spmi@c440000/pmic@0'


def cells(raw):
    if len(raw)%4:raise ValueError('Invalid cells')
    return list(struct.unpack('>'+str(len(raw)//4)+'I',raw))


def audit(base_blob,candidate_blob,vendor_blob):
    if hashlib.sha256(base_blob).hexdigest()!=BASE_SHA or hashlib.sha256(vendor_blob).hexdigest()!=VENDOR_SHA:raise ValueError('Unpinned baseline/vendor')
    base=nodes(base_blob);candidate=nodes(candidate_blob);vendor=nodes(vendor_blob)
    if any(candidate.get(n)!=p for n,p in base.items()):raise ValueError('Existing wifi2 node changed/removed')
    expected={PREFIX,PREFIX+'/pon@800',PREFIX+'/pon@800/pwrkey'}
    if set(candidate)-set(base)!=expected:raise ValueError('Only primary PM8150/PON/power key may be added')
    pmic=candidate[PREFIX];pon=candidate[PREFIX+'/pon@800'];key=candidate[PREFIX+'/pon@800/pwrkey']
    if pmic!={'compatible':b'qcom,pm8150\0qcom,spmi-pmic\0','reg':struct.pack('>II',0,0),'#address-cells':struct.pack('>I',1),'#size-cells':struct.pack('>I',0)}:raise ValueError('Unexpected primary PMIC')
    if pon!={'compatible':b'qcom,pm8998-pon\0','reg':struct.pack('>I',0x800)}:raise ValueError('Unexpected PON properties/mode-magic')
    if key!={'compatible':b'qcom,pm8941-pwrkey\0','interrupts':struct.pack('>4I',0,8,0,3),'debounce':struct.pack('>I',15625),'bias-pull-up':b'','linux,code':struct.pack('>I',116)}:raise ValueError('Unexpected power key properties')
    matches=[(n,p) for n,p in vendor.items() if n.endswith('/qcom,pm8150@0/qcom,power-on@800')]
    if len(matches)!=1:raise ValueError('No unique own PM8150 PON')
    n,p=matches[0]
    if cells(p['interrupts'])[:4]!=[0,8,0,3] or cells(p['qcom,pon-dbc-delay'])!=[15625]:raise ValueError('Factory IRQ/debounce mismatch')
    factory=[v for path,v in vendor.items() if path.startswith(n+'/') and v.get('linux,code')==struct.pack('>I',116)]
    if len(factory)!=1 or cells(factory[0]['qcom,pon-type'])!=[0] or 'qcom,pull-up' not in factory[0]:raise ValueError('Factory power code/type/pull mismatch')
    if fixed_regions(base)!=fixed_regions(candidate):raise ValueError('Reserved memory changed')
    return {'status':'passed_offline_only_exact_wifi2_plus_own_power_key','hardware_tested':False,'candidate_dtb_sha256':hashlib.sha256(candidate_blob).hexdigest(),'baseline_dtb_sha256':BASE_SHA,'vendor_dtb_sha256':VENDOR_SHA,'all_existing_nodes_byte_properties_preserved':True,'added_nodes':sorted(expected),'power_key':{'usid':0,'peripheral':8,'irq':0,'edge_both':True,'linux_code':116,'debounce_us':15625,'pull_up':True},'volume_down_added':False,'reset_timers_reboot_magic_or_display_rails_changed':False,'probe_write_scope':'pm8941-pwrkey standard debounce/pull bits; shutdown/reboot notifier programs standard PS_HOLD mode only on actual shutdown/reboot','hardware_power_on_forced_reset_or_clean_poweroff_accepted':False}
