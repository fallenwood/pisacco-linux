#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One explicitly permitted 7.3.1 PON capture, with PID1 bounds and owned cleanup.

No power actions, PMIC writes, arbitrary addresses, load retries or boot enablement.
Machine-specific permission/pins stay in a private root0400 file, not this source.
"""
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

BASE = Path('/opt/picasso-pon-audit-7.3.1-read1')
ASSETS = Path('/opt/picasso-pon-audit-7.3.1')
STATE = Path('/var/lib/picasso-power/pon-audit731-read1')
UNIT = 'picasso-pon-audit731-read1.service'
MODULE = 'picasso_pon_reason_audit731'
RELEASE = '7.3.1-picasso-wifi2'
SCOPE = 'pon731-fixed-readonly-once'
SNAPSHOT = Path('/sys/kernel') / MODULE / 'snapshot'
START_MC, ABORT_MC = 40000, 45000


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def boottime():
    return time.clock_gettime(time.CLOCK_BOOTTIME)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def root_file(path, mode=0o400):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0
            and stat.S_IMODE(info.st_mode) == mode, 'Wrong protected regular file: ' + path.name)


def record(name, value):
    require('/' not in name and name not in ('.', '..'), 'Record basename required')
    data = (json.dumps(value, indent=2) + '\n').encode()
    fd = os.open(STATE / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(data)
        while view:
            count = os.write(fd, view)
            require(count > 0, 'Short durable record')
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    fd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def validate_policy(policy):
    require(policy.get('scope') == SCOPE and policy.get('authorized') is True,
            'Explicit fixed read-only permission required')
    require(policy.get('kernel_release') == RELEASE, 'Wrong permission kernel')
    require(re.fullmatch(r'[0-9a-f]{32}', policy.get('run_token', '')) is not None, 'Invalid run token')
    require(re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', policy.get('boot_id', ''))
            is not None, 'Invalid boot binding')
    for key in ('collector_sha256', 'module_sha256', 'decoder_sha256', 'unit_sha256',
                'config_sha256', 'fdt_sha256'):
        require(re.fullmatch(r'[0-9a-f]{64}', policy.get(key, '')) is not None, 'Invalid asset pin')
    before, after = policy.get('not_before_boottime'), policy.get('not_after_boottime')
    require(all(type(value) in (int, float) and math.isfinite(value) for value in (before, after))
            and 0 <= before < after <= before + 300, 'Permission window must be finite and at most300s')


def read_policy():
    require(os.geteuid() == 0, 'Native root required')
    root_file(BASE / 'permit.json')
    policy = json.loads((BASE / 'permit.json').read_text())
    validate_policy(policy)
    info = STATE.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0
            and stat.S_IMODE(info.st_mode) == 0o700, 'Private existing state directory required')
    return policy


def temperatures():
    values = {p.parent.name: int(p.read_text())
              for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')}
    require(values and all(-10000 <= value <= 150000 for value in values.values()),
            'Invalid temperature telemetry')
    return values


def pid_start(pid):
    # /proc stat comm can contain spaces and parentheses.
    return int(Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[19])


def invocation():
    value = os.environ.get('INVOCATION_ID', '')
    require(re.fullmatch(r'[0-9a-f]{32}', value) is not None, 'PID1 invocation required')
    require('/' + UNIT in Path('/proc/self/cgroup').read_text(), 'Expected bounded PID1 unit required')
    return value


def lease_ok(claim, policy, now, pid, start, inv):
    return (claim.get('boot_id') == policy['boot_id']
            and claim.get('run_token') == policy['run_token']
            and claim.get('pid') == pid and claim.get('pid_start_ticks') == start
            and claim.get('invocation_id') == inv
            and claim['created_boottime'] <= now < claim['deadline_boottime'] <= policy['not_after_boottime'])


def owner_ok(intent, policy, boot, inv):
    return (intent.get('boot_id') == boot == policy['boot_id']
            and intent.get('run_token') == policy['run_token']
            and intent.get('module_sha256') == policy['module_sha256']
            and intent.get('initial_module_absent') is True
            and intent.get('invocation_id') == inv)


def module_present():
    return Path('/sys/module', MODULE).exists()


def cleanup(policy):
    result = {'module_present_before': module_present(), 'unload_requested': False}
    if result['module_present_before']:
        require(not (STATE / 'unloaded.json').exists(), 'Ownership already ended; refuse unrelated module')
        root_file(STATE / 'load-intent.json', 0o600)
        intent = json.loads((STATE / 'load-intent.json').read_text())
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        require(owner_ok(intent, policy, boot, invocation()), 'Wrong module/boot/run/invocation ownership')
        require(digest(ASSETS / 'picasso-pon-reason-audit731.ko') == policy['module_sha256'],
                'Owned module file changed')
        process = subprocess.run(['/usr/bin/rmmod', MODULE], capture_output=True, text=True, timeout=5)
        result.update(unload_requested=True, returncode=process.returncode,
                      stdout=process.stdout, stderr=process.stderr)
        record('unload-attempt-' + str(time.monotonic_ns()) + '.json', result)
        require(process.returncode == 0, 'Owned sampler unload failed')
        require(not module_present(), 'Owned sampler remains loaded')
        record('unloaded.json', {'boot_id': boot, 'run_token': policy['run_token'],
                                'invocation_id': intent['invocation_id'], 'boottime': boottime()})
    result.update(module_unloaded=not module_present(), snapshot_absent=not SNAPSHOT.parent.exists())
    record('cleanup-' + str(time.monotonic_ns()) + '.json', result)
    require(result['module_unloaded'] and result['snapshot_absent'], 'Sampler cleanup incomplete')
    return result


def validate_snapshot(snapshot, now, claim):
    require(snapshot.get('access') == 'existing-primary-regmap'
            and snapshot.get('kernel_release') == RELEASE, 'Wrong native sampler snapshot')
    captured = snapshot.get('capture_boottime_ns')
    require(type(captured) is int and captured > 0, 'Invalid capture time')
    capture = captured / 1e9
    require(claim['created_boottime'] <= capture <= now and now - capture <= 3,
            'Capture predates ownership or is stale')


def sample(policy):
    child = None
    claimed = False
    result = {'status': 'preflight', 'module_load_attempted': False,
              'PMIC_register_writes': False, 'power_actions': False, 'peak_sampled_temperature_mc': 0}
    begin, pid = boottime(), os.getpid()
    start, inv = pid_start(pid), invocation()
    claim = {'boot_id': policy['boot_id'], 'run_token': policy['run_token'], 'pid': pid,
             'pid_start_ticks': start, 'invocation_id': inv, 'created_boottime': begin,
             'deadline_boottime': min(begin + 15, policy['not_after_boottime'])}

    def tick():
        require(lease_ok(claim, policy, boottime(), os.getpid(), pid_start(pid), invocation()),
                'Collector PID/boot/run/invocation lease expired')
        values = temperatures()
        result['peak_sampled_temperature_mc'] = max(result['peak_sampled_temperature_mc'], max(values.values()))
        require(max(values.values()) < ABORT_MC, '45C thermal abort')
        return values

    try:
        require(os.uname().release == RELEASE, 'Matching native kernel required')
        require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == policy['boot_id'],
                'Same explicitly permitted boot required')
        require(policy['not_before_boottime'] <= begin < policy['not_after_boottime'], 'Permission expired/not yet valid')
        require(digest(Path('/sys/firmware/fdt')) == policy['fdt_sha256'], 'Native FDT changed')
        require(hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest()
                == policy['config_sha256'], 'Native kernel config changed')
        for path, key in ((BASE / 'collect-pon731.py', 'collector_sha256'),
                          (ASSETS / 'picasso-pon-reason-audit731.ko', 'module_sha256'),
                          (ASSETS / 'power-pon-reasons.py', 'decoder_sha256'),
                          (Path('/etc/systemd/system') / UNIT, 'unit_sha256')):
            root_file(path)
            require(digest(path) == policy[key], 'Changed pinned collector/module/decoder/unit')
        require(not module_present() and not SNAPSHOT.parent.exists(), 'Sampler already present')
        require(not Path('/sys/module/picasso_pon_reason_audit').exists(), 'Legacy sampler unexpectedly present')
        require(not (STATE / 'consumed').exists(), 'One-shot already consumed; never replay')
        result['start_temperatures_mc'] = tick()
        require(max(result['start_temperatures_mc'].values()) < START_MC, 'Start strictly below40C')
        record('consumed', {**claim, 'scope': SCOPE, 'no_retry': True})
        claimed = True
        record('load-intent.json', {**claim, 'module_sha256': policy['module_sha256'],
                                    'initial_module_absent': True})
        require(max(tick().values()) < START_MC, 'Start strictly below40C immediately before load')
        result['module_load_attempted'] = True
        child = subprocess.Popen(['/usr/bin/insmod', str(ASSETS / 'picasso-pon-reason-audit731.ko'),
                                  'confirm_readonly=1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        record('load-child.json', {'pid': child.pid, 'pid_start_ticks': pid_start(child.pid),
                                   'collector_pid': pid, 'invocation_id': inv})
        until = boottime() + 8
        while child.poll() is None:
            tick()
            require(boottime() < until, '8s module-load deadline, no retry')
            time.sleep(.05)
        out, err = child.communicate()
        result.update(insmod_returncode=child.returncode, insmod_stdout=out, insmod_stderr=err)
        record('load-return.json', {'returncode': child.returncode, 'stdout': out, 'stderr': err})
        require(child.returncode == 0, 'Sampler load failed, no retry')
        tick()
        root_file(SNAPSHOT)
        with SNAPSHOT.open('rb') as stream:
            raw = stream.read(4097)
        require(len(raw) <= 4096, 'Oversized fixed snapshot')
        snapshot = json.loads(raw)
        record('snapshot.json', snapshot)  # Preserve raw input before interpretation.
        validate_snapshot(snapshot, boottime(), claim)
        spec = importlib.util.spec_from_file_location('pon731_decoder', ASSETS / 'power-pon-reasons.py')
        decoder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(decoder)
        decoded = decoder.decode(snapshot)
        record('decoded.json', decoded)
        tick()
        result.update(status='sampled_once_readonly', snapshot=snapshot, decoded=decoded)
    except Exception as exc:
        result.update(status='failed_no_retry', error=type(exc).__name__ + ': ' + str(exc))
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                result['load_process_did_not_terminate'] = True
        if claimed:
            try:
                result['cleanup'] = cleanup(policy)
            except Exception as exc:
                result.update(status='cleanup_review_required', cleanup_error=type(exc).__name__ + ': ' + str(exc))
        try:
            result['end_temperatures_mc'] = temperatures()
            peak = max(result['end_temperatures_mc'].values())
            result['peak_sampled_temperature_mc'] = max(result['peak_sampled_temperature_mc'], peak)
            require(peak < ABORT_MC, '45C final thermal abort')
        except Exception as exc:
            result.update(status='thermal_review_required', thermal_error=type(exc).__name__ + ': ' + str(exc))
        result['duration_seconds'] = boottime() - begin
        record('result.json' if claimed else 'refusal-' + str(time.monotonic_ns()) + '.json', result)
    print(json.dumps(result), flush=True)
    return 0 if result['status'] == 'sampled_once_readonly' else 1


def main():
    require(sys.argv[1:] in (['--sample-once'], ['--cleanup']), 'Explicit one-shot or cleanup mode required')
    os.umask(0o077)
    sys.dont_write_bytecode = True
    policy = read_policy()
    if sys.argv[1] == '--cleanup':
        cleanup(policy)
        return 0
    return sample(policy)


if __name__ == '__main__':
    raise SystemExit(main())
