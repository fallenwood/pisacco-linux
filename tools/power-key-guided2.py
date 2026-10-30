#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Separate guided2 power-key attempt. Default disarmed; no reset writes.

Only an explicitly armed, audited candidate boot can request orderly shutdown.
Normal boot #10 has no power input and must fail closed, not synthesize it.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import stat
import struct
import subprocess
import time

CANDIDATE_FDT='ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c'
EVENT=struct.Struct('@llHHi')


def require(ok,message):
    if not ok:raise RuntimeError(message)


class TemperaturePreflightError(RuntimeError):
    def __init__(self,values):
        super().__init__('Start below 40C; observer not entered')
        self.temperatures_mc=values


def guidance_stage(pressed_at,now,previous):
    if pressed_at is None:return 0,None
    elapsed=now-pressed_at
    if elapsed>3 and previous<2:return 2,'\a已超过3秒，本次无效：请立即松开，不要继续长按！'
    if elapsed>=2 and previous<1:return 1,'\a已满2秒：现在立即松开电源键！'
    return previous,None


def persist_armed_trial(result):
    """Keep intent/events across shutdown; acceptance is NOT proof of power-off."""
    if not result['armed_orderly_poweroff']:return
    base=Path('/var/lib/picasso-power/shutdown-trial-20261028');base.mkdir(mode=0o700,parents=True,exist_ok=True)
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();target=base/(boot+'-guided2.json');temp=base/(boot+'-guided2.new')
    data=(json.dumps({'recorded_boot_id':boot,**result},indent=2)+'\n').encode()
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        view=memoryview(data)
        while view:
            count=os.write(fd,view);require(count>0,'Short durable shutdown record');view=view[count:]
        os.fsync(fd)
    finally:os.close(fd)
    temp.replace(target);directory=os.open(base,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)


