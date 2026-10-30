#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""CN-only regulatory adapter for pinned guarded real-wlan0 UP service.
Original SG worker/controller/config retained byte-for-byte, not re-enabled.
Only exact historical country request, audit and audit-field naming differ.
No automatic SSID activation, RF restart loop, or relaxed safety checks.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

ROOT=Path('/opt/picasso-wifi-cn')
RADIO=Path('/opt/picasso-wifi-radio/wifi-radio-service.py')
RADIO_SHA='a1d1e5e71e535cb2980695ad6e91d9276d477ab6d191fbd1817dd32520e5ffe5'


def require(ok,message):
    if not ok:raise RuntimeError(message)


def country_command(args):
    # The unmodified base startup has exactly this historical SG request.
    # Do not translate arbitrary argv, shell strings or other countries.
    return ['iw','reg','set','CN'] if args==['iw','reg','set','SG'] else args


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def private(path):
    s=path.lstat();require(stat.S_ISREG(s.st_mode) and not s.st_uid and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o400,'Root0400 CN policy/reference required')
    return path.read_text()


def fixed_assets():
    policy=json.loads(private(ROOT/'policy.json'));require(policy.get('user_request')=='从SG切换到CN' and policy.get('country')=='CN','Explicit CN policy required')
    reference=private(ROOT/'regulatory-CN-reference.txt');require(hashlib.sha256(reference.encode()).hexdigest()==policy['reference_sha256'],'CN reference changed')
    require(hashlib.sha256(RADIO.read_bytes()).hexdigest()==RADIO_SHA,'Pinned radio controller changed')
    path=ROOT/'audit-wifi-regulatory-cn.py';require(hashlib.sha256(path.read_bytes()).hexdigest()==policy['auditor_sha256'],'CN auditor changed')
    auditor=load(path,'strict_CN_auditor');auditor.cn_rules(reference)
    radio=load(RADIO,'pinned_radio_up');worker=radio.load_base()
    return radio,worker,auditor,reference


def service_type(radio,worker,auditor,reference):
    class CNRadio(radio.service_type(worker)):
        def text(self,args,**kwargs):
            return super().text(country_command(args),**kwargs)

        def audit(self,reapply=False):
            if reapply:self.text(['iw','reg','set','CN']);self.pause(.3)
            phy=Path('/sys/class/net/wlan0/phy80211').resolve().name
            data=self.text(['iw','phy',phy,'info'])
            require('HT20/HT40' not in data and 'VHT Capabilities' not in data,'Unaudited wide PHY')
            effective=self.text(['iw','reg','get'])
            # Preserve the actual rejected domain/rules if a future handoff fails.
            self.record['last_regulatory_observation']={'requested':'CN','effective':effective,
                'channel_lines':[line.strip() for line in data.splitlines() if ' MHz [' in line]}
            try:return auditor.audit(reference,effective,data)
            except ValueError:
                self.record['regulatory_failure_observed']=self.record['last_regulatory_observation'];self.save();raise

        def save(self):
            self.record['country_requested']='CN'
            self.record['CN_reference_sha256']=hashlib.sha256(reference.encode()).hexdigest()
            for old,new in (('initial_sg_audit','initial_cn_audit'),('radio_sg_audit','radio_cn_audit'),('post_assoc_sg_audit','post_assoc_cn_audit')):
                if old in self.record:self.record[new]=self.record.pop(old)
            return super().save()
    return CNRadio


def main(args):
    require(args in (['--run-radio-up-cn'],['--cleanup'],['--check-files']),'Explicit CN run/cleanup/check-files required')
    require(os.geteuid()==0,'Native root required');radio,worker,auditor,reference=fixed_assets()
    if args==['--check-files']:
        print(json.dumps({'status':'CN_files_policy_and_unchanged_pinned_guards_verified_no_RF','country':'CN'}));return 0
    if args==['--cleanup']:
        out=worker.cleanup();print(json.dumps({'status':out['status']}));return 0 if out['status'] in ('nothing_armed','safe_cleanup_complete') else 1
    return service_type(radio,worker,auditor,reference)().execute_radio()


if __name__=='__main__':
    os.umask(0o077);raise SystemExit(main(sys.argv[1:]))
