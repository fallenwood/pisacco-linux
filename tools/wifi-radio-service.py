#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Keep the real wlan0 administratively UP, including while unassociated.
No automatic SSID activation or retries. Existing worker owns RF, private FD
backend, exact PID lease and independent emergency cleanup. UP != Internet.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import sys

SOURCE=Path('/opt/picasso-wifi/wifi-auto-service.py')
SOURCE_SHA='a5000fef3c7f4641e917dbb206a4993861ccd46eb56b649c7e748630a5b99c96'
NAMES=('Chaldea','Chaldea-2.4G')


def require(ok,message):
    if not ok:raise RuntimeError(message)


def link_metadata(text):
    out={'ssid':None,'frequency_mhz':None,'signal_dbm':None}
    for line in text.splitlines():
        value=line.strip()
        if value.startswith('SSID: '):out['ssid']=value[6:]
        elif value.startswith('freq: '):out['frequency_mhz']=float(value.split()[1])
        elif value.startswith('signal: '):out['signal_dbm']=float(value.split()[1])
    require(out['ssid'] is None or out['ssid'] in NAMES,'Unapproved associated SSID')
    return out


def check_link_flags(rows):
    require(len(rows)==1 and rows[0].get('ifname')=='wlan0' and 'UP' in rows[0].get('flags',[]),'Administrative wlan0 UP changed')
    # NO-CARRIER/DORMANT/DOWN operstate are normal for an unassociated UP NIC.
    return {'administrative_up':True,'operstate':rows[0].get('operstate'),'carrier_flag':'LOWER_UP' in rows[0].get('flags',[])}


def load_base():
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA,'Pinned guarded worker changed')
    spec=importlib.util.spec_from_file_location('pinned_guarded_worker',SOURCE)
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);return base


def service_type(base):
    class RadioService(base.Service):
        def radio_monitor(self):
            self.identity()
            for cpu in ('6','7'):
                require(int(Path('/sys/devices/system/cpu/cpufreq/policy'+cpu+'/scaling_max_freq').read_text())==1094400,'Active CPU cap changed')
            for unit in self.record['children']:
                require(self.text(['systemctl','is-active',unit]).strip()=='active','Radio dependency stopped')
            metadata=link_metadata(self.text(['iw','dev','wlan0','link']))
            code,zone=self.run(['firewall-cmd','--get-zone-of-interface=wlan0'],check=False);zone=zone.strip()
            if zone!='drop':
                require(zone in ('','no zone'),'Unexpected WLAN firewall zone')
                # NM may remove a runtime binding on ordinary disconnect.
                # Rebind only an unassigned interface; never trust a whole zone.
                self.text(['firewall-cmd','--zone=drop','--add-interface=wlan0'])
            require(self.text(['firewall-cmd','--get-zone-of-interface=wlan0']).strip()=='drop','WLAN drop zone changed')
            changed=metadata['ssid']!=self.record.get('association_observed_ssid')
            self.record['radio_sg_audit']=self.audit(reapply=bool(changed and metadata['ssid']))
            state=check_link_flags(json.loads(self.text(['ip','-j','link','show','dev','wlan0'])))
            require('off' in self.text(['iw','dev','wlan0','get','power_save']),'Power-save policy changed')
            station=self.text(['iw','dev','wlan0','station','dump'])
            authorized=bool(re.search(r'authorized:\s+yes\b',station))
            if metadata['ssid'] and authorized:
                require('width: 20 MHz' in self.text(['iw','dev','wlan0','info']),'Authorized link width changed')
            self.record.update(status='radio_up_idle' if metadata['ssid'] is None else 'radio_up_association_observed_not_internet_validated',
                administrative_up=state['administrative_up'],operstate=state['operstate'],carrier_flag=state['carrier_flag'],
                association_observed_ssid=metadata['ssid'],association_authorized_observed=bool(metadata['ssid'] and authorized),
                association_signal_dbm=metadata['signal_dbm'],association_frequency_mhz=metadata['frequency_mhz'],
                internet_connectivity_validated=False,automatic_activation_attempts_allowed=False)

        def execute_radio(self):
            def stop(*args):self.stopping=True
            signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
            failed=False
            try:
                self.record.update(mode='persistent_real_wlan0_UP_no_auto_association',ordinary_link_loss_closes_radio=False,safety_fault_still_requires_shutdown=True)
                self.save();self.startup();self.deadline=float('inf');self.radio_monitor();self.save()
                base.atomic(Path(self.record['history'])/'radio-ready.json',self.record)
                base.notify('READY=1\nSTATUS=wlan0 UP; association/Internet NOT implied; safety guards active')
                while True:self.pause(2);self.radio_monitor();self.save()
            except InterruptedError:self.record['status']='operator_stop'
            except Exception as exc:
                failed=True;self.record.update(status='failed_safety_shutdown',error=type(exc).__name__+': '+str(exc))
            finally:
                base.notify('STOPPING=1\nSTATUS=Guarded radio shutdown on explicit stop or safety fault')
                self.live=False;self.stop_event.set()
                if self.health_thread:self.health_thread.join(timeout=1)
                self.save();out=base.cleanup();self.record['cleanup_status']=out['status']
                if self.helper:
                    self.helper.terminate()
                    try:self.helper.wait(timeout=2)
                    except base.subprocess.TimeoutExpired:self.helper.kill();self.helper.wait()
                base.atomic(Path(self.record['history'])/'result.json',self.record);self.save()
                if out['status']!='safe_cleanup_complete':failed=True
                print(json.dumps({'status':self.record['status'],'cleanup':out['status']}),flush=True)
            return 1 if failed else 0
    return RadioService


def main(args):
    require(args in (['--run-radio-up'],['--cleanup']),'Explicit --run-radio-up or --cleanup required')
    require(os.geteuid()==0,'Native root required');base=load_base()
    if args==['--cleanup']:
        out=base.cleanup();print(json.dumps({'status':out['status']}));return 0 if out['status'] in ('nothing_armed','safe_cleanup_complete') else 1
    return service_type(base)().execute_radio()


if __name__=='__main__':
    os.umask(0o077);raise SystemExit(main(sys.argv[1:]))
