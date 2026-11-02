#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bounded per-boot retries around the unchanged guarded Wi-Fi worker.
No RF/NV operations here. New PID1 worker units preserve every prior failure.
"""
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid

STATE=Path('/var/lib/picasso-wifi-reconnect')
RUN=Path('/run/picasso-wifi-reconnect')
WIFI=Path('/var/lib/picasso-wifi')
WRUN=Path('/run/picasso-wifi')
OPT=Path('/opt/picasso-wifi')
WORK=Path('/var/lib/picasso-wifi-nv/work-wifi2')
SELF_UNIT='picasso-wifi-reconnect.service'
WORKER=OPT/'wifi-auto-service.py'
WORKER_SHA='a5000fef3c7f4641e917dbb206a4993861ccd46eb56b649c7e748630a5b99c96'
CONFIG_SHA='8ea11949855a7fbefb54e7eceb0cf75e2efbba50fda6d3d13699a79ebc8eda5a'
FDTS=('62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388','ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c')
DELAYS=(10,30,60)
MAX_ATTEMPTS=4
RETRY_ERRORS=frozenset(('RuntimeError: Fallback link lost; no restart loop','RuntimeError: Both authorized SSIDs failed bounded activation','RuntimeError: Runtime fallback failed'))
CHILD=re.compile(r'picasso-wifi-session-[0-9a-f]{8}-[0-9a-f]{12}\.service\Z')
STOP=False


def require(ok,message):
    if not ok:raise RuntimeError(message)


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def read_json(path):return json.loads(Path(path).read_text())


def durable(path,value,exclusive=False):
    path=Path(path);data=(json.dumps(value,indent=2)+'\n').encode();tmp=path if exclusive else path.with_name(path.name+'.'+uuid.uuid4().hex+'.new')
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        view=memoryview(data)
        while view:
            n=os.write(fd,view);require(n>0,'Short durable record');view=view[n:]
        os.fsync(fd)
    finally:os.close(fd)
    if not exclusive:tmp.replace(path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def notify(text):
    address=os.environ.get('NOTIFY_SOCKET')
    if address:
        if address.startswith('@'):address='\0'+address[1:]
        with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as s:s.sendto(text.encode(),address)


def temperatures():
    values={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
    require(values and all(-10000<=v<=150000 for v in values.values()),'Invalid thermal telemetry')
    require(max(values.values())<45000,'45C thermal abort, no retry');return values


def retry_allowed(unit,record,cleanup):
    # Exact error allowlist, not a generic nonzero exit/restart policy.
    return (unit.get('Result')=='exit-code' and unit.get('ExecMainStatus')=='1'
        and record.get('status')=='failed' and record.get('error') in RETRY_ERRORS
        and record.get('cleanup_status')=='safe_cleanup_complete'
        and not record.get('unsafe_nv_stop') and record.get('nv_armed') is True
        and type(record.get('peak_temperature_mc')) is int and 0<=record['peak_temperature_mc']<45000
        and cleanup.get('status')=='safe_cleanup_complete'
        and all(cleanup.get(k) is True for k in ('children_stopped','wlan_absent','original_core_restored','cpu_limits_restored','private_copy_checkpoint_committed'))
        and cleanup.get('dsp')=='offline' and cleanup.get('shared_ram_cleared_bytes')==2621440)


def retry_delay(attempts_used):
    require(type(attempts_used) is int and 0<=attempts_used<MAX_ATTEMPTS,'Per-boot attempt budget exhausted')
    return 0 if attempts_used==0 else DELAYS[attempts_used-1]


def worker_body():
    return f'''[Unit]
Description=One guarded Picasso Wi-Fi session (bounded supervisor)
BindsTo={SELF_UNIT}
After={SELF_UNIT} NetworkManager.service firewalld.service
Wants=NetworkManager.service firewalld.service
[Service]
Type=notify
NotifyAccess=main
ExecStart=/usr/bin/python3 -I {WORKER}
ExecStopPost=/usr/bin/python3 -I {WORKER} --cleanup
Restart=no
WatchdogSec=8s
TimeoutStartSec=180s
TimeoutStopSec=45s
KillMode=control-group
CPUAffinity=0 1 2 3
MemoryMax=256M
UMask=0077
RuntimeDirectory=picasso-wifi
RuntimeDirectoryMode=0700
RuntimeDirectoryPreserve=yes
'''


def simple_run(args,timeout=8):return subprocess.run(args,capture_output=True,text=True,timeout=timeout)


def props(name,runner=simple_run):
    require(name==SELF_UNIT or bool(CHILD.fullmatch(name)) or name in ('picasso-wifi.service','picasso-wifi-auto.service') or bool(re.fullmatch(r'picasso-(?:rmtfs|tftp)-auto-[0-9a-f]{12}\.service',name)),'Unexpected unit name')
    p=runner(['systemctl','show',name,'-p','LoadState','-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus','-p','MainPID','-p','InvocationID'])
    require(p.returncode==0,'Cannot query unit '+name)
    return dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)


def clean_ready(runner=simple_run):
    require(not (WIFI/'dirty.json').exists(),'Unclean working-copy lifecycle; never delete dirty marker')
    require(not list(Path('/sys/class/net').glob('wlan*')),'Existing WLAN refused')
    procs=list(Path('/sys/class/remoteproc').glob('*'));require(len(procs)<=1,'Unexpected remoteproc topology')
    for proc in procs:
        require((proc/'firmware').read_text().strip()=='qcom/sm7250/picasso/modem.mdt' and (proc/'state').read_text().strip()=='offline','DSP not safely offline')
    for cpu,expected in ((6,2208000),(7,2400000)):
        require(int(Path(f'/sys/devices/system/cpu/cpufreq/policy{cpu}/scaling_max_freq').read_text())==expected,'CPU limits not restored')
    for old in ('picasso-wifi.service','picasso-wifi-auto.service'):
        require(props(old,runner).get('ActiveState') in ('inactive','failed'),'Legacy controller active')
    if (WRUN/'session.json').exists():
        previous=read_json(WRUN/'session.json')
        for child in previous.get('children',[]):require(props(child,runner).get('ActiveState') in ('inactive','failed'),'Previous proxy/TFTP not stopped')
    checkpoint=read_json(WIFI/'work-checkpoint.json');require(set(checkpoint)=={'modem_fs1','modem_fs2','modem_fsg'},'Unexpected checkpoint files')
    identities=set()
    for name,expected in checkpoint.items():
        p=WORK/name;s=p.lstat();require(stat.S_ISREG(s.st_mode) and not s.st_uid and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size==8388608,'Unsafe ordinary work file')
        require((s.st_dev,s.st_ino) not in identities,'Aliased work copies');identities.add((s.st_dev,s.st_ino))
        require(digest(p)==expected,'Work checkpoint mismatch; no reset to original NV')
    cfg=read_json(OPT/'config-auto.json');require(digest(cfg['installed_core_path'])==cfg['installed_core_sha256'],'Original core changed')
    require(not Path('/sys/module/ath10k_core/parameters/picasso_ht20_only').exists(),'Diagnostic core not restored')


def fixed_assets():
    require(os.geteuid()==0 and os.uname().release=='6.18.58-picasso-lts-wifi2','Matching native root required')
    require(Path('/etc/picasso-fedora-root').read_text().strip()=='PICASSO_FEDORA44_DISKROOT_V2','Native install marker changed')
    require(Path('/etc/picasso-install-partuuid').read_text().strip()=='32684d05-1c3b-836e-c936-7d4638bf1be9','Root identity changed')
    require(hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest()=='f60bc2723f34cd08da927b4a3a79673bddc7bcd9052114cdd055cf958106dfbc','Config changed')
    require(digest('/sys/firmware/fdt') in FDTS,'Unapproved live FDT')
    require(digest(WORKER)==WORKER_SHA and digest(OPT/'config-auto.json')==CONFIG_SHA,'Worker/config changed')


def budget_path():
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();require(str(uuid.UUID(boot))==boot,'Invalid boot ID');return boot,STATE/'boots'/(boot+'.json')


def cleanup_owned():
    """Independent ExecStopPost: only stop a child recorded before its creation."""
    boot,path=budget_path()
    if not path.exists():return {'status':'nothing_owned'}
    budget=read_json(path);name=budget.get('current_unit')
    if not name:return {'status':'no_active_owned_unit'}
    require(budget['boot_id']==boot and CHILD.fullmatch(name) and any(x['unit']==name for x in budget['attempts']),'Unproven child ownership')
    entry=next(x for x in budget['attempts'] if x['unit']==name)
    if not entry.get('definition_identity'):
        clean_ready();return {'status':'planned_child_not_created_no_stop','unit':name}
    p=Path('/run/systemd/system')/name;identity=p.lstat()
    require(stat.S_ISREG(identity.st_mode) and identity.st_uid==0 and identity.st_nlink==1 and [identity.st_dev,identity.st_ino]==entry['definition_identity'] and p.read_text()==worker_body(),'Child definition/identity changed; do not stop unknown unit')
    unit=props(name)
    if unit.get('ActiveState') not in ('inactive','failed'):
        p=simple_run(['systemctl','stop','--no-block',name]);require(p.returncode==0,'Owned child stop request failed');until=time.monotonic()+60
        while time.monotonic()<until:
            unit=props(name)
            if unit.get('ActiveState') in ('inactive','failed'):break
            time.sleep(.2)
        else:raise RuntimeError('Owned child did not stop in60s')
    clean_ready();return {'status':'owned_child_stopped_and_lifecycle_clean','unit':name,'unit_result':unit.get('Result')}


class Supervisor:
    def __init__(self):
        self.peak=0;self.stopping=False;self.boot,self.path=budget_path();self.owner=uuid.uuid4().hex
        for path in (STATE/'boots',STATE/'events',RUN):path.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.lock=os.open(RUN/'owner.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600);fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if self.path.exists():
            self.budget=read_json(self.path);require(self.budget['schema']==1 and self.budget['boot_id']==self.boot and self.budget['phase']=='operator_stopped_clean','Existing per-boot state requires inspection, not replay')
            require(len(self.budget['attempts'])<MAX_ATTEMPTS,'Per-boot budget exhausted')
        else:self.budget={'schema':1,'boot_id':self.boot,'attempts':[],'phase':'created','current_unit':None,'retry_delays_seconds':list(DELAYS),'max_attempts':MAX_ATTEMPTS}
        self.budget['owner']=self.owner

    def tick(self):
        values=temperatures();self.peak=max(self.peak,max(values.values()));notify('WATCHDOG=1')
        if STOP:raise InterruptedError('Operator requested supervisor stop')
        return values

    def run(self,args,timeout=10):
        self.tick();p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);until=time.monotonic()+timeout
        try:
            while True:
                try:out,err=p.communicate(timeout=.2);break
                except subprocess.TimeoutExpired:self.tick();require(time.monotonic()<until,'Command deadline: '+args[0])
        except BaseException:
            p.terminate()
            try:p.communicate(timeout=1)
            except subprocess.TimeoutExpired:p.kill();p.communicate()
            raise
        self.tick();return subprocess.CompletedProcess(args,p.returncode,out,err)

    def save(self,phase,**fields):
        self.budget.update(phase=phase,supervisor_peak_temperature_mc=self.peak,**fields)
        durable(STATE/'events'/(self.boot+'-'+str(time.monotonic_ns())+'-'+phase+'.json'),self.budget,True)
        durable(self.path,self.budget);durable(RUN/'session.json',self.budget)
        notify('STATUS='+phase+'; attempts '+str(len(self.budget['attempts']))+'/4')

    def pause(self,seconds):
        until=time.monotonic()+seconds
        while time.monotonic()<until:self.tick();time.sleep(min(.2,max(0,until-time.monotonic())))

    def cold_start_gate(self):
        until=time.monotonic()+120;stable=0
        while time.monotonic()<until:
            values=self.tick();stable=stable+1 if max(values.values())<40000 else 0
            if stable>=3:return
            self.pause(.5)
        raise RuntimeError('120s cooldown refusal; no RF retry')

    def attempt(self):
        index=len(self.budget['attempts']);delay=retry_delay(index);self.save('backoff',backoff_seconds=delay);self.pause(delay)
        fixed_assets();clean_ready(self.run);self.cold_start_gate()
        require(max(self.tick().values())<40000,'Start strictly below40C')
        previous=read_json(WRUN/'session.json').get('session') if (WRUN/'session.json').exists() else None
        name='picasso-wifi-session-'+self.boot[:8]+'-'+uuid.uuid4().hex[:12]+'.service'
        self.budget['attempts'].append({'unit':name,'index':index+1,'prior_worker_session':previous,'intent_monotonic':time.monotonic()});self.save('intent_before_worker_create',current_unit=name)
        definition=worker_body();durable(STATE/'events'/(name+'.definition.json'),{'unit':name,'owner':self.owner,'body':definition},True)
        target=Path('/run/systemd/system')/name;fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:require(os.write(fd,definition.encode())==len(definition.encode()),'Short unit definition');os.fsync(fd)
        finally:os.close(fd)
        created=target.lstat();self.budget['attempts'][-1]['definition_identity']=[created.st_dev,created.st_ino];self.save('definition_written_before_start')
        for args in (['systemd-analyze','verify',str(target)],['systemctl','daemon-reload'],['systemctl','start','--no-block',name]):
            p=self.run(args);require(p.returncode==0,'Cannot create/start known worker: '+p.stderr.strip())
        self.save('connecting');seen=False;ready=False;deadline=time.monotonic()+240
        while True:
            self.tick();unit=props(name,self.run);record=read_json(WRUN/'session.json') if (WRUN/'session.json').exists() else {}
            new=record.get('boot_id')==self.boot and record.get('session') not in (None,previous)
            seen=seen or unit.get('ActiveState') in ('activating','active','deactivating') or new
            if unit.get('ActiveState')=='active' and new and record.get('status')=='connected_guarded':
                if not ready:
                    ready=True;self.budget['attempts'][-1].update(worker_session=record['session'],ssid=record.get('ssid'));self.save('online')
                notify('STATUS=online '+str(record.get('ssid'))+'; attempts '+str(index+1)+'/4')
            elif seen and unit.get('ActiveState') in ('inactive','failed'):
                require(new,'Worker exited without fresh native session evidence')
                cleanup=read_json(WRUN/'cleanup.json');summary={k:record.get(k) for k in ('session','status','error','cleanup_status','peak_temperature_mc','ssid','history')}
                self.budget['attempts'][-1].update(terminal_unit=unit,terminal_record=summary,retryable=retry_allowed(unit,record,cleanup));self.save('worker_terminal')
                clean_ready(self.run)
                if record.get('status')=='operator_stop':return 'operator_stop'
                return 'retryable' if retry_allowed(unit,record,cleanup) else 'safety_or_unknown_failure'
            require(ready or time.monotonic()<deadline,'Worker startup/cleanup240s deadline')
            self.pause(.5)

    def execute(self):
        failure=None;operator=False
        try:
            fixed_assets();self.tick();clean_ready(self.run);self.save('supervision_ready')
            # Supervisor readiness is NOT a claim of a connected WLAN.
            notify('READY=1\nSTATUS=Guarded reconnect supervisor ready; WLAN not yet connected')
            while len(self.budget['attempts'])<MAX_ATTEMPTS:
                outcome=self.attempt()
                if outcome=='operator_stop':operator=True;break
                require(outcome=='retryable','Safety/unknown worker failure: no automatic retry')
                if len(self.budget['attempts'])==MAX_ATTEMPTS:raise RuntimeError('Initial plus3 retries exhausted for this boot')
        except InterruptedError:operator=True
        except Exception as exc:failure=type(exc).__name__+': '+str(exc)
        finally:
            notify('STOPPING=1\nSTATUS=Stopping only owned guarded worker')
            try:cleanup=cleanup_owned()
            except Exception as exc:cleanup={'status':'cleanup_requires_attention','error':type(exc).__name__+': '+str(exc)};failure=failure or cleanup['error']
            self.save('operator_stopped_clean' if operator and not failure else 'halted_safety_or_budget',error=failure,final_cleanup=cleanup)
            os.close(self.lock)
        return 1 if failure else 0


if __name__=='__main__':
    os.umask(0o077)
    def stop(*args):
        global STOP
        STOP=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    if sys.argv[1:]==['--cleanup']:
        result=cleanup_owned();print(json.dumps(result));raise SystemExit(0)
    if sys.argv[1:]==['--check-files']:
        fixed_assets();require(max(temperatures().values())<40000,'Check below40C');clean_ready()
        p=simple_run(['systemctl','daemon-reload']);require(p.returncode==0,'Read-only-RF sandbox manager access failed')
        print(json.dumps({'status':'files_clean_state_manager_bus_check_passed_no_RF_or_budget_consumption'}));raise SystemExit(0)
    require(sys.argv[1:]==['--run-installed'],'Explicit --run-installed, --check-files or --cleanup required')
    raise SystemExit(Supervisor().execute())
