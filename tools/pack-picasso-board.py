#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Wrap an unchanged own-device default BDF for measured Picasso QMI IDs.

Only for measured chip_id=0x320, board_id=0xff and Xiaomi-Picasso variant.
Source must be the factory bdwlan.bin from the same phone's modem firmware.
This does not generate calibration, change RF data, or validate radio safety.
"""
import argparse
import hashlib
from pathlib import Path
import struct

MAGIC=b'QCA-ATH10K-BOARD\0'
NAME=b'bus=snoc,qmi-board-id=ff,qmi-chip-id=320,variant=Xiaomi-Picasso'

def ie(kind,data):
    return struct.pack('<II',kind,len(data))+data+bytes((-len(data))%4)

def pack(data):
    if len(data)!=26328:raise ValueError('Unexpected factory WCN3990 BDF length')
    return MAGIC+bytes((-len(MAGIC))%4)+ie(0,ie(0,NAME)+ie(1,data))

def unpack(blob):
    if not blob.startswith(MAGIC):raise ValueError('Bad board magic')
    off=(len(MAGIC)+3)&~3
    kind,n=struct.unpack_from('<II',blob,off);off+=8
    if kind!=0 or off+n!=len(blob):raise ValueError('Bad outer board IE')
    end=off+n;out={}
    while off<end:
        kind,n=struct.unpack_from('<II',blob,off);off+=8
        if kind in out or off+n>end:raise ValueError('Duplicate/truncated board IE')
        out[kind]=blob[off:off+n];off+=(n+3)&~3
    if off!=end or set(out)!={0,1} or out[0]!=NAME:raise ValueError('Wrong board identity')
    return out[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--confirm-own-device-factory-bdf',action='store_true',required=True)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=a.input.read_bytes()
    if hashlib.sha256(data).hexdigest()!=a.sha256:p.error('Factory BDF hash mismatch')
    blob=pack(data)
    if unpack(blob)!=data:raise RuntimeError('BDF roundtrip mismatch')
    with a.output.open('xb') as f:f.write(blob)
    print('Wrapped unchanged factory BDF for exact Picasso QMI identity; hardware validation still required.')

if __name__=='__main__':main()
