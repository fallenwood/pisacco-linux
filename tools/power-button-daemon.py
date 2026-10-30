#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Installed release-only KEY_POWER service. USB-powered autostart is accepted,
not fixed. Never change PMIC triggers/timers, charging, suspend or boot files.
"""
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import stat
import struct
import subprocess
import sys
import time
import uuid

BASE=Path('/opt/picasso-power-button')
STATE=Path('/var/lib/picasso-power-button')
RUNTIME=Path('/run/picasso-power-button')
FDT='ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c'
POLICY_SHA='c1d27bb4d41bfa5a2c2df2519e2033945d9e6b0d1b50b992ecc2a0db67b58670'
EVENT=struct.Struct('@llHHi')
STOP=False


def require(ok,message):
    if not ok:raise RuntimeError(message)


def notify(text):
    target=os.environ.get('NOTIFY_SOCKET')
    if not target:return
    if target.startswith('@'):target='\0'+target[1:]
    with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as s:s.sendto(text.encode(),target)


def temps():
    values={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
    require(values and all(-10000<=v<=150000 for v in values.values()),'Invalid temperature telemetry');return values


def write_json(path,value,exclusive=False):
    data=(json.dumps(value,indent=2)+'\n').encode();target=path if exclusive else path.with_name(path.name+'.new')
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        view=memoryview(data)
        while view:
            count=os.write(fd,view);require(count>0,'Short durable record');view=view[count:]
        os.fsync(fd)
    finally:os.close(fd)
    if not exclusive:target.replace(path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def validate_files():
    require(os.geteuid()==0,'Native root required')
    auth=BASE/'authorization.json';s=auth.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o400,'Root0400 authorization required')
    value=json.loads(auth.read_text())
    require(all(value.get(k) is True for k in ('accepts_usb_autostart','allow_boot_only','enable_long_hold_service')),'User acceptance/installation authorization required')
    require(value['image_sha256']=='002147068dd9a03b467e27cf95398b3147bf5452af411f3e6a90c443e92b2c5f','Only tested power DTB image authorized')
    require(hashlib.sha256((BASE/'power-hold-policy.py').read_bytes()).hexdigest()==POLICY_SHA,'Changed hold policy')
    return value


def decode_events(raw,now,last_stamp):
    require(raw and len(raw)%EVENT.size==0,'Evdev stream error');events=[];last=last_stamp
    for off in range(0,len(raw),EVENT.size):
        sec,usec,kind,code,value=EVENT.unpack_from(raw,off);require(not (kind==0 and code==3),'SYN_DROPPED, refuse shutdown')
        if kind!=1:continue
        stamp=sec+usec/1000000
        require(sec>=0 and 0<=usec<1000000 and code==116 and value in (0,1,2),'Wrong input event')
        require(-.5<=now-stamp<=1 and stamp>=last,'Stale/nonmonotonic event');last=stamp;events.append((code,value,stamp))
    return events,last


def held(fd):
    bitmap=bytearray(96);fcntl.ioctl(fd,0x80604518,bitmap,True);return bool(bitmap[116//8] & (1<<(116%8)))


def main():
    global STOP
    validate_files();require(os.uname().release=='6.18.58-picasso-lts-wifi2','Matching kernel required')
    require(hashlib.sha256(Path('/sys/firmware/fdt').read_bytes()).hexdigest()==FDT,'Installed power-capable FDT required')
    require(hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest()=='f60bc2723f34cd08da927b4a3a79673bddc7bcd9052114cdd055cf958106dfbc','Matching tested kernel config required')
    for p in (STATE/'history',STATE/'requests',RUNTIME):p.mkdir(mode=0o700,parents=True,exist_ok=True)
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();run=boot[:12]+'-'+uuid.uuid4().hex[:8]
    state={'status':'cooling_before_arming','run_id':run,'boot_id':boot,'pid':os.getpid(),'shutdown_requested':False,'usb_autostart_accepted_not_fixed':True,'hold_min_seconds':2,'hold_max_seconds':3,'release_only':True,'hardware_timers_triggers_or_charging_modified':False,'system_suspend':False,'peak_temperature_mc':0,'events':[]}
    lock=os.open(RUNTIME/'owner.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600);fd=None;selector=selectors.DefaultSelector()
    def save():write_json(RUNTIME/'session.json',state)
    def tick():
        values=temps();state['peak_temperature_mc']=max(state['peak_temperature_mc'],max(values.values()));require(max(values.values())<45000,'45C thermal abort')
        notify('WATCHDOG=1');return values
    def stop(signum,frame):
        global STOP
        STOP=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(not (STATE/'requests'/(boot+'.intent.json')).exists(),'This boot already has a shutdown intent; no repeat')
        write_json(STATE/'history'/(run+'-start.json'),state,True);save()
        until=time.monotonic()+120;stable=0
        while time.monotonic()<until and not STOP:
            values=tick();stable=stable+1 if max(values.values())<40000 else 0
            notify('STATUS=Cooling before arming, all sensors must be below40C')
            if stable>=3:break
            time.sleep(.5)
        if STOP:state['status']='stopped_before_arming';return 0
        require(stable>=3,'120s start-temperature refusal, no input armed')
        spec=importlib.util.spec_from_file_location('power_policy',BASE/'power-hold-policy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);policy=m.PowerHoldPolicy()
        state['status']='waiting_for_power_input';save();input_deadline=time.monotonic()+15
        while True:
            tick();nodes=[p for p in Path('/sys/class/input').glob('event*') if (p/'device/name').read_text().strip()=='pm8941_pwrkey']
            require(len(nodes)<=1,'Multiple PM8150 power inputs')
            if nodes:break
            if STOP:state['status']='stopped_before_input';return 0
            require(time.monotonic()<input_deadline,'15s power-input enumeration deadline')
            notify('STATUS=Waiting for the single real PM8150 power input');time.sleep(.1)
        n=nodes[0];require(n.name in ('event0','event1'),'Input outside exact device allowance');bits=0
        for word in (n/'device/capabilities/key').read_text().split():bits=(bits<<64)|int(word,16)
        require(bits==1<<116 and (n/'device/phys').read_text().strip()=='pm8941_pwrkey/input0','Wrong key capability/provenance')
        device=Path('/dev/input')/n.name;s=device.lstat();require(stat.S_ISCHR(s.st_mode) and os.major(s.st_rdev)==13,'Wrong evdev device')
        require((n/'dev').read_text().strip()==f'{os.major(s.st_rdev)}:{os.minor(s.st_rdev)}','Input device identity mismatch')
        fd=os.open(device,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW);require(os.fstat(fd).st_rdev==s.st_rdev,'Input changed at open');require(not held(fd),'Release power before starting service')
        fcntl.ioctl(fd,0x40044590,1);fcntl.ioctl(fd,0x400445a0,struct.pack('@i',1));selector.register(fd,selectors.EVENT_READ)
        require(max(tick().values())<40000,'Start below40C at readiness')
        state.update(status='waiting_for_new_real_power_key',input=n.name);save();notify('READY=1\nSTATUS=Physical KEY_POWER2..3s hold then release; USB autostart unresolved')
        last_stamp=0
        while not STOP:
            tick()
            for key,mask in selector.select(.1):
                events,last_stamp=decode_events(os.read(key.fd,EVENT.size*16),time.monotonic(),last_stamp)
                for code,value,stamp in events:
                    action=policy.key(code,value,stamp);event={'code':code,'value':value,'monotonic':stamp,'policy_action':action};state['events'].append(event);state['events']=state['events'][-32:];save()
                    if action:
                        require(not held(fd),'Key is held again; refuse poweroff while held');tick()
                        state.update(status='intent_before_pid1_request',shutdown_requested=None);write_json(STATE/'requests'/(boot+'.intent.json'),state,True);save()
                        subprocess.run(['/usr/bin/systemctl','poweroff','--no-block','--no-ask-password'],check=True,capture_output=True,timeout=10)
                        state.update(status='pid1_accepted_not_physical_poweroff_proof',shutdown_requested=True);write_json(STATE/'requests'/(boot+'.accepted.json'),state,True);return 0
        state['status']='stopped_without_shutdown_request';return 0
    except Exception as exc:state.update(status='failed_no_retry',error=type(exc).__name__+': '+str(exc));return 1
    finally:
        if fd is not None:os.close(fd)
        selector.close();os.close(lock);save();write_json(STATE/'history'/(run+'-end.json'),state,True)
        notify('STOPPING=1')


if __name__=='__main__':
    os.umask(0o077)
    if sys.argv[1:]==['--check-files']:
        validate_files();subprocess.run(['/usr/bin/systemctl','show','-p','Version'],check=True,capture_output=True,timeout=5);notify('READY=1');print('Files/authorization/PID1 read-only bus access passed; input and shutdown NOT tested.')
    elif sys.argv[1:]==['--run-installed']:raise SystemExit(main())
    else:raise SystemExit('Explicit --run-installed or --check-files required')
