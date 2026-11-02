import copy,hashlib,importlib.util,math,struct,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 s=importlib.util.spec_from_file_location(name.replace('-','_'),ROOT/'tools'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=load('audit-wifi-regulatory-cn-raw');P=load('audit-wifi-regulatory-cn');C=load('wifi-cn-raw-radio-service');N=load('wifi-nl80211-channels')
H=load('wifi-router-country');B=load('wifi-bss')
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

 def fixed_service(self,domain):
  events=[]
  class Base:
   def text(self,args):
    events.append(args)
    if args==['iw','reg','get']:return 'global\ncountry '+domain+': DFS-FCC\n'
    return ''
   def pause(self,seconds):events.append(('pause',seconds))
  klass=C.service_type(SimpleNamespace(service_type=lambda *args:Base),None,None,P,REF,A)
  return klass(),events

 def test_fixed_cn_refreshes_foreign_domain_without_an_ssid_change_or_ap_country_trust(self):
  service,events=self.fixed_service('US')
  with patch.object(C,'observe_channels',return_value={'country_requested':'CN'}) as observe:
   self.assertEqual(service.audit()['country_requested'],'CN')
  self.assertEqual(events,[['iw','reg','get'],['iw','reg','set','CN'],('pause',.3)])
  self.assertEqual(observe.call_args.args[-1],'CN')
  self.assertIs(observe.call_args.args[1],REF)

 def test_fixed_cn_and_intersection_still_use_complete_raw_audit_without_unneeded_writes(self):
  for domain in ('CN','98'):
   service,events=self.fixed_service(domain)
   with self.subTest(domain=domain),patch.object(C,'observe_channels',side_effect=ValueError('raw CN limits exceeded')),self.assertRaises(ValueError):
    service.audit()
   self.assertEqual(events,[['iw','reg','get']])
  service,events=self.fixed_service('CN')
  with patch.object(C,'observe_channels',return_value={}):service.audit(reapply=True)
  self.assertIn(['iw','reg','set','CN'],events)

class RouterCountryAudit(unittest.TestCase):
 US=REF.replace('country CN:','country US:').replace('(N/A, 20)','(N/A, 30)',1)
 LINK='Connected to 00:11:22:33:44:55 (on wlan0)\n\tSSID: Chaldea\n\tfreq: 5240\n'
 SCAN='BSS 00:11:22:33:44:55(on wlan0)\n\tfreq: 5240\n\tSSID: Chaldea\n\tCountry: US\tEnvironment: Indoor/Outdoor\n'

 def test_selected_country_requires_exact_bssid_ssid_and_frequency(self):
  identity=H.link_identity(self.LINK,('Chaldea',))
  self.assertEqual(H.country_from_records(B.target_bss_records(self.SCAN,'Chaldea'),identity),'US')
  self.assertEqual(H.country_from_records(B.bss_records(self.SCAN.replace('SSID: Chaldea','SSID: ')),identity),'US')
  for scan in (self.SCAN.replace('00:11:22:33:44:55','00:11:22:33:44:56'),
               self.SCAN.replace('5240','5180'),self.SCAN.replace('Chaldea','Other'),
               self.SCAN.replace('\tCountry: US\tEnvironment: Indoor/Outdoor\n',''),
               self.SCAN+'\tCountry: CN\n'):
   with self.subTest(scan=scan),self.assertRaises(ValueError):
    H.country_from_records(B.target_bss_records(scan,'Chaldea'),identity)
  with self.assertRaises(ValueError):
   H.country_from_records(B.bss_records(self.SCAN.replace('SSID: Chaldea','SSID: Other')),identity)

 def test_country_reference_requires_review_and_signed_kernel_country_not_cn_relabeling(self):
  policy={'mode':'reviewed_router_country_ie','router_country_legitimate':True,'country':'US'}
  self.assertEqual(H.validate_policy(policy,self.US),'US')
  for cfg,ref in (({**policy,'router_country_legitimate':False},self.US),(policy,REF),
                  (policy,self.US+'\nphy#0\n'),({**policy,'country':'00'},self.US)):
   with self.subTest(policy=cfg),self.assertRaises(ValueError):H.validate_policy(cfg,ref)
  rules=H.kernel_rules(self.US+'\n (902 - 904 @ 2), (N/A, 30), (N/A)\n','US')
  self.assertTrue(any(rule[2]==2 for rule in rules))

 def test_decimal_iw_frequency_and_matching_beacon_probe_country_are_not_ambiguous(self):
  identity=H.link_identity(self.LINK.replace('5240','5240.0'),('Chaldea',))
  scan=self.SCAN.replace('5240','5240.000')+'\tSSID: Chaldea\n\tCountry: US\n'
  self.assertEqual(H.country_from_records(B.bss_records(scan),identity),'US')
  for value in ('5240.5','nan','-5240'):
   with self.subTest(frequency=value),self.assertRaises(ValueError):
    H.link_identity(self.LINK.replace('5240',value),('Chaldea',))
  with self.assertRaises(ValueError):
   H.country_from_records(B.bss_records(scan+'\tCountry: CN\n'),identity)

 def test_router_reference_limits_all_raw_channels_and_keeps_dfs_indoor_no_ir(self):
  c=channel(2447,2300,False)
  r=A.audit(self.US,self.US,report([c]),0,'phy0','* 2447 MHz [8] (23.0 dBm)',
            lambda ref:H.kernel_rules(ref,'US'),expected_country='US')
  self.assertEqual(r['country_requested'],'US')
  for c,ref,info in ((channel(2447,3100,False),self.US,'* 2447 MHz [8] (31.0 dBm)'),
                     (channel(5260,2000,True,False),self.US,'* 5260 MHz [52] (20.0 dBm)'),
                     (channel(indoor=False),self.US,'* 5180 MHz [36] (23.0 dBm)'),
                     (channel(),self.US.replace('NO-OUTDOOR, AUTO-BW','NO-OUTDOOR, PASSIVE-SCAN'),'* 5180 MHz [36] (23.0 dBm)')):
   with self.subTest(channel=c),self.assertRaises(ValueError):
    A.audit(ref,ref,report([c]),0,'phy0',info,lambda value:H.kernel_rules(value,'US'),expected_country='US')

 def test_router_no20_channel_is_excluded_but_still_requires_raw_provenance_and_limits(self):
  c=channel(5845,2700,True);c['no_20mhz']=True;c['observed_attribute_ids'].append(16)
  info='* 5180 MHz [36] (23.0 dBm)\n* 5845 MHz [169] (27.0 dBm)'
  result=A.audit(self.US,self.US,report([channel(),c]),0,'phy0',info,
                 lambda ref:H.kernel_rules(ref,'US'),expected_country='US')
  self.assertEqual(result['enabled_non20_channels_excluded'],[5845])
  self.assertEqual(result['enabled_20mhz_channels_verified'],1)
  for bad in ('power','provenance','all_unusable'):
   other=copy.deepcopy(c)
   if bad=='power':other['max_tx_power_mbm']=3400
   if bad=='provenance':other['observed_attribute_ids'].remove(16)
   channels=[other] if bad=='all_unusable' else [channel(),other]
   listing='* 5845 MHz [169] (27.0 dBm)' if bad=='all_unusable' else info
   with self.subTest(bad=bad),self.assertRaises(ValueError):
    A.audit(self.US,self.US,report(channels),0,'phy0',listing,
            lambda ref:H.kernel_rules(ref,'US'),expected_country='US')

 def service(self):
  events=[]
  class Base:
   def __init__(self):self.cfg={'router_country':'US'};self.record={}
   def identity(self):pass
   def pause(self,seconds):events.append(('pause',seconds))
   def text(self,args,**kw):
    events.append(args)
    if args==['iw','dev','wlan0','link']:return RouterCountryAudit.LINK
    if args==['iw','dev','wlan0','scan','dump']:return RouterCountryAudit.SCAN
    if args==['iw','reg','get']:return REF
    return ''
   def save(self):return self.record.copy()
   def guard(self):pass
   def execute_radio(self):pass
  worker=SimpleNamespace(Service=Base,NAMES=('Chaldea',),load=lambda name:B)
  r1=SimpleNamespace(service_type=lambda *args:Base)
  klass=C.service_type(r1,None,worker,P,REF,A,{'helper':H,'reference':self.US,'country':'US'})
  return klass(),events,Base

 def test_same_ssid_reconnect_refreshes_foreign_domain_without_waiting_for_ssid_change(self):
  service,events,base=self.service()
  with patch.object(C,'observe_channels',return_value={'country_requested':'US'}) as observe:
   self.assertEqual(service.audit()['country_requested'],'US')
  self.assertIn(['iw','reg','set','US'],events)
  self.assertNotIn(['iw','reg','set','CN'],events)
  self.assertEqual(observe.call_args.args[-1],'US')
  for name in ('guard','execute_radio'):self.assertIs(getattr(type(service),name),getattr(base,name))

 def test_unreviewed_selected_ap_country_fails_before_regulatory_write(self):
  service,events,_=self.service();original=service.text
  def text(args,**kw):
   value=original(args,**kw)
   return value.replace('Country: US','Country: CN') if args==['iw','dev','wlan0','scan','dump'] else value
  service.text=text
  with self.assertRaises(RuntimeError):service.audit()
  self.assertFalse(any(isinstance(args,list) and args[:3]==['iw','reg','set'] for args in events))

 def test_ap_identity_change_during_channel_dump_refuses_acceptance(self):
  service,events,_=self.service()
  def observe(*args):
   original=service.text
   service.text=lambda command,**kw: original(command,**kw).replace('00:11:22:33:44:55','00:11:22:33:44:56')
   return {'country_requested':'US'}
  with patch.object(C,'observe_channels',side_effect=observe),self.assertRaises(RuntimeError):service.audit()

 def test_selected_router_channel_cannot_use_no20_exclusion(self):
  service,_,_=self.service()
  with patch.object(C,'observe_channels',return_value={'enabled_non20_channels_excluded':[5240]}),self.assertRaises(RuntimeError):
   service.audit()
if __name__=='__main__':unittest.main()
