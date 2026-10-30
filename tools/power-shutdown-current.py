#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One explicitly confirmed, physical-key-triggered orderly shutdown trial.

Does not shut down on launch: waits for a new real 2..3s hold and RELEASE.
No system suspend, hardware reset timer changes, reboot or flash operations.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

BASE=Path('/opt/picasso-power')
OBS=Path('/var/lib/picasso-power/observations-20261028')
STATE=Path('/var/lib/picasso-power/shutdown-trial-20261028')


def require(ok,message):
    if not ok:raise RuntimeError(message)


def valid_observation(accept,result,boot):
    return (accept.get('status')=='passed_real_power_hold_release_detection_disarmed_only'
            and accept.get('boot_id')==boot and accept.get('armed') is False
            and accept.get('shutdown_requested') is False
            and result.get('armed_orderly_poweroff') is False
            and result.get('shutdown_requested') is False
            and any(v.get('policy_action')=='orderly_poweroff' for v in result.get('events',[])))


def main():
    os.umask(0o077)
    require(sys.argv[1:]==['--confirmed-local-shutdown-test'] and os.geteuid()==0,'Explicit local confirmation flag and native root required')
    require(os.uname().release=='6.18.58-picasso-lts-wifi2','Matching kernel required')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(hashlib.sha256(Path('/sys/firmware/fdt').read_bytes()).hexdigest()=='ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c','Same audited power-input candidate required')
    accept=json.loads((OBS/'acceptance.json').read_text());raw=(OBS/'result.json').read_bytes();result=json.loads(raw)
    require(valid_observation(accept,result,boot),'Same-boot real disarmed observation must pass first')
    require(hashlib.sha256(raw).hexdigest()==accept['result_sha256'],'Observation record changed')
    require(not Path('/run/picasso-power-armed/observer-consumed').exists(),'Armed attempt already consumed; inspect, do not replay')
    for name,pinned in [('power-key-service.py','f402b1b79923ef75b240aef67e78c3af635977363f0fc0f997ce8694c4bebb00'),('power-hold-policy.py','c1d27bb4d41bfa5a2c2df2519e2033945d9e6b0d1b50b992ecc2a0db67b58670')]:
        require(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==pinned,'Changed shutdown trial asset')
    STATE.mkdir(mode=0o700,parents=True,exist_ok=True);launch=STATE/('launch-'+boot+'.json')
    require(not launch.exists(),'Shutdown trial already launched; inspect durable evidence')
    control=Path('/run/picasso-power-shutdown-control.json')
    info={'boot_id':boot,'pid':os.getpid(),'process_start_ticks':Path('/proc/self/stat').read_text().rpartition(')')[2].split()[19]}
    fd=os.open(control,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:os.write(fd,(json.dumps(info)+'\n').encode());os.fsync(fd)
    finally:os.close(fd)
    os.sched_setaffinity(0,{0,1,2,3});until=time.monotonic()+120;stable=0;last=0;peak=0
    while time.monotonic()<until:
        temps={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
        require(temps and all(-10000<=v<=150000 for v in temps.values()),'Missing/invalid temperature data')
        peak=max(peak,max(temps.values()));require(max(temps.values())<45000,'45C abort before arming')
        stable=stable+1 if max(temps.values())<40000 else 0
        if time.monotonic()-last>=5:print(f'关机测试启动前最高温度 {max(temps.values())/1000:.1f}°C；等待全部低于40°C。',flush=True);last=time.monotonic()
        if stable>=3:
            record={'status':'explicit_armed_trial_launch_waiting_for_new_key','boot_id':boot,'prior_observation_sha256':accept['result_sha256'],'peak_before_armed_mc':peak,'explicit_confirmation_flag_supplied':True,'shutdown_requested':False}
            data=(json.dumps(record,indent=2)+'\n').encode();fd=os.open(launch,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            try:
                view=memoryview(data)
                while view:
                    count=os.write(fd,view);require(count>0,'Short launch record');view=view[count:]
                os.fsync(fd)
            finally:os.close(fd)
            print('即将ARM正常关机。等下一条ready，再按住电源约2秒后松开，不超过3秒。',flush=True)
            os.execv('/usr/bin/python3',['/usr/bin/python3','-I',str(BASE/'power-key-service.py'),'--arm-orderly-poweroff'])
        time.sleep(.5)
    raise RuntimeError('120s cooldown expired; no shutdown trial armed')


if __name__=='__main__':main()
