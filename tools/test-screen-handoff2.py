#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exclusive visual2: redraw AFTER each unblank, BEFORE low backlight on.

fbcon unblank overwrote the first trial's pattern. The old trial/result stays
unchanged. This is not DSI/panel-reset, system resume, or an all-three-key test.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import selectors
import stat
import struct
import subprocess
import time

BASE=Path('/opt/picasso-display-trial')
RUN=Path('/run/picasso-screen-visual2')
BL=Path('/sys/class/backlight/picasso-handoff')
MODULE_SHA='e9198bfa9f59081225e74b64673b78df151f31b767770a62a97a0ef34a037935'
EVENT=struct.Struct('@llHHi')


def require(ok,message):
    if not ok:raise RuntimeError(message)


def framebuffer_info(fd):
    fixed=bytearray(80);var=bytearray(160)
    fcntl.ioctl(fd,0x4602,fixed,True);fcntl.ioctl(fd,0x4600,var,True)
    require(bytes(fixed[:16]).rstrip(b'\0')==b'simpledrmdrmfb','Wrong framebuffer driver')
    require(struct.unpack_from('@Q',fixed,16)[0]==0,'Expected audited DRM shadow buffer, not physical mapping')
    require(struct.unpack_from('@I',fixed,24)[0]==10368000 and struct.unpack_from('@I',fixed,48)[0]==4320,'Wrong framebuffer length/stride')
    require(struct.unpack_from('@8I',var)==(1080,2400,1080,2400,0,0,32,0),'Wrong framebuffer mode/offset')
    require([struct.unpack_from('@3I',var,x) for x in (32,44,56,68)]==[(16,8,0),(8,8,0),(0,8,0),(0,0,0)],'Wrong RGB bitfields')


def pattern_row(y):
    # Static, subdued grayscale + RGB bars; no strobing or old-pixel readback.
    color=(32,32,32)
    if 300<=y<700:color=(96,24,24)
    elif 900<=y<1300:color=(24,96,24)
    elif 1500<=y<1900:color=(24,24,96)
    return bytes((color[2],color[1],color[0],0))*1080


def draw_pattern(fd,frame,tick):
    """Repaint the whole known frame after fbcon has completed its redraw."""
    view=memoryview(frame);offset=0
    while view:
        count=os.pwrite(fd,view,offset);require(count>0,'Short framebuffer write')
        view=view[count:];offset+=count;tick()
    require(offset==10368000,'Framebuffer span mismatch')


def screen_on(fd,frame,tick,set_brightness):
    Path('/sys/class/graphics/fb0/blank').write_text('0')
    draw_pattern(fd,frame,tick)
    set_brightness(64)


