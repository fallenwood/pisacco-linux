# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class TrialGuards(unittest.TestCase):
    def test_fixed_msa_defaults_to_explicit_readonly_opt_in(self):
        p=(ROOT/'src/linux-6.18.58/drivers/net/wireless/ath/ath10k/qmi.c')
        if not p.exists():self.skipTest('prepared kernel source not present')
        s=p.read_text();self.assertIn('static bool picasso_fixed_msa;',s)
        self.assertIn('module_param_named(picasso_fixed_msa, picasso_fixed_msa, bool, 0400)',s)
    def test_fixed_msa_checks_actual_resource_not_fallback_hint(self):
        p=ROOT/'src/linux-6.18.58/drivers/net/wireless/ath/ath10k/qmi.c'
        if not p.exists():self.skipTest('prepared kernel source not present')
        s=p.read_text();self.assertIn('of_machine_is_compatible("xiaomi,picasso")',s)
        self.assertIn('ar->msa.paddr != 0x8ba00000 || ar->msa.mem_size != SZ_2M',s)
        self.assertNotIn('msa_size != SZ_2M',s)
    def test_only_exact_shared_char_device_is_allowed(self):
        s=(ROOT/'tools/rmtfs-private-proxy.service.in').read_text()
        allowed=[l for l in s.splitlines() if l.startswith('DeviceAllow=')]
        self.assertEqual(allowed,['DeviceAllow=/dev/qcom_rmtfs_mem1 rw'])
        self.assertIn('DevicePolicy=closed',s);self.assertIn('PrivateDevices=yes',s)
        self.assertIn('DynamicUser=yes',s);self.assertIn('CapabilityBoundingSet=\n',s)
    def test_original_nv_paths_never_passed_to_service(self):
        s=(ROOT/'tools/rmtfs-private-proxy.service.in').read_text()
        f=[l for l in s.splitlines() if l.startswith('OpenFile=')]
        self.assertEqual(len(f),4)
        self.assertFalse(any('/dev/sd' in l or 'original-' in l or 'by-partlabel' in l for l in f))
    def test_actual_rmtfs_module_is_blacklisted(self):
        s=(ROOT/'tools/picasso-wifi-blacklist.conf').read_text()
        self.assertIn('blacklist rmtfs_mem\n',s)
        self.assertNotIn('blacklist qcom_rmtfs_mem\n',s)
if __name__=='__main__':unittest.main()
