#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One-device, explicitly authorized PRIVATE NV backup; source FDs are O_RDONLY.

Input: JSON with targets from the previously hashed original GPT. Emits metadata
only, never NV bytes. No mount, block write, format, discard, or modem startup.
"""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys
import time

NAMES={'modemst1','modemst2','fsg'}
DEST=Path('/var/lib/picasso-wifi-nv/original-20261027')


def require(ok,message):
    if not ok:raise RuntimeError(message)


def props(p):
    return dict(l.split('=',1) for l in (p/'uevent').read_text().splitlines() if '=' in l)


def hash_fd(fd,size):
    os.lseek(fd,0,os.SEEK_SET);h=hashlib.sha256();left=size
    while left:
        b=os.read(fd,min(left,1024**2));require(bool(b),'Short device read');h.update(b);left-=len(b)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--confirm-authorized-private-nv-copy',action='store_true',required=True)
    ap.parse_args()
    r=json.load(sys.stdin)
    require(os.geteuid()==0 and os.uname().machine=='aarch64','Require native phone root')
    require(os.uname().release=='6.18.58-picasso-lts','Require installed baseline kernel, DSP offline')
    require(Path('/proc/1/exe').resolve()==Path('/usr/lib/systemd/systemd'),'Require native systemd')
    require(hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest()=='78d5a451ed01af58807e1add0cc42506255b5fd03bd46e974a7db595b1813589','Unexpected kernel config')
    require(not list(Path('/sys/class/remoteproc').glob('*')),'Do not copy NV with a DSP registered')
    require(set(r['targets'])==NAMES,'Only the three authorized names are allowed')
    root=[x.split() for x in Path('/proc/mounts').read_text().splitlines() if x.split()[1]=='/']
    require(len(root)==1 and root[0][2]=='xfs','Require installed XFS root')
    rp=Path('/sys/class/block')/Path(root[0][0]).name
    require(props(rp).get('PARTUUID')=='32684d05-1c3b-836e-c936-7d4638bf1be9','Wrong root partition')
    require(os.stat('/var/lib').st_dev==os.stat('/').st_dev,'Destination must stay on userdata')
    mounted={l.split()[2] for l in Path('/proc/self/mountinfo').read_text().splitlines()}
    swap_devs=set()
    for l in Path('/proc/swaps').read_text().splitlines()[1:]:
        s=os.stat(l.split()[0]);swap_devs.add(s.st_rdev if stat.S_ISBLK(s.st_mode) else None)
    sources={}
    for label,expected in r['targets'].items():
        matches=[(p,props(p)) for p in Path('/sys/class/block').iterdir() if props(p).get('PARTNAME')==label]
        require(len(matches)==1,'Nonunique partition name: '+label)
        p,q=matches[0];size=int((p/'size').read_text())*512
        require(q.get('PARTUUID')==expected['partuuid'] and size==expected['bytes']==8388608,'GPT identity mismatch: '+label)
        require(not list((p/'holders').iterdir()),'Block holders exist: '+label)
        ident=q['MAJOR']+':'+q['MINOR'];devnum=os.makedev(int(q['MAJOR']),int(q['MINOR']))
        require(ident not in mounted and devnum not in swap_devs,'Mounted or swap target: '+label)
        node=Path('/dev')/p.name
        # Open all three read-only and exclusively before creating any backups.
        fd=os.open(node,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_EXCL)
        s=os.fstat(fd)
        require(stat.S_ISBLK(s.st_mode) and s.st_rdev==devnum,'Block node identity mismatch')
        raw=fcntl.ioctl(fd,0x80081272,bytes(8)) # BLKGETSIZE64, read-only ioctl
        require(struct.unpack('=Q',raw)[0]==size,'Block size ioctl mismatch')
        sources[label]=(fd,dict(partuuid=q['PARTUUID'],bytes=size,observed_node=str(node),device=ident))
    os.umask(0o077)
    require(not DEST.exists() and not DEST.is_symlink(),'Refuse overwriting originals')
    if not DEST.parent.exists():DEST.parent.mkdir(mode=0o700)
    require(not DEST.parent.is_symlink() and DEST.parent.stat().st_uid==0 and stat.S_IMODE(DEST.parent.stat().st_mode)==0o700,'Unsafe private parent')
    DEST.mkdir(mode=0o700)
    result={'status':'private_read_only_nv_backup','user_authorized_names':sorted(NAMES),'sources_opened_read_only':True,'raw_block_writes':False,'mounted_nv':False,'persist_or_fsc_access':False,'created_at_epoch':time.time(),'files':{}}
    try:
        for label,(fd,info) in sorted(sources.items()):
            target=DEST/(label+'.bin');out=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            h=hashlib.sha256();left=info['bytes']
            try:
                while left:
                    b=os.read(fd,min(left,1024**2));require(bool(b),'Short NV read');h.update(b);left-=len(b)
                    v=memoryview(b)
                    while v:
                        n=os.write(out,v);require(n>0,'Short backup write');v=v[n:]
                os.fsync(out);os.fchmod(out,0o400);os.fsync(out)
            finally:os.close(out)
            digest=h.hexdigest()
            require(hash_fd(fd,info['bytes'])==digest,'Source changed during copy: '+label)
            with target.open('rb') as f:require(hashlib.file_digest(f,'sha256').hexdigest()==digest,'Backup readback mismatch')
            result['files'][label+'.bin']={**info,'sha256':digest,'mode':'0400','source_second_read_matches':True,'backup_readback_matches':True}
        p=DEST/'manifest.json'
        with p.open('x') as f:json.dump(result,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        p.chmod(0o400)
        for d in (DEST,DEST.parent):
            fd=os.open(d,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
    finally:
        for fd,_ in sources.values():os.close(fd)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
