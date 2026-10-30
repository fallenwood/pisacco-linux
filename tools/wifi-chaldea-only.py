#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One explicitly attended Chaldea-only session; deny any fallback activation.
All radio/NV/thermal/cleanup operations remain in the pinned existing worker.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

SOURCE=Path('/opt/picasso-wifi/wifi-auto-service.py')
SOURCE_SHA='428495f9e7007d9728b0df9887b630c62013622b9137af39d4afcf532191b725'


def require(ok,message):
    if not ok:raise RuntimeError(message)


def allowed_request(ssid,band,seconds):
    require(ssid=='Chaldea' and band=='a' and type(seconds) is int and seconds==20,'Chaldea-only request: fallback/other activation disabled')


def service_type(base):
    class ChaldeaOnly(base.Service):
        def activate(self,ssid,band,seconds):
            # Both initial and runtime fallback pass through this override.
            # Refuse before calling the inherited native nmcli implementation.
            allowed_request(ssid,band,seconds)
            return super().activate(ssid,band,seconds)
    return ChaldeaOnly


def load_base():
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA,'Guarded worker changed')
    spec=importlib.util.spec_from_file_location('pinned_guarded_worker',SOURCE)
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);return base


def main(args):
    require(args in (['--run-chaldea-only'],['--cleanup']),'Explicit --run-chaldea-only or --cleanup required')
    require(os.geteuid()==0,'Native root required');base=load_base()
    if args==['--cleanup']:
        out=base.cleanup();print(json.dumps({'status':out['status']}));return 0 if out['status'] in ('nothing_armed','safe_cleanup_complete') else 1
    worker=service_type(base)();worker.record.update(requested_only_ssid='Chaldea',fallback_authorized=False)
    worker.save();return worker.execute()


if __name__=='__main__':
    os.umask(0o077);raise SystemExit(main(sys.argv[1:]))
