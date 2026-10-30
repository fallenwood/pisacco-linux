# SPDX-License-Identifier: GPL-2.0-only
import importlib.util,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'tools/audit-wifi-regulatory.py'
s=importlib.util.spec_from_file_location('reg_check',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
REF='''global
country SG: DFS-FCC
 (2400 - 2483 @ 40), (N/A, 23), (N/A)
 (5150 - 5250 @ 80), (N/A, 23), (N/A), AUTO-BW
 (5250 - 5350 @ 80), (N/A, 20), (0 ms), DFS, AUTO-BW
 (5470 - 5730 @ 160), (N/A, 26), (0 ms), DFS
 (5725 - 5850 @ 80), (N/A, 30), (N/A)
'''
class Regulatory(unittest.TestCase):
 def test_stricter_intersection_with_sg(self):
  r=m.audit(REF,'global\ncountry 98: DFS-FCC','* 2412 MHz [1] (23.0 dBm)\n* 5500 MHz [100] (24.0 dBm) (radar detection)')
  self.assertEqual(r['enabled_20mhz_channels_verified'],2)
 def test_decimal_iw_frequencies_are_actually_audited(self):
  self.assertEqual(m.audit(REF,REF,'* 2412.0 MHz [1] (23.0 dBm)')['enabled_20mhz_channels_verified'],1)
  with self.assertRaisesRegex(ValueError,'exceeds observed SG'):
   m.audit(REF,REF,'* 2412.0 MHz [1] (30.0 dBm)')
 def test_out_of_country_frequency_or_power_rejected(self):
  for line in ('* 2484 MHz [14] (20.0 dBm)','* 2412 MHz [1] (30.0 dBm)','* 5865 MHz [173] (23.0 dBm)'):
   with self.assertRaises(ValueError):m.audit(REF,REF,line)
 def test_dfs_must_be_retained(self):
  with self.assertRaises(ValueError):m.audit(REF,REF,'* 5500 MHz [100] (24.0 dBm)')
 def test_unknown_domain_empty_phy_or_non_sg_reference_rejected(self):
  for ref,eff,phy in ((REF,'global\ncountry US:','* 2412 MHz [1] (20.0 dBm)'),(REF,REF,''),(REF.replace('SG','US'),REF,'* 2412 MHz [1] (20.0 dBm)')):
   with self.assertRaises(ValueError):m.audit(ref,eff,phy)
 def test_ap_cn_country_ie_is_not_user_sg_even_on_valid_current_channel(self):
  # Actual post-association regression: a permitted current frequency is not
  # permission to accept the AP's foreign global domain for the entire PHY.
  with self.assertRaisesRegex(ValueError,'Neither SG'):
   m.audit(REF,'global\ncountry CN: DFS-FCC','* 2447.0 MHz [8] (20.0 dBm)')
 def test_kernel_intersection_label_still_requires_actual_limits(self):
  effective='global\ncountry 98: DFS-FCC'
  good=m.audit(REF,effective,'* 2447.0 MHz [8] (20.0 dBm)')
  self.assertEqual(good['effective_global_domain'],'98-intersection')
  for bad in ('* 2447.0 MHz [8] (30.0 dBm)','* 5745.0 MHz [149] (33.0 dBm)','* 5500.0 MHz [100] (20.0 dBm)'):
   with self.assertRaises(ValueError):m.audit(REF,effective,bad)
if __name__=='__main__':unittest.main()