def main():
    os.umask(0o077)
    require(os.geteuid()==0 and os.uname().release=='6.18.58-picasso-lts-wifi2','Native tested wifi2 only')
    require(Path('/etc/picasso-fedora-root').read_text().strip()=='PICASSO_FEDORA44_DISKROOT_V2','Wrong disk root')
    require(hashlib.sha256(Path('/sys/firmware/fdt').read_bytes()).hexdigest()=='62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388','Different display/PMIC tree')
    RUN.mkdir(mode=0o700)
    result={'status':'running','revision':2,'scope':'post-unblank full redraw + bounded backlight; volume-UP only','physical_visual_confirmed':False,'old_pixels_read':False,'phases':[],'physical_volume_up_event':False,'peak_temperature_mc':0}
    fb=None;keyfd=None;frame=None;pixel_written=False;module_started=False;selector=selectors.DefaultSelector()
    def save():
        temp=RUN/'result.new';temp.write_text(json.dumps(result,indent=2)+chr(10));temp.replace(RUN/'result.json')
    def tick():
        values={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')};require(bool(values),'No thermal telemetry')
        result['peak_temperature_mc']=max(result['peak_temperature_mc'],max(values.values()));require(max(values.values())<45000,'45C thermal abort')
    def brightness(value):
        (BL/'brightness').write_text(str(value));require(int((BL/'actual_brightness').read_text())==value,'Actual backlight readback mismatch')
    def phase(name,on):
        nonlocal pixel_written
        tick()
        if on:
            pixel_written=True
            screen_on(fb,frame,tick,brightness)
        else:
            brightness(0);Path('/sys/class/graphics/fb0/blank').write_text('4')
        result['phase']=name;result['phases'].append({'phase':name,'monotonic':time.monotonic(),'actual_brightness':int((BL/'actual_brightness').read_text()),'full_redraw_after_unblank':on});save()
    def wait(seconds,wake=False):
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            tick()
            for key,mask in selector.select(timeout=0.1):
                data=os.read(key.fd,24*16)
                require(bool(data) and len(data)%24==0,'Evdev stream error')
                for offset in range(0,len(data),24):
                    sec,usec,kind,code,value=EVENT.unpack_from(data,offset)
                    if wake and kind==1 and code==115 and value==1:
                        result['physical_volume_up_event']=True;save();return
    try:
        require(max(int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp'))<40000,'Start below 40C')
        require(not list(Path('/sys/class/backlight').glob('*')),'Existing backlight owner refused')
        require(not Path('/sys/module/picasso_wled_handoff').exists(),'Existing handoff session refused')
        require(not Path('/sys/module/picasso_wled_audit').exists(),'Read-only audit still owned')
        module=BASE/'picasso-wled-handoff.ko';require(hashlib.sha256(module.read_bytes()).hexdigest()==MODULE_SHA,'Module changed')
        nodes=[]
        for p in Path('/sys/class/input').glob('event*'):
            if (p/'device/name').read_text().strip()=='gpio-keys':nodes.append(p)
        require(len(nodes)==1,'Expected one GPIO volume-up input')
        event=Path('/dev/input')/nodes[0].name;s=event.lstat();require(stat.S_ISCHR(s.st_mode) and os.major(s.st_rdev)==13,'Wrong evdev identity')
        # Match the audited bitmap: KEY_VOLUMEUP115 only, not a keyboard.
        words=(nodes[0]/'device/capabilities/key').read_text().split();bitmap=0
        for word in words:bitmap=(bitmap<<64)|int(word,16)
        require(bitmap==1<<115,'GPIO input is not the audited volume-UP-only device')
        keyfd=os.open(event,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW);fcntl.ioctl(keyfd,0x40044590,1);selector.register(keyfd,selectors.EVENT_READ)
        s=Path('/dev/fb0').lstat();require(stat.S_ISCHR(s.st_mode) and s.st_rdev==os.makedev(29,0),'Wrong fb0 character device')
        fb=os.open('/dev/fb0',os.O_RDWR|os.O_NOFOLLOW);framebuffer_info(fb)
        subprocess.run(['modprobe','backlight'],check=True,capture_output=True,timeout=5)
        subprocess.run(['insmod',str(module),'confirm_handoff=1','duration_seconds=70'],check=True,capture_output=True,timeout=10)
        module_started=True
        require(int((BL/'max_brightness').read_text())==256 and 'hardware_max=4095' in (BL/'boot_config_verified').read_text(),'Unexpected bounded handoff provider')
        # fb_write uses the DRM shadow/damage path. Never mmap physical memory.
        # Do not rely on the image surviving fbcon blank/unblank transitions.
        frame=b''.join(pattern_row(y) for y in range(2400))
        phase('pattern_on_first_15s',True);wait(15)
        phase('off_press_only_volume_up_within_20s',False);wait(20,wake=True)
        phase('pattern_on_by_volume_up' if result['physical_volume_up_event'] else 'pattern_on_scheduled_no_key_seen',True);wait(15)
        phase('final_off',False);result['status']='completed_bounded_sequence_visual_confirmation_required'
    except Exception as exc:
        result.update(status='failed_bounded_visual_trial',error=type(exc).__name__+': '+str(exc))
    finally:
        if module_started and BL.exists():
            try:brightness(0)
            except Exception as exc:result['off_error']=type(exc).__name__
        if fb is not None:
            try:
                if pixel_written:
                    zero=bytes(1024*1024);offset=0
                    while offset<10368000:
                        count=os.pwrite(fb,zero[:min(len(zero),10368000-offset)],offset)
                        require(count>0,'Short framebuffer clear');offset+=count
            except Exception as exc:result['framebuffer_clear_error']=type(exc).__name__
            finally:os.close(fb)
        if module_started:
            try:Path('/sys/class/graphics/fb0/blank').write_text('4')
            except Exception as exc:result['blank_cleanup_error']=type(exc).__name__
        if keyfd is not None:
            try:fcntl.ioctl(keyfd,0x40044590,0)
            except Exception as exc:result['input_ungrab_error']=type(exc).__name__
            finally:os.close(keyfd)
        selector.close()
        if module_started and Path('/sys/module/picasso_wled_handoff').exists():
            p=subprocess.run(['rmmod','picasso_wled_handoff'],capture_output=True,text=True,timeout=8);result['rmmod_returncode']=p.returncode
        result['module_unloaded']=not Path('/sys/module/picasso_wled_handoff').exists();save()
        print(json.dumps({'status':result['status'],'physical_volume_up_event':result['physical_volume_up_event'],'module_unloaded':result['module_unloaded']}),flush=True)
    return 0 if result['status'].startswith('completed_') and result['module_unloaded'] else 1


if __name__=='__main__':raise SystemExit(main())
