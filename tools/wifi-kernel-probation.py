#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run the same candidate CN worker for a bounded probation, never its radio loop."""
import importlib.util
import sys
from pathlib import Path


def main(args):
    if args not in (['--run'], ['--cleanup']):
        raise SystemExit('Explicit --run or --cleanup required')
    base = Path(__file__).resolve().parent.parent
    source = base / 'picasso-wifi-cn-raw/wifi-cn-raw-radio-service.py'
    spec = importlib.util.spec_from_file_location('candidate_raw_cn', source)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    parts = adapter.fixed_assets()
    worker = parts[2]
    worker.CONFIG = worker.OPT / 'config-probation.json'
    if args == ['--cleanup']:
        result = worker.cleanup()
        print(result['status'], flush=True)
        return 0 if result['status'] in ('nothing_armed', 'safe_cleanup_complete') else 1
    service = adapter.service_type(*parts)()
    if service.cfg['probation_seconds'] != 45:
        raise RuntimeError('Candidate probation must remain bounded to 45 seconds')
    return service.execute()


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
