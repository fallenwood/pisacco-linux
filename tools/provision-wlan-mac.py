#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Provision the device-reported DMS WLAN MAC into WLFW runtime, before WLAN.

No random/stable-hash address generation, NV parsing, partition access, or
persistent firmware write. QMI 0x0033 / TLV 0x10 follows qmi_wlfw_v01.{h,c}.
Operator must arrange bounded MPSS/RMTFS lifetime and keep wlan0 unmanaged.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import select
import stat
import struct
import time

HEADER=struct.Struct('<BHHH')
MSG=0x33
TXN=0x4d41


def address_from_record(record,expected_sha256):
    if (record.get('returncode')!=0 or record.get('query_read_only') is not True or
        record.get('persist_read') is not False or
        record.get('source')!='libqmi DMS Get MAC Address WLAN, same-device modem using authorized private NV copies'):
        raise ValueError('Require successful device DMS WLAN provenance')
    text=record.get('mac','')
    if not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}',text):
        raise ValueError('Malformed device address')
    mac=bytes.fromhex(text.replace(':',''))
    if mac in (bytes(6),b'\xff'*6) or mac[0]&3:
        raise ValueError('Require globally administered unicast DMS address; no fallback')
    if hashlib.sha256(mac).hexdigest()!=expected_sha256:
        raise ValueError('DMS query checkpoint changed')
    return mac


def request(mac):
    if len(mac)!=6 or mac[0]&3 or mac==bytes(6):raise ValueError('Invalid factory address')
    body=struct.pack('<BH',0x10,6)+mac
    return HEADER.pack(0,TXN,MSG,len(body))+body


def response(packet):
    if len(packet)!=14:raise ValueError('Unexpected MAC response length')
    flags,txn,msg,size=HEADER.unpack_from(packet)
    if (flags,txn,msg,size)!=(2,TXN,MSG,7):raise ValueError('Unexpected QMI response')
    tag,n,result,error=struct.unpack_from('<BHHH',packet,HEADER.size)
    if (tag,n)!=(2,4):raise ValueError('Invalid result TLV')
    if result or error:raise ValueError(f'WLFW rejected MAC: result={result}, error={error}')
    return {'status':'device_dms_mac_provisioned_in_wlfw_runtime','random_or_derived_mac_used':False,'raw_partition_access':False}


class Address(C.Structure):
    _fields_=[('family',C.c_ushort),('node',C.c_uint32),('port',C.c_uint32)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record',type=Path,required=True);p.add_argument('--record-mac-sha256',required=True)
    p.add_argument('--library',type=Path,required=True);p.add_argument('--library-sha256',required=True)
    p.add_argument('--port',type=int,required=True)
    p.add_argument('--hold-seconds',type=int,default=0,help='Keep client alive during bounded driver initialization')
    a=p.parse_args()
    if os.geteuid()!=0 or os.uname().release!='6.18.58-picasso-lts-wifi2' or not 0<a.port<0xffff or not 0<=a.hold_seconds<=120:
        p.error('Require bounded native wifi2 trial and discovered local WLFW endpoint')
    s=a.record.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_uid or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1 or s.st_size>8192:
        p.error('Require private root-owned DMS record')
    if hashlib.sha256(a.library.read_bytes()).hexdigest()!=a.library_sha256:p.error('QRTR library hash mismatch')
    mac=address_from_record(json.loads(a.record.read_text()),a.record_mac_sha256)
    lib=C.CDLL(str(a.library),use_errno=True);lib.qrtr_open.argtypes=[C.c_uint32];lib.qrtr_open.restype=C.c_int
    c=C.CDLL(None,use_errno=True)
    c.sendto.argtypes=[C.c_int,C.c_void_p,C.c_size_t,C.c_int,C.POINTER(Address),C.c_uint];c.sendto.restype=C.c_ssize_t
    c.recvfrom.argtypes=[C.c_int,C.c_void_p,C.c_size_t,C.c_int,C.POINTER(Address),C.POINTER(C.c_uint)];c.recvfrom.restype=C.c_ssize_t
    fd=lib.qrtr_open(0)
    if fd<0:raise OSError(C.get_errno(),'qrtr_open')
    try:
        target=Address(42,0,a.port);data=request(mac)
        if c.sendto(fd,data,len(data),0,C.byref(target),C.sizeof(target))!=len(data):raise OSError(C.get_errno(),'sendto')
        until=time.monotonic()+8
        while time.monotonic()<until:
            if not select.select([fd],[],[],max(0,until-time.monotonic()))[0]:break
            buf=C.create_string_buffer(256);src=Address();n=C.c_uint(C.sizeof(src))
            count=c.recvfrom(fd,buf,len(buf),0,C.byref(src),C.byref(n))
            if count<0:raise OSError(C.get_errno(),'recvfrom')
            if src.family!=42 or src.node!=0 or src.port!=a.port:continue
            print(json.dumps(response(buf.raw[:count])),flush=True)
            if a.hold_seconds:time.sleep(a.hold_seconds)
            return
        raise TimeoutError('No matching WLFW MAC response')
    finally:os.close(fd)


if __name__=='__main__':main()
