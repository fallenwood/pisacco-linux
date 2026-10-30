import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('wifi_auto',ROOT/'tools/wifi-auto-service.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)


class WifiAutoTests(unittest.TestCase):
 def test_exact_two_preserved_topology_FDTs_only(self):
  for fdt in A.APPROVED_FDTS:A.approved_fdt(A.APPROVED_FDTS[0],fdt)
  for base,live in ((A.APPROVED_FDTS[1],A.APPROVED_FDTS[1]),(A.APPROVED_FDTS[0],'0'*64)):
   with self.assertRaises(RuntimeError):A.approved_fdt(base,live)
 def test_bound_mode_does_not_consume_or_require_gate(self):
  with patch.object(A,'STATE',Path('/does-not-exist')):A.probation_gate({'probation_seconds':45})
  for value in (True,-1,'0'):
   with self.assertRaises(RuntimeError):A.probation_gate({'probation_seconds':value})
 def test_unbounded_requires_native_full_success_exact_controller(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'auto-enable-consent-20261029.json';good={'user_request':'启用wifi自动连接','unit_result':'success','native_status':'passed_bounded_probation','cleanup_status':'safe_cleanup_complete','probation_seconds':45,'service_sha256':hashlib.sha256(Path(A.__file__).read_bytes()).hexdigest()}
   with patch.object(A,'STATE',Path(d)),patch.object(Path,'lstat',return_value=SimpleNamespace(st_mode=stat.S_IFREG|0o400,st_uid=0,st_nlink=1)):
    p.write_text(json.dumps(good));A.probation_gate({'probation_seconds':0})
    for key,bad in (('unit_result','watchdog'),('cleanup_status','cleanup_requires_attention'),('service_sha256','0'*64)):
     p.write_text(json.dumps({**good,key:bad}))
     with self.assertRaises(RuntimeError):A.probation_gate({'probation_seconds':0})
 def test_nonroot_cannot_forge_acceptance(self):
  with patch.object(Path,'lstat',return_value=SimpleNamespace(st_mode=stat.S_IFREG|0o400,st_uid=1000,st_nlink=1)):
   with self.assertRaises(RuntimeError):A.probation_gate({'probation_seconds':0})
 def test_invalid_sensor_telemetry_rejected(self):
  for value in ('-10001','150001','bad'):
   node=SimpleNamespace(parent=SimpleNamespace(name='thermal_zone0'),read_text=lambda:value)
   with patch.object(Path,'glob',return_value=[node]):
    with self.assertRaises((RuntimeError,ValueError)):A.temperatures()
 def test_stopping_notification_precedes_cleanup_no_RF(self):
  with tempfile.TemporaryDirectory() as d:
   o=A.Service.__new__(A.Service);o.record={'history':d};o.live=False;o.stop_event=threading.Event();o.health_thread=None;o.helper=None;o.save=lambda:None
   o.startup=lambda:(_ for _ in ()).throw(RuntimeError('offline injected refusal'));seen=[]
   def cleanup():
    self.assertTrue(any(x.startswith('STOPPING=1') for x in seen));self.assertTrue(o.stop_event.is_set());return {'status':'safe_cleanup_complete'}
   with patch.object(A,'notify',side_effect=seen.append),patch.object(A,'cleanup',side_effect=cleanup):self.assertEqual(o.execute(),1)
 def test_unit_retains_watchdog_stop_limit_and_no_restart(self):
  u=(ROOT/'tools/picasso-wifi-auto.service').read_text()
  for text in ('WatchdogSec=8s','TimeoutStopSec=45s','Restart=no','MemoryMax=256M','wifi-auto-service.py --cleanup'):self.assertIn(text,u)
 def test_no_password_export_or_trigger_safety_weakening(self):
  t=(ROOT/'tools/wifi-auto-service.py').read_text()
  for text in ('self.audit()','45000','40000','1094400',"'passwd-file'",'private_file(CREDENTIALS'):
   self.assertIn(text,t)
  for text in ('--show-secrets','reset-failed','modemst1.bin','/dev/mem'):self.assertNotIn(text,t)


if __name__=='__main__':unittest.main()
