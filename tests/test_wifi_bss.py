import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('wifi_bss', Path(__file__).resolve().parents[1] / 'tools/wifi-bss.py')
bss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bss)


class WifiBssTests(unittest.TestCase):
    def test_internal_headings_do_not_split_record(self):
        text = ('BSS 00:11:22:33:44:55(on wlan0)\n\tSSID: Chaldea\n'
                '\tBSS Load:\n\t\tstation count: 2\n'
                '\tHT operation:\n\tVHT operation:\n'
                '\tOverlapping BSS scan params:\n\t\tinterval: 300\n')
        self.assertEqual(len(bss.bss_records(text)), 1)
        self.assertIn('VHT operation:', bss.target_bss_records(text, 'Chaldea')[0])
        self.assertIn('interval: 300', bss.target_bss_records(text, 'Chaldea')[0])

    def test_only_exact_authorized_ssid_retained(self):
        text = ('BSS aa:aa:aa:aa:aa:aa(on wlan0)\n\tSSID: ChaldeaGuest\n'
                'BSS 00:11:22:33:44:55(on wlan0)\n\tSSID: Chaldea\n\tBSS Load:\n'
                'BSS bb:bb:bb:bb:bb:bb(on wlan0)\n\tSSID: Other\n')
        records = bss.target_bss_records(text, 'Chaldea')
        self.assertEqual(len(records), 1)
        self.assertNotIn('ChaldeaGuest', records[0])
        self.assertNotIn('Other', records[0])
        self.assertEqual(len(bss.bss_records(text)), 3)

    def test_multiple_target_bands_and_decimal_frequencies_preserved(self):
        text = ('BSS 00:11:22:33:44:55(on wlan0)\n\tfreq: 2412.0\n\tSSID: Chaldea\n'
                'BSS 00:11:22:33:44:56(on wlan0)\n\tfreq: 5240.0\n\tSSID: Chaldea\n')
        self.assertEqual(len(bss.target_bss_records(text, 'Chaldea')), 2)

    def test_active_discovery_uses_allowed_band_not_one_old_channel(self):
        phy='* 2412.0 MHz [1] (23.0 dBm)\n* 2447.0 MHz [8] (23.0 dBm)\n* 2462 MHz [11] (23.0 dBm)'
        self.assertEqual(bss.active_2g_frequencies(phy), [2412,2447,2462])

    def test_active_discovery_never_enables_disabled_or_no_ir_channels(self):
        phy='* 2412 MHz [1] (23.0 dBm)\n* 2447 MHz [8] (disabled)\n* 2462 MHz [11] (23.0 dBm) (no IR)\n* 2484 MHz [14] (20.0 dBm)\n* 5240 MHz [48] (23.0 dBm)'
        self.assertEqual(bss.active_2g_frequencies(phy), [2412])
        with self.assertRaises(ValueError):
            bss.active_2g_frequencies('* 2447 MHz [8] (20.0 dBm) (no IR)')

    def test_active_discovery_rejects_empty_or_nonchannel_frequency(self):
        for phy in ('', '* 2447.5 MHz [8] (23.0 dBm)', '* 2448 MHz [8] (23.0 dBm)'):
            with self.assertRaises(ValueError):
                bss.active_2g_frequencies(phy)

    def test_empty_scan_and_invalid_selectors(self):
        self.assertEqual(bss.bss_records('scan completed\n'), [])
        for selector in ('', 'Chaldea\nSSID: Other', 'Chaldea\r', 'Chaldea\0'):
            with self.assertRaises(ValueError):
                bss.target_bss_records('', selector)


if __name__ == '__main__':
    unittest.main()
