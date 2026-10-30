#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Show native tty1/fbcon only. No pixels, terminal text, or fake UI written."""
import fcntl
import os
from pathlib import Path
import stat
import struct


def require(ok,message):
    if not ok:raise RuntimeError(message)


def framebuffer_info(fd):
    fixed=bytearray(80);var=bytearray(160)
    fcntl.ioctl(fd,0x4602,fixed,True);fcntl.ioctl(fd,0x4600,var,True)
    require(bytes(fixed[:16]).rstrip(b'\0')==b'simpledrmdrmfb','Wrong framebuffer driver')
    require(struct.unpack_from('@Q',fixed,16)[0]==0,'Expected audited DRM shadow buffer')
    require(struct.unpack_from('@I',fixed,24)[0]==10368000 and struct.unpack_from('@I',fixed,48)[0]==4320,'Wrong framebuffer length/stride')
    require(struct.unpack_from('@8I',var)==(1080,2400,1080,2400,0,0,32,0),'Wrong framebuffer mode/offset')
    require([struct.unpack_from('@3I',var,x) for x in (32,44,56,68)]==[(16,8,0),(8,8,0),(0,8,0),(0,0,0)],'Wrong RGB bitfields')


def console_info():
    require(Path('/sys/class/tty/tty0/active').read_text().strip()=='tty1','Only audited active tty1 supported; do not switch VT')
    bound=[]
    for node in Path('/sys/class/vtconsole').glob('vtcon*'):
        if 'frame buffer device' in (node/'name').read_text() and (node/'bind').read_text().strip()=='1':bound.append(node.name)
    require(len(bound)==1,'Expected one bound native framebuffer console')
    s=Path('/dev/tty1').lstat();require(stat.S_ISCHR(s.st_mode) and s.st_rdev==os.makedev(4,1),'Wrong tty1 character identity')
    fd=os.open('/dev/tty1',os.O_RDONLY|os.O_NOCTTY|os.O_NOFOLLOW)
    try:
        require(os.fstat(fd).st_rdev==s.st_rdev,'tty1 changed during open')
        mode=bytearray(4);fcntl.ioctl(fd,0x4b3b,mode,True)  # KDGETMODE only, never KDSETMODE.
        require(struct.unpack('@i',mode)[0]==0,'Native VT must remain KD_TEXT; do not override a graphics owner')
    finally:os.close(fd)
    return {'active_tty':'tty1','mode':'KD_TEXT','fbcon':bound[0],'pixel_or_terminal_payload_read_or_written':False}


def screen_on(tick,set_brightness):
    console_info()
    blank=Path('/sys/class/graphics/fb0/blank')
    # Caller has already verified actual backlight 0. Force a native fbcon
    # redraw even on first start, to replace leftover OLD diagnostic pixels.
    blank.write_text('4');require(blank.read_text().strip() in ('1','4'),'Native blank not acknowledged')
    tick()
    blank.write_text('0');require(blank.read_text().strip()=='0','Native unblank not acknowledged')
    tick()
    set_brightness(64)  # fbcon/agetty owns contents; no framebuffer/TTY writes.
