import copy,hashlib,importlib.util,math,struct,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 s=importlib.util.spec_from_file_location(name.replace('-','_'),ROOT/'tools'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=load('audit-wifi-regulatory-cn-raw');P=load('audit-wifi-regulatory-cn');C=load('wifi-cn-raw-radio-service');N=load('wifi-nl80211-channels')
REF='''global
country CN: DFS-FCC
 (2400 - 2483 @ 40), (N/A, 20), (N/A)
 (5150 - 5250 @ 80), (N/A, 23), (N/A), NO-OUTDOOR, AUTO-BW
 (5250 - 5350 @ 80), (N/A, 20), (0 ms), NO-OUTDOOR, DFS, AUTO-BW
 (5725 - 5850 @ 80), (N/A, 33), (N/A)
'''
def channel(freq=5180,power=2300,indoor=True,radar=False):
 data=N.attribute(1,struct.pack('=I',freq))+N.attribute(6,struct.pack('=I',power))
 if indoor:data+=N.attribute(14)
 if radar:data+=N.attribute(5)
 c=N.decode_frequency(data);c['band_index']=0 if freq<3000 else 1;return c

def report(channels=None):
 return {'source':'read_only_raw_nl80211_split_GET_WIPHY','kernel_release':'6.18.58-picasso-lts-wifi2','split_requested':True,'complete_dump':True,'protocol_features':1,'phys':[{'index':0,'name':'phy0','channels':channels or [channel()]}]}

def check(r=None,info='* 5180 MHz [36] (23.0 dBm)',effective=REF,reference=REF):return A.audit(reference,effective,r or report(),0,'phy0',info,P.cn_rules)

class RawCNAudit(unittest.TestCase):
 def test_actual_raw_indoor_present_succeeds_without_iw_marker(self):
  self.assertEqual(check()['actual_INDOOR_ONLY_frequencies_mhz'],[5180.0])
  with self.assertRaises(ValueError):P.audit(REF,REF,'* 5180 MHz [36] (23.0 dBm)')
 def test_genuine_missing_indoor_bit_still_rejected(self):
  with self.assertRaises(ValueError):check(report([channel(indoor=False)]))
 def test_cannot_invent_indoor_true_without_attr14(self):
  c=channel(indoor=False);c['indoor_only']=True
  with self.assertRaises(ValueError):check(report([c]))
 def test_actual_DFS_required(self):
  for radar in (False,True):
   args=(report([channel(5260,2000,True,radar)]),'* 5260 MHz [52] (20.0 dBm)')
   if radar:self.assertTrue(check(*args)['actual_CN_EIRP_DFS_NO_OUTDOOR_IR_subset_verified'])
   else:
    with self.assertRaises(ValueError):check(*args)
 def test_actual_mBm_power_not_global_country_label(self):
  with self.assertRaises(ValueError):check(report([channel(2447,2300,False)]),'* 2447 MHz [8] (23.0 dBm)')
 def test_inventory_must_include_all_channels_and_match(self):
  for r,info in ((report(),'* 5180 MHz [36] (23.0 dBm)\n* 5500 MHz [100] (20.0 dBm)'),(report([channel(),channel(2447,2000,False)]),'* 5180 MHz [36] (23.0 dBm)')):
   with self.assertRaises(ValueError):check(r,info)
 def test_wrong_PHY_identity_or_multiple_PHYs_rejected(self):
  for key,val in (('index',1),('name','phy1')):
   r=report();r['phys'][0][key]=val
   with self.assertRaises(ValueError):check(r)
  r=report();r['phys']*=2
  with self.assertRaises(ValueError):check(r)
 def test_incomplete_or_unpinned_evidence_rejected(self):
  for key,val in (('complete_dump',False),('split_requested',False),('protocol_features',0),('kernel_release','other'),('source','iw-text')):
   r=report();r[key]=val
   with self.assertRaises(ValueError):check(r)
 def test_foreign_country_rejected_98_requires_limits(self):
  for domain in ('SG','US','00'):
   with self.assertRaises(ValueError):check(effective='global\ncountry '+domain+': DFS-FCC')
  self.assertEqual(check(effective='global\ncountry 98: DFS-FCC')['effective_global_domain'],'98-intersection')
 def test_NO_IR_rule_requires_actual_attr(self):
  ref=REF.replace('NO-OUTDOOR, AUTO-BW','NO-OUTDOOR, NO-IR, AUTO-BW')
  with self.assertRaises(ValueError):check(reference=ref)
  c=channel();c['no_ir']=True;c['observed_attribute_ids'].append(3);self.assertTrue(check(report([c]),reference=ref))
 def test_duplicate_invalid_frequency_or_nonbool_rejected(self):
  for change in ('duplicate','nan','nonbool'):
   r=report()
   if change=='duplicate':r['phys'][0]['channels']*=2
   elif change=='nan':r['phys'][0]['channels'][0]['frequency_mhz']=float('nan')
   else:r['phys'][0]['channels'][0]['indoor_only']=1
   with self.assertRaises(ValueError):check(r)
 def test_only_audit_override_inherits_all_original_guards(self):
  class Base:
   def guard(self):pass
   def startup(self):pass
   def execute_radio(self):pass
   def save(self):pass
  klass=C.service_type(SimpleNamespace(service_type=lambda *args:Base),None,None,None,'ref',A)
  self.assertEqual({name for name,value in klass.__dict__.items() if callable(value)},{'audit'})
  for name in ('guard','startup','execute_radio','save'):self.assertIs(getattr(klass,name),getattr(Base,name))
 def test_runtime_safety_and_failed_R1_source_pin_unchanged(self):
  self.assertEqual(hashlib.sha256((ROOT/'tools/wifi-cn-radio-service.py').read_bytes()).hexdigest(),C.R1_SHA)
  text=(ROOT/'tools/picasso-wifi-radio-cn-raw.service').read_text()
  for value in ('WatchdogSec=8s','TimeoutStopSec=45s','Restart=no','MemoryMax=256M','--cleanup'):self.assertIn(value,text)
  self.assertNotIn('self.activate(', (ROOT/'tools/wifi-cn-raw-radio-service.py').read_text())
 def test_country_prohibited_5500_rejected_even_DFS(self):
  with self.assertRaises(ValueError):check(report([channel(5500,2000,True,True)]),'* 5500 MHz [100] (20.0 dBm)')
 def test_disabled_channel_retained_in_inventory(self):
  c=channel(5500,2000,False);c['disabled']=True;c['observed_attribute_ids'].append(2)
  r=check(report([channel(),c]),'* 5180 MHz [36] (23.0 dBm)\n* 5500 MHz [100] (disabled)');self.assertEqual(r['enabled_20mhz_channels_verified'],1)
 def test_no20MHz_enabled_channel_rejected(self):
  c=channel();c['no_20mhz']=True;c['observed_attribute_ids'].append(16)
  with self.assertRaises(ValueError):check(report([c]))
if __name__=='__main__':unittest.main()
