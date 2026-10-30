#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Summarize one observed current-boot beacon-loss chain; no identifiers/keys.

Input is already collected journal JSON rows. This is evidence analysis, NOT a
current connection or a substitute for live guard checks. Observation cmd=1 is
Linux DISABLE_KEY; roam reason=2 is WMI_ROAM_REASON_BEACON_MISS in this source.
"""
import re


def analyze(kernel,supplicant):
    def events(rows):
        return sorted([(int(r.get('__MONOTONIC_TIMESTAMP',0))/1e6,r.get('MESSAGE','')) for r in rows if isinstance(r.get('MESSAGE'),str)],key=lambda x:x[0])
    k=events(kernel);s=events(supplicant)
    starts=[t for t,m in s if m.startswith('wlan0: CTRL-EVENT-CONNECTED')]
    if not starts:raise ValueError('No connected event in provided run')
    start=starts[-1]
    ends=[(t,m) for t,m in s if t>=start and m.startswith('wlan0: CTRL-EVENT-DISCONNECTED')]
    if not ends:raise ValueError('No later disconnect event; cannot infer loss chain')
    end,disconnect=ends[0]
    active=[(t,m) for t,m in k if start<=t<=end]
    def first(fragment):
        return next(((t,m) for t,m in active if fragment in m),None)
    roam=next(((t,m) for t,m in active if re.search(r'Picasso link observation: roam vdev \d+ reason 2\b',m)),None)
    miss=first('Picasso link observation: beacon_miss ')
    work=first('Picasso link observation: loss_work ')
    deletion=first('Picasso link observation: key_begin cmd 1 ')
    timeout=first('Picasso link observation: key_wait_done cmd 1 completed 0')
    beaconloss=next(((t,m) for t,m in s if start<=t<=end and 'CTRL-EVENT-BEACON-LOSS' in m),None)
    scans=[t for t,m in active if 'Picasso link observation: scan type ' in m]
    sets=[t for t,m in k if start-5<=t<=start and 'Picasso link observation: key_wait_done cmd 0 completed 1' in m]
    # mac80211's probe-failure path may start teardown before the driver's
    # independent three-second delayed work. Do not force the opposite ordering.
    earlier_set_timeout=any(start-5<=t<=(miss[0] if miss else end) and 'Picasso link observation: key_wait_done cmd 0 completed 0' in m for t,m in k)
    ordered=all((roam,miss,work,deletion,timeout,beaconloss)) and not earlier_set_timeout and roam[0]<=miss[0]<=deletion[0]<timeout[0]<=end and miss[0]<=work[0]<=end
    reason=re.search(r'reason=(\d+)',disconnect)
    out={'connected_seconds':start,'disconnected_seconds':end,'connected_duration_seconds':round(end-start,6),'local_disconnect':bool(re.search(r'locally_generated=1\b',disconnect)),'disconnect_reason':int(reason[1]) if reason else None,'initial_set_key_completions_before_connected':len(sets),'firmware_beacon_miss_loss_work_delete_timeout_chain_verified':bool(ordered and re.search(r'roam vdev \d+ reason 2\b',roam[1])),'scan_events_during_connected_interval':len(scans),'key_timeout_is_disable_key_not_initial_install':bool(deletion and timeout and not earlier_set_timeout),'earlier_set_key_timeout_observed':earlier_set_timeout,'sole_lower_layer_cause_proven':False,'not_a_current_connection_acceptance':True}
    for name,value in [('firmware_roam',roam),('driver_beacon_miss',miss),('supplicant_beacon_loss',beaconloss),('driver_loss_work',work),('key_disable_begin',deletion),('key_disable_timeout',timeout)]:
        if value:out[name+'_after_connected_seconds']=round(value[0]-start,6)
    if miss:
        fields={key:int(value) for key,value in re.findall(r'(own_beacons|scan_state|beacon_age_ms|pre_filter|errors) (\d+)',miss[1])}
        out['beacon_miss_metadata']=fields
    if ordered:
        out['teardown_started_before_driver_delayed_loss_work']=deletion[0]<work[0]
        out['diagnosis']='Firmware-reported beacon miss precedes driver/mac80211 loss; later DISABLE_KEY completion timeout is teardown, not initial key installation failure. Probe failure may initiate teardown before delayed loss work.'
    else:out['diagnosis']='Incomplete observation chain; do not claim initiation or root cause from ordering alone.'
    return out
