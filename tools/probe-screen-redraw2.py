#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One exclusive shadow-buffer redraw probe while real WLED gate is OFF.

Readback is limited to the framebuffer after our complete synthetic write.
Only equality-to-pattern/all-zero booleans leave the process, never pixels or
unknown-pixel hashes. No panel/reset/PMIC writes or real backlight activation.
"""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import time

BASE=Path('/opt/picasso-display-trial')
RUN=Path('/run/picasso-fb-redraw2')
KNOWN_FRAME=None
BLANK=Path('/sys/class/graphics/fb0/blank')
SIZE=10368000


def require(ok,message):
    if not ok:raise RuntimeError(message)


def load_helper():
    path=BASE/'test-screen-handoff.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest()=='f067ce302f690ccedc9c1a89c9ab82f65f7bf27b34fc6e1ec8dc8b0b1251dc0f','Original helper changed')
    spec=importlib.util.spec_from_file_location('fb_helper',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def write_all(fd,data):
    view=memoryview(data);offset=0
    while view:
        count=os.pwrite(fd,view,offset);require(count>0,'Short fb write');view=view[count:];offset+=count


def compare_owned_pixels(fd,expected,zero):
    # Distinguish a tiny fbcon cursor change from loss of the complete picture.
    # Only numerical equality statistics escape, no raw pixels/unknown hashes.
    global KNOWN_FRAME
    if KNOWN_FRAME is None:KNOWN_FRAME=b''.join(load_helper().pattern_row(y) for y in range(2400))
    require(hashlib.sha256(KNOWN_FRAME).digest()==expected,'Wrong known test pattern')
    h=hashlib.sha256();offset=0;rgb_matches=0
    while offset<SIZE:
        chunk=os.pread(fd,min(1024*1024,SIZE-offset),offset);require(bool(chunk) and len(chunk)%4==0,'Short fb readback');h.update(chunk)
        wanted=memoryview(KNOWN_FRAME)[offset:offset+len(chunk)].cast('I')
        rgb_matches+=sum((actual&0xffffff)==(reference&0xffffff) for actual,reference in zip(memoryview(chunk).cast('I'),wanted))
        offset+=len(chunk)
    digest=h.digest()
    return {'matches_synthetic_pattern':digest==expected,'matches_all_zero':digest==zero,'rgb_pattern_match_ppm':round(rgb_matches*1000000/(SIZE//4))}


def cleanup():
    # Can also run independently as ExecStopPost after a killed main process.
    if not RUN.exists():return
    before=RUN/'before.json'
    if (RUN/'synthetic-write-started').exists():
        fd=os.open('/dev/fb0',os.O_RDWR|os.O_NOFOLLOW)
        try:
            load_helper().framebuffer_info(fd);write_all(fd,bytes(SIZE))
        finally:os.close(fd)
    if before.exists():
        level=json.loads(before.read_text())['blank'];require(level in (0,1,4),'Wrong saved blank state');BLANK.write_text(str(level))
    if (RUN/'audit-owned').exists() and Path('/sys/module/picasso_wled_audit').exists():subprocess.run(['rmmod','picasso_wled_audit'],check=True,capture_output=True,timeout=5)


def main():
    os.umask(0o077)
    require(os.geteuid()==0 and os.uname().release=='6.18.58-picasso-lts-wifi2','Native tested kernel/root required')
    require(hashlib.sha256(Path('/sys/firmware/fdt').read_bytes()).hexdigest()=='62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388','Different hardware tree')
    require(Path('/etc/picasso-fedora-root').read_text().strip()=='PICASSO_FEDORA44_DISKROOT_V2','Wrong disk root')
    RUN.mkdir(mode=0o700)
    result={'status':'running','scope':'WLED-off synthetic fbcon redraw probe','raw_pixels_exported_or_saved':False,'unknown_pixel_hash_exported_or_saved':False,'old_framebuffer_before_synthetic_write_read':False,'events':[]}
    fd=None
    def tick():
        values=[int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')];require(bool(values),'No temperature telemetry');require(max(values)<45000,'45C thermal abort')
        result['peak_temperature_mc']=max(result.get('peak_temperature_mc',0),max(values))
    try:
        require(not list(Path('/sys/class/backlight').glob('*')),'Backlight owner exists')
        require(not Path('/sys/module/picasso_wled_handoff').exists(),'Handoff owner exists')
        require(not Path('/sys/module/picasso_wled_audit').exists(),'Read-only audit already owned')
        values=[int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')];require(values and max(values)<40000,'Start below 40C')
        helper=load_helper();module=BASE/'picasso-wled-audit-v2.ko'
        require(hashlib.sha256(module.read_bytes()).hexdigest()=='d34d8c40b5d21d9aafd95169a14c5fdaab60e9863172e547574c199f1902a9d4','Audit module changed')
        (RUN/'audit-owned').touch(mode=0o600)
        subprocess.run(['insmod',str(module),'confirm_readonly=1'],check=True,capture_output=True,timeout=5)
        snapshot=Path('/sys/kernel/picasso_wled_audit/snapshot');require(snapshot.is_file(),'No audited read-only WLED snapshot')
        registers={int(line.split('=')[0],16):int(line.split('=')[1],16) for line in snapshot.read_text().splitlines()[1:]}
        require(registers[0xd846]&128==0,'Real WLED gate must be OFF before synthetic probe');result['actual_wled_gate_verified_off']=True
        s=Path('/dev/fb0').lstat();require(stat.S_ISCHR(s.st_mode) and s.st_rdev==os.makedev(29,0),'Wrong fb0')
        fd=os.open('/dev/fb0',os.O_RDWR|os.O_NOFOLLOW);helper.framebuffer_info(fd)
        before={'blank':int(BLANK.read_text())};(RUN/'before.json').write_text(json.dumps(before))
        frame=b''.join(helper.pattern_row(y) for y in range(2400));expected=hashlib.sha256(frame).digest();zero=hashlib.sha256(bytes(SIZE)).digest()
        (RUN/'synthetic-write-started').touch(mode=0o600)
        write_all(fd,frame);tick()
        result['events'].append({'phase':'after_full_own_pattern_write',**compare_owned_pixels(fd,expected,zero)})
        BLANK.write_text('4');time.sleep(0.1);tick()
        result['events'].append({'phase':'after_blank4','fb_blank_readback':int(BLANK.read_text()),**compare_owned_pixels(fd,expected,zero)})
        BLANK.write_text('0');time.sleep(0.1);tick()
        result['events'].append({'phase':'after_unblank_without_redraw','fb_blank_readback':int(BLANK.read_text()),**compare_owned_pixels(fd,expected,zero)})
        write_all(fd,frame);tick()
        result['events'].append({'phase':'immediately_after_explicit_post_unblank_redraw',**compare_owned_pixels(fd,expected,zero)})
        time.sleep(0.2);tick()
        result['events'].append({'phase':'after_post_unblank_redraw_and_200ms',**compare_owned_pixels(fd,expected,zero)})
        result['status']='completed_synthetic_redraw_probe'
    except Exception as exc:result.update(status='failed_synthetic_redraw_probe',error=type(exc).__name__+': '+str(exc))
    finally:
        if fd is not None:os.close(fd)
        try:cleanup();result['cleanup_ok']=True
        except Exception as exc:result.update(cleanup_ok=False,cleanup_error=type(exc).__name__+': '+str(exc))
        (RUN/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['status']=='completed_synthetic_redraw_probe' and result['cleanup_ok'] else 1


if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--cleanup']:cleanup()
    elif len(sys.argv)==1:raise SystemExit(main())
    else:raise SystemExit('No arbitrary arguments supported')
