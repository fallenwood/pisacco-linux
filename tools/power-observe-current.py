#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Resume the unused observer in the EXISTING candidate boot after cooldown.

No reboot, fastboot, flash, input injection, shutdown, or increased thresholds.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

BASE=Path('/opt/picasso-power')
RUN=Path('/run/picasso-power-observe')


def require(ok,message):
    if not ok:raise RuntimeError(message)


def ready(values):
    return bool(values) and all(-10000<=v<40000 for v in values.values())


def main():
    os.umask(0o077)
    require(len(sys.argv)==1 and os.geteuid()==0,'Native root, no arguments')
    require(os.uname().release=='6.18.58-picasso-lts-wifi2','Matching kernel required')
    require(hashlib.sha256(Path('/sys/firmware/fdt').read_bytes()).hexdigest()=='ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c','Existing candidate boot required; never boot automatically')
    require(not (RUN/'observer-consumed').exists(),'Existing observer already consumed; inspect saved result, do not replay')
    for name,pinned in [('power-key-service.py','e819dc6a9bc8ee0dce49d3b1d5240925ce8141a1fb89e6a82afd3a42090b98f3'),('power-hold-policy.py','c1d27bb4d41bfa5a2c2df2519e2033945d9e6b0d1b50b992ecc2a0db67b58670')]:
        require(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==pinned,'Changed observer asset')
    os.sched_setaffinity(0,{0,1,2,3})
    RUN.mkdir(mode=0o700,parents=True,exist_ok=True)
    record={'status':'waiting_for_cool_start','boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'observer_start_below_mc':40000,'abort_mc':45000,'observer_slot_consumed':False,'armed_orderly_poweroff':False,'peak_sampled_temperature_mc':0,'started_monotonic':time.monotonic()}
    target=RUN/('cooldown-'+str(time.monotonic_ns())+'.json')
    def save():
        target.write_text(json.dumps(record,indent=2)+'\n');p=RUN/'cooldown-last.new';p.write_text(json.dumps({'record':target.name,**record},indent=2)+'\n');p.replace(RUN/'cooldown-last.json')
    try:
        until=time.monotonic()+120;stable=0;last_print=0
        while time.monotonic()<until:
            values={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
            require(values and all(-10000<=v<=150000 for v in values.values()),'Missing/invalid sensors')
            record['peak_sampled_temperature_mc']=max(record['peak_sampled_temperature_mc'],max(values.values()));record['temperatures_mc']=values
            require(max(values.values())<45000,'45C abort; no observer started')
            stable=stable+1 if ready(values) else 0
            if time.monotonic()-last_print>=5:
                print(f'当前最高温度 {max(values.values())/1000:.1f}°C；等待所有传感器低于40°C，不启动按键观察。',flush=True);last_print=time.monotonic()
            if stable>=3:
                record['status']='cooled_ready_exec_disarmed_observer_same_boot';record['ready_monotonic']=time.monotonic();save()
                print('温度检查通过。接下来等待观察器 ready 提示后，电源键按住约2秒后松开，不超过3秒。',flush=True)
                os.execv('/usr/bin/python3',['/usr/bin/python3','-I',str(BASE/'power-key-service.py')])
            time.sleep(.5)
        raise RuntimeError('120s cooldown wait expired; no observer started')
    except Exception as exc:
        record.update(status='cooldown_refused_no_observer_start',error=type(exc).__name__+': '+str(exc));save();print(json.dumps(record),flush=True);return 1


if __name__=='__main__':raise SystemExit(main())
