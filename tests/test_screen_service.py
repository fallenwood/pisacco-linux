import importlib.util
from pathlib import Path
import re
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=module('volume_policy',ROOT/'tools/screen-volume-policy.py')
S=module('screen_service',ROOT/'tools/screen-service.py')


class PersistentScreenTests(unittest.TestCase):
 def test_exact_fifteen_second_idle_no_loop_or_automatic_wake(self):
  p=P.VolumePolicy(10);self.assertIsNone(p.tick(24.99));self.assertEqual(p.tick(25),'off');self.assertIsNone(p.tick(1000));self.assertFalse(p.on)
 def test_only_real_volume_up_press_wakes_and_release_rearms(self):
  p=P.VolumePolicy();p.tick(15)
  for code in (114,116,1):self.assertIsNone(p.key(code,1,16))
  self.assertFalse(p.on);self.assertEqual(p.key(115,1,17),'on');self.assertEqual(p.deadline,32)
  self.assertIsNone(p.key(115,1,20));self.assertIsNone(p.key(115,2,20));self.assertEqual(p.deadline,32)
  p.key(115,0,20);p.key(115,1,21);self.assertEqual(p.deadline,36)
 def test_initially_held_key_does_not_count_as_new_press(self):
  p=P.VolumePolicy(0,True);p.tick(15);self.assertIsNone(p.key(115,1,16));self.assertFalse(p.on)
  p.key(115,0,16);self.assertEqual(p.key(115,1,17),'on')
 def test_kernel_default_off_fixed_lease_parent_pid_object_not_number(self):
  t=(ROOT/'kernel/display/picasso-wled-service.c').read_text()
  for text in ('#define LEASE_MS    3000','#define CHECK_MS    250','task_tgid(current) != lease_owner','get_task_pid(rcu_dereference(current->real_parent), PIDTYPE_TGID)','props.brightness = 0','put_pid(lease_owner)','static DEVICE_ATTR_WO(lease)'):
   self.assertIn(text,t)
  self.assertNotIn('duration_seconds',t);self.assertNotIn('owner_pid,',t)
 def test_only_gate_brightness_and_sync_writes(self):
  t=(ROOT/'kernel/display/picasso-wled-service.c').read_text();calls=re.findall(r'regmap_(?:bulk_write|update_bits)\(map,\s*(\w+)',t)
  self.assertEqual(set(calls),{'CTRL_ENABLE','MOD_BRIGHT','MOD_SYNC'})
  self.assertIn('zero writes on an unaudited configuration',t);self.assertIn('ret = -ETIMEDOUT',t)
 def test_worker_stops_rearming_after_expiry_and_exit_cancels(self):
  t=(ROOT/'kernel/display/picasso-wled-service.c').read_text()
  self.assertIn('again = !expired;',t);self.assertIn('cancel_delayed_work_sync(&expiry_work)',t)
  self.assertIn('time_after_eq(jiffies, expires)',t)
 def test_no_suspend_or_raw_io_program_paths(self):
  t=(ROOT/'tools/screen-service.py').read_text()
  for forbidden in ('/sys/power/state','/dev/mem','systemctl suspend','systemctl reboot','os.pread','uinput'):
   self.assertNotIn(forbidden,t)
  self.assertIn("console.screen_on(tick,brightness)",t)
  self.assertNotIn('visual-render.py',t);self.assertNotIn('pattern_row',t)
  self.assertIn("os.open('/dev/fb0',os.O_RDONLY|os.O_NOFOLLOW)",t)
  self.assertIn("bitmap==1<<115",t);self.assertIn("node.name in ('event0','event1')",t)
 def test_service_no_automatic_restart_bounded_watchdog_and_exact_devices(self):
  t=(ROOT/'tools/picasso-screen.service').read_text()
  for text in ('Restart=no','WatchdogSec=8s','DevicePolicy=closed','DeviceAllow=/dev/fb0 r','DeviceAllow=/dev/input/event0 r','DeviceAllow=/dev/tty1 r','Requires=getty@tty1.service','CapabilityBoundingSet=CAP_SYS_MODULE','WantedBy=multi-user.target','InaccessiblePaths=-/sys/power/state'):
   self.assertIn(text,t)
  self.assertNotIn('char-input',t);self.assertNotIn('/dev/mem',t)
 def test_explicit_65C_runtime_and_startup_limits_fail_at_the_boundary(self):
  self.assertEqual(S.STARTUP_LIMIT_MC,65000);self.assertEqual(S.RUNTIME_ABORT_MC,65000)
  for limit in (S.STARTUP_LIMIT_MC,S.RUNTIME_ABORT_MC):
   for value in (40000,45000,60000,64999):self.assertTrue(S.below_temperature_limit({'cpu':value},limit))
   for value in (65000,65001,110000):self.assertFalse(S.below_temperature_limit({'cool_cpu':30000,'hot_cpu':value},limit))
   for invalid in ({},{'cpu':-10001},{'cpu':150001},{'cpu':True}):
    with self.assertRaises(RuntimeError):S.below_temperature_limit(invalid,limit)
  t=(ROOT/'tools/screen-service.py').read_text();self.assertIn('below_temperature_limit(values,RUNTIME_ABORT_MC)',t);self.assertIn('below_temperature_limit(temperatures(),STARTUP_LIMIT_MC)',t)
 def test_unapproved_brightness_rejected_without_writing(self):
  with self.assertRaises(RuntimeError):S.brightness(65)
 def test_missing_thermal_sensors_fail_closed(self):
  class Empty:
   def glob(self,x):return []
  with patch.object(S,'Path',return_value=Empty()):
   with self.assertRaises(RuntimeError):S.temperatures()


if __name__=='__main__':unittest.main()
