#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Guarded persistent Wi-Fi; private credentials are NEVER read by this code.

Manual MPSS start, no DSP recovery/restart, exact ordered SSIDs, live SG/MAC/
HT20/thermal checks. Parent watchdog + kernel-authenticated three-second proxy
lease + independent ExecStopPost. Default lifetime may be unbounded only after
native probation; -- cleanup always leaves consented persistent secrets intact.
"""
import argparse
import gzip
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import re
import select
import signal
import socket
import stat
import struct
import subprocess
import sys
import threading
import time
import uuid

OPT=Path('/opt/picasso-wifi')
STATE=Path('/var/lib/picasso-wifi')
RUN=Path('/run/picasso-wifi')
WORK=Path('/var/lib/picasso-wifi-nv/work-wifi2')
CREDENTIALS=STATE/'credentials'
NAMES=('Chaldea','Chaldea-2.4G')
FIRMWARE='qcom/sm7250/picasso/modem.mdt'


def require(ok,message):
    if not ok:raise RuntimeError(message)


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def load(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),OPT/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def atomic(path,value):
    path=Path(path);temp=path.with_name(path.name+'.new')
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        data=(json.dumps(value,indent=2)+'\n').encode();view=memoryview(data)
        while view:
            n=os.write(fd,view);require(n>0,'Short state write');view=view[n:]
        os.fsync(fd)
    finally:os.close(fd)
    os.replace(temp,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def temperatures():
    out={p.parent.name:int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
    require(bool(out),'No thermal telemetry')
    return out


def work_hashes():
    out={};ids=set()
    for name in ('modem_fs1','modem_fs2','modem_fsg'):
        p=WORK/name;s=p.lstat()
        require(stat.S_ISREG(s.st_mode) and not s.st_uid and s.st_nlink==1 and s.st_size==8388608 and stat.S_IMODE(s.st_mode)==0o600,'Unsafe ordinary NV working copy')
        require((s.st_dev,s.st_ino) not in ids,'Aliased private copies');ids.add((s.st_dev,s.st_ino));out[name]=digest(p)
    return out


def notify(text):
    addr=os.environ.get('NOTIFY_SOCKET')
    if addr:
        if addr.startswith('@'):addr='\0'+addr[1:]
        with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as sock:sock.sendto(text.encode(),addr)


def validate_memory(tree,mem):
    """Pure range validation: exact live FDT plus freshly discovered sysfs data."""
    base,size=mem['physical_address'],mem['usable_bytes'];start=base-4096;end=base+size+4096
    require(size==0x280000 and base%4096==0 and 0x80000000<=start<end<=0x100000000,'Bad dynamic RAM span')
    banks=[]
    for name,props in tree.items():
        if props.get('device_type')==b'memory\0':banks.extend(struct.iter_unpack('>QQ',props['reg']))
    require(any(s<=start and end<=s+n for s,n in banks),'RMTFS allocation outside one Linux memory bank')
    for region in load('fdt').fixed_regions(tree):
        require(end<=region['start'] or start>=region['start']+region['size'],'RMTFS overlaps fixed carveout')
    require(mem['major']>=234 and mem['minor']==1,'Unexpected RMTFS character identity')


def cleanup():
    """Independent, repeatable; errors are evidence, not silently reset."""
    if not (RUN/'session.json').exists():return {'status':'nothing_armed'}
    r=json.loads((RUN/'session.json').read_text());out={'actions':[],'persistent_credentials_retained_by_consent':True}
    def run(args,timeout=10):
        try:
            p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
            out['actions'].append({'program':args[0],'returncode':p.returncode});return p
        except Exception as exc:out['actions'].append({'program':args[0],'error':type(exc).__name__});return None
    if r.get('radio_armed'):
        for name in NAMES:run(['nmcli','--wait','3','connection','down','picasso-auto-'+name],5)
        run(['nmcli','device','set','wlan0','managed','no'])
        run(['modprobe','-r','ath10k_snoc'],15)
    safe=True;crashed=False
    if r.get('proc'):
        try:
            proc=Path(r['proc']);require(proc.parent==Path('/sys/class/remoteproc'),'Unexpected remoteproc path')
            require((proc/'firmware').read_text().strip()==FIRMWARE,'Remoteproc firmware changed')
            old=(proc/'state').read_text().strip();crashed=old=='crashed'
            if old in ('running','crashed'):(proc/'state').write_text('stop')
            require((proc/'state').read_text().strip()=='offline','DSP did not stop');out['dsp']='offline'
        except Exception as exc:safe=False;out['dsp_error']=type(exc).__name__
    else:out['dsp']='not_started'
    children_stopped=True
    for name in r.get('children',[]):
        if not re.fullmatch(r'picasso-(?:rmtfs|tftp)-auto-[0-9a-f]{12}\.service',name):safe=False;continue
        p=run(['systemctl','stop',name],10)
        if p is None or p.returncode:children_stopped=False
    out['children_stopped']=children_stopped
    if safe and r.get('memory'):
        try:
            m=r['memory'];p=Path('/sys/class/rmtfs/qcom_rmtfs_mem1')
            require(int((p/'phys_addr').read_text(),16)==m['physical_address'] and int((p/'size').read_text(),16)==m['usable_bytes']==0x280000,'Memory identity changed')
            node=Path('/dev/qcom_rmtfs_mem1');s=node.lstat()
            require(stat.S_ISCHR(s.st_mode) and s.st_rdev==os.makedev(m['major'],m['minor']),'Memory device changed')
            fd=os.open(node,os.O_RDWR|os.O_NOFOLLOW)
            try:
                for off in range(0,0x280000,512*1024):
                    block=bytes(min(512*1024,0x280000-off));require(os.pwrite(fd,block,off)==len(block) and os.pread(fd,len(block),off)==block,'RAM clear/readback failed')
            finally:os.close(fd)
            out['shared_ram_cleared_bytes']=0x280000
        except Exception as exc:safe=False;out['memory_error']=type(exc).__name__
    wlan=run(['iw','dev']);out['wlan_absent']=wlan is not None and not wlan.stdout.strip()
    if safe and out['wlan_absent'] and r.get('core_armed'):
        a=run(['modprobe','-r','ath10k_core']);b=run(['modprobe','ath10k_core','debug_mask=0x200000'])
        cfg=json.loads((OPT/'config.json').read_text())
        out['original_core_restored']=a is not None and b is not None and not a.returncode and not b.returncode and not Path('/sys/module/ath10k_core/parameters/picasso_ht20_only').exists() and digest(cfg['installed_core_path'])==cfg['installed_core_sha256']
        safe=safe and out['original_core_restored']
    try:
        for cpu,value in r.get('cpu_before',{}).items():
            require((cpu,value) in (('6',2208000),('7',2400000)),'Unexpected saved CPU policy')
            p=Path('/sys/devices/system/cpu/cpufreq/policy'+cpu)/'scaling_max_freq';p.write_text(str(value))
            for _ in range(40):
                if int(p.read_text())==value:break
                time.sleep(0.05)
            require(int(p.read_text())==value,'CPU restoration did not settle')
        out['cpu_limits_restored']=True
    except Exception as exc:safe=False;out['cpu_error']=type(exc).__name__
    if r.get('nv_armed') and safe and children_stopped and not crashed and not r.get('unsafe_nv_stop') and out['wlan_absent']:
        try:
            hashes=work_hashes();atomic(STATE/'work-checkpoint.json',hashes)
            dirty=STATE/'dirty.json'
            if dirty.exists():
                require(json.loads(dirty.read_text())['session']==r['session'],'Dirty marker belongs to another run');dirty.unlink()
                fd=os.open(STATE,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(fd)
                finally:os.close(fd)
            out['private_copy_checkpoint_committed']=True
        except Exception as exc:safe=False;out['checkpoint_error']=type(exc).__name__
    elif r.get('nv_armed'):safe=False;out['checkpoint_not_committed_unclean_stop']=True
    out['status']='safe_cleanup_complete' if safe and children_stopped and out['wlan_absent'] else 'cleanup_requires_attention'
    out['temperatures']=temperatures();atomic(RUN/'cleanup.json',out)
    if r.get('history'):atomic(Path(r['history'])/'cleanup.json',out)
    return out


class Service:
    def __init__(self):
        self.cfg=json.loads((OPT/'config.json').read_text());self.rules=load('wifi-fallback-policy');self.reg=load('audit-wifi-regulatory')
        self.proc=None;self.mac=None;self.helper=None;self.live=False;self.stopping=False;self.failure=None;self.last_progress=time.monotonic()
        self.deadline=time.monotonic()+150;self.stop_event=threading.Event();self.health_thread=None
        session=uuid.uuid4().hex[:12];history=STATE/'history'/session;history.mkdir(mode=0o700,parents=True)
        self.record={'session':session,'history':str(history),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'status':'starting','attempts':[],'peak_temperature_mc':0,'credential_contents_read':False,'cpu_before':{},'children':[]}
        self.save()
        self.lease='picasso-rmtfs-'+session

    def save(self):atomic(RUN/'session.json',self.record)

    def guard(self):
        with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as lease:
            while not self.stop_event.wait(0.2):
                try:
                    t=temperatures();self.record['peak_temperature_mc']=max(self.record['peak_temperature_mc'],max(t.values()))
                    require(max(t.values())<45000,'45C thermal abort')
                    require(time.monotonic()-self.last_progress<4,'Controller progress lease expired')
                    if self.live:
                        if (self.proc/'state').read_text().strip()!='running':
                            self.record['unsafe_nv_stop']=True
                            raise RuntimeError('DSP stopped or crashed')
                    try:lease.sendto(b'LIVE','\0'+self.lease)
                    except (FileNotFoundError,ConnectionRefusedError):pass
                    notify('WATCHDOG=1')
                except Exception as exc:self.failure=type(exc).__name__+': '+str(exc);return

    def tick(self):
        self.last_progress=time.monotonic()
        if self.failure:raise RuntimeError(self.failure)
        if self.stopping:raise InterruptedError('Operator requested stop')
        require(time.monotonic()<self.deadline,'Startup/activation budget expired')

    def pause(self,seconds):
        until=time.monotonic()+seconds
        while time.monotonic()<until:self.tick();time.sleep(min(0.1,max(0,until-time.monotonic())))

    def run(self,args,timeout=10,check=True):
        self.tick();p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);until=time.monotonic()+timeout
        try:
            while True:
                try:out,err=p.communicate(timeout=0.2);break
                except subprocess.TimeoutExpired:
                    self.tick();require(time.monotonic()<until,'Command deadline: '+args[0])
        except BaseException:
            p.terminate()
            try:p.communicate(timeout=1)
            except subprocess.TimeoutExpired:p.kill();p.communicate()
            raise
        self.tick()
        if check:require(p.returncode==0,'Command failed: '+args[0]+' code '+str(p.returncode))
        return p.returncode,out

    def text(self,args,**kwargs):return self.run(args,**kwargs)[1]

    def identity(self):
        iface=Path('/sys/class/net/wlan0')
        require((iface/'address').read_text().strip()==(iface/'phy80211/macaddress').read_text().strip()==self.mac,'Current/permanent MAC differs from device DMS')

    def audit(self,reapply=False):
        if reapply:self.text(['iw','reg','set','SG']);self.pause(0.3)
        phy=(Path('/sys/class/net/wlan0/phy80211')).resolve().name
        data=self.text(['iw','phy',phy,'info']);require('HT20/HT40' not in data and 'VHT Capabilities' not in data,'Unaudited wide PHY')
        return self.reg.audit(self.cfg['sg_reference'],self.text(['iw','reg','get']),data)

    def startup(self):
        require(os.geteuid()==0 and os.uname().release=='6.18.58-picasso-lts-wifi2','Wrong native kernel')
        require(Path('/proc/1/exe').resolve()==Path('/usr/lib/systemd/systemd'),'Not native systemd')
        require(Path('/etc/picasso-fedora-root').read_text().strip()=='PICASSO_FEDORA44_DISKROOT_V2','Wrong disk root')
        require(Path('/etc/picasso-install-partuuid').read_text().strip()=='32684d05-1c3b-836e-c936-7d4638bf1be9','Wrong root PARTUUID')
        require(hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest()==self.cfg['config_sha256'],'Kernel config changed')
        fdt=Path('/sys/firmware/fdt').read_bytes();require(hashlib.sha256(fdt).hexdigest()==self.cfg['fdt_sha256'],'Live FDT changed')
        require(not (STATE/'dirty.json').exists(),'Unclean NV lifecycle; operator review required')
        require(work_hashes()==json.loads((STATE/'work-checkpoint.json').read_text()),'Private work checkpoint changed')
        require(not self.text(['iw','dev']).strip(),'Existing WLAN refused')
        require(not list(Path('/sys/class/remoteproc').glob('*')) or all(p.read_text().strip()=='offline' for p in Path('/sys/class/remoteproc').glob('*/state')),'Active DSP refused')
        for name in NAMES:self.rules.private_file(CREDENTIALS/(name+'.passwd'),65,255)
        consent=json.loads(self.rules.private_file(CREDENTIALS/'consent.json').read_text())
        require(consent['targets']==list(NAMES) and '1094400' in consent['scope'],'Missing explicit persistent/CPU-cap consent')
        for path,sha in self.cfg['file_sha256'].items():require(digest(path)==sha,'Installed asset hash changed')
        require(digest(self.cfg['installed_core_path'])==self.cfg['installed_core_sha256'],'Installed baseline core changed')
        module=load('provision-wlan-mac');rec=json.loads(self.rules.private_file('/var/lib/picasso-wifi-nv/dms-wlan-mac-query-20261027.json').read_text())
        self.mac=module.address_from_record(rec,self.cfg['factory_mac_sha256']).hex(':')
        self.health_thread=threading.Thread(target=self.guard,daemon=True);self.health_thread.start()
        for _ in range(60):
            if max(temperatures().values())<40000:break
            self.pause(1)
        require(max(temperatures().values())<40000,'Start temperature >=40C')
        for cpu,expected in ((6,2208000),(7,2400000)):
            p=Path('/sys/devices/system/cpu/cpufreq/policy'+str(cpu))
            require((p/'related_cpus').read_text().strip()==str(cpu) and (p/'scaling_driver').read_text().strip()=='qcom-cpufreq-hw','CPU topology changed')
            require(int((p/'scaling_max_freq').read_text())==expected and int((p/'scaling_min_freq').read_text())<=1094400 and 1094400 in map(int,(p/'scaling_available_frequencies').read_text().split()),'Unexpected original CPU limits')
            self.record['cpu_before'][str(cpu)]=expected
        self.save()
        for cpu in self.record['cpu_before']:
            p=Path('/sys/devices/system/cpu/cpufreq/policy'+cpu)/'scaling_max_freq';p.write_text('1094400')
            for _ in range(40):
                if int(p.read_text())==1094400:break
                self.pause(0.05)
            require(int(p.read_text())==1094400,'CPU cap did not settle')
        self.text(['modprobe','-r','ath10k_core','ath','mac80211','cfg80211'])
        self.text(['modprobe','-a','ath','mac80211']);self.text(['modprobe','rmtfs_mem'])
        mem=Path('/sys/class/rmtfs/qcom_rmtfs_mem1')
        for _ in range(20):
            if mem.exists():break
            self.pause(0.1)
        require(len(list(Path('/sys/class/rmtfs').glob('*')))==1,'Unexpected RMTFS clients')
        major,minor=map(int,(mem/'dev').read_text().split(':'))
        m={'physical_address':int((mem/'phys_addr').read_text(),16),'usable_bytes':int((mem/'size').read_text(),16),'major':major,'minor':minor}
        require((mem/'client_id').read_text().strip()=='1' and str((mem/'device/of_node').resolve()).endswith('/reserved-memory/rmtfs'),'Wrong RAM client')
        validate_memory(load('fdt').nodes(fdt),m)
        node=Path('/dev/qcom_rmtfs_mem1');st=node.lstat();require(stat.S_ISCHR(st.st_mode) and st.st_rdev==os.makedev(major,minor),'RMTFS node identity changed')
        fd=os.open(node,os.O_RDWR|os.O_NOFOLLOW)
        try:
            for off in range(0,0x280000,512*1024):
                data=bytes(min(512*1024,0x280000-off));require(os.pwrite(fd,data,off)==len(data) and os.pread(fd,len(data),off)==data,'Shared RAM clear test failed')
            require(os.pread(fd,1,0x280000)==b'' and os.pwrite(fd,b'\0',0x280000)==0,'Shared RAM EOF check failed')
        finally:os.close(fd)
        self.record['memory']=m;self.save()
        # Cold boot does not necessarily autoload the GLINK QRTR transport.
        # Earlier attended trials had explicitly loaded this before their scan.
        self.text(['modprobe','qrtr_smd'])
        self.text(['modprobe','qcom_pd_mapper'])
        self.text(['modprobe','qcom_q6v5_pas'])
        for _ in range(30):
            procs=list(Path('/sys/class/remoteproc').glob('*'))
            if procs:break
            self.pause(0.1)
        require(len(procs)==1 and (procs[0]/'firmware').read_text().strip()==FIRMWARE,'Require unique Picasso MPSS')
        self.proc=procs[0];require((self.proc/'state').read_text().strip()=='offline','MPSS auto-started unexpectedly')
        (self.proc/'recovery').write_text('disabled');require((self.proc/'recovery').read_text().strip()=='disabled','Automatic recovery not disabled')
        self.record['proc']=str(self.proc);self.record['core_armed']=True;self.save()
        self.text(['insmod',self.cfg['observer_module'],'picasso_mgmt_status=0','picasso_ht20_only=1','debug_mask=0x200000'])
        for name,value in (('picasso_ht20_only','Y'),('picasso_mgmt_status','N')):
            p=Path('/sys/module/ath10k_core/parameters')/name;require(p.read_text().strip()==value and not p.stat().st_mode&0o222,'Read-only core option failed')
        self.text(['systemctl','restart','wpa_supplicant.service'])
        rf='picasso-rmtfs-auto-'+self.record['session']+'.service';tf='picasso-tftp-auto-'+self.record['session']+'.service'
        self.record['children']=[rf,tf];self.save()
        template=(OPT/'rmtfs-supervised.service.in').read_text()
        values={'@WORKDIR@':str(WORK),'@MEM_BASE@':hex(m['physical_address']),'@MEM_MAJOR@':str(major),'@MEM_MINOR@':str(minor),'@PID@':str(os.getpid()),'@LEASE@':self.lease,'@ENGINE_SHA@':self.cfg['rmtfs_engine_sha256'],'@LIB_SHA@':self.cfg['qrtr_library_sha256']}
        for old,new in values.items():template=template.replace(old,new)
        for name,body in ((rf,template),(tf,(OPT/'tftp-supervised.service.in').read_text())):
            p=Path('/run/systemd/system')/name
            with p.open('x') as out:out.write(body)
        self.text(['systemctl','daemon-reload']);self.text(['systemctl','start',tf,rf])
        for _ in range(30):
            if 'supervised_private_fd_proxy_ready' in self.text(['journalctl','-b','-u',rf,'-n','10','--no-pager','-o','cat']):break
            self.pause(0.1)
        else:raise RuntimeError('Supervised proxy did not become ready')
        atomic(STATE/'dirty.json',{'session':self.record['session'],'boot_id':self.record['boot_id']});self.record['nv_armed']=True;self.save()
        (self.proc/'state').write_text('start');require((self.proc/'state').read_text().strip()=='running','DSP failed to start');self.live=True
        endpoints=[]
        for _ in range(20):
            text=self.text(['env','LD_LIBRARY_PATH=/opt/picasso-wifi-trial/userspace/usr/lib64','/opt/picasso-wifi-trial/userspace/usr/bin/qrtr-lookup'])
            endpoints=[int(v[4]) for line in text.splitlines() if len(v:=line.split())>=5 and v[:2]==['69','1'] and v[3]=='0']
            if endpoints:break
            self.pause(0.5)
        require(len(endpoints)==1,'No unique local WLFW endpoint')
        self.helper=subprocess.Popen(['python3',str(OPT/'provision-wlan-mac.py'),'--record','/var/lib/picasso-wifi-nv/dms-wlan-mac-query-20261027.json','--record-mac-sha256',self.cfg['factory_mac_sha256'],'--library','/opt/picasso-wifi-trial/userspace/usr/lib64/libqrtr.so.1','--library-sha256',self.cfg['qrtr_library_sha256'],'--port',str(endpoints[0]),'--hold-seconds','120'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        until=time.monotonic()+10
        while not select.select([self.helper.stdout],[],[],0.1)[0]:self.tick();require(time.monotonic()<until,'WLFW MAC deadline')
        response=self.helper.stdout.readline();require(bool(response) and json.loads(response)['status']=='device_dms_mac_provisioned_in_wlfw_runtime','MAC provision failed')
        self.record['mac_provisioned_this_dsp_boot']=True;self.record['radio_armed']=True;self.save()
        self.text(['insmod',self.cfg['snoc_module'],'picasso_fixed_msa=1'])
        for _ in range(30):
            if Path('/sys/class/net/wlan0').exists():break
            self.pause(0.2)
        self.identity();self.pause(2)
        require(self.text(['iw','reg','get']).startswith('global\ncountry US:'),'Driver regulatory hint did not settle')
        self.text(['iw','reg','set','SG']);self.pause(2);self.record['initial_sg_audit']=self.audit()
        self.text(['ip','link','set','wlan0','up']);self.text(['nmcli','device','set','wlan0','autoconnect','no'])
        self.text(['nmcli','device','set','wlan0','managed','yes'])
        self.text(['iw','dev','wlan0','set','power_save','off'])
        require('off' in self.text(['iw','dev','wlan0','get','power_save']),'Power-save readback failed')
        self.record['runtime_power_save']='off'
        self.record['status']='activating';self.save()

    def activate(self,ssid,band,seconds):
        require(ssid in NAMES,'Unauthorized SSID')
        self.identity();self.audit(reapply=True)
        if band=='bg':
            phy=(Path('/sys/class/net/wlan0/phy80211')).resolve().name
            frequencies=load('wifi-bss').active_2g_frequencies(self.text(['iw','phy',phy,'info']))
            self.run(['iw','dev','wlan0','scan','freq',*map(str,frequencies),'ssid',ssid],timeout=5,check=False)
        profile='picasso-auto-'+ssid
        for key,value in [('802-11-wireless.ssid',ssid),('802-11-wireless.band',band),('802-11-wireless.hidden','yes'),('802-11-wireless.powersave','disable'),('802-11-wireless.cloned-mac-address','permanent'),('802-11-wireless-security.key-mgmt','wpa-psk'),('802-11-wireless-security.proto','rsn'),('802-11-wireless-security.pairwise','ccmp'),('802-11-wireless-security.group','ccmp'),('802-11-wireless-security.psk-flags','2'),('connection.autoconnect','no'),('connection.zone','drop'),('ipv4.method','auto'),('ipv6.method','disabled')]:
            require(self.text(['nmcli','-g',key,'connection','show',profile]).strip()==value,'Unsafe profile property '+key)
        self.cutoff=float(Path('/proc/uptime').read_text().split()[0]);start=time.monotonic()
        code,_=self.run(['nmcli','--wait',str(seconds),'connection','up','id',profile,'ifname','wlan0','passwd-file',str(CREDENTIALS/(ssid+'.passwd'))],timeout=seconds+4,check=False)
        self.record['attempts'].append({'ssid':ssid,'nmcli_returncode':code,'elapsed_seconds':round(time.monotonic()-start,3),'budget_seconds':seconds});self.save()
        return code==0

    def disconnect(self,ssid):self.run(['nmcli','--wait','3','connection','down','picasso-auto-'+ssid],timeout=5,check=False)

    def validate(self,ssid):
        self.identity();info=self.text(['iw','dev','wlan0','info']);require('width: 20 MHz' in info,'Actual width is not 20MHz')
        for _ in range(15):
            try:self.record['post_assoc_sg_audit']=self.audit(reapply=True);break
            except ValueError:self.pause(0.2)
        else:raise RuntimeError('Actual SG intersection rejected')
        require(re.search(r'authorized:\s+yes\b',self.text(['iw','dev','wlan0','station','dump'])),'Station not authorized')
        require(any(l.strip()=='SSID: '+ssid for l in self.text(['iw','dev','wlan0','link']).splitlines()),'Unexpected associated SSID')
        require(self.text(['nmcli','-g','GENERAL.STATE','device','show','wlan0']).strip().startswith('100 '),'NM not activated')
        self.record['encryption_evidence']=load('wifi-auth-evidence').verify_ccmp_handshake(self.text(['journalctl','-b','-u','wpa_supplicant.service','-n','100','-o','json','--no-pager']),self.cutoff,rsn_only=True)
        require('dhcp_server_identifier' in self.text(['nmcli','-g','DHCP4.OPTION','device','show','wlan0']),'No fresh DHCP options')
        routes=json.loads(self.text(['ip','-j','-4','route','show']));require(any(v.get('dst')=='default' and v.get('dev')=='wlan0' for v in routes),'No WLAN IPv4 default')
        require(self.text(['firewall-cmd','--get-zone-of-interface=wlan0']).strip()=='drop','WLAN not in drop zone')
        fields=self.text(['nmcli','-g','IP4.GATEWAY,IP4.DNS','device','show','wlan0']).splitlines();ipaddress.IPv4Address(fields[0])
        dns=next(x for x in fields[1:] if x and ':' not in x);ipaddress.IPv4Address(dns)
        require(json.loads(self.text(['ip','-j','-4','route','get',dns]))[0]['dev']=='wlan0','DNS route is not WLAN')
        ident=int.from_bytes(os.urandom(2),'big');query=struct.pack('!HHHHHH',ident,0x0100,1,0,0,0)+b'\x07example\x03com\0'+struct.pack('!HH',1,1)
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_BINDTODEVICE,b'wlan0\0');sock.settimeout(0.2);sock.sendto(query,(dns,53));until=time.monotonic()+3
            while True:
                try:data,peer=sock.recvfrom(4096);break
                except socket.timeout:self.tick();require(time.monotonic()<until,'Fresh DNS deadline')
        require(peer==(dns,53) and len(data)>=12,'Wrong DNS peer/header')
        tx,flags,questions,answers,_,_=struct.unpack_from('!HHHHHH',data)
        require(tx==ident and flags&0x8000 and flags&15==0 and answers>0,'DNS response rejected')
        self.record['dns']={'bound_interface':'wlan0','fresh_transaction':True,'rcode':0,'answer_count':answers}
        address=self.text(['getent','ahostsv4','example.com'],timeout=7).split()[0];ipaddress.IPv4Address(address)
        require(json.loads(self.text(['ip','-j','-4','route','get',address]))[0]['dev']=='wlan0','Resolved HTTPS route is not WLAN')
        probe=self.text(['curl','-4','--interface','wlan0','--noproxy','*','--proto','=https','--connect-timeout','4','--max-time','8','--max-filesize','1048576','--silent','--show-error','--output','/dev/null','--write-out','%{http_code} %{ssl_verify_result} %{size_download} %{time_total}','https://example.com/'],timeout=10).split()
        require(len(probe)==4 and probe[0]=='200' and probe[1]=='0' and float(probe[2])>0,'WLAN certificate-verified HTTPS failed')
        self.record['https']={'interface':'wlan0','http_code':200,'ssl_verify_result':0,'bytes':int(float(probe[2])),'seconds':float(probe[3])}
        self.record['ssid']=ssid;self.record['permanent_mac_matches']=True;self.record['actual_20mhz']=True;self.save()

    def monitor(self):
        self.identity();self.record['post_assoc_sg_audit']=self.audit()
        for cpu in ('6','7'):require(int((Path('/sys/devices/system/cpu/cpufreq/policy'+cpu)/'scaling_max_freq').read_text())==1094400,'Active CPU cap changed')
        for unit in self.record['children']:require(self.text(['systemctl','is-active',unit]).strip()=='active','Dependency stopped')
        require(self.text(['firewall-cmd','--get-zone-of-interface=wlan0']).strip()=='drop','Drop zone changed')
        link=self.text(['iw','dev','wlan0','link'])
        connected=any(l.strip()=='SSID: '+self.record['ssid'] for l in link.splitlines())
        station=self.text(['iw','dev','wlan0','station','dump'])
        if not connected or not re.search(r'authorized:\s+yes\b',station):
            require(self.record['ssid']=='Chaldea','Fallback link lost; no restart loop')
            self.disconnect('Chaldea');require(self.activate('Chaldea-2.4G','bg',25),'Runtime fallback failed')
            self.validate('Chaldea-2.4G');self.record['runtime_fallback_used']=True
        # A disconnected interface can legitimately omit width. Check live
        # authorization before interpreting missing channel info as a width change.
        info=self.text(['iw','dev','wlan0','info'])
        require('width: 20 MHz' in info,'Connected interface width changed')
        require('off' in self.text(['iw','dev','wlan0','get','power_save']),'Live power-save policy changed')
        if time.monotonic()-getattr(self,'last_keepalive',0)>=5:
            gateway=self.text(['nmcli','-g','IP4.GATEWAY','device','show','wlan0']).strip();ipaddress.IPv4Address(gateway)
            self.run(['ping','-n','-I','wlan0','-c','1','-W','1',gateway],timeout=3,check=False)
            self.last_keepalive=time.monotonic();self.record['gateway_keepalive_interval_seconds']=5
        return True

    def execute(self):
        def stop(*_):self.stopping=True
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        failed=False
        try:
            self.startup()
            if self.cfg.get('diagnostic_2g_only',False):
                require(self.cfg.get('probation_seconds',0)>0,'2G-only diagnosis must remain bounded')
                require(self.activate('Chaldea-2.4G','bg',25),'Diagnostic 2G activation failed')
                self.validate('Chaldea-2.4G')
                self.record.update(ssid='Chaldea-2.4G',diagnostic_2g_only=True,attempt_order=['Chaldea-2.4G'],fallback_used=False)
            else:
                result=self.rules.attempt_order(self.activate,self.validate,self.disconnect);self.record.update(result)
            self.record['status']='connected_guarded';self.record['ready_monotonic']=time.monotonic();self.save()
            atomic(Path(self.record['history'])/'connected.json',self.record)
            notify('READY=1\nSTATUS=Guarded '+self.record['ssid'])
            self.deadline=float('inf');probation=self.cfg.get('probation_seconds',30)
            while True:
                self.pause(2);self.monitor();self.save()
                if probation and time.monotonic()-self.record['ready_monotonic']>=probation:
                    self.record['status']='passed_bounded_probation';break
        except InterruptedError:self.record['status']='operator_stop'
        except Exception as exc:
            failed=True;self.record['status']='failed';self.record['error']=type(exc).__name__+': '+str(exc)
        finally:
            self.live=False;self.stop_event.set()
            if self.health_thread:self.health_thread.join(timeout=1)
            self.save()
            out=cleanup();self.record['cleanup_status']=out['status']
            if self.helper:
                self.helper.terminate()
                try:self.helper.wait(timeout=2)
                except subprocess.TimeoutExpired:self.helper.kill();self.helper.wait()
            atomic(Path(self.record['history'])/'result.json',self.record);self.save()
            print(json.dumps({'status':self.record['status'],'ssid':self.record.get('ssid'),'cleanup':out['status']}),flush=True)
            if out['status']!='safe_cleanup_complete':failed=True
        return 1 if failed else 0


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cleanup',action='store_true');args=parser.parse_args()
    require(os.geteuid()==0,'Root controller required')
    if args.cleanup:
        out=cleanup();print(json.dumps({'status':out['status']}));return 0 if out['status'] in ('nothing_armed','safe_cleanup_complete') else 1
    return Service().execute()


if __name__=='__main__':sys.exit(main())
