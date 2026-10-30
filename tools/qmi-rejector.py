#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bounded RMTFS dependency diagnostic, NOT a filesystem/storage server.

Every valid QMI request receives NOT_SUPPORTED. No requested path is opened,
no file handles or memory buffers are granted, and no data payload is logged.
Run only inside an unprivileged PrivateDevices systemd sandbox with a unique
DynamicUser/UID, not shared nobody. NOT_SUPPORTED may crash firmware requiring
RMTFS: disable automatic DSP recovery and arrange bounded DSP shutdown first.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import select
import struct
import time

HEADER=struct.Struct('<BHHH')
KNOWN_PATHS={b'/boot/modem_fs1',b'/boot/modem_fs2',b'/boot/modem_fsg'}


def reject(packet):
    """Return an error-only response and non-data metadata; no I/O."""
    if len(packet)<HEADER.size:
        return None
    flags,txn,msg,size=HEADER.unpack_from(packet)
    if flags!=0 or size!=len(packet)-HEADER.size:
        return None
    pos=HEADER.size; fields=[]
    while pos<len(packet):
        if len(packet)-pos<3:
            return None
        tag,length=struct.unpack_from('<BH',packet,pos);pos+=3
        if length>len(packet)-pos:
            return None
        value=packet[pos:pos+length]
        field={'type':tag,'bytes':length}
        # QMI strings may include a length byte. Match only fixed factory paths;
        # never print other strings, data, DMA addresses, identifiers or NV.
        for path in KNOWN_PATHS:
            if value in (path,path+b'\0',bytes([len(path)])+path):
                field['known_factory_path']=path.decode('ascii')
        fields.append(field);pos+=length
    result=struct.pack('<BHHH',2,4,1,0x5e) # result=FAILURE, NOT_SUPPORTED
    response=HEADER.pack(2,txn,msg,len(result))+result
    return response,{'message_id':msg,'fields':fields,'reply':'NOT_SUPPORTED','storage_access':False}


class Address(C.Structure):
    _fields_=[('family',C.c_ushort),('node',C.c_uint32),('port',C.c_uint32)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-reject-only',action='store_true',required=True)
    p.add_argument('--duration',type=int,default=20)
    p.add_argument('--library',type=Path,required=True)
    p.add_argument('--library-sha256',required=True)
    a=p.parse_args()
    if not (0<a.duration<=30 and os.geteuid()!=0 and os.uname().release=='6.18.58-picasso-lts-wifi1'):
        p.error('Require unprivileged wifi1 trial sandbox and duration <=30 seconds')
    if hashlib.sha256(a.library.read_bytes()).hexdigest()!=a.library_sha256:
        p.error('QRTR library hash mismatch')
    qrtr=C.CDLL(str(a.library),use_errno=True)
    qrtr.qrtr_open.argtypes=[C.c_uint32];qrtr.qrtr_open.restype=C.c_int
    qrtr.qrtr_publish.argtypes=[C.c_int,C.c_uint32,C.c_uint32,C.c_uint32];qrtr.qrtr_publish.restype=C.c_int
    libc=C.CDLL(None,use_errno=True)
    libc.recvfrom.argtypes=[C.c_int,C.c_void_p,C.c_size_t,C.c_int,C.POINTER(Address),C.POINTER(C.c_uint)]
    libc.recvfrom.restype=C.c_ssize_t
    libc.sendto.argtypes=[C.c_int,C.c_void_p,C.c_size_t,C.c_int,C.POINTER(Address),C.c_uint]
    libc.sendto.restype=C.c_ssize_t
    fd=qrtr.qrtr_open(0)
    if fd<0:raise OSError(C.get_errno(),'qrtr_open')
    try:
        if qrtr.qrtr_publish(fd,14,1,0)<0:raise OSError(C.get_errno(),'qrtr_publish')
        print(json.dumps({'status':'reject_only_registered','service':14,'uid':os.geteuid(),'storage_access':False}),flush=True)
        until=time.monotonic()+a.duration
        count=0
        while time.monotonic()<until and count<128:
            if not select.select([fd],[],[],min(0.5,max(0,until-time.monotonic())))[0]:continue
            buf=C.create_string_buffer(8192);addr=Address();length=C.c_uint(C.sizeof(addr))
            n=libc.recvfrom(fd,buf,len(buf),0,C.byref(addr),C.byref(length))
            if n<0:raise OSError(C.get_errno(),'recvfrom')
            if addr.family!=42 or addr.port==0xffff:continue
            r=reject(buf.raw[:n])
            if r is None:continue
            response,metadata=r
            if libc.sendto(fd,response,len(response),0,C.byref(addr),C.sizeof(addr))!=len(response):
                raise OSError(C.get_errno(),'sendto')
            count+=1
            print(json.dumps(metadata),flush=True)
        print(json.dumps({'status':'reject_only_finished','requests_rejected':count,'storage_access':False}),flush=True)
    finally:os.close(fd)


if __name__=='__main__':main()
