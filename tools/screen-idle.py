#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Screen-only idle/wake daemon; refuses incomplete backlight or key hardware.

Uses backlight class and fb blank sysfs only, never raw PMIC/MMIO, poweroff or
system suspend. Grabs only explicitly discovered power/volume evdev devices.
No touch/keyboard/secret capture. Real visual/button acceptance is separate.
"""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import stat
import struct
import sys
import time

EV_KEY=1
EVENT=struct.Struct('@llHHi')
EVIOCGRAB=0x40044590
NAMES={'gpio-keys','pm8941_pwrkey','pm8941_resin'}


def require(value,message):
    if not value:raise RuntimeError(message)


def key_bits(text,word_bits=64):
    words=text.split();value=0
    for word in words:
        part=int(word,16)
        if part<0 or part>=1<<word_bits:raise ValueError('Bad key bitmap word')
        value=(value<<word_bits)|part
    return {i for i in (114,115,116) if value&(1<<i)}


def policy_module():
    p=Path(__file__).with_name('screen-idle-policy.py')
    s=importlib.util.spec_from_file_location('screen_policy',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def notify(text):
    addr=os.environ.get('NOTIFY_SOCKET')
    if addr:
        if addr.startswith('@'):addr='\0'+addr[1:]
        with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as sock:sock.sendto(text.encode(),addr)


def discover(require_keys=True):
    require(os.geteuid()==0 and os.uname().machine=='aarch64','Native root AArch64 required')
    require(Path('/etc/picasso-fedora-root').read_text().strip()=='PICASSO_FEDORA44_DISKROOT_V2','Wrong disk root')
    matches=[]
    for p in Path('/sys/class/backlight').glob('*'):
        of=p/'device/of_node'
        if not of.exists():continue
        compatible=(of/'compatible').read_bytes().split(b'\0')
        if b'qcom,pm8150l-wled' not in compatible:continue
        require(str(of.resolve()).endswith('/pmic@5/backlight@d800'),'Unexpected WLED USID/address')
        for name,expected in [('qcom,current-limit-microamp',22500),('qcom,ovp-millivolt',28000),('qcom,cabc-sel',1)]:
            require(int.from_bytes((of/name).read_bytes(),'big')==expected,'Unaudited WLED property '+name)
        require((of/'qcom,enabled-strings').read_bytes()==struct.pack('>III',0,1,2),'Unaudited WLED strings')
        require(int((p/'max_brightness').read_text())==4095,'Unexpected backlight range')
        matches.append(p.resolve())
    require(len(matches)==1,'No unique audited real PM8150L backlight; do not substitute framebuffer blank for physical off')
    fb=Path('/sys/class/graphics/fb0').resolve()
    require((fb/'name').read_text().strip()=='simpledrmdrmfb','Only audited splash handoff supported by this phase')
    require((fb/'virtual_size').read_text().strip()=='1080,2400' and (fb/'bits_per_pixel').read_text().strip()=='32','Framebuffer geometry mismatch')
    devices=[];coverage=set()
    for p in (Path('/sys/class/input').glob('event*') if require_keys else []):
        name=(p/'device/name').read_text().strip()
        if name not in NAMES:continue
        bits=key_bits((p/'device/capabilities/key').read_text())
        if not bits:continue
        node=Path('/dev/input')/p.name;s=node.lstat()
        require(stat.S_ISCHR(s.st_mode) and os.major(s.st_rdev)==13,'Unexpected evdev character identity')
        require((os.major(s.st_rdev),os.minor(s.st_rdev))==tuple(map(int,(p/'dev').read_text().split(':'))),'evdev sysfs identity mismatch')
        devices.append({'path':str(node),'name':name,'keys':sorted(bits)});coverage|=bits
    if require_keys:require(coverage=={114,115,116},'Power and both volume keys must be present before blanking')
    return {'backlight':str(matches[0]),'framebuffer':str(fb),'inputs':devices,'scope':'bootloader splash handoff + physical backlight only; not native DSI or system suspend'}


def temps():
    out={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
    require(bool(out),'No thermal telemetry');return out


def write_verified(path,value,accepted=None):
    fd=os.open(path,os.O_WRONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        data=str(value).encode();require(os.write(fd,data)==len(data),'Short sysfs write')
    finally:os.close(fd)
    actual=int(Path(path).read_text())
    require(actual in ((value,) if accepted is None else accepted),'Sysfs state did not read back')


def apply(hardware,on,brightness):
    bl=Path(hardware['backlight'])/'brightness';fb=Path(hardware['framebuffer'])/'blank'
    if on:
        require(max(temps().values())<45000,'Thermal interlock blocks screen-on')
        write_verified(fb,0);write_verified(bl,brightness)
    else:
        # Physical backlight off first; never equate virtual DPMS with LED off.
        write_verified(bl,0)
        # fbcon_fb_blanked can synchronously re-enter fb_blank and normalize
        # POWERDOWN(4) to NORMAL(1). Accept either only AFTER real LED-off=0.
        write_verified(fb,4,accepted=(1,4))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',action='store_true');parser.add_argument('--off',action='store_true')
    parser.add_argument('--idle-seconds',type=int,default=60)
    parser.add_argument('--brightness',type=int,default=64)
    parser.add_argument('--runtime-seconds',type=int,default=120)
    args=parser.parse_args();os.umask(0o077)
    require(1<=args.brightness<=256,'Trial brightness restricted to 1..256/4095')
    require(1<=args.runtime_seconds<=300,'Only bounded screen trial allowed until real visual/key acceptance')
    m=policy_module();policy=m.ScreenPolicy(args.idle_seconds,time.monotonic())
    hardware=discover(require_keys=not args.off)
    if args.probe:print(json.dumps(hardware,indent=2));return 0
    if args.off:apply(hardware,False,args.brightness);return 0
    require(max(temps().values())<40000,'Start below 40C')
    require(EVENT.size==24,'Unexpected native input-event ABI')
    run=Path('/run/picasso-screen');run.mkdir(mode=0o700,exist_ok=True)
    lock=os.open(run/'owner.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    stopped=False
    def stop(*_):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    fds=[];buffers={};events=[];selector=selectors.DefaultSelector();started=time.monotonic()
    try:
        for device in hardware['inputs']:
            fd=os.open(device['path'],os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC)
            fds.append(fd);fcntl.ioctl(fd,EVIOCGRAB,1);selector.register(fd,selectors.EVENT_READ);buffers[fd]=b''
        apply(hardware,True,args.brightness);notify('READY=1\nSTATUS=Bounded screen-only trial; short power/volume keys')
        events.append({'state':'on','seconds':0})
        while not stopped and time.monotonic()-started<args.runtime_seconds:
            now=time.monotonic();temperature=temps();require(max(temperature.values())<45000,'45C thermal abort')
            action=policy.tick(now)
            if action:apply(hardware,False,args.brightness);events.append({'state':'off','cause':'idle','seconds':round(now-started,3)})
            for key,mask in selector.select(timeout=0.25):
                fd=key.fd
                data=os.read(fd,EVENT.size*16);require(bool(data),'evdev disconnected')
                buffers[fd]+=data
                while len(buffers[fd])>=EVENT.size:
                    frame,buffers[fd]=buffers[fd][:EVENT.size],buffers[fd][EVENT.size:]
                    sec,usec,kind,code,value=EVENT.unpack(frame)
                    if kind!=EV_KEY:continue
                    action=policy.key(code,value,time.monotonic())
                    if action:
                        apply(hardware,action=='on',args.brightness)
                        events.append({'state':action,'cause':'allowed-physical-key','key_code':code,'seconds':round(time.monotonic()-started,3)})
            notify('WATCHDOG=1')
        return 0
    finally:
        try:apply(hardware,False,args.brightness)
        finally:
            for fd in fds:
                try:fcntl.ioctl(fd,EVIOCGRAB,0)
                finally:os.close(fd)
            selector.close();os.close(lock)
            (run/'trial-result.json').write_text(json.dumps({'scope':hardware['scope'],'events':events,'real_visual_acceptance':False,'system_suspend_attempted':False,'credential_files_accessed':False},indent=2)+'\n')


if __name__=='__main__':sys.exit(main())
