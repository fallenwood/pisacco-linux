import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=mod('power_policy',ROOT/'tools/power-hold-policy.py')
A=mod('power_audit',ROOT/'tools/audit-power-key.py')


class PowerKeyTests(unittest.TestCase):
 def test_no_shutdown_until_released_after_two_seconds(self):
  p=P.PowerHoldPolicy();self.assertIsNone(p.key(116,1,1));self.assertIsNone(p.key(116,2,3.2));self.assertEqual(p.key(116,0,3.2),'orderly_poweroff')
 def test_short_unmatched_and_other_keys_do_nothing(self):
  p=P.PowerHoldPolicy();self.assertIsNone(p.key(116,0,1));p.key(115,1,1);self.assertIsNone(p.key(115,0,4));p.key(116,1,5);self.assertIsNone(p.key(116,0,5.2))
 def test_duplicate_press_does_not_move_start_and_action_only_once(self):
  p=P.PowerHoldPolicy();p.key(116,1,1);p.key(116,1,2);self.assertEqual(p.key(116,0,3.1),'orderly_poweroff');p.key(116,1,5);self.assertIsNone(p.key(116,0,7.1))
 def test_overlong_and_reversed_timestamp_are_not_orderly_shutdown_proof(self):
  p=P.PowerHoldPolicy();p.key(116,1,10);self.assertIsNone(p.key(116,0,14));p.key(116,1,20);self.assertIsNone(p.key(116,0,19))
 def test_controller_default_disarmed_real_input_only(self):
  text=(ROOT/'tools/power-key-service.py').read_text()
  for x in ('def main(armed=False)','--arm-orderly-poweroff',"bits==1<<116","'pm8941_pwrkey'",'CANDIDATE_FDT','SYN_DROPPED',"['systemctl','poweroff','--no-block']"):
   self.assertIn(x,text)
  for x in ('/dev/mem','regmap','force','systemctl suspend','uinput'):
   self.assertNotIn(x,text)
 def test_candidate_exact_addition_audit(self):
  d=ROOT/'out/power-key-preparation-20261028/power-trial.dtb'
  if not d.exists():self.skipTest('Optional prepared power trial DTB not present')
  base=(ROOT/'out/wifi-rmtfs-20261027/picasso.dtb').read_bytes();vendor=(ROOT/'out/rom-audit/merged-09-19.dtb').read_bytes();r=A.audit(base,d.read_bytes(),vendor)
  self.assertFalse(r['hardware_tested']);self.assertFalse(r['volume_down_added']);self.assertEqual(r['power_key']['linux_code'],116)
 def test_existing_node_mutation_is_rejected(self):
  d=ROOT/'out/power-key-preparation-20261028/power-trial.dtb'
  if not d.exists():self.skipTest('Optional prepared power trial DTB not present')
  base=(ROOT/'out/wifi-rmtfs-20261027/picasso.dtb').read_bytes();vendor=(ROOT/'out/rom-audit/merged-09-19.dtb').read_bytes();old=A.nodes(base);new=A.nodes(d.read_bytes());new['/']['model']=b'wrong\0'
  with patch.object(A,'nodes',side_effect=[old,new,A.nodes(vendor)]):
   with self.assertRaises(ValueError):A.audit(base,d.read_bytes(),vendor)
 def test_resume_fastboot_never_reenters_phone_reboot_branch(self):
  text=(ROOT/'tools/test-power-input.sh').read_text();start=text.rindex('if [[ $MODE == normal ]]; then');normal,rest=text[start:].split('\nelse\n',1);resume=rest.split('\nfi\n',1)[0]
  self.assertIn('systemctl reboot',normal);self.assertNotIn('systemctl reboot',resume);self.assertIn('--resume-fastboot',text)
 def test_host_fastboot_operations_use_normal_local_sudo(self):
  text=(ROOT/'tools/test-power-input.sh').read_text()
  self.assertIn('sudo -v',text);self.assertIn("['sudo','-n',fb,'-s','79b5ecfc','getvar','product']",text)
  self.assertIn('sudo -n "$FB" -s 79b5ecfc boot',text);self.assertNotIn('chmod 666',text);self.assertNotIn('docker ',text)
 def test_boot_request_marker_prevents_duplicate_ram_boot(self):
  text=(ROOT/'tools/test-power-input.sh').read_text()
  self.assertIn('fastboot-boot-request.json',text);self.assertIn('os.O_EXCL',text);self.assertIn('observer_result_missing',text)
  self.assertIn('OBSERVE=$?',text);self.assertIn('exit "$OBSERVE"',text)
 def test_no_reset_timer_or_reboot_magic_in_new_dts(self):
  text=(ROOT/'dts/sm7250-xiaomi-picasso-power-trial.dts').read_text()
  for x in ('qcom,s1-timer','qcom,s2-timer','qcom,s2-type','mode-bootloader','qcom,pm8941-resin'):
   self.assertNotIn(x,text)
  self.assertIn('sm7250-xiaomi-picasso-wifi-rmtfs.dts',text)


if __name__=='__main__':unittest.main()
