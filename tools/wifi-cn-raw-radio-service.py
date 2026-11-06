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
R1_SHA='17b97ffddd670f52084134a59bf49061a72e627fc05319b68e52be5fabb5b3e7'


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
    router=None
    if 'router_country_policy' in policy:
        for name in ('wifi-router-country.py','regulatory-router-reference.txt'):
            data=r1.private(ROOT/name)
            require(hashlib.sha256(data.encode()).hexdigest()==policy['file_sha256'][name],'Router-country asset changed')
        helper=load(ROOT/'wifi-router-country.py','reviewed_router_country')
        router_reference=r1.private(ROOT/'regulatory-router-reference.txt')
        country=helper.validate_policy(policy['router_country_policy'],router_reference)
        require(policy['router_country_policy'].get('regdb_sha256')=={
            str(path):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path('/usr/lib/firmware/regulatory.db'),Path('/usr/lib/firmware/regulatory.db.p7s'))},
            'Reviewed signed regulatory database changed')
        router={'helper':helper,'reference':router_reference,'country':country}
    return r1,radio,worker,parser,reference,auditor,router


def observe_channels(service,reference,auditor,parse_rules,country):
    service.identity();path=Path('/sys/class/net/wlan0/phy80211').resolve();name=path.name;index=int((path/'index').read_text())
    require((path/'name').read_text().strip()==name,'PHY sysfs name changed')
    legacy=service.text(['iw','phy',name,'info'])
    require('HT20/HT40' not in legacy and 'VHT Capabilities' not in legacy,'Unaudited wide PHY')
    before=service.text(['iw','reg','get']);observation={'requested':country,'effective':before,
        'channel_lines':[line.strip() for line in legacy.splitlines() if ' MHz [' in line],'evidence_version':'raw_nl80211_R2'}
    service.record['last_regulatory_observation']=observation
    try:
        report=json.loads(service.text(['python3','-I',str(ROOT/'wifi-nl80211-channels.py'),'--read-only','--phy-index',str(index)],timeout=10))
        observation['raw']=report
        after=service.text(['iw','reg','get']);require(after==before,'Regulatory state changed during raw dump')
        require(path==Path('/sys/class/net/wlan0/phy80211').resolve() and int((path/'index').read_text())==index,'PHY changed during raw dump')
        service.identity()
        return auditor.audit(reference,after,report,index,name,legacy,parse_rules,expected_country=country)
    except (ValueError,RuntimeError):
        service.record['regulatory_failure_observed']=observation;service.save();raise


def service_type(r1,radio,worker,parser,reference,auditor,router=None):
    class RawCN(r1.service_type(radio,worker,parser,reference)):
        def audit(self,reapply=False):
            effective=self.text(['iw','reg','get'])
            if reapply or not effective.startswith(('global\ncountry CN:','global\ncountry 98:')):
                self.text(['iw','reg','set','CN']);self.pause(.3)
            return observe_channels(self,reference,auditor,parser.cn_rules,'CN')
    if router is None:return RawCN
    helper=router['helper'];country=router['country']
    class RouterCountry(RawCN):
        def __init__(self):
            super().__init__()
            require(self.cfg.get('router_country')==country,'Router config/policy country mismatch')

        def text(self,args,**kwargs):
            if args in (['iw','reg','set','SG'],['iw','reg','set','CN']):
                args=['iw','reg','set',country]
            return super().text(args,**kwargs)

        def save(self):
            self.record['country_requested']=country
            self.record['regulatory_policy']='reviewed_router_country_ie'
            for old,new in (('initial_sg_audit','initial_router_audit'),('radio_sg_audit','radio_router_audit'),('post_assoc_sg_audit','post_assoc_router_audit')):
                if old in self.record:self.record[new]=self.record.pop(old)
            return worker.Service.save(self)

        def audit(self,reapply=False):
            self.identity()
            link=self.text(['iw','dev','wlan0','link']);selected=None;records=[]
            try:
                selected=helper.link_identity(link,worker.NAMES)
                if selected:
                    records=worker.load('wifi-bss').bss_records(self.text(['iw','dev','wlan0','scan','dump']))
                    require(helper.country_from_records(records,selected)==country,'Selected router country changed; policy review required')
            except ValueError as exc:
                self.record['router_country_failure_evidence']={'link':link,'selected_ap':selected,
                    'cached_selected_bss':[record for record in records if selected and record.lower().startswith(selected['bssid'])],
                    'error':type(exc).__name__+': '+str(exc)}
                self.save();raise
            effective=self.text(['iw','reg','get'])
            if reapply or not effective.startswith(('global\ncountry '+country+':','global\ncountry 98:')):
                self.text(['iw','reg','set',country]);self.pause(.3)
            self.record['router_country_observation']={'country':country,'selected_ap':selected,
                'source':'selected_cached_BSS_Country_IE' if selected else 'reviewed_router_bootstrap_no_association'}
            result=observe_channels(self,router['reference'],auditor,lambda ref:helper.kernel_rules(ref,country),country)
            require(selected is None or selected['frequency_mhz'] not in result.get('enabled_non20_channels_excluded',[]),
                    'Selected AP channel prohibits the required 20MHz mode')
            require(helper.link_identity(self.text(['iw','dev','wlan0','link']),worker.NAMES)==selected,'Selected AP changed during router-country audit')
            return result
    return RouterCountry


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
