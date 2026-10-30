import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
O=mod('durable_power_core',ROOT/'tools/power-key-service.py')
A=mod('armed_power_wrapper',ROOT/'tools/power-shutdown-current.py')


class PowerShutdownTests(unittest.TestCase):
 def test_requires_same_boot_disarmed_observation_before_arming(self):
  accept={'status':'passed_real_power_hold_release_detection_disarmed_only','boot_id':'boot1','armed':False,'shutdown_requested':False}
  result={'armed_orderly_poweroff':False,'shutdown_requested':False,'events':[{'policy_action':'orderly_poweroff'}]}
  self.assertTrue(A.valid_observation(accept,result,'boot1'));self.assertFalse(A.valid_observation(accept,result,'boot2'))
  result['shutdown_requested']=True;self.assertFalse(A.valid_observation(accept,result,'boot1'))
 def test_disarmed_path_never_writes_shutdown_durable_record(self):
  with patch.object(O,'Path') as p:O.persist_armed_trial({'armed_orderly_poweroff':False});p.assert_not_called()
 def test_armed_intent_preserves_explicit_not_yet_requested_flag(self):
  with tempfile.TemporaryDirectory() as d:
   real=Path;root=real(d);boot=root/'boot_id';boot.write_text('testboot\n')
   def path(value):return boot if str(value)=='/proc/sys/kernel/random/boot_id' else root/'state'
   data={'armed_orderly_poweroff':True,'shutdown_requested':False,'poweroff_request_stage':'intent_before_pid1_request','events':[{'code':116,'value':0}]}
   with patch.object(O,'Path',side_effect=path):O.persist_armed_trial(data)
   saved=json.loads((root/'state/testboot.json').read_text());self.assertFalse(saved['shutdown_requested']);self.assertEqual(saved['poweroff_request_stage'],'intent_before_pid1_request')
 def test_durable_release_and_intent_precede_standard_pid1_request(self):
  text=(ROOT/'tools/power-key-service.py').read_text()
  intent=text.index("result['poweroff_request_stage']='intent_before_pid1_request';persist_armed_trial(result)")
  action=text.index("subprocess.run(['systemctl','poweroff','--no-block']")
  self.assertLess(intent,action);self.assertIn('pid1_accepted_not_physical_poweroff_proof',text)
 def test_armed_wrapper_requires_explicit_flag_but_only_execs_key_waiter(self):
  text=(ROOT/'tools/power-shutdown-current.py').read_text()
  for x in ('--confirmed-local-shutdown-test','observations-20261028',"not Path('/run/picasso-power-armed/observer-consumed').exists()",'--arm-orderly-poweroff','max(temps.values())<40000','max(temps.values())<45000'):
   self.assertIn(x,text)
  self.assertNotIn("['systemctl','poweroff'",text)
 def test_cancel_targets_only_recorded_pid_and_checks_pid_reuse(self):
  text=(ROOT/'tools/power-shutdown-cancel.py').read_text()
  for x in ('process_start_ticks',"r['boot_id']!=boot",'--confirmed-local-shutdown-test','--arm-orderly-poweroff','signal.SIGTERM','cannot_cancel_already_accepted_pid1_request'):
   self.assertIn(x,text)
  self.assertNotIn("glob('*')",text);self.assertNotIn('SIGKILL',text)
 def test_interrupt_requests_disarm_and_warns_not_undoing_pid1(self):
  text=(ROOT/'tools/test-power-shutdown.sh').read_text()
  self.assertIn('trap cancel_trial INT HUP TERM',text);self.assertIn('power-shutdown-cancel.py',text)
  self.assertIn('已提交给PID1的关机请求不能靠取消撤销',text)
 def test_local_helper_confirmation_and_no_flash_reset_suspend(self):
  text=(ROOT/'tools/test-power-shutdown.sh').read_text()
  for x in ("[[ $answer == 'POWER OFF' ]]",'StrictHostKeyChecking=yes','usb_absent_20s_without_key_press','automatic_return_without_power_press',"[[ $off == OFF ]]",'after-manual-power-on.json'):
   self.assertIn(x,text)
  for x in ('fastboot boot','fastboot flash','systemctl reboot','systemctl suspend','reset-failed'):
   self.assertNotIn(x,text)


if __name__=='__main__':unittest.main()
