import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
O=mod('power_observer',ROOT/'tools/power-key-service.py')
C=mod('power_cooldown',ROOT/'tools/power-observe-current.py')


class PowerCooldownTests(unittest.TestCase):
 def test_all_sensors_strictly_below40_no_threshold_increase(self):
  self.assertTrue(C.ready({'a':39999,'b':36000}));self.assertFalse(C.ready({'a':40000,'b':35000}));self.assertFalse(C.ready({'a':45000}));self.assertFalse(C.ready({}));self.assertFalse(C.ready({'a':-20000}))
 def test_refused_temperature_saved_without_consuming_observer(self):
  with tempfile.TemporaryDirectory() as d:
   run=Path(d)
   with patch.object(O,'main',side_effect=O.TemperaturePreflightError({'zone0':40500})),patch.object(O,'Path',return_value=run):self.assertEqual(O.entry(),1)
   self.assertFalse((run/'observer-consumed').exists());records=list(run.glob('startup-refusal-*.json'));self.assertEqual(len(records),1)
   data=json.loads(records[0].read_text());self.assertEqual(data['temperatures_at_guard_mc'],{'zone0':40500});self.assertFalse(data['shutdown_requested']);self.assertFalse(data['observer_slot_consumed'])
 def test_each_refusal_is_retained_and_no_original_result_rewritten(self):
  with tempfile.TemporaryDirectory() as d:
   run=Path(d);original='{"status":"historical"}\n';(run/'result.json').write_text(original)
   with patch.object(O,'main',side_effect=O.TemperaturePreflightError({'zone0':40000})),patch.object(O,'Path',return_value=run):
    O.entry();O.entry()
   self.assertEqual(len(list(run.glob('startup-refusal-*.json'))),2);self.assertEqual((run/'result.json').read_text(),original)
 def test_unhandled_armed_consumed_error_not_falsely_reported_no_shutdown(self):
  with tempfile.TemporaryDirectory() as d:
   run=Path(d);(run/'observer-consumed').touch()
   with patch.object(O,'main',side_effect=RuntimeError('test ambiguous exit')),patch.object(O,'Path',return_value=run):O.entry(True)
   data=json.loads((run/'startup-last.json').read_text());self.assertTrue(data['observer_slot_consumed']);self.assertIsNone(data['shutdown_requested'])
 def test_existing_boot_only_disarmed_exec_and_bounded_cooldown(self):
  text=(ROOT/'tools/power-observe-current.py').read_text()
  self.assertIn('time.monotonic()+120',text);self.assertIn('stable>=3',text);self.assertIn('max(values.values())<45000',text)
  self.assertIn("['/usr/bin/python3','-I',str(BASE/'power-key-service.py')]",text)
  for x in ('--arm-orderly-poweroff','systemctl reboot','fastboot boot','reset-failed','unlink('):self.assertNotIn(x,text)
 def test_local_continue_only_and_preserves_every_attempt(self):
  text=(ROOT/'tools/observe-power-key.sh').read_text()
  self.assertIn('StrictHostKeyChecking=yes',text);self.assertIn('power-observe-current.py',text);self.assertIn('observer-current-$STAMP.json',text)
  for x in ('systemctl reboot','fastboot boot','--arm-orderly-poweroff','observer-local-result.json'):self.assertNotIn(x,text)


if __name__=='__main__':unittest.main()
