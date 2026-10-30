#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bounded metadata-only observer atop the unchanged guarded service engine.

Never reads credentials, changes default service/config, or alters beacon/key
handling. Module must be independently hashed. Normal lifecycle/SG/identity/
thermal checks and independent cleanup are inherited, not bypassed.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import time

ENGINE=Path('/opt/picasso-wifi/wifi-service.py')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--module-sha256',required=True)
    p.add_argument('--seconds',type=int,default=45)
    args=p.parse_args()
    if os.geteuid()!=0 or not 1<=args.seconds<=90:raise SystemExit('Bounded root diagnostic only')
    cfg=json.loads(Path('/opt/picasso-wifi/config.json').read_text())
    if hashlib.sha256(ENGINE.read_bytes()).hexdigest()!=cfg['file_sha256'][str(ENGINE)]:raise SystemExit('Service engine changed')
    if hashlib.sha256(args.module.read_bytes()).hexdigest()!=args.module_sha256:raise SystemExit('Diagnostic module changed')
    spec=importlib.util.spec_from_file_location('guarded_wifi',ENGINE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

    class Diagnostic(m.Service):
        def __init__(self):
            super().__init__()
            self.cfg=copy.deepcopy(self.cfg)
            self.cfg.update(observer_module=str(args.module),diagnostic_2g_only=True,probation_seconds=args.seconds)
            self.cfg['file_sha256'][str(args.module)]=args.module_sha256
            self.record['diagnostic_metadata_observer']=True
            self.record['diagnostic_module_sha256']=args.module_sha256
            self.record['samples']=[]
            self.save()

        def run(self,argv,**kwargs):
            if argv[:2]==['insmod',str(args.module)]:argv=[*argv,'picasso_link_observe=1']
            return super().run(argv,**kwargs)

        def startup(self):
            super().startup()
            param=Path('/sys/module/ath10k_core/parameters/picasso_link_observe')
            m.require(param.read_text().strip()=='Y' and not param.stat().st_mode&0o222,'Observer read-only opt-in not active')
            self.record['link_observer_readonly_enabled']=True;self.save()

        def monitor(self):
            sample={'monotonic_seconds':time.monotonic()}
            for field,cmd in [('link',['iw','dev','wlan0','link']),('station',['iw','dev','wlan0','station','dump'])]:
                code,text=self.run(cmd,check=False);sample[field]=text;sample[field+'_returncode']=code
            sample['interface_counters']={n:int((Path('/sys/class/net/wlan0/statistics')/n).read_text()) for n in ('rx_bytes','tx_bytes','rx_packets','tx_packets','rx_errors','tx_errors')}
            self.record['samples'].append(sample);self.save()
            return super().monitor()

    return Diagnostic().execute()


if __name__=='__main__':sys.exit(main())
