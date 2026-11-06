import hashlib,importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 s=importlib.util.spec_from_file_location(name.replace('-','_'),ROOT/'tools'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=load('audit-wifi-regulatory-cn');C=load('wifi-cn-radio-service')
REF='''global
country CN: DFS-FCC
 (2400 - 2483 @ 40), (N/A, 20), (N/A)
 (5150 - 5250 @ 80), (N/A, 23), (N/A), NO-OUTDOOR, AUTO-BW
 (5250 - 5350 @ 80), (N/A, 20), (0 ms), NO-OUTDOOR, DFS, AUTO-BW
 (5725 - 5850 @ 80), (N/A, 33), (N/A)
'''
class WifiCNTests(unittest.TestCase):
 def test_valid_CN_actual_subset_not_country_label_only(self):
  p='* 2447.0 MHz [8] (20.0 dBm)\n* 5180 MHz [36] (20.0 dBm) (indoor only)\n* 5260 MHz [52] (20.0 dBm) (indoor only) (radar detection)\n* 5745 MHz [149] (20.0 dBm)'
  r=A.audit(REF,REF,p);self.assertEqual(r['country_requested'],'CN');self.assertEqual(r['enabled_20mhz_channels_verified'],4)
 def test_sg_us_unknown_domain_rejected(self):
  for domain in ('SG','US','00'):
   with self.assertRaises(ValueError):A.audit(REF,REF.replace('CN',domain),'* 2447 MHz [8] (20.0 dBm)')
 def test_CN_reference_isolated_and_complete(self):
  for ref in (REF.replace('CN','SG'),REF+'\nphy#0\n',REF.split(' (5250')[0]):
   with self.assertRaises(ValueError):A.cn_rules(ref)
 def test_CN20_dBm_2g_limit_not_SG23_limit(self):
  with self.assertRaises(ValueError):A.audit(REF,REF,'* 2447 MHz [8] (23.0 dBm)')
 def test_98_intersection_still_checks_all_limits(self):
  eff='global\ncountry 98: DFS-FCC';self.assertEqual(A.audit(REF,eff,'* 2447 MHz [8] (20.0 dBm)')['effective_global_domain'],'98-intersection')
  for p in ('* 2484 MHz [14] (20.0 dBm)','* 5500 MHz [100] (20.0 dBm) (radar detection)','* 5745 MHz [149] (34.0 dBm)'):
   with self.assertRaises(ValueError):A.audit(REF,eff,p)
 def test_NO_OUTDOOR_retained_not_replaced_by_no_IR(self):
  for flags in ('','(no IR)'):
   with self.assertRaises(ValueError):A.audit(REF,REF,'* 5180 MHz [36] (20.0 dBm) '+flags)
 def test_DFS_retained_even_indoor(self):
  with self.assertRaises(ValueError):A.audit(REF,REF,'* 5260 MHz [52] (20.0 dBm) (indoor only)')
 def test_all_enabled_channels_not_just_connected_channel(self):
  with self.assertRaises(ValueError):A.audit(REF,REF,'* 2447 MHz [8] (20.0 dBm)\n* 5500 MHz [100] (20.0 dBm) (radar detection)')
 def test_unknown_enabled_channel_or_empty_phy_rejected(self):
  for p in ('','* 2447 MHz [8] (no IR)'):
   with self.assertRaises(ValueError):A.audit(REF,REF,p)
 def test_exact_country_request_adapter_only(self):
  self.assertEqual(C.country_command(['iw','reg','set','SG']),['iw','reg','set','CN'])
  for args in (['iw','reg','get'],['iw','reg','set','US'],['sh','-c','iw reg set SG']):self.assertIs(C.country_command(args),args)
 def test_only_country_audit_and_field_names_override_no_guards(self):
  class Base:
   def text(self,args,**kw):return args
   def save(self):return self.record.copy()
   def startup(self):pass
   def guard(self):pass
   def execute_radio(self):pass
  klass=C.service_type(SimpleNamespace(service_type=lambda worker:Base),None,A,REF);o=klass();o.record={'initial_sg_audit':{'country_requested':'CN'}};r=o.save()
  self.assertEqual(r['country_requested'],'CN');self.assertIn('initial_cn_audit',r);self.assertNotIn('initial_sg_audit',r)
  for name in ('startup','guard','execute_radio'):self.assertIs(getattr(klass,name),getattr(Base,name))
  self.assertEqual({name for name,value in klass.__dict__.items() if callable(value)},{'text','audit','save'})
 def test_pinned_original_sources_and_runtime_safety_not_relaxed(self):
  self.assertEqual(hashlib.sha256((ROOT/'tools/wifi-radio-service.py').read_bytes()).hexdigest(),C.RADIO_SHA)
  self.assertEqual(hashlib.sha256((ROOT/'tools/wifi-auto-service.py').read_bytes()).hexdigest(),load('wifi-radio-service').SOURCE_SHA)
  s=(ROOT/'tools/picasso-wifi-radio-cn.service').read_text()
  for value in ('WatchdogSec=8s','TimeoutStopSec=45s','Restart=no','MemoryMax=256M','--cleanup'):self.assertIn(value,s)
  src=(ROOT/'tools/wifi-cn-radio-service.py').read_text();self.assertNotIn('self.activate(',src);self.assertNotIn('reset-failed',src);self.assertNotIn('--show-secrets',src)
if __name__=='__main__':unittest.main()
