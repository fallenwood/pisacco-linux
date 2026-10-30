#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline decoder only: no device access, power action or root-cause claim.

Gen2 banks from pinned MiCode 236f9eb qpnp-power-on.c, not a generic PMIC map.
Latched bits may be stale; multiple flags are preserved, not reduced to ffs().
"""
import json
import sys

ADDRESSES={'0104','0105','0805','08c0','08c2','08c7','08c5','08c8','08c9','08ca'}
PON=('HARD_RESET','SMPL','RTC','DC_CHARGER','USB_CHARGER','PON1','CBL_POWER','KPDPWR')
POFF=('SOFTWARE','PS_HOLD','PMIC_WATCHDOG','GP1','GP2','KPDPWR_AND_RESIN','RESIN','KPDPWR')
FAULT=('GP_FAULT0','GP_FAULT1','GP_FAULT2','GP_FAULT3','MBG_FAULT','OVLO','UVLO','AVDD_RB','RESERVED8','RESERVED9','RESERVED10','FAULT_N','PBS_WATCHDOG','PBS_NACK','RESTART_PON','OTST3')
S3=('RESERVED0','RESERVED1','RESERVED2','RESERVED3','FAULT_N','PBS_WATCHDOG','PBS_NACK','KPDPWR_ANDOR_RESIN')


def flags(value,names):return [name for bit,name in enumerate(names) if value & (1<<bit)]


def decode(snapshot):
    if (snapshot.get('scope')!='picasso-pm8150-gen2-readonly' or type(snapshot.get('usid')) is not int
            or snapshot['usid']!=0 or type(snapshot.get('base')) is not int or snapshot['base']!=2048):
        raise ValueError('Wrong fixed board/SID/PON scope')
    r=snapshot['registers']
    if set(r)!=ADDRESSES:raise ValueError('Unexpected/missing register; Gen1 and control addresses forbidden')
    for value in r.values():
        if value is not None and (type(value) is not int or not 0<=value<=255):raise ValueError('Non-byte input')
    if [r[k] for k in ('0104','0105','0805')]!=[0x51,0x1e,0x04]:raise ValueError('Not PM8150 Gen2 primary')
    if any(r[k] is None for k in ('08c0','08c2','08c7')):raise ValueError('Missing common status')
    off=r['08c7'];sequences=[];decoded={}
    for mask,name,keys,names in ((0x80,'POFF',('08c5',),POFF),(0x40,'FAULT',('08c8','08c9'),FAULT),(0x20,'S3',('08ca',),S3)):
        active=bool(off&mask)
        if active and any(r[k] is None for k in keys):raise ValueError('Selected bank not captured')
        if not active and any(r[k] is not None for k in keys):raise ValueError('Unselected bank read outside conditional plan')
        if active:
            sequences.append(name);raw=sum(r[k]<<(8*i) for i,k in enumerate(keys));decoded[name]={'raw':raw,'all_flags':flags(raw,names)}
    return {'status':'decoded_latched_flags_only_not_causality','pon_all_flags':flags(r['08c0'],PON),'warm_reason_raw':r['08c2'],'sequence_all_flags':sequences,'multiple_sequences_ambiguous':len(sequences)>1,'unknown_sequence_bits':off&0x1f,'selected_banks':decoded,'register_freshness_or_firmware_clearing_not_established':True,'hardware_read_performed_by_this_tool':False,'root_cause_proven':False,'full_powercycle_accepted':False}


if __name__=='__main__':print(json.dumps(decode(json.load(sys.stdin)),indent=2))
