import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('wifi_fallback_policy',ROOT/'tools/wifi-fallback-policy.py')
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)


class WifiFallbackPolicyTests(unittest.TestCase):
    def test_exact_authorized_order_and_bands(self):
        self.assertEqual(policy.TARGETS,(('Chaldea','a',20),('Chaldea-2.4G','bg',25)))

    def test_primary_success_never_attempts_fallback(self):
        attempts=[]
        r=policy.attempt_order(lambda s,b,t:attempts.append(s) or True,lambda s:None,lambda s:None)
        self.assertEqual(attempts,['Chaldea']);self.assertFalse(r['fallback_used'])

    def test_primary_normal_failure_then_fallback(self):
        attempts=[];disconnected=[];validated=[]
        def activate(ssid,band,timeout):
            attempts.append(ssid);return ssid=='Chaldea-2.4G'
        r=policy.attempt_order(activate,validated.append,disconnected.append)
        self.assertEqual(attempts,['Chaldea','Chaldea-2.4G'])
        self.assertEqual(disconnected,['Chaldea']);self.assertEqual(validated,['Chaldea-2.4G'])
        self.assertTrue(r['fallback_used'])

    def test_both_fail_no_retry_loop(self):
        attempts=[]
        with self.assertRaises(RuntimeError):
            policy.attempt_order(lambda s,b,t:attempts.append(s) or False,lambda s:None,lambda s:None)
        self.assertEqual(attempts,['Chaldea','Chaldea-2.4G'])

    def test_thermal_dsp_fault_not_a_reason_to_fallback(self):
        attempts=[]
        def activate(s,b,t):
            attempts.append(s);raise RuntimeError('thermal/DSP failure')
        with self.assertRaises(RuntimeError):policy.attempt_order(activate,lambda s:None,lambda s:None)
        self.assertEqual(attempts,['Chaldea'])

    def test_identity_regulatory_failure_is_fatal(self):
        attempts=[]
        def validate(s):raise ValueError('unsafe actual regulatory state')
        with self.assertRaises(ValueError):
            policy.attempt_order(lambda s,b,t:attempts.append(s) or True,validate,lambda s:None)
        self.assertEqual(attempts,['Chaldea'])

    def test_same_passphrase_distinct_ssid_pmks(self):
        values=policy.derive_both('fixture-only-not-a-real-password')
        self.assertEqual(set(values),{'Chaldea','Chaldea-2.4G'})
        self.assertNotEqual(values['Chaldea'],values['Chaldea-2.4G'])
        self.assertTrue(all(len(v)==64 for v in values.values()))

    def test_raw_psk_and_invalid_passphrases_refused(self):
        for value in ('a'*64,'short','password\nunsafe','password\0unsafe','é'*32):
            with self.subTest(value_length=len(value)):
                with self.assertRaises(ValueError):policy.derive_both(value)

    def test_wrapper_pins_ssh_and_cannot_start_radio(self):
        text=(ROOT/'tools/enter-wifi-autoconnect.sh').read_text()
        self.assertIn('StrictHostKeyChecking=yes',text)
        self.assertIn('UserKnownHostsFile=',text)
        self.assertIn('[[ $# == 0 ]]',text)
        self.assertIn('-t 0',text)
        self.assertNotIn('systemctl start',text)

    def test_persistent_entry_is_explicit_and_never_uses_nmcli_secret_api(self):
        text=(ROOT/'tools/enter-wifi-autoconnect.py').read_text()
        self.assertIn('SAVE AND ENABLE',text)
        self.assertIn('getpass.getpass',text)
        self.assertIn('os.O_NOFOLLOW',text)
        self.assertIn('os.O_EXCL',text)
        self.assertIn('os.fsync',text)
        self.assertNotIn('--show-secrets',text)
        self.assertNotIn('systemctl',text)


if __name__=='__main__':unittest.main()
