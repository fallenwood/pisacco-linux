import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COOL = load('wait-for-cool')
AUTO = load('wifi-autoconnect-cn-service')
POLICY = load('wifi-fallback-policy')


class CooldownTests(unittest.TestCase):
    def test_hot_sample_resets_three_consecutive_cool_samples(self):
        samples = iter((64999, 64999, 65000, 64999, 64999, 64999))
        with patch.object(COOL, 'temperatures', side_effect=lambda: {'cpu': next(samples)}), \
                patch.object(COOL.time, 'sleep') as sleep:
            COOL.wait_for_cool()
        self.assertEqual(sleep.call_count, 5)

    def test_65C_startup_limit_allows_warm_but_below_limit_samples(self):
        self.assertEqual(COOL.STARTUP_LIMIT_MC, 65000)
        with patch.object(COOL, 'temperatures', return_value={'cpu': 60000}), \
                patch.object(COOL.time, 'sleep') as sleep:
            COOL.wait_for_cool()
        self.assertEqual(sleep.call_count, 2)

    def test_hot_boot_times_out_instead_of_arming_hardware(self):
        with patch.object(COOL, 'temperatures', return_value={'cpu': 65000}), \
                patch.object(COOL.time, 'monotonic', side_effect=(0, 0, 300)), \
                patch.object(COOL.time, 'sleep'):
            with self.assertRaises(TimeoutError):
                COOL.wait_for_cool()

    def test_invalid_or_missing_telemetry_is_not_a_cool_sample(self):
        for readings in ([], [SimpleNamespace(parent=SimpleNamespace(name='cpu'),
                                             read_text=lambda: '150001')]):
            with patch.object(Path, 'glob', return_value=readings):
                with self.assertRaises(RuntimeError):
                    COOL.temperatures()


class BootAutoconnectTests(unittest.TestCase):
    def controller(self, primary_success=False, validation_error=False):
        calls = []

        class Base:
            def __init__(self):
                self.record = {}
                self.rules = POLICY

            def startup(self):
                calls.append('guarded_startup')

            def activate(self, ssid, band, seconds):
                calls.append(('activate', ssid, band, seconds))
                return primary_success or ssid == 'Chaldea-2.4G'

            def disconnect(self, ssid):
                calls.append(('disconnect', ssid))

            def validate(self, ssid):
                calls.append(('validate', ssid))
                if validation_error:
                    raise RuntimeError('CN regulatory/thermal validation failure')

            def save(self):
                pass

            def radio_monitor(self):
                calls.append('guarded_monitor')

        adapter = SimpleNamespace(service_type=lambda *parts: Base)
        return AUTO.service_type(adapter, ())(), calls, Base

    def test_guarded_startup_then_primary_timeout_then_validated_fallback(self):
        controller, calls, _ = self.controller()
        controller.startup()
        self.assertEqual(calls, [
            'guarded_startup', ('activate', 'Chaldea', 'a', 20),
            ('disconnect', 'Chaldea'), ('activate', 'Chaldea-2.4G', 'bg', 25),
            ('validate', 'Chaldea-2.4G'),
        ])
        self.assertTrue(controller.record['boot_autoconnect_completed'])
        self.assertEqual(controller.record['ssid'], 'Chaldea-2.4G')

    def test_primary_success_does_not_attempt_fallback(self):
        controller, calls, _ = self.controller(primary_success=True)
        controller.startup()
        self.assertEqual(controller.record['attempt_order'], ['Chaldea'])
        self.assertNotIn(('activate', 'Chaldea-2.4G', 'bg', 25), calls)

    def test_safety_validation_error_is_not_a_reason_to_try_fallback(self):
        controller, calls, _ = self.controller(primary_success=True, validation_error=True)
        with self.assertRaises(RuntimeError):
            controller.startup()
        self.assertNotIn('boot_autoconnect_completed', controller.record)
        self.assertNotIn(('activate', 'Chaldea-2.4G', 'bg', 25), calls)

    def test_idle_monitor_does_not_start_another_connection_or_radio(self):
        controller, calls, base = self.controller()
        controller.radio_monitor()
        self.assertEqual(calls, ['guarded_monitor'])
        self.assertFalse(controller.record['automatic_reconnection_enabled'])
        for method in ('activate', 'validate', 'disconnect'):
            self.assertIs(getattr(type(controller), method), getattr(base, method))

    def test_exact_raw_CN_parent_is_unchanged(self):
        self.assertEqual(
            hashlib.sha256((ROOT / 'tools/wifi-cn-raw-radio-service.py').read_bytes()).hexdigest(),
            AUTO.SOURCE_SHA,
        )


if __name__ == '__main__':
    unittest.main()
