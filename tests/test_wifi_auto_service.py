import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import stat
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('wifi_auto',ROOT/'tools/wifi-auto-service.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)


class WifiAutoTests(unittest.TestCase):
 def test_ipv6_profile_policy_is_checked_before_activation_and_used_for_disconnect(self):
  for name in ('wifi-auto-service','wifi-service'):
   spec=importlib.util.spec_from_file_location('profile_worker',ROOT/'tools'/(name+'.py'))
   worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
   rules_spec=importlib.util.spec_from_file_location('profile_rules',ROOT/'tools/wifi-fallback-policy.py')
   rules=importlib.util.module_from_spec(rules_spec);rules_spec.loader.exec_module(rules)
   for enabled,actual in ((False,'disabled'),(True,'auto'),(True,'disabled')):
    with self.subTest(worker=name,enabled=enabled,actual=actual):
     obj=worker.Service.__new__(worker.Service);obj.cfg={'ipv6_auto':enabled};obj.rules=rules;obj.network=rules.network_policy(obj.cfg)
     obj.record={'attempts':[]};obj.identity=lambda:None;obj.audit=lambda **kw:None;obj.save=lambda:None;calls=[]
     values={'802-11-wireless.ssid':worker.NAMES[0],'802-11-wireless.band':'a','802-11-wireless.hidden':'yes','802-11-wireless.powersave':'disable','802-11-wireless.cloned-mac-address':'permanent','802-11-wireless-security.key-mgmt':'wpa-psk','802-11-wireless-security.proto':'rsn','802-11-wireless-security.pairwise':'ccmp','802-11-wireless-security.group':'ccmp','802-11-wireless-security.psk-flags':'2','connection.autoconnect':'no','connection.zone':'drop','ipv4.method':'auto','ipv6.method':actual,'ipv6.may-fail':'yes'}
     obj.text=lambda args:values[args[2]]
     obj.run=lambda args,**kw:(calls.append(args) or (0,''))
     if enabled and actual=='disabled':
      with self.assertRaisesRegex(RuntimeError,'ipv6.method'):obj.activate(worker.NAMES[0],'a',20)
      self.assertFalse(calls)
     else:
      self.assertTrue(obj.activate(worker.NAMES[0],'a',20))
      profile=rules.profile_name(obj.cfg,worker.NAMES[0]);self.assertIn(profile,calls[0])
      obj.disconnect(worker.NAMES[0]);self.assertEqual(calls[-1][-1],profile)
 def test_shutdown_disarms_runtime_watchdog_in_actual_notification(self):
  with tempfile.TemporaryDirectory() as d,socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as receiver:
   address=str(Path(d)/'notify');receiver.bind(address);receiver.settimeout(1)
   with patch.dict(A.os.environ,{'NOTIFY_SOCKET':address}):
    A.notify('STOPPING=1\nSTATUS=Orderly guarded Wi-Fi cleanup')
   self.assertEqual(receiver.recv(4096).decode().splitlines(),
                    ['STOPPING=1','STATUS=Orderly guarded Wi-Fi cleanup','WATCHDOG_USEC=0'])
 def test_runtime_notifications_do_not_disarm_watchdog(self):
  with tempfile.TemporaryDirectory() as d,socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as receiver:
   address=str(Path(d)/'notify');receiver.bind(address);receiver.settimeout(1)
   with patch.dict(A.os.environ,{'NOTIFY_SOCKET':address}):
    for message in ('READY=1','WATCHDOG=1','STATUS=not a STOPPING=1 tag'):
     A.notify(message);self.assertEqual(receiver.recv(4096).decode(),message)
 def test_explicit_65C_startup_and_runtime_boundary(self):
  self.assertEqual(A.STARTUP_LIMIT_MC,65000);self.assertEqual(A.RUNTIME_ABORT_MC,65000)
  for limit in (A.STARTUP_LIMIT_MC,A.RUNTIME_ABORT_MC):
   for value in (40000,45000,60000,64999):self.assertTrue(A.below_temperature_limit({'cpu':value},limit))
   for value in (65000,65001,110000):self.assertFalse(A.below_temperature_limit({'cool_cpu':30000,'hot_cpu':value},limit))
   for invalid in ({},{'cpu':-10001},{'cpu':150001},{'cpu':True}):
    with self.assertRaises(RuntimeError):A.below_temperature_limit(invalid,limit)
 def test_guard_rejects_65C_before_sending_RF_lease(self):
  o=A.Service.__new__(A.Service);o.stop_event=SimpleNamespace(wait=lambda _:False);o.record={'peak_temperature_mc':0};o.failure=None
  with patch.object(A,'temperatures',return_value={'cpu':65000}),patch.object(A,'notify') as notify:
   o.guard()
  self.assertIn('65C thermal abort',o.failure);notify.assert_not_called()
 def test_thermal_qos_can_only_lower_cpu_ceiling_on_hardware_frequencies(self):
  frequencies=(652800,940800,1094400,1478400,2208000)
  for cap in frequencies[:3]:self.assertEqual(A.validate_cpu_cap(cap,652800,1094400,frequencies),cap)
  for cap in (0,-1,True,600000,1000000,1478400,2208000):
   with self.subTest(cap=cap),self.assertRaises(RuntimeError):A.validate_cpu_cap(cap,652800,1094400,frequencies)
 def test_read_cpu_cap_checks_actual_minimum_and_hardware_table(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'scaling_max_freq').write_text('940800');(p/'scaling_min_freq').write_text('652800');(p/'scaling_available_frequencies').write_text('652800 940800 1094400 2208000')
   with patch.object(A,'Path',return_value=p):self.assertEqual(A.read_cpu_cap(6,1094400),940800)
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
 def test_no_password_export_or_other_guard_weakening(self):
  t=(ROOT/'tools/wifi-auto-service.py').read_text()
  for text in ('self.audit()','STARTUP_LIMIT_MC = 65000','RUNTIME_ABORT_MC = 65000','1094400',"'passwd-file'",'private_file(CREDENTIALS'):
   self.assertIn(text,t)
  for text in ('--show-secrets','reset-failed','modemst1.bin','/dev/mem'):self.assertNotIn(text,t)


if __name__=='__main__':unittest.main()