def main(armed=False):
    os.umask(0o077)
    require(os.geteuid()==0,'Native root required')
    require(os.uname().release=='6.18.58-picasso-lts-wifi2','Matching tested kernel required')
    require(hashlib.sha256(Path('/sys/firmware/fdt').read_bytes()).hexdigest()==CANDIDATE_FDT,'Audited input-capable trial DTB required')
    spec=importlib.util.spec_from_file_location('power_policy',Path(__file__).with_name('power-hold-policy.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);policy=m.PowerHoldPolicy()
    nodes=[p for p in Path('/sys/class/input').glob('event*') if (p/'device/name').read_text().strip()=='pm8941_pwrkey'];require(len(nodes)==1,'Expected one real PM8150 power key')
    n=nodes[0];bits=0
    for word in (n/'device/capabilities/key').read_text().split():bits=(bits<<64)|int(word,16)
    require(bits==1<<116,'Unexpected input capabilities')
    require((n/'device/phys').read_text().strip()=='pm8941_pwrkey/input0','Wrong power input provenance')
    values={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
    if not values or max(values.values())>=40000 or any(v < -10000 or v > 150000 for v in values.values()):raise TemperaturePreflightError(values)
    device=Path('/dev/input')/n.name;s=device.lstat();require(stat.S_ISCHR(s.st_mode) and os.major(s.st_rdev)==13,'Wrong evdev character device')
    require((n/'dev').read_text().strip()==f'{os.major(s.st_rdev)}:{os.minor(s.st_rdev)}','Input node identity mismatch')
    fd=os.open(device,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW);selector=selectors.DefaultSelector()
    result={'status':'running','attempt':'guided2','guidance':[],'armed_orderly_poweroff':armed,'real_power_input':n.name,'events':[],'shutdown_requested':False,'hardware_power_on_or_reset_timers_modified':False,'system_suspend':False}
    run=Path('/run/picasso-power-armed-guided2' if armed else '/run/picasso-power-observe');run.mkdir(mode=0o700,parents=True,exist_ok=True)
    require(not (run/'observer-consumed').exists(),'Exclusive observer already consumed; inspect saved result')
    (run/'observer-consumed').touch(mode=0o600)
    try:
        require(os.fstat(fd).st_rdev==s.st_rdev,'Input changed at open')
        held=bytearray(96);fcntl.ioctl(fd,0x80604518,held,True);require(not held[116//8]&(1<<(116%8)),'Release power before starting observer')
        fcntl.ioctl(fd,0x40044590,1);fcntl.ioctl(fd,0x400445a0,struct.pack('@i',1)) # CLOCK_MONOTONIC
        selector.register(fd,selectors.EVENT_READ)
        persist_armed_trial(result)
        print('Power observer ready: hold about 2 seconds and RELEASE before 3 seconds. '+('Orderly shutdown ARMED.' if armed else 'Observation ONLY, will not shut down.'),flush=True)
        until=time.monotonic()+60;prompt_stage=0
        while time.monotonic()<until:
            prompt_stage,hint=guidance_stage(policy.pressed_at,time.monotonic(),prompt_stage)
            if hint:
                print(hint,flush=True);result['guidance'].append({'monotonic':time.monotonic(),'message':hint,'stage':prompt_stage})
            temps=[int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')];require(temps and all(-10000<=v<=150000 for v in temps) and max(temps)<45000,'Invalid thermal state/45C abort')
            for key,mask in selector.select(.1):
                raw=os.read(key.fd,24*16);require(bool(raw) and len(raw)%24==0,'Evdev stream error')
                for offset in range(0,len(raw),24):
                    sec,usec,kind,code,value=EVENT.unpack_from(raw,offset);stamp=sec+usec/1000000
                    require(not (kind==0 and code==3),'SYN_DROPPED; power action disarmed')
                    if kind!=1:continue
                    require(code==116 and -0.5<=time.monotonic()-stamp<=1,'Unexpected/stale power input')
                    first_down=value==1 and policy.pressed_at is None
                    action=policy.key(code,value,stamp)
                    if first_down:prompt_stage=0;print('电源已按下：等满2秒提示再立即松开，不能超过3秒。',flush=True)
                    event={'code':code,'value':value,'monotonic':stamp,'policy_action':action};result['events'].append(event);print(json.dumps(event),flush=True)
                    if action:
                        result['status']='observed_real_hold_release_orderly_poweroff_candidate'
                        (run/'result.json').write_text(json.dumps(result,indent=2)+'\n')
                        if armed:
                            # Standard PID1 shutdown; no raw reboot, reset or PMIC IO.
                            # Flush real release+intent before PID1 may terminate SSH.
                            result['poweroff_request_stage']='intent_before_pid1_request';persist_armed_trial(result)
                            subprocess.run(['systemctl','poweroff','--no-block'],check=True,capture_output=True,timeout=10)
                            result['shutdown_requested']=True;result['poweroff_request_stage']='pid1_accepted_not_physical_poweroff_proof';persist_armed_trial(result)
                        return 0
        result['status']='observer_timed_out_no_valid_long_release';return 1
    except Exception as exc:result.update(status='failed_power_key_trial',error=type(exc).__name__+': '+str(exc));return 1
    finally:
        os.close(fd);selector.close();(run/'result.json').write_text(json.dumps(result,indent=2)+'\n');persist_armed_trial(result)


def entry(armed=False):
    """Record rejected starts separately, without consuming or erasing trials."""
    try:return main(armed)
    except Exception as exc:
        run=Path('/run/picasso-power-armed-guided2' if armed else '/run/picasso-power-observe')
        run.mkdir(mode=0o700,parents=True,exist_ok=True)
        consumed=(run/'observer-consumed').exists()
        result={'status':'observer_exit_error_review_required' if consumed else 'startup_refused_without_poweroff','error':type(exc).__name__+': '+str(exc),'temperatures_at_guard_mc':getattr(exc,'temperatures_mc',None),'observer_slot_consumed':consumed,'shutdown_requested':None if armed and consumed else False,'armed_orderly_poweroff':armed}
        p=run/('startup-refusal-'+str(time.monotonic_ns())+'.json')
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:
            view=memoryview((json.dumps(result,indent=2)+'\n').encode())
            while view:
                count=os.write(fd,view);require(count>0,'Short refusal record');view=view[count:]
            os.fsync(fd)
        finally:os.close(fd)
        temp=run/'startup-last.new';temp.write_text(json.dumps({'record':p.name,**result},indent=2)+'\n');temp.replace(run/'startup-last.json')
        print(json.dumps(result),flush=True);return 1


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--arm-orderly-poweroff',action='store_true');args=parser.parse_args();raise SystemExit(entry(args.arm_orderly_poweroff))
