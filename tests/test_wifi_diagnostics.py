# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / 'kernel/diagnostics'


def additions(name):
    return '\n'.join(line[1:] for line in (DIAG / name).read_text().splitlines()
                     if line.startswith('+') and not line.startswith('+++'))


class DiagnosticGuards(unittest.TestCase):
    def test_not_in_normal_patch_series(self):
        series = (ROOT / 'kernel/patches/series').read_text()
        self.assertNotIn('mgmt-observer', series)
        self.assertNotIn('ht20-only', series)

    def test_observer_explicit_readonly_picasso_snoc_scope(self):
        text = additions('ath10k-picasso-mgmt-observer.patch')
        self.assertIn('static bool picasso_mgmt_status;', text)
        self.assertIn('module_param(picasso_mgmt_status, bool, 0444)', text)
        self.assertIn('ar->hif.bus == ATH10K_BUS_SNOC', text)
        self.assertIn('of_machine_is_compatible("xiaomi,picasso")', text)
        self.assertIn('msdu->len >= 24', text)
        self.assertIn('ieee80211_is_auth', text)
        for forbidden in ('param->status =', 'info->flags', '%pM', 'dbg_dump', 'dma_map'):
            self.assertNotIn(forbidden, text)

    def test_ht20_only_removes_capabilities_not_regulatory_or_power(self):
        text = additions('ath10k-picasso-ht20-only.patch')
        self.assertIn('static bool picasso_ht20_only;', text)
        self.assertIn('module_param(picasso_ht20_only, bool, 0444)', text)
        self.assertIn('ar->hif.bus == ATH10K_BUS_SNOC', text)
        self.assertIn('of_machine_is_compatible("xiaomi,picasso")', text)
        self.assertIn('ht_cap.cap &= ~(', text)
        self.assertIn('IEEE80211_HT_CAP_SUP_WIDTH_20_40', text)
        self.assertIn('memset(&vht_cap, 0, sizeof(vht_cap))', text)
        for forbidden in ('IEEE80211_CHAN_', 'REGULATORY_', 'qcom_scm', 'tx_power', 'tx_chainmask', 'wmi_pdev_set_param'):
            self.assertNotIn(forbidden, text)

    def test_diagnostics_do_not_enable_by_default(self):
        for name in ('ath10k-picasso-mgmt-observer.patch', 'ath10k-picasso-ht20-only.patch'):
            text = additions(name)
            self.assertNotIn('= true', text)
            self.assertNotIn('picasso_fixed_msa', text)


if __name__ == '__main__':
    unittest.main()
