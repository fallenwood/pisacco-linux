import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
G=mod('guided_core',ROOT/'tools/power-key-guided2.py')
W=mod('guided_wrapper',ROOT/'tools/power-shutdown-guided2.py')
P=mod('original_hold',ROOT/'tools/power-hold-policy.py')


class GuidedPowerTests(unittest.TestCase):
 def test_no_hint_before_two_seconds(self):
  self.assertEqual(G.guidance_stage(None,10,0),(0,None));self.assertEqual(G.guidance_stage(10,11.99,0),(0,None))
 def test_two_second_hint_is_not_a_poweroff_action(self):
  policy=P.PowerHoldPolicy();policy.key(116,1,10)
  stage,message=G.guidance_stage(policy.pressed_at,12,0)
  self.assertEqual(stage,1);self.assertIn('立即松开',message);self.assertFalse(policy.requested)
  self.assertEqual(G.guidance_stage(10,12.5,1),(1,None));self.assertEqual(policy.key(116,0,12.22),'orderly_poweroff')
 def test_overlong_warning_does_not_widen_policy(self):
  policy=P.PowerHoldPolicy();policy.key(116,1,10);stage,message=G.guidance_stage(10,13.01,1)
  self.assertEqual(stage,2);self.assertIn('本次无效',message);self.assertIsNone(policy.key(116,0,14.559807))
 def test_first_timeout_must_have_no_candidate_or_request(self):
  r={'status':'observer_timed_out_no_valid_long_release','armed_orderly_poweroff':True,'shutdown_requested':False,'events':[{'policy_action':None}]}
  self.assertTrue(W.valid_prior_failure(r));r['shutdown_requested']=True;self.assertFalse(W.valid_prior_failure(r));r['shutdown_requested']=False;r['events'][0]['policy_action']='orderly_poweroff';self.assertFalse(W.valid_prior_failure(r))
 def test_immutable_original_policy_and_pinned_guided_core(self):
  sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
  self.assertEqual(sha(ROOT/'tools/power-hold-policy.py'),'c1d27bb4d41bfa5a2c2df2519e2033945d9e6b0d1b50b992ecc2a0db67b58670')
  self.assertIn(sha(ROOT/'tools/power-key-guided2.py'),(ROOT/'tools/power-shutdown-guided2.py').read_text())
 def test_guided_runtime_and_persistent_files_are_separate(self):
  text=(ROOT/'tools/power-key-guided2.py').read_text();self.assertIn('/run/picasso-power-armed-guided2',text);self.assertIn("boot+'-guided2.json'",text)
  wrapper=(ROOT/'tools/power-shutdown-guided2.py').read_text();self.assertIn('launch-guided2-',wrapper);self.assertIn('valid_prior_failure(saved)',wrapper)
 def test_guided_durable_record_does_not_overwrite_first_attempt(self):
  with tempfile.TemporaryDirectory() as d:
   real=Path;root=real(d);boot=root/'boot_id';boot.write_text('testboot\n');base=root/'state';base.mkdir();old=base/'testboot.json';old.write_text('original_failure')
   def path(value):return boot if str(value)=='/proc/sys/kernel/random/boot_id' else base
   with patch.object(G,'Path',side_effect=path):G.persist_armed_trial({'armed_orderly_poweroff':True,'shutdown_requested':False,'attempt':'guided2'})
   self.assertEqual(old.read_text(),'original_failure');self.assertEqual(json.loads((base/'testboot-guided2.json').read_text())['attempt'],'guided2')
 def test_local_guided_helper_uses_only_new_output_directory(self):
  text=(ROOT/'tools/test-power-shutdown-guided2.sh').read_text();self.assertNotIn('power-shutdown-trial-20261028',text)
  for x in ('power-shutdown-trial-guided2-20261028','power-shutdown-cancel-guided2.py','power-shutdown-guided2.py','已满2秒','waiter-exit.json'):
   self.assertIn(x,text)
 def test_default_disarmed_thermal_limits_and_release_only_unchanged(self):
  text=(ROOT/'tools/power-key-guided2.py').read_text();self.assertIn('def main(armed=False)',text);self.assertIn('max(values.values())>=40000',text);self.assertIn('max(temps)<45000',text)
  self.assertLess(text.index('action=policy.key(code,value,stamp)'),text.index("subprocess.run(['systemctl','poweroff','--no-block']"))


if __name__=='__main__':unittest.main()
