#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""CN radio R2: replace only audit evidence with same-PHY raw nl80211 flags.
Pinned R1 command/save adapter and original startup/lease/cleanup remain intact.
No automatic SSID activation or retries. Genuine missing indoor bit still fails.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path('/opt/picasso-wifi-cn-raw')
R1=Path('/opt/picasso-wifi-cn/wifi-cn-radio-service.py')
R1_SHA='53aa3980c9a77c49348282ccddb3466fb8141f893b46c006ac690bb4943f2e34'


def require(ok,message):
    if not ok:raise RuntimeError(message)


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixed_assets():
    require(hashlib.sha256(R1.read_bytes()).hexdigest()==R1_SHA,'Pinned CN R1 changed')
    r1=load(R1,'pinned_CN_R1');policy=json.loads(r1.private(ROOT/'policy.json'))
    require(policy.get('user_request')=='继续修复' and policy.get('country')=='CN','Explicit CN raw repair policy required')
    for name in ('wifi-nl80211-channels.py','audit-wifi-regulatory-cn-raw.py'):
        data=r1.private(ROOT/name);require(hashlib.sha256(data.encode()).hexdigest()==policy['file_sha256'][name],'Raw evidence asset changed')
    radio,worker,parser,reference=r1.fixed_assets()
    require(hashlib.sha256(reference.encode()).hexdigest()==policy['CN_reference_sha256'],'CN reference changed')
    auditor=load(ROOT/'audit-wifi-regulatory-cn-raw.py','strict_raw_CN_auditor')
    return r1,radio,worker,parser,reference,auditor


def service_type(r1,radio,worker,parser,reference,auditor):
    class RawCN(r1.service_type(radio,worker,parser,reference)):
        def audit(self,reapply=False):
            if reapply:self.text(['iw','reg','set','CN']);self.pause(.3)
            self.identity();path=Path('/sys/class/net/wlan0/phy80211').resolve();name=path.name;index=int((path/'index').read_text())
            require((path/'name').read_text().strip()==name,'PHY sysfs name changed')
            legacy=self.text(['iw','phy',name,'info'])
            require('HT20/HT40' not in legacy and 'VHT Capabilities' not in legacy,'Unaudited wide PHY')
            before=self.text(['iw','reg','get']);observation={'requested':'CN','effective':before,
                'channel_lines':[line.strip() for line in legacy.splitlines() if ' MHz [' in line],'evidence_version':'raw_nl80211_R2'}
            self.record['last_regulatory_observation']=observation
            try:
                report=json.loads(self.text(['python3','-I',str(ROOT/'wifi-nl80211-channels.py'),'--read-only','--phy-index',str(index)],timeout=10))
                observation['raw']=report
                after=self.text(['iw','reg','get']);require(after==before,'Regulatory state changed during raw dump')
                require(path==Path('/sys/class/net/wlan0/phy80211').resolve() and int((path/'index').read_text())==index,'PHY changed during raw dump')
                self.identity()
                return auditor.audit(reference,after,report,index,name,legacy,parser.cn_rules)
            except (ValueError,RuntimeError):
                self.record['regulatory_failure_observed']=observation;self.save();raise
    return RawCN


def main(args):
    require(args in (['--run-radio-up-cn-raw'],['--cleanup'],['--check-files']),'Explicit CN raw run/cleanup/check-files required')
    require(os.geteuid()==0,'Native root required');parts=fixed_assets();worker=parts[2]
    if args==['--check-files']:
        print(json.dumps({'status':'R2_raw_files_and_unchanged_pinned_guards_verified_no_RF'}));return 0
    if args==['--cleanup']:
        out=worker.cleanup();print(json.dumps({'status':out['status']}));return 0 if out['status'] in ('nothing_armed','safe_cleanup_complete') else 1
    return service_type(*parts)().execute_radio()


if __name__=='__main__':
    os.umask(0o077);raise SystemExit(main(sys.argv[1:]))
