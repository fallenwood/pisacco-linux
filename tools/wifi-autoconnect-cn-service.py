#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Boot association using the unchanged raw-CN radio owner and safety guards."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path('/opt/picasso-wifi-autoconnect-cn')
SOURCE = Path('/opt/picasso-wifi-cn-raw/wifi-cn-raw-radio-service.py')
SOURCE_SHA = '317615bf70725858f34385dc0638e5faa891ff2d4fdd511a5c79411301bed696'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def fixed_assets():
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA,
            'Pinned raw CN radio owner changed')
    spec = importlib.util.spec_from_file_location('pinned_raw_CN_radio', SOURCE)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    parts = adapter.fixed_assets()
    policy = json.loads(parts[0].private(ROOT / 'policy.json'))
    require(policy.get('user_request') == '把自动熄屏和自动连接wlan写入手机'
            and policy.get('country') == 'CN'
            and policy.get('targets') == ['Chaldea', 'Chaldea-2.4G'],
            'Explicit CN boot autoconnect policy required')
    require(policy.get('service_sha256') == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'Boot autoconnect policy does not match this controller')
    return adapter, parts


def service_type(adapter, parts):
    class AutoCN(adapter.service_type(*parts)):
        def startup(self):
            super().startup()
            result = self.rules.attempt_order(self.activate, self.validate, self.disconnect)
            self.record.update(result)
            self.record['boot_autoconnect_completed'] = True
            self.save()

        def radio_monitor(self):
            super().radio_monitor()
            self.record.update(
                mode='persistent_real_wlan0_UP_with_boot_autoconnect_CN',
                automatic_activation_attempts_allowed=True,
                automatic_reconnection_enabled=False,
            )
    return AutoCN


def main(args):
    require(args in (['--run'], ['--cleanup'], ['--check-files']),
            'Explicit run/cleanup/check-files required')
    require(os.geteuid() == 0, 'Native root required')
    adapter, parts = fixed_assets()
    worker = parts[2]
    if args == ['--check-files']:
        print(json.dumps({'status': 'CN_boot_autoconnect_files_verified_no_RF'}))
        return 0
    if args == ['--cleanup']:
        out = worker.cleanup()
        print(json.dumps({'status': out['status']}))
        return 0 if out['status'] in ('nothing_armed', 'safe_cleanup_complete') else 1
    return service_type(adapter, parts)().execute_radio()


if __name__ == '__main__':
    os.umask(0o077)
    raise SystemExit(main(sys.argv[1:]))
