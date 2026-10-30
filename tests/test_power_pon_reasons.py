import importlib.util
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('pon_decoder',ROOT/'tools/power-pon-reasons.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D)


def fixture():
 return {'scope':'picasso-pm8150-gen2-readonly','usid':0,'base':2048,'registers':{'0104':0x51,'0105':0x1e,'0805':4,'08c0':0x10,'08c2':0,'08c7':0x80,'08c5':2,'08c8':None,'08c9':None,'08ca':None}}


class PonReasonTests(unittest.TestCase):
 def test_usb_and_pshold_are_only_flags_not_cause(self):
  r=D.decode(fixture());self.assertEqual(r['pon_all_flags'],['USB_CHARGER']);self.assertEqual(r['selected_banks']['POFF']['all_flags'],['PS_HOLD']);self.assertFalse(r['root_cause_proven']);self.assertFalse(r['full_powercycle_accepted'])
 def test_multiple_pon_bits_preserved_not_ffs(self):
  f=fixture();f['registers']['08c0']=0x91;self.assertEqual(D.decode(f)['pon_all_flags'],['HARD_RESET','USB_CHARGER','KPDPWR'])
 def test_multiple_sequence_banks_ambiguous_and_retained(self):
  f=fixture();f['registers'].update({'08c7':0xc0,'08c8':0,'08c9':0x10});r=D.decode(f);self.assertTrue(r['multiple_sequences_ambiguous']);self.assertEqual(r['selected_banks']['FAULT']['all_flags'],['PBS_WATCHDOG'])
 def test_unknown_sequence_bits_and_no_sequence_not_off_proof(self):
  f=fixture();f['registers'].update({'08c7':1,'08c5':None});r=D.decode(f);self.assertEqual(r['unknown_sequence_bits'],1);self.assertEqual(r['sequence_all_flags'],[]);self.assertFalse(r['root_cause_proven'])
 def test_identity_and_gen1_control_addresses_refused(self):
  f=fixture();f['registers']['0805']=1
  with self.assertRaises(ValueError):D.decode(f)
  f=fixture();f['registers']['0808']=1
  with self.assertRaises(ValueError):D.decode(f)
 def test_selected_missing_and_unselected_bank_data_refused(self):
  f=fixture();f['registers']['08c5']=None
  with self.assertRaises(ValueError):D.decode(f)
  f=fixture();f['registers']['08c8']=0
  with self.assertRaises(ValueError):D.decode(f)
 def test_nonbytes_and_other_sid_refused(self):
  for v in (True,-1,256):
   f=fixture();f['registers']['08c0']=v
   with self.assertRaises(ValueError):D.decode(f)
  for sid in (5,False,'0'):
   f=fixture();f['usid']=sid
   with self.assertRaises(ValueError):D.decode(f)
 def test_kernel_sampler_fixed_readonly_no_probe_or_arbitrary_api(self):
  text=(ROOT/'kernel/power/picasso-pon-reason-audit.c').read_text();block=text.split('static const u16 addresses[] = {',1)[1].split('};',1)[0]
  self.assertEqual({f'{int(s,16):04x}' for s in re.findall(r'0x[0-9a-f]+',block)},D.ADDRESSES)
  for bad in ('spmi_device_add(', 'spmi_command_', 'spmi_ext_register_write', 'regmap_write(', 'regmap_update_bits(', 'writel(', 'register_reboot_notifier(', 'of_overlay_fdt_apply('):self.assertNotIn(bad,text)
  for good in ('spmi_ext_register_readl(', 'ctrl->dev.of_node != node', 'target->usid = 0', '__ATTR(snapshot, 0400', 'confirm_readonly', 'values[5] & BIT(7)', 'values[5] & BIT(6)', 'values[5] & BIT(5)'):self.assertIn(good,text)


if __name__=='__main__':unittest.main()
