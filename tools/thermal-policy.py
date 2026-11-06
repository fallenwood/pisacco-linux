#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Early passive CPU cooling; never writes critical trips, voltage or RF power."""
import argparse
import json
import os
from pathlib import Path
import time

SYSFS = Path('/sys/class/thermal')
PASSIVE_MC = 40000
ORIGINAL_PASSIVE_MC = 90000
CRITICAL_MC = 110000


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def inspect(root=SYSFS):
    paths = list(root.glob('thermal_zone*'))
    zones = {p.joinpath('type').read_text().strip(): p for p in paths}
    require(len(paths) == len(zones) == 8 and set(zones) == {f'cpu{i}-thermal' for i in range(8)},
            'Unexpected sensor topology')
    result = []
    for cpu in range(8):
        zone = zones[f'cpu{cpu}-thermal']
        values = {name: zone.joinpath(name).read_text().strip() for name in (
            'temp', 'policy', 'mode', 'trip_point_0_type', 'trip_point_0_temp',
            'trip_point_0_hyst', 'trip_point_1_type', 'trip_point_1_temp', 'trip_point_1_hyst')}
        require(-10000 <= int(values['temp']) <= 150000, 'Invalid thermal telemetry')
        require(values['policy'] == 'step_wise' and values['mode'] == 'enabled',
                'Native kernel thermal governor must remain enabled')
        require(values['trip_point_0_type'] == 'passive'
                and int(values['trip_point_0_temp']) in (ORIGINAL_PASSIVE_MC, PASSIVE_MC)
                and values['trip_point_0_hyst'] == '2000', 'Unexpected passive trip')
        require(values['trip_point_1_type'] == 'critical'
                and int(values['trip_point_1_temp']) == CRITICAL_MC
                and values['trip_point_1_hyst'] == '1000', 'Critical protection changed')
        cooling = list(zone.glob('cdev[0-9]'))
        require(len(cooling) == 1, 'Expected one mapped CPU cooler')
        cooler = cooling[0].resolve(strict=True)
        policy_cpu = 0 if cpu < 6 else cpu
        require(cooler.joinpath('type').read_text().strip() == f'cpufreq-cpu{policy_cpu}'
                and int(cooler.joinpath('max_state').read_text()) > 0, 'Wrong CPU cooler')
        result.append((zone, values))
    return result


def apply(root=SYSFS):
    before = inspect(root)  # Validate every zone before the first write.
    written = []
    for zone, values in before:
        if int(values['trip_point_0_temp']) != PASSIVE_MC:
            zone.joinpath('trip_point_0_temp').write_text(str(PASSIVE_MC))
            written.append(zone.name)
        require(int(zone.joinpath('trip_point_0_temp').read_text()) == PASSIVE_MC,
                'Passive trip readback failed')
    after = inspect(root)
    require(all(int(values['trip_point_0_temp']) == PASSIVE_MC for _, values in after),
            'Incomplete passive cooling deployment')
    # On partial failure leave stricter trips in place and fail the dependent RF
    # startup. Never roll temperatures upward automatically to hide a failure.
    return {'status': 'early_passive_cooling_applied', 'passive_mc': PASSIVE_MC,
            'hysteresis_mc': 2000, 'critical_mc_unchanged': CRITICAL_MC,
            'zones_written': written, 'before': {p.name: v for p, v in before},
            'after': {p.name: v for p, v in after}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    require(os.geteuid() == 0 and os.uname().release == '7.3.1-picasso-wifi2',
            'Native Picasso 7.3.1 root required')
    for cpu in (0, 6, 7):
        policy = Path('/sys/devices/system/cpu/cpufreq') / f'policy{cpu}'
        require(policy.joinpath('scaling_driver').read_text().strip() == 'qcom-cpufreq-hw',
                'Unexpected cpufreq driver')
    result = {'status': 'checked_no_writes'}
    try:
        if args.apply:
            result = apply()
        else:
            result['zones'] = {p.name: v for p, v in inspect()}
    except Exception as exc:
        result = {'status': 'failed_partial_cooling_may_remain', 'error': str(exc)}
        raise
    finally:
        if args.apply:
            directory = Path('/var/lib/picasso-thermal-policy')
            directory.mkdir(mode=0o700, exist_ok=True)
            path = directory / f'apply-{time.time_ns()}.json'
            with path.open('x') as stream:
                json.dump(result, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    os.umask(0o077)
    main()
