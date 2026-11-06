"""Synthetic collector tests only; insmod/rmmod and all native inputs are mocked."""
from contextlib import ExitStack
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pon731_collector', ROOT / 'tools/collect-pon731.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
BOOT = '00000000-0000-0000-0000-000000000001'  # OFFLINE FIXTURE, not a device identity.
INV = 'a' * 32


def policy():
    p = {'scope': C.SCOPE, 'authorized': True, 'kernel_release': C.RELEASE,
         'boot_id': BOOT, 'run_token': 'b' * 32,
         'not_before_boottime': 90, 'not_after_boottime': 120}
    for key in ('collector_sha256', 'module_sha256', 'decoder_sha256', 'unit_sha256', 'fdt_sha256'):
        p[key] = '1' * 64
    p['config_sha256'] = hashlib.sha256(b'config-fixture').hexdigest()
    return p


def snapshot():
    return {'scope': 'picasso-pm8150-gen2-readonly', 'access': 'existing-primary-regmap',
            'kernel_release': C.RELEASE, 'usid': 0, 'base': 2048,
            'capture_boottime_ns': 100_000_000_000,
            'registers': {'0104': 0x51, '0105': 0x1e, '0805': 4, '08c0': 0x10,
                          '08c2': 0, '08c7': 0x80, '08c5': 2,
                          '08c8': None, '08c9': None, '08ca': None}}


class CollectorGuardTests(unittest.TestCase):
    def test_explicit_fixed_scope_finite_window_and_all_pins_required(self):
        C.validate_policy(policy())
        for key, bad in (('authorized', 1), ('kernel_release', 'other'), ('scope', 'power'),
                         ('run_token', 'bad'), ('module_sha256', 'bad'), ('boot_id', 'other'),
                         ('not_after_boottime', float('nan')), ('not_after_boottime', 400),
                         ('not_before_boottime', True)):
            with self.subTest(key=key, bad=bad), self.assertRaises(RuntimeError):
                C.validate_policy({**policy(), key: bad})

    def test_pid_start_parses_comm_with_spaces_and_parentheses(self):
        line = '12 (name with (extra) parens) S ' + ' '.join(map(str, range(1, 23)))
        with patch.object(Path, 'read_text', return_value=line):
            self.assertEqual(C.pid_start(12), 19)

    def test_lease_requires_exact_pid_start_invocation_boot_and_deadline(self):
        p = policy()
        claim = {'boot_id': BOOT, 'run_token': p['run_token'], 'pid': 12, 'pid_start_ticks': 88,
                 'invocation_id': INV, 'created_boottime': 100, 'deadline_boottime': 115}
        self.assertTrue(C.lease_ok(claim, p, 101, 12, 88, INV))
        for now, pid, start, inv in ((115, 12, 88, INV), (99, 12, 88, INV),
                                     (101, 13, 88, INV), (101, 12, 89, INV), (101, 12, 88, 'c' * 32)):
            self.assertFalse(C.lease_ok(claim, p, now, pid, start, inv))
        self.assertFalse(C.lease_ok({**claim, 'boot_id': 'other'}, p, 101, 12, 88, INV))
        self.assertFalse(C.lease_ok({**claim, 'run_token': 'other'}, p, 101, 12, 88, INV))

    def test_cleanup_owner_binding_is_distinct_from_expired_runtime_lease(self):
        p = policy()
        intent = {'boot_id': BOOT, 'run_token': p['run_token'], 'module_sha256': p['module_sha256'],
                  'initial_module_absent': True, 'invocation_id': INV}
        self.assertTrue(C.owner_ok(intent, {**p, 'not_after_boottime': 1}, BOOT, INV))
        for key, bad in (('boot_id', 'other'), ('run_token', 'other'), ('module_sha256', 'other'),
                         ('initial_module_absent', False), ('invocation_id', 'other')):
            self.assertFalse(C.owner_ok({**intent, key: bad}, p, BOOT, INV))

    def test_exclusive_durable_records_refuse_overwrite_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(C, 'STATE', Path(tmp)):
            C.record('consumed', {'first': True})
            with self.assertRaises(FileExistsError):
                C.record('consumed', {'second': True})
            self.assertEqual(json.loads((Path(tmp) / 'consumed').read_text()), {'first': True})
            (Path(tmp) / 'symlink').symlink_to(Path(tmp) / 'outside')
            with self.assertRaises(FileExistsError):
                C.record('symlink', {})
            self.assertFalse((Path(tmp) / 'outside').exists())
            with self.assertRaises(RuntimeError):
                C.record('../outside', {})

    def test_snapshot_must_match_native_access_and_capture_ownership_window(self):
        claim = {'created_boottime': 99}
        C.validate_snapshot(snapshot(), 101, claim)
        for f, now in (({**snapshot(), 'access': 'other'}, 101),
                       ({**snapshot(), 'kernel_release': 'other'}, 101),
                       ({**snapshot(), 'capture_boottime_ns': True}, 101),
                       (snapshot(), 104), (snapshot(), 99)):
            with self.assertRaises(RuntimeError):
                C.validate_snapshot(f, now, claim)
        with self.assertRaises(RuntimeError):
            C.validate_snapshot(snapshot(), 101, {'created_boottime': 100.5})

    def test_pid1_unit_is_static_bounded_independently_cleaned_and_sandboxed(self):
        text = (ROOT / 'tools/picasso-pon-audit731-read1.service').read_text()
        for value in ('ConditionKernelVersion=7.3.1-picasso-wifi2',
                      'Requisite=picasso-thermal-policy.service', 'Type=exec',
                      'ExecStopPost=', '--cleanup', 'Restart=no', 'RuntimeMaxSec=20',
                      'TimeoutStopSec=6', 'KillMode=control-group', 'CAP_SYS_MODULE',
                      'CPUAffinity=0 1 2 3', 'ProtectSystem=strict', 'NoNewPrivileges=yes',
                      'DevicePolicy=closed', '@reboot', '@raw-io'):
            self.assertIn(value, text)
        self.assertNotIn('[Install]', text)
        self.assertNotIn('SuccessExitStatus=', text)

    def test_one_load_site_and_no_power_or_force_operations(self):
        text = (ROOT / 'tools/collect-pon731.py').read_text()
        self.assertEqual(text.count("subprocess.Popen(['/usr/bin/insmod'"), 1)
        for bad in ('systemctl reboot', 'systemctl poweroff', 'fastboot', '/dev/mem', '--force'):
            self.assertNotIn(bad, text)
        self.assertIn('START_MC, ABORT_MC = 40000, 45000', text)
        self.assertIn("record('snapshot.json', snapshot)", text)
        self.assertLess(text.index("record('snapshot.json', snapshot)"), text.index('decoder.decode(snapshot)'))


class SyntheticExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        root = Path(self.tmp.name)
        self.state = root / 'state'
        self.state.mkdir()
        assets = root / 'assets'
        assets.mkdir()
        (assets / 'power-pon-reasons.py').write_text((ROOT / 'tools/power-pon-reasons.py').read_text())
        self.node = root / 'mock-sysfs' / 'snapshot'
        self.present = False
        self.insmod_count = self.rmmod_count = 0
        self.load_rc = 0
        self.p = policy()
        original_read = Path.read_text

        def read_text(path, *args, **kwargs):
            if str(path) == '/proc/sys/kernel/random/boot_id':
                return BOOT
            return original_read(path, *args, **kwargs)

        class FakeChild:
            pid = 1234

            def __init__(child, argv, **kwargs):
                self.assertEqual(argv[0], '/usr/bin/insmod')
                self.insmod_count += 1
                child.returncode = self.load_rc
                if not self.load_rc:
                    self.present = True
                    self.node.parent.mkdir()
                    self.node.write_text(json.dumps(snapshot()))

            def poll(child):
                return child.returncode

            def communicate(child):
                return '', ''

        def unload(argv, **kwargs):
            self.assertEqual(argv, ['/usr/bin/rmmod', C.MODULE])
            self.rmmod_count += 1
            self.present = False
            self.node.unlink()
            self.node.parent.rmdir()
            return SimpleNamespace(returncode=0, stdout='', stderr='')

        patches = (patch.object(C, 'STATE', self.state), patch.object(C, 'ASSETS', assets),
                   patch.object(C, 'SNAPSHOT', self.node),
                   patch.object(C, 'root_file'), patch.object(C, 'digest', return_value='1' * 64),
                   patch.object(C, 'boottime', return_value=100),
                   patch.object(C, 'pid_start', side_effect=lambda pid: pid * 10),
                   patch.object(C, 'invocation', return_value=INV),
                   patch.object(C, 'temperatures', return_value={'mock-zone': 35000}),
                   patch.object(C, 'module_present', side_effect=lambda: self.present),
                   patch.object(C.os, 'getpid', return_value=123),
                   patch.object(C.os, 'uname', return_value=SimpleNamespace(release=C.RELEASE)),
                   patch.object(C.gzip, 'decompress', return_value=b'config-fixture'),
                   patch.object(Path, 'read_bytes', return_value=gzip.compress(b'config-fixture')),
                   patch.object(Path, 'read_text', read_text),
                   patch.object(C.subprocess, 'Popen', FakeChild),
                   patch.object(C.subprocess, 'run', side_effect=unload),
                   patch.object(C.sys, 'stdout'))
        for item in patches:
            self.stack.enter_context(item)

    def result(self):
        return json.loads((self.state / 'result.json').read_text())

    def test_success_one_capture_unload_and_independent_noop_cleanup(self):
        self.assertEqual(C.sample(self.p), 0)
        result = self.result()
        self.assertEqual(result['status'], 'sampled_once_readonly')
        self.assertFalse(result['decoded']['root_cause_proven'])
        self.assertTrue(result['cleanup']['snapshot_absent'])
        self.assertEqual((self.insmod_count, self.rmmod_count), (1, 1))
        self.assertTrue(C.cleanup(self.p)['module_unloaded'])
        self.assertEqual(self.rmmod_count, 1)
        self.assertTrue((self.state / 'consumed').exists())
        self.assertTrue((self.state / 'load-intent.json').exists())

    def test_consumed_second_invocation_never_loads_or_replaces_result(self):
        self.assertEqual(C.sample(self.p), 0)
        before = (self.state / 'result.json').read_text()
        self.assertEqual(C.sample(self.p), 1)
        self.assertEqual(self.insmod_count, 1)
        self.assertEqual((self.state / 'result.json').read_text(), before)
        self.assertEqual(len(list(self.state.glob('refusal-*.json'))), 1)

    def test_exact40c_start_refuses_without_consuming_or_loading(self):
        with patch.object(C, 'temperatures', return_value={'mock-zone': 40000}):
            self.assertEqual(C.sample(self.p), 1)
        self.assertEqual(self.insmod_count, 0)
        self.assertFalse((self.state / 'consumed').exists())

    def test_immediate_preload_temperature_recheck_still_requires_below40c(self):
        with patch.object(C, 'temperatures', side_effect=[{'zone': 35000}, {'zone': 40000}, {'zone': 35000}]):
            self.assertEqual(C.sample(self.p), 1)
        self.assertEqual(self.insmod_count, 0)
        self.assertTrue((self.state / 'consumed').exists())

    def test_load_failure_is_consumed_and_never_retried(self):
        self.load_rc = 1
        self.assertEqual(C.sample(self.p), 1)
        self.assertEqual(self.result()['status'], 'failed_no_retry')
        self.assertEqual((self.insmod_count, self.rmmod_count), (1, 0))
        self.assertTrue((self.state / 'consumed').exists())

    def test_exact45c_after_load_aborts_and_unloads_without_read_retry(self):
        with patch.object(C, 'temperatures', side_effect=[{'zone': 35000}, {'zone': 35000},
                                                         {'zone': 45000}, {'zone': 35000}]):
            self.assertEqual(C.sample(self.p), 1)
        self.assertEqual((self.insmod_count, self.rmmod_count), (1, 1))
        self.assertFalse((self.state / 'snapshot.json').exists())
        self.assertTrue(self.result()['cleanup']['module_unloaded'])

    def test_preexisting_unowned_module_never_unloaded(self):
        self.present = True
        self.assertEqual(C.sample(self.p), 1)
        self.assertEqual((self.insmod_count, self.rmmod_count), (0, 0))
        with self.assertRaises(FileNotFoundError):
            C.cleanup(self.p)
        self.assertEqual(self.rmmod_count, 0)

    def test_wrong_boot_or_invocation_refuses_cleanup(self):
        intent = {'boot_id': BOOT, 'run_token': self.p['run_token'], 'module_sha256': self.p['module_sha256'],
                  'initial_module_absent': True, 'invocation_id': 'c' * 32}
        C.record('load-intent.json', intent)
        self.present = True
        with self.assertRaises(RuntimeError):
            C.cleanup(self.p)
        self.assertEqual(self.rmmod_count, 0)

    def test_unloaded_marker_ends_ownership_and_blocks_unrelated_later_module(self):
        self.assertEqual(C.sample(self.p), 0)
        self.present = True
        with self.assertRaises(RuntimeError):
            C.cleanup(self.p)
        self.assertEqual(self.rmmod_count, 1)


if __name__ == '__main__':
    unittest.main()
