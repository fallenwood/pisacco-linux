import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('power_daemon',ROOT/'tools/power-button-daemon.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D)
s=importlib.util.spec_from_file_location('hold_original',ROOT/'tools/power-hold-policy.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
def event(sec,usec,kind,code,value):return D.EVENT.pack(sec,usec,kind,code,value)


class PowerDaemonTests(unittest.TestCase):
 def test_valid_real_format_policy_release_only(self):
  raw=event(10,0,1,116,1);events,last=D.decode_events(raw,10.1,0);p=P.PowerHoldPolicy();self.assertIsNone(p.key(*events[0]));self.assertFalse(p.requested)
  events,last=D.decode_events(event(12,300000,1,116,0),12.4,last);self.assertEqual(p.key(*events[0]),'orderly_poweroff')
 def test_entire_batch_syn_drop_rejected_before_action(self):
  raw=event(12,300000,1,116,0)+event(12,300001,0,3,0)
  with self.assertRaises(RuntimeError):D.decode_events(raw,12.4,10)
 def test_wrong_code_value_stale_and_nonmonotonic_rejected(self):
  for args,now,last in [((12,0,1,115,1),12.1,0),((12,0,1,116,9),12.1,0),((12,0,1,116,0),15,0),((12,0,1,116,0),12.1,13),((12,1000000,1,116,0),13,0)]:
   with self.assertRaises(RuntimeError):D.decode_events(event(*args),now,last)
 def test_repeat_and_duplicate_do_not_move_hold_start(self):
  p=P.PowerHoldPolicy();p.key(116,1,10);p.key(116,1,11);p.key(116,2,12);self.assertEqual(p.key(116,0,12.3),'orderly_poweroff')
 def test_short_overlong_unmatched_release_ignored(self):
  for duration in (1.682461,4.559807):
   p=P.PowerHoldPolicy();p.key(116,1,10);self.assertIsNone(p.key(116,0,10+duration))
  self.assertIsNone(P.PowerHoldPolicy().key(116,0,10))
 def test_request_records_exclusive_and_acceptance_distinct(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'boot.intent.json';D.write_json(p,{'shutdown_requested':None},True)
   with self.assertRaises(FileExistsError):D.write_json(p,{'shutdown_requested':True},True)
   self.assertIsNone(json.loads(p.read_text())['shutdown_requested'])
 def test_hardened_unit_no_restart_exact_devices_and_notify(self):
  text=(ROOT/'tools/picasso-power-button.service').read_text()
  for x in ('Type=notify','WatchdogSec=8s','Restart=no','CapabilityBoundingSet=','@reboot','@module','DeviceAllow=/dev/input/event0 r','DeviceAllow=/dev/input/event1 r'):
   self.assertIn(x,text)
  self.assertNotIn('/dev/input/event2',text)
 def test_input_enumeration_wait_is_bounded_and_still_rechecks_start_temp(self):
  text=(ROOT/'tools/power-button-daemon.py').read_text();self.assertIn('input_deadline=time.monotonic()+15',text);self.assertIn("len(nodes)<=1",text)
  self.assertLess(text.index('15s power-input enumeration deadline'),text.index('Start below40C at readiness'))
 def test_daemon_preserves_known_limit_no_trial_replay_or_suspend(self):
  text=(ROOT/'tools/power-button-daemon.py').read_text()
  for x in ('usb_autostart_accepted_not_fixed','--check-files',"<40000,'Start below40C at readiness'",'<45000',"boot+'.intent.json'",'120s start-temperature refusal'):
   self.assertIn(x,text)
  for x in ('observer-consumed','systemctl suspend','/dev/mem','fastboot','reset-failed'):
   self.assertNotIn(x,text)


if __name__=='__main__':unittest.main()
