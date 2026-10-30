#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Experimental FD-only RMTFS: three regular working copies, never raw NV.

Wire schema: linux-msm/rmtfs b30a3eb38f9af283f18dbd3c7755653efc52c094,
qmi_rmtfs.qmi. No requested path is opened. Use a DynamicUser RootDirectory,
PrivateDevices and systemd OpenFile= for four prevalidated descriptors. Disable
DSP automatic recovery and use a bounded, attended hardware test.
"""
import argparse
import ctypes as C
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import struct
import time

HEADER=struct.Struct('<BHHH')
PATHS={b'/boot/modem_fs1':'modem_fs1',b'/boot/modem_fs2':'modem_fs2',b'/boot/modem_fsg':'modem_fsg'}
IMAGE_SIZE=8*1024**2
MEMORY_SIZE=0x280000
MAX_TRANSFER=2*1024**2


def require(ok,message):
    if not ok:raise ValueError(message)


def tlv(tag,data):return struct.pack('<BH',tag,len(data))+data


def parse(packet):
    require(len(packet)>=7,'short header')
    flags,txn,msg,size=HEADER.unpack_from(packet)
    require(flags==0 and size==len(packet)-7,'bad request header')
    fields={};pos=7
    while pos<len(packet):
        require(len(packet)-pos>=3,'short TLV')
        tag,n=struct.unpack_from('<BH',packet,pos);pos+=3
        require(n<=len(packet)-pos and tag not in fields,'bad or duplicate TLV')
        fields[tag]=packet[pos:pos+n];pos+=n
    return txn,msg,fields


def scalar(fields,tag,width):
    data=fields[tag];require(len(data)==width,'bad scalar width')
    return int.from_bytes(data,'little')


def within(offset,length,size):
    return 0<=offset<=size and 0<=length<=size-offset


class Backend:
    """Pure protocol/FD engine; constructor does not open filesystem paths."""
    def __init__(self,memory_fd,images,base,size=MEMORY_SIZE):
        require(set(images)==set(PATHS.values()),'only three authorized copies')
        require(base%4096==0 and 0x80000000<=base<base+size<=0x100000000,'bad memory range')
        require(size==MEMORY_SIZE,'bad shared memory size')
        self.mem=memory_fd;self.images=images;self.base=base;self.size=size
        self.handles={};self.next_handle=1;self.allocations={};self.granted_size=0
        self.read_bytes=0;self.write_bytes=0;self.requests=0

    def handle(self,packet,node=0):
        txn,msg,fields=parse(packet)
        optional=b'';err=0
        meta={'message_id':msg,'storage':'private_regular_copies_only'}
        try:
            require(node==0,'wrong modem node')
            if msg==1:
                require(set(fields)=={1},'bad open fields')
                # Top-level QMI_STRING uses the TLV length, no extra prefix.
                path=fields[1];require(path in PATHS,'unapproved path (redacted)')
                name=PATHS[path];meta['path']=path.decode('ascii')
                handle=next((k for k,v in self.handles.items() if v==name),None)
                if handle is None:
                    require(len(self.handles)<3,'too many handles')
                    handle=self.next_handle;self.next_handle+=1;self.handles[handle]=name
                optional=tlv(0x10,struct.pack('<I',handle))
            elif msg in (2,3,4,5):
                handle=scalar(fields,1,4);meta['caller_id']=handle
                require(handle in self.handles,'invalid or closed caller id')
                name=self.handles[handle];fd=self.images[name]
                if msg==2:
                    require(set(fields)=={1},'bad close fields')
                    os.fdatasync(fd);del self.handles[handle];self.allocations.pop(handle,None)
                elif msg==4:
                    require(set(fields)=={1,2},'bad allocation fields')
                    n=scalar(fields,2,4);require(0<n<=self.size,'oversized allocation')
                    self.allocations[handle]=n
                    # Upstream rmtfs_mem_alloc/free define ONE client-1 buffer,
                    # shared across all NV file handles (free is a no-op).
                    self.granted_size=max(self.granted_size,n)
                    optional=tlv(0x10,struct.pack('<Q',self.base))
                    meta['allocation_bytes']=n
                elif msg==5:
                    require(set(fields)=={1},'bad error-query fields')
                    optional=tlv(0x10,b'\0')
                else:
                    require(set(fields)=={1,2,3,4},'bad iovec fields')
                    direction=scalar(fields,2,1);force=scalar(fields,4,1)
                    require(direction in (0,1) and force in (0,1),'bad direction/sync')
                    v=fields[3];require(bool(v) and len(v)==1+v[0]*12,'bad iovec count')
                    require(self.granted_size>0,'buffer not allocated')
                    plan=[];total=0
                    # Validate every descriptor before any data is touched.
                    for i in range(v[0]):
                        sector,address,count=struct.unpack_from('<III',v,1+i*12)
                        diskoff=sector*512;memoff=address-self.base;n=count*512
                        require(within(diskoff,n,IMAGE_SIZE),'outside private image')
                        require(within(memoff,n,self.granted_size),'outside granted buffer')
                        total+=n;require(total<=MAX_TRANSFER,'excessive transfer')
                        plan.append((diskoff,memoff,n))
                    for diskoff,memoff,n in plan:
                        if not n:continue
                        source,dest,so,do=(self.mem,fd,memoff,diskoff) if direction else (fd,self.mem,diskoff,memoff)
                        data=os.pread(source,n,so);require(len(data)==n,'short read; no zero-filled NV')
                        require(os.pwrite(dest,data,do)==n,'short write')
                    if direction:os.fdatasync(fd);self.write_bytes+=total
                    else:self.read_bytes+=total
                    meta.update(direction='write_copy' if direction else 'read_copy',bytes=total)
            else:raise ValueError('unsupported message')
        except (ValueError,KeyError,OSError) as exc:
            err=1;optional=b'';meta['error']=type(exc).__name__
            if isinstance(exc,ValueError):meta['reason']=str(exc) # fixed require() messages only
            elif isinstance(exc,OSError):meta['errno']=exc.errno
            # Never include unknown strings, NV payload, or DMA contents.
        self.requests+=1
        body=tlv(2,struct.pack('<HH',1 if err else 0,err))+optional
        return HEADER.pack(2,txn,msg,len(body))+body,meta

    def sync(self):
        for fd in self.images.values():os.fdatasync(fd)


class Address(C.Structure):
    _fields_=[('family',C.c_ushort),('node',C.c_uint32),('port',C.c_uint32)]


def inherited_fds(expected_major,expected_minor):
    require(os.environ.get('LISTEN_PID')==str(os.getpid()),'wrong fd activation PID')
    names=os.environ.get('LISTEN_FDNAMES','').split(':')
    require(os.environ.get('LISTEN_FDS')=='4' and len(set(names))==4,'need exactly four named FDs')
    fds=dict(zip(names,range(3,7)))
    require(set(fds)=={'rmtfs_mem',*PATHS.values()},'unexpected inherited descriptors')
    identities=set()
    for name,fd in fds.items():
        s=os.fstat(fd)
        require(fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_ACCMODE==os.O_RDWR,'need read-write working descriptor')
        if name=='rmtfs_mem':
            require(stat.S_ISCHR(s.st_mode) and expected_major>=234 and expected_minor==1 and s.st_rdev==os.makedev(expected_major,expected_minor),'not the validated client-1 RMTFS char device')
        else:
            require(stat.S_ISREG(s.st_mode) and s.st_size==IMAGE_SIZE and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_uid==0,'not a private working image; raw blocks/0400 masters forbidden')
            identity=(s.st_dev,s.st_ino);require(identity not in identities,'aliased image FDs');identities.add(identity)
    return fds


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--confirm-private-copy-only',action='store_true',required=True)
    p.add_argument('--memory-base',type=lambda x:int(x,0),required=True)
    p.add_argument('--memory-major',type=int,required=True)
    p.add_argument('--memory-minor',type=int,required=True)
    p.add_argument('--library',type=Path,required=True)
    p.add_argument('--library-sha256',required=True)
    p.add_argument('--duration',type=int,default=120)
    a=p.parse_args()
    require(os.geteuid()!=0 and os.uname().release=='6.18.58-picasso-lts-wifi2','require unprivileged wifi2 trial sandbox')
    require(0<a.duration<=180,'bounded run only')
    fds=inherited_fds(a.memory_major,a.memory_minor)
    backend=Backend(fds['rmtfs_mem'],{n:fds[n] for n in PATHS.values()},a.memory_base)
    require(hashlib.sha256(a.library.read_bytes()).hexdigest()==a.library_sha256,'QRTR library hash mismatch')
    qrtr=C.CDLL(str(a.library),use_errno=True)
    qrtr.qrtr_open.argtypes=[C.c_uint32];qrtr.qrtr_open.restype=C.c_int
    qrtr.qrtr_publish.argtypes=[C.c_int,C.c_uint32,C.c_uint32,C.c_uint32];qrtr.qrtr_publish.restype=C.c_int
    libc=C.CDLL(None,use_errno=True)
    libc.recvfrom.argtypes=[C.c_int,C.c_void_p,C.c_size_t,C.c_int,C.POINTER(Address),C.POINTER(C.c_uint)];libc.recvfrom.restype=C.c_ssize_t
    libc.sendto.argtypes=[C.c_int,C.c_void_p,C.c_size_t,C.c_int,C.POINTER(Address),C.c_uint];libc.sendto.restype=C.c_ssize_t
    stop=False
    def done(*_):
        nonlocal stop
        stop=True
    signal.signal(signal.SIGTERM,done);signal.signal(signal.SIGINT,done)
    fd=qrtr.qrtr_open(0)
    if fd<0:raise OSError(C.get_errno(),'qrtr_open')
    try:
        require(qrtr.qrtr_publish(fd,14,1,0)>=0,'QRTR publication failed')
        print(json.dumps({'status':'private_fd_proxy_ready','uid':os.geteuid(),'raw_block_devices':False}),flush=True)
        until=time.monotonic()+a.duration
        while not stop and time.monotonic()<until and backend.requests<100000:
            if not select.select([fd],[],[],0.5)[0]:continue
            buf=C.create_string_buffer(8192);addr=Address();length=C.c_uint(C.sizeof(addr))
            n=libc.recvfrom(fd,buf,len(buf),0,C.byref(addr),C.byref(length))
            if n<0:raise OSError(C.get_errno(),'recvfrom')
            if addr.family!=42 or addr.port==0xffff:continue
            try:reply,metadata=backend.handle(buf.raw[:n],addr.node)
            except ValueError:continue # malformed header/TLV, no state changes
            require(libc.sendto(fd,reply,len(reply),0,C.byref(addr),C.sizeof(addr))==len(reply),'send failed')
            if backend.requests<=30 or 'error' in metadata or backend.requests%500==0:
                print(json.dumps(metadata),flush=True)
    finally:
        os.close(fd);backend.sync()
        print(json.dumps({'status':'proxy_stopped','requests':backend.requests,'read_bytes':backend.read_bytes,'private_copy_write_bytes':backend.write_bytes,'raw_nv_writes':False}),flush=True)


if __name__=='__main__':main()
