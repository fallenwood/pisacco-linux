import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('wifi_loss_evidence',ROOT/'tools/wifi-loss-evidence.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def row(t,message):return {'__MONOTONIC_TIMESTAMP':str(int(t*1e6)),'MESSAGE':message}


def fixture(early_probe=False):
    p='ath10k: Picasso link observation: '
    kernel=[row(9.8,p+'key_wait_done cmd 0 completed 1'),row(9.9,p+'key_wait_done cmd 0 completed 1'),
            row(24,p+'roam vdev 0 reason 2'),row(24.01,p+'beacon_miss vdev 0 own_beacons 2 scan_state 0 beacon_age_ms 6100 pre_filter 2 errors 0'),
            row(27,p+'loss_work vdev 0 is_up 1 own_beacons 2'),row(24.6 if early_probe else 27.1,p+'key_begin cmd 1 vdev 0 flags 0'),
            row(27.7 if early_probe else 30.2,p+'key_wait_done cmd 1 completed 0')]
    supplicant=[row(10,'wlan0: CTRL-EVENT-CONNECTED - fixture'),row(24.02,'wlan0: CTRL-EVENT-BEACON-LOSS'),
                row(31,'wlan0: CTRL-EVENT-DISCONNECTED reason=4 locally_generated=1')]
    return kernel,supplicant


class LossEvidenceTests(unittest.TestCase):
    def test_driver_delayed_loss_before_teardown(self):
        r=m.analyze(*fixture())
        self.assertTrue(r['firmware_beacon_miss_loss_work_delete_timeout_chain_verified'])
        self.assertFalse(r['teardown_started_before_driver_delayed_loss_work'])
        self.assertTrue(r['key_timeout_is_disable_key_not_initial_install'])
        self.assertEqual(r['initial_set_key_completions_before_connected'],2)
        self.assertEqual(r['beacon_miss_metadata']['errors'],0)
        self.assertFalse(r['sole_lower_layer_cause_proven'])

    def test_probe_failure_can_teardown_before_delayed_driver_work(self):
        r=m.analyze(*fixture(True))
        self.assertTrue(r['firmware_beacon_miss_loss_work_delete_timeout_chain_verified'])
        self.assertTrue(r['teardown_started_before_driver_delayed_loss_work'])

    def test_missing_beacon_event_does_not_invent_chain(self):
        k,s=fixture();s=[r for r in s if 'BEACON-LOSS' not in r['MESSAGE']]
        self.assertFalse(m.analyze(k,s)['firmware_beacon_miss_loss_work_delete_timeout_chain_verified'])

    def test_earlier_set_timeout_not_misclassified_as_teardown_only(self):
        k,s=fixture();k.append(row(20,'Picasso link observation: key_wait_done cmd 0 completed 0'))
        r=m.analyze(k,s)
        self.assertFalse(r['firmware_beacon_miss_loss_work_delete_timeout_chain_verified'])
        self.assertFalse(r['key_timeout_is_disable_key_not_initial_install'])

    def test_scan_events_counted_only_while_connected(self):
        k,s=fixture();k.extend([row(9,'Picasso link observation: scan type 2 reason 0'),row(22,'Picasso link observation: scan type 1 reason 7'),row(32,'Picasso link observation: scan type 1 reason 7')])
        self.assertEqual(m.analyze(k,s)['scan_events_during_connected_interval'],1)

    def test_no_disconnect_cannot_claim_loss(self):
        k,s=fixture()
        with self.assertRaises(ValueError):m.analyze(k,s[:-1])

    def test_observer_default_off_readonly_and_board_bus_guard(self):
        text=(ROOT/'kernel/diagnostics/ath10k-picasso-link-observer.patch').read_text()
        self.assertIn('module_param(picasso_link_observe, bool, 0444)',text)
        self.assertIn('ATH10K_BUS_SNOC',text);self.assertIn('xiaomi,picasso',text)
        added='\n'.join(l[1:] for l in text.splitlines() if l.startswith('+') and not l.startswith('+++'))
        self.assertNotIn('%pM',added);self.assertNotIn('key->key',added)
        self.assertNotIn('ATH10K_CONNECTION_LOSS_HZ',added)
        self.assertNotIn('ieee80211_beacon_loss',added)
        self.assertNotIn('ieee80211_connection_loss',added)
        self.assertNotIn('complete(&ar->install_key_done)',added)

    def test_diagnostic_never_overwrites_default_config_or_reads_password(self):
        text=(ROOT/'tools/diagnose-wifi-link.py').read_text()
        self.assertIn('copy.deepcopy(self.cfg)',text)
        self.assertIn("not 1<=args.seconds<=90",text)
        self.assertNotIn('passwd',text)
        self.assertNotIn('config.json\').write',text)


if __name__=='__main__':unittest.main()
