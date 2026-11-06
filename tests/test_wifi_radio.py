import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('wifi_radio',ROOT/'tools/wifi-radio-service.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R)


class WifiRadioTests(unittest.TestCase):
 def fake_radio(self,zone='drop'):
  class Base:
   def __init__(self):self.record={'children':['stub']};self.link='Not connected.\n';self.commands=[];self.zone=zone
   def identity(self):pass
   def audit(self,**kwargs):return {'audited':True}
   def activate(self,*args):raise AssertionError('No automatic activation allowed')
   def run(self,args,**kwargs):return 0,self.zone
   def text(self,args):
    self.commands.append(args)
    if args[:2]==['systemctl','is-active']:return 'active\n'
    if args==['firewall-cmd','--zone=drop','--add-interface=wlan0']:self.zone='drop';return 'success\n'
    if args[0]=='firewall-cmd':return self.zone+'\n'
    if args[:3]==['ip','-j','link']:return json.dumps([{'ifname':'wlan0','flags':['UP'],'operstate':'DOWN'}])
    if args[-1]=='link':return self.link
    if args[-1]=='power_save':return 'Power save: off\n'
    if args[-2:]==['station','dump']:return ''
    raise AssertionError(args)
  spec=importlib.util.spec_from_file_location('cpu_cap_worker',ROOT/'tools/wifi-auto-service.py')
  worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
  return R.service_type(SimpleNamespace(Service=Base,read_cpu_cap=worker.read_cpu_cap))()
 def test_no_association_is_valid_not_an_error(self):
  self.assertIsNone(R.link_metadata('Not connected.\n')['ssid'])
 def test_only_approved_ssids_observed(self):
  self.assertEqual(R.link_metadata('SSID: Chaldea\nfreq: 5240\nsignal: -75 dBm')['ssid'],'Chaldea')
  with self.assertRaises(RuntimeError):R.link_metadata('SSID: OtherNetwork\n')
 def test_up_without_carrier_even_operstate_down_is_valid(self):
  for oper in ('DOWN','DORMANT','UP'):
   r=R.check_link_flags([{'ifname':'wlan0','flags':['UP'],'operstate':oper}]);self.assertTrue(r['administrative_up']);self.assertFalse(r['carrier_flag'])
 def test_actual_administrative_down_is_not_hidden(self):
  with self.assertRaises(RuntimeError):R.check_link_flags([{'ifname':'wlan0','flags':[],'operstate':'DOWN'}])
 def test_idle_monitor_keeps_interface_and_does_not_activate(self):
  o=self.fake_radio()
  with patch.object(Path,'read_text',return_value='1094400'):o.radio_monitor()
  self.assertEqual(o.record['status'],'radio_up_idle');self.assertTrue(o.record['administrative_up']);self.assertFalse(o.record['internet_connectivity_validated'])
 def test_ordinary_link_loss_becomes_idle_not_cleanup(self):
  o=self.fake_radio();o.link='SSID: Chaldea\nfreq: 5240\nsignal: -75 dBm'
  with patch.object(Path,'read_text',return_value='1094400'):
   o.radio_monitor();o.link='Not connected.\n';o.radio_monitor()
  self.assertEqual(o.record['status'],'radio_up_idle');self.assertIsNone(o.record['association_observed_ssid']);self.assertTrue(o.record['administrative_up'])
 def test_unassigned_firewall_binding_reasserted_not_other_zone(self):
  o=self.fake_radio('')
  with patch.object(Path,'read_text',return_value='1094400'):o.radio_monitor()
  self.assertIn(['firewall-cmd','--zone=drop','--add-interface=wlan0'],o.commands)
  o=self.fake_radio('trusted')
  with patch.object(Path,'read_text',return_value='1094400'):
   with self.assertRaises(RuntimeError):o.radio_monitor()
 def test_native_thermal_qos_lower_cap_keeps_radio_but_higher_cap_fails(self):
  o=self.fake_radio()
  def read(p):
   if p.name=='scaling_available_frequencies':return '652800 806400 940800 1094400 1478400'
   if p.name=='scaling_min_freq':return '652800' if p.parent.name=='policy6' else '806400'
   return '940800' if p.parent.name=='policy6' else '806400'
  with patch.object(Path,'read_text',read):o.radio_monitor()
  self.assertEqual(o.record['status'],'radio_up_idle')
  def high(p):return '1478400' if p.name=='scaling_max_freq' else read(p)
  with patch.object(Path,'read_text',high),self.assertRaises(RuntimeError):o.radio_monitor()
 def test_native_guards_and_stop_cleanup_remain_pinned(self):
  self.assertEqual(hashlib.sha256((ROOT/'tools/wifi-auto-service.py').read_bytes()).hexdigest(),R.SOURCE_SHA)
  text=(ROOT/'tools/picasso-wifi-radio.service').read_text()
  for x in ('WatchdogSec=8s','TimeoutStopSec=45s','Restart=no','MemoryMax=256M','--cleanup'):self.assertIn(x,text)
  code=(ROOT/'tools/wifi-radio-service.py').read_text();self.assertNotIn('self.activate(',code);self.assertNotIn('--show-secrets',code);self.assertNotIn('reset-failed',code)
 def test_safety_exception_still_cleans_even_when_keep_up_requested(self):
  with tempfile.TemporaryDirectory() as d:
   seen=[]
   class Base:
    def __init__(self):self.record={'history':d};self.health_thread=None;self.helper=None;self.stop_event=threading.Event()
    def save(self):pass
    def startup(self):raise RuntimeError('45C thermal abort')
   def cleanup():seen.append('cleanup');return {'status':'safe_cleanup_complete'}
   base=SimpleNamespace(Service=Base,notify=lambda text:seen.append(text),cleanup=cleanup,atomic=lambda *args:None)
   o=R.service_type(base)();self.assertEqual(o.execute_radio(),1);self.assertIn('cleanup',seen);self.assertLess(next(i for i,v in enumerate(seen) if v.startswith('STOPPING=1')),seen.index('cleanup'));self.assertEqual(o.record['status'],'failed_safety_shutdown')


if __name__=='__main__':unittest.main()
