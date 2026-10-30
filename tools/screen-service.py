#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Persisted, owner-PID-leased screen-only service; NO system suspend.

Native Fedora tty1/fbcon contents only; no synthetic image or terminal writes.
15s idle off; only real volume-UP wakes/rearms. No power or volume-down.
"""
import argparse
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
import time
import uuid

BASE=Path('/opt/picasso-screen')
BL=Path('/sys/class/backlight/picasso-screen')
MODULE='picasso_wled_service'
MODULE_SHA='5d88d0c2ebefdd89971b66274555f484a4f1d5d0fcaf046adef05b594022d6dd'
CONSOLE_SHA='551ec1a2a70924f2476e06f3cf819fa2e8913fc2ec84fc6e8e069223ebe836f9'
POLICY_SHA='9be6863e4791828e32159fbc938b195dc07c25064ebee8cfe85d2c9c49113af2'
FDT_SHA='62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388'
# Explicit audited extension: all original nodes identical, only own PON key added.
POWER_TRIAL_FDT_SHA='ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c'
CONFIG_SHA='f60bc2723f34cd08da927b4a3a79673bddc7bcd9052114cdd055cf958106dfbc'
EVENT=struct.Struct('@llHHi')
STOP=False


def require(ok,message):
    if not ok:raise RuntimeError(message)


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def temperatures():
    values={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
    require(bool(values) and all(-10000<=v<=150000 for v in values.values()),'Invalid/missing thermal telemetry')
    return values


def notify(text):
    target=os.environ.get('NOTIFY_SOCKET')
    if not target:return
    if target.startswith('@'):target='\0'+target[1:]
    with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as sock:sock.sendto(text.encode(),target)


def save(path,value):
    p=path.with_suffix('.new');p.write_text(json.dumps(value,indent=2)+'\n');p.replace(path)


def brightness(value):
    require(value in (0,64),'Only approved zero/low brightness')
    (BL/'brightness').write_text(str(value))
    require(int((BL/'actual_brightness').read_text())==value,'Actual backlight mismatch')


def cleanup(run):
    """Independent ExecStopPost. Kernel lease is the first line of fail-off."""
    state=run/'session.json'
    data=json.loads(state.read_text()) if state.exists() else {}
    result={'status':'no_owned_module','systemd_result':os.environ.get('SERVICE_RESULT'),'run_id':data.get('run_id')}
    if (run/'module-owned').exists() and Path('/sys/module',MODULE).exists():
        if BL.exists():
            try:brightness(0)
            except Exception as exc:result['off_error']=type(exc).__name__
        p=subprocess.run(['rmmod',MODULE],capture_output=True,text=True,timeout=8)
        require(p.returncode==0,'Could not unload owned screen module');result['status']='owned_module_off_unloaded'
    result['module_unloaded']=not Path('/sys/module',MODULE).exists()
    save(run/'cleanup.json',result)
    if data.get('run_id'):save(Path('/var/lib/picasso-screen/history')/(data['run_id']+'-cleanup.json'),result)
    return result


def stop(signum,frame):
    global STOP
    STOP=True


def main(probe=None):
    os.umask(0o077)
    require(os.geteuid()==0 and os.uname().release=='6.18.58-picasso-lts-wifi2','Native installed kernel/root only')
    run=Path('/run/picasso-screen'+('-'+probe+'-probe' if probe else ''))
    run.mkdir(mode=0o700,parents=True,exist_ok=True)
    lock=os.open(run/'owner.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for name in ('module-owned','cleanup.json'):
        p=run/name
        if p.exists():require(not Path('/sys/module',MODULE).exists(),'Previous module remains owned');p.unlink()
    history=Path('/var/lib/picasso-screen/history');history.mkdir(mode=0o700,parents=True,exist_ok=True)
    data={'run_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()[:12]+'-'+uuid.uuid4().hex[:8],'status':'starting','pid':os.getpid(),'probe':probe,'screen_on':False,'idle_seconds':15,'brightness':64,'only_key':115,'system_suspend_allowed':False,'display_mode':'native_tty1_fbcon','synthetic_pixels_written':False,'peak_temperature_mc':0,'physical_volume_up_presses':0,'on_count':0,'off_count':0,'events':[]}
    save(run/'session.json',data)
    fd=None;keyfd=None;leasefd=None;owned=False;selector=selectors.DefaultSelector();last_save=0;last_config=0;expected=0
    def record(event):
        item={'event':event,'monotonic':time.monotonic(),'actual_brightness':int((BL/'actual_brightness').read_text()) if BL.exists() else None}
        data['events'].append(item);data['events']=data['events'][-32:];save(run/'session.json',data);print(json.dumps(item),flush=True)
    def tick():
        nonlocal last_save,last_config
        values=temperatures();data['peak_temperature_mc']=max(data['peak_temperature_mc'],max(values.values()));require(max(values.values())<45000,'45C thermal abort')
        now=time.monotonic()
        if leasefd is not None:
            require(os.pwrite(leasefd,b'LIVE\n',0)==5,'Short lease renewal')
            require(int((BL/'actual_brightness').read_text())==expected,'Unexpected actual backlight (expired/fault)')
            if now-last_config>=5:
                require('ovp_mv=28000' in (BL/'boot_config_verified').read_text(),'Unverified boot electrical configuration');last_config=now
        if now-last_save>=5:save(run/'session.json',data);last_save=now
        notify('WATCHDOG=1')
    def apply(on,event):
        nonlocal expected
        tick()
        if on:
            console.screen_on(tick,brightness);expected=64;data['on_count']+=1
        else:
            brightness(0);expected=0;Path('/sys/class/graphics/fb0/blank').write_text('4');data['off_count']+=1
        data['screen_on']=on;record(event)
    try:
        require(Path('/etc/picasso-fedora-root').read_text().strip()=='PICASSO_FEDORA44_DISKROOT_V2','Wrong disk root')
        require(hashlib.sha256(Path('/sys/firmware/fdt').read_bytes()).hexdigest() in (FDT_SHA,POWER_TRIAL_FDT_SHA),'Different display/PMIC tree')
        require(hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest()==CONFIG_SHA,'Different kernel config')
        for name,h in [('picasso-wled-service.ko',MODULE_SHA),('screen-console.py',CONSOLE_SHA),('screen-volume-policy.py',POLICY_SHA)]:require(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==h,'Changed asset: '+name)
        require(not list(Path('/sys/class/backlight').glob('*')),'Existing backlight owner')
        require(not any(Path('/sys/module',n).exists() for n in (MODULE,'picasso_wled_handoff','picasso_wled_audit')),'Display module already owned')
        require(max(temperatures().values())<40000,'Start below 40C')
        console=load('native_console',BASE/'screen-console.py');policy_module=load('volume_policy',BASE/'screen-volume-policy.py')
        data['console']=console.console_info()
        nodes=[p for p in Path('/sys/class/input').glob('event*') if (p/'device/name').read_text().strip()=='gpio-keys'];require(len(nodes)==1,'Expected one GPIO input')
        node=nodes[0];require(node.name in ('event0','event1'),'Audited device index changed')
        bitmap=0
        for word in (node/'device/capabilities/key').read_text().split():bitmap=(bitmap<<64)|int(word,16)
        require(bitmap==1<<115,'Input is not volume-UP only')
        device=Path('/dev/input')/node.name;s=device.lstat();require(stat.S_ISCHR(s.st_mode) and s.st_rdev==os.makedev(13,64+int(node.name[5:])),'Wrong evdev character identity')
        keyfd=os.open(device,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW);require(os.fstat(keyfd).st_rdev==s.st_rdev,'Input changed during open')
        fcntl.ioctl(keyfd,0x40044590,1);selector.register(keyfd,selectors.EVENT_READ)
        held=bytearray(96);fcntl.ioctl(keyfd,0x80604518,held,True);initially_held=bool(held[115//8]&(1<<(115%8)))
        s=Path('/dev/fb0').lstat();require(stat.S_ISCHR(s.st_mode) and s.st_rdev==os.makedev(29,0),'Wrong fb0')
        fd=os.open('/dev/fb0',os.O_RDONLY|os.O_NOFOLLOW);console.framebuffer_info(fd)
        subprocess.run(['modprobe','backlight'],check=True,capture_output=True,timeout=5)
        (run/'module-owned').touch(mode=0o600)
        subprocess.run(['insmod',str(BASE/'picasso-wled-service.ko'),'confirm_service=1'],check=True,capture_output=True,timeout=5);owned=True
        leasefd=os.open(BL/'lease',os.O_WRONLY|os.O_NOFOLLOW)
        require(f'owner_pid={os.getpid()} ' in (BL/'lease_state').read_text(),'Lease owner is not this process')
        require(int((BL/'max_brightness').read_text())==256 and int((BL/'actual_brightness').read_text())==0,'Wrong provider/initial state')
        for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,stop)
        policy=policy_module.VolumePolicy(time.monotonic(),initially_held);apply(True,'startup_on')
        data['status']='running';save(run/'session.json',data);save(history/(data['run_id']+'-start.json'),data);notify('READY=1\nSTATUS=Native tty1/fbcon; 15s idle; volume-UP; no system suspend')
        until=time.monotonic()+({'idle':35,'guard':60}[probe]) if probe else None
        while not STOP and (until is None or time.monotonic()<until):
            tick()
            for key,mask in selector.select(timeout=0.25):
                raw=os.read(key.fd,24*16);require(bool(raw) and len(raw)%24==0,'Evdev stream lost')
                for offset in range(0,len(raw),24):
                    sec,usec,kind,code,value=EVENT.unpack_from(raw,offset)
                    require(not (kind==0 and code==3),'SYN_DROPPED; fail off')
                    if kind==1:
                        if code==115 and value==1 and not policy.held:data['physical_volume_up_presses']+=1
                        action=policy.key(code,value,time.monotonic())
                        if action=='on':apply(True,'physical_volume_up_on')
            if policy.tick(time.monotonic())=='off':apply(False,'idle_15s_off')
        data['status']='stopped_cleanly'
    except Exception as exc:data.update(status='failed_safe_off',error=type(exc).__name__+': '+str(exc))
    finally:
        if owned and BL.exists():
            try:brightness(0);expected=0;data['screen_on']=False
            except Exception as exc:data['off_error']=type(exc).__name__
        if leasefd is not None:os.close(leasefd)
        if fd is not None:os.close(fd)
        if keyfd is not None:os.close(keyfd)
        selector.close()
        if owned:
            try:cleanup(run)
            except Exception as exc:data['cleanup_error']=type(exc).__name__+': '+str(exc)
        data['module_unloaded']=not Path('/sys/module',MODULE).exists();save(run/'session.json',data);save(history/(data['run_id']+'-end.json'),data)
        print(json.dumps({'status':data['status'],'module_unloaded':data['module_unloaded']}),flush=True);os.close(lock)
    return 0 if data['status']=='stopped_cleanly' and data['module_unloaded'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--probe',choices=('idle','guard'));parser.add_argument('--cleanup',action='store_true');args=parser.parse_args()
    if args.cleanup:
        cleanup(Path('/run/picasso-screen'+('-'+args.probe+'-probe' if args.probe else '')))
    else:raise SystemExit(main(args.probe))
