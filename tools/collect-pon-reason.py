#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One explicitly permitted PON sample, PID1-bounded with separate cleanup.
No shutdown/reboot/flash, register writes or retries. Does not prove causality.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import time

BASE=Path('/opt/picasso-power/pon-read1')
STATE=Path('/var/lib/picasso-power/pon-reason-read1-20261028')
MODULE='picasso_pon_reason_audit'
BOOT='2f080316-e4da-44f0-abc6-8d2319976308'
MODULE_SHA='416e1e03d65d8bb27bcc1ea322229a682f451018626bc1f9ee97bf31e5a9990e'
DECODER_SHA='b99e73fe67509098c50fc577f707f271244a0973ff4c8ec522d7281377d915e0'


def require(ok,message):
    if not ok:raise RuntimeError(message)


def record(name,value):
    data=(json.dumps(value,indent=2)+'\n').encode();fd=os.open(STATE/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        view=memoryview(data)
        while view:
            count=os.write(fd,view);require(count>0,'Short durable record');view=view[count:]
        os.fsync(fd)
    finally:os.close(fd)
    directory=os.open(STATE,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)


def temperatures():
    values={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
    require(values and all(-10000<=v<=150000 for v in values.values()),'Invalid temperature telemetry');return values


def owner_ok(value,boot):
    return value.get('boot_id')==boot==BOOT and value.get('module_sha256')==MODULE_SHA and value.get('initial_module_absent') is True


def cleanup():
    intent=STATE/'load-intent.json';present=Path('/sys/module',MODULE).exists();result={'module_present_before':present,'unload_requested':False}
    if present:
        require(intent.exists(),'No ownership intent; refuse to unload unrelated module')
        value=json.loads(intent.read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();require(owner_ok(value,boot),'Wrong owner/boot/module intent')
        p=subprocess.run(['/usr/bin/rmmod',MODULE],capture_output=True,text=True,timeout=5);result.update(unload_requested=True,returncode=p.returncode,stderr=p.stderr)
        require(p.returncode==0,'Read-only sampler unload failed')
    result['module_unloaded']=not Path('/sys/module',MODULE).exists();require(result['module_unloaded'],'Read-only sampler remains loaded')
    record('cleanup-'+str(time.monotonic_ns())+'.json',result);return result


def main():
    result={'status':'running','module_load_attempted':False,'PMIC_register_writes':False,'power_actions':False,'peak_sampled_temperature_mc':0};child=None
    def tick():
        values=temperatures();result['peak_sampled_temperature_mc']=max(result['peak_sampled_temperature_mc'],max(values.values()));require(max(values.values())<45000,'45C thermal abort');return values
    try:
        require(os.geteuid()==0,'Native root required');require(os.uname().release=='6.18.58-picasso-lts-wifi2','Matching kernel required')
        boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();require(boot==BOOT,'Same explicitly permitted current boot required')
        require(hashlib.sha256(Path('/sys/firmware/fdt').read_bytes()).hexdigest()=='62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388','Matching default FDT required')
        for name,pinned in [('picasso-pon-reason-audit.ko',MODULE_SHA),('power-pon-reasons.py',DECODER_SHA)]:require(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==pinned,'Changed sampler/decoder asset')
        require(not Path('/sys/module',MODULE).exists() and not Path('/sys/kernel/picasso_pon_reason_audit').exists(),'Sampler already present')
        require(not (STATE/'consumed').exists(),'One-shot consumed; inspect saved records, do not replay')
        result['start_temperatures_mc']=tick();require(max(result['start_temperatures_mc'].values())<40000,'Start below40C')
        record('consumed',{'boot_id':boot,'pid':os.getpid(),'scope':'authorized fixed readonly PON snapshot, no retry'})
        record('load-intent.json',{'boot_id':boot,'pid':os.getpid(),'module_sha256':MODULE_SHA,'initial_module_absent':True})
        result['module_load_attempted']=True
        child=subprocess.Popen(['/usr/bin/insmod',str(BASE/'picasso-pon-reason-audit.ko'),'confirm_readonly=1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        until=time.monotonic()+8
        while child.poll() is None:
            tick();require(time.monotonic()<until,'8s module-load deadline');time.sleep(.05)
        out,err=child.communicate();result.update(insmod_returncode=child.returncode,insmod_stdout=out,insmod_stderr=err);require(child.returncode==0,'Sampler load failed, no retry')
        tick();node=Path('/sys/kernel/picasso_pon_reason_audit/snapshot');info=node.lstat();require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o400,'Wrong root0400 snapshot')
        with node.open('rb') as f:raw=f.read(4097)
        require(len(raw)<=4096,'Oversized fixed snapshot');snapshot=json.loads(raw);record('snapshot.json',snapshot)
        require(0<=time.clock_gettime(time.CLOCK_BOOTTIME)-snapshot['capture_boottime_ns']/1e9<=3,'Snapshot capture is stale')
        spec=importlib.util.spec_from_file_location('pon_decoder',BASE/'power-pon-reasons.py');decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder);decoded=decoder.decode(snapshot);record('decoded.json',decoded)
        result.update(status='sampled_fixed_readonly_PON_snapshot',snapshot=snapshot,decoded=decoded)
    except Exception as exc:result.update(status='failed_one_shot_no_retry',error=type(exc).__name__+': '+str(exc))
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:result['load_process_did_not_terminate']=True
        try:result['cleanup']=cleanup()
        except Exception as exc:result.update(status='cleanup_review_required',cleanup_error=type(exc).__name__+': '+str(exc))
        try:result['end_temperatures_mc']=tick()
        except Exception as exc:result.update(status='thermal_review_required',thermal_error=type(exc).__name__+': '+str(exc))
        record('result.json',result)
    print(json.dumps(result),flush=True);return 0 if result['status']=='sampled_fixed_readonly_PON_snapshot' else 1


if __name__=='__main__':
    os.umask(0o077)
    import sys
    require(sys.argv[1:] in (['--confirmed-readonly'],['--cleanup']),'Explicit sampler or cleanup mode required')
    STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
    if sys.argv[1]=='--cleanup':cleanup()
    else:raise SystemExit(main())
