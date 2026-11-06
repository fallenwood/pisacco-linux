# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('thermal_policy', ROOT / 'tools/thermal-policy.py')
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)


class ThermalPolicyTests(unittest.TestCase):
    def fixture(self, root):
        for cpu in (0, 6, 7):
            cooler = root / f'cooling_device{cpu}'
            cooler.mkdir()
            (cooler / 'type').write_text(f'cpufreq-cpu{cpu}')
            (cooler / 'max_state').write_text('8')
        for cpu in range(8):
            zone = root / f'thermal_zone{cpu}'
            zone.mkdir()
            values = {'type': f'cpu{cpu}-thermal', 'temp': '33000', 'policy': 'step_wise',
                      'mode': 'enabled', 'trip_point_0_type': 'passive', 'trip_point_0_temp': '90000',
                      'trip_point_0_hyst': '2000', 'trip_point_1_type': 'critical',
                      'trip_point_1_temp': '110000', 'trip_point_1_hyst': '1000'}
            for name, value in values.items():
                (zone / name).write_text(value)
            (zone / 'cdev0').symlink_to(root / f'cooling_device{0 if cpu < 6 else cpu}')
            (zone / 'cdev0_trip_point').write_text('0')
            (zone / 'cdev0_weight').write_text('0')

    def test_all_passive_trips_lowered_critical_and_governor_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            original = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            result = T.apply(root)
            self.assertEqual(result['status'], 'early_passive_cooling_applied')
            for path, old in original.items():
                self.assertEqual(path.read_bytes(), b'40000' if path.name == 'trip_point_0_temp' else old)
            self.assertEqual(len(result['zones_written']), 8)
            self.assertEqual(T.apply(root)['zones_written'], [])

    def test_invalid_topology_trip_or_cooler_refuses_before_any_write(self):
        for field, bad in (('type', 'unexpected'), ('trip_point_1_temp', '120000'),
                           ('trip_point_0_temp', '80000'), ('trip_point_0_hyst', '0'),
                           ('policy', 'user_space'), ('mode', 'disabled'), ('temp', '150001')):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.fixture(root)
                (root / 'thermal_zone7' / field).write_text(bad)
                with patch.object(Path, 'write_text') as write, self.assertRaises(RuntimeError):
                    T.apply(root)
                write.assert_not_called()

    def test_missing_or_duplicate_sensor_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            (root / 'thermal_zone7' / 'type').write_text('cpu0-thermal')
            with self.assertRaises(RuntimeError):
                T.inspect(root)

    def test_wrong_or_missing_cpu_cooling_map_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            (root / 'cooling_device7' / 'type').write_text('cpufreq-cpu0')
            with self.assertRaises(RuntimeError):
                T.inspect(root)

    def test_partial_failure_is_not_hidden_by_upward_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            original = Path.write_text
            def write(path, value, *args, **kwargs):
                if path.parent.name == 'thermal_zone3' and path.name == 'trip_point_0_temp':
                    raise OSError('injected sysfs refusal')
                return original(path, value, *args, **kwargs)
            with patch.object(Path, 'write_text', write), self.assertRaises(OSError):
                T.apply(root)
            self.assertEqual((root / 'thermal_zone0/trip_point_0_temp').read_text(), '40000')
            self.assertEqual((root / 'thermal_zone3/trip_point_0_temp').read_text(), '90000')
            self.assertEqual((root / 'thermal_zone0/trip_point_1_temp').read_text(), '110000')

    def test_unit_is_early_bounded_and_does_not_poweroff_or_restart(self):
        unit = (ROOT / 'tools/picasso-thermal-policy.service').read_text()
        for marker in ('ConditionKernelVersion=7.3.1-picasso-wifi2', 'Before=picasso-wifi',
                       'Type=oneshot', 'Restart=no', 'TimeoutStartSec=15s', 'ProtectSystem=strict'):
            self.assertIn(marker, unit)
        code = (ROOT / 'tools/thermal-policy.py').read_text()
        for forbidden in ('systemctl poweroff', 'thermal_zone*/mode', '/dev/mem'):
            self.assertNotIn(forbidden, code)


if __name__ == '__main__':
    unittest.main()
