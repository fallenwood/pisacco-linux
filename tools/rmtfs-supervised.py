#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Opt-in supervised lifetime, using unchanged validated four-FD RMTFS engine.

No new file/device access. An abstract AF_UNIX datagram socket accepts LIVE only
from the exact root controller PID, authenticated by kernel SCM_CREDENTIALS.
Missing lease >3s exits and syncs copies. Old attended proxy remains unchanged.
"""
import argparse
import ctypes as C
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import socket
import struct
import time


class RootLease:
    def __init__(self,name,pid,timeout=3.0):
        if not name or len(name)>80 or pid<=1 or not 0<timeout<=3:
            raise ValueError('Unsafe lease parameters')
        self.pid=pid;self.timeout=timeout;self.last=time.monotonic()
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_PASSCRED,1)
        self.sock.bind('\0'+name);self.sock.setblocking(False)

    def poll(self):
        # Bounded drain; an untrusted datagram flood cannot extend the lease.
        for _ in range(32):
            try:data,anc,flags,_=self.sock.recvmsg(16,socket.CMSG_SPACE(12))
            except BlockingIOError:break
            if flags&(socket.MSG_TRUNC|socket.MSG_CTRUNC):continue
            for level,kind,value in anc:
                if level==socket.SOL_SOCKET and kind==socket.SCM_CREDENTIALS and len(value)==12:
                    pid,uid,gid=struct.unpack('3i',value)
                    if data==b'LIVE' and uid==0 and pid==self.pid:self.last=time.monotonic()
        if time.monotonic()-self.last>self.timeout:raise TimeoutError('Root controller lease expired')

    def close(self):self.sock.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--controller-pid',required=True,type=int)
    p.add_argument('--lease-name',required=True)
    p.add_argument('--memory-base',required=True,type=lambda x:int(x,0))
    p.add_argument('--memory-major',required=True,type=int)
    p.add_argument('--memory-minor',required=True,type=int)
    p.add_argument('--engine-sha256',required=True)
    p.add_argument('--library-sha256',required=True)
    a=p.parse_args()
    if os.geteuid()==0 or os.uname().release!='6.18.58-picasso-lts-wifi2':raise ValueError('Require confined unprivileged native wifi2')
    src=Path('/proxy/rmtfs-private-proxy.py')
    if hashlib.sha256(src.read_bytes()).hexdigest()!=a.engine_sha256:raise ValueError('RMTFS engine changed')
    spec=importlib.util.spec_from_file_location('rmtfs_engine',src);engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
    fds=engine.inherited_fds(a.memory_major,a.memory_minor)
    backend=engine.Backend(fds['rmtfs_mem'],{n:fds[n] for n in engine.PATHS.values()},a.memory_base)
    lib=Path('/proxy/libqrtr.so.1')
    if hashlib.sha256(lib.read_bytes()).hexdigest()!=a.library_sha256:raise ValueError('QRTR library changed')
    lease=RootLease(a.lease_name,a.controller_pid)
    qrtr=C.CDLL(str(lib),use_errno=True);qrtr.qrtr_open.argtypes=[C.c_uint32];qrtr.qrtr_open.restype=C.c_int
    qrtr.qrtr_publish.argtypes=[C.c_int,C.c_uint32,C.c_uint32,C.c_uint32];qrtr.qrtr_publish.restype=C.c_int
    libc=C.CDLL(None,use_errno=True)
    libc.recvfrom.argtypes=[C.c_int,C.c_void_p,C.c_size_t,C.c_int,C.POINTER(engine.Address),C.POINTER(C.c_uint)];libc.recvfrom.restype=C.c_ssize_t
    libc.sendto.argtypes=[C.c_int,C.c_void_p,C.c_size_t,C.c_int,C.POINTER(engine.Address),C.c_uint];libc.sendto.restype=C.c_ssize_t
    stopped=False
    def stop(*_):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    fd=qrtr.qrtr_open(0)
    if fd<0:raise OSError('qrtr_open failed')
    try:
        engine.require(qrtr.qrtr_publish(fd,14,1,0)>=0,'QRTR publication failed')
        print(json.dumps({'status':'supervised_private_fd_proxy_ready','preopened_fds':4,'lease_seconds':3,'raw_nv_writes':False}),flush=True)
        while not stopped:
            lease.poll()
            if not select.select([fd],[],[],0.1)[0]:continue
            buf=C.create_string_buffer(8192);addr=engine.Address();size=C.c_uint(C.sizeof(addr))
            n=libc.recvfrom(fd,buf,len(buf),0,C.byref(addr),C.byref(size))
            if n<0:raise OSError('QRTR receive failed')
            if addr.family!=42 or addr.port==0xffff:continue
            try:reply,metadata=backend.handle(buf.raw[:n],addr.node)
            except ValueError:continue
            engine.require(libc.sendto(fd,reply,len(reply),0,C.byref(addr),C.sizeof(addr))==len(reply),'QRTR send failed')
            if 'error' in metadata:print(json.dumps(metadata),flush=True)
    finally:
        os.close(fd);lease.close();backend.sync()
        print(json.dumps({'status':'supervised_proxy_stopped','requests':backend.requests,'raw_nv_writes':False}),flush=True)


if __name__=='__main__':main()
