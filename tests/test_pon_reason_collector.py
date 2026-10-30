import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('pon_collector',ROOT/'tools/collect-pon-reason.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)


class PonCollectorTests(unittest.TestCase):
 def test_cleanup_owner_requires_same_boot_pinned_module_initial_absent(self):
  v={'boot_id':C.BOOT,'module_sha256':C.MODULE_SHA,'initial_module_absent':True}
  self.assertTrue(C.owner_ok(v,C.BOOT));self.assertFalse(C.owner_ok(v,'other'))
  v['initial_module_absent']=False;self.assertFalse(C.owner_ok(v,C.BOOT))
 def test_exclusive_records_cannot_replace_consumed_or_results(self):
  with tempfile.TemporaryDirectory() as d:
   with patch.object(C,'STATE',Path(d)):
    C.record('consumed',{'attempt':1})
    with self.assertRaises(FileExistsError):C.record('consumed',{'attempt':2})
    self.assertEqual(json.loads((Path(d)/'consumed').read_text()),{'attempt':1})
 def test_pid1_independent_cleanup_bounded_no_auto_enable(self):
  text=(ROOT/'tools/picasso-pon-reason-read1.service').read_text()
  for x in ('ExecStopPost=','--cleanup','RuntimeMaxSec=20','TimeoutStopSec=6','Restart=no','CAP_SYS_MODULE','NoNewPrivileges=yes','@reboot','CPUAffinity=0 1 2 3'):
   self.assertIn(x,text)
  self.assertNotIn('[Install]',text)
 def test_thermal_limits_single_load_and_no_power_or_writes(self):
  text=(ROOT/'tools/collect-pon-reason.py').read_text()
  self.assertIn("<40000,'Start below40C'",text);self.assertIn("<45000,'45C thermal abort'",text)
  self.assertEqual(text.count("subprocess.Popen(['/usr/bin/insmod'"),1)
  for x in ('systemctl poweroff','systemctl reboot','fastboot','/dev/mem','--force'):
   self.assertNotIn(x,text)
 def test_collector_assets_match_prepared_sampler_and_decoder(self):
  import hashlib
  self.assertEqual(hashlib.sha256((ROOT/'kernel/power/picasso-pon-reason-audit.ko').read_bytes()).hexdigest(),C.MODULE_SHA)
  self.assertEqual(hashlib.sha256((ROOT/'tools/power-pon-reasons.py').read_bytes()).hexdigest(),C.DECODER_SHA)


if __name__=='__main__':unittest.main()
