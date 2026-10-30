import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('wifi_reconnect',ROOT/'tools/wifi-reconnect-service.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R)


def clean_case():
 return ({'Result':'exit-code','ExecMainStatus':'1'},
 {'status':'failed','error':'RuntimeError: Fallback link lost; no restart loop','cleanup_status':'safe_cleanup_complete','nv_armed':True,'peak_temperature_mc':38400},
 {'status':'safe_cleanup_complete','children_stopped':True,'wlan_absent':True,'original_core_restored':True,'cpu_limits_restored':True,'private_copy_checkpoint_committed':True,'dsp':'offline','shared_ram_cleared_bytes':2621440})


class WifiReconnectTests(unittest.TestCase):
 def test_exact_backoff_initial_and_three_no_wraparound(self):
  self.assertEqual([R.retry_delay(i) for i in range(4)],[0,10,30,60])
  for n in (-1,4,5,True):
   with self.assertRaises(RuntimeError):R.retry_delay(n)
 def test_only_exact_ordinary_errors_with_complete_cleanup_retry(self):
  u,r,c=clean_case()
  for error in R.RETRY_ERRORS:self.assertTrue(R.retry_allowed(u,{**r,'error':error},c))
  for error in ('RuntimeError: 45C thermal abort','RuntimeError: DSP stopped or crashed','RuntimeError: Actual SG intersection rejected','RuntimeError: Work checkpoint mismatch','RuntimeError: unknown'):
   self.assertFalse(R.retry_allowed(u,{**r,'error':error},c))
 def test_watchdog_timeout_signal_and_nonstandard_exit_never_retry(self):
  u,r,c=clean_case()
  for result in ('watchdog','timeout','signal','oom-kill','success'):self.assertFalse(R.retry_allowed({**u,'Result':result},r,c))
  self.assertFalse(R.retry_allowed({**u,'ExecMainStatus':'2'},r,c))
 def test_each_cleanup_proof_is_mandatory(self):
  u,r,c=clean_case()
  for key in c:
   changed=dict(c);changed.pop(key);self.assertFalse(R.retry_allowed(u,r,changed),key)
 def test_safety_and_exact_45c_stop_not_retry(self):
  u,r,c=clean_case()
  for change in ({'unsafe_nv_stop':True},{'nv_armed':False},{'peak_temperature_mc':45000},{'peak_temperature_mc':-1},{'peak_temperature_mc':True}):self.assertFalse(R.retry_allowed(u,{**r,**change},c))
 def test_template_unchanged_worker_independent_cleanup_bound_to_owner(self):
  body=R.worker_body()
  for x in ('BindsTo=picasso-wifi-reconnect.service','After=picasso-wifi-reconnect.service','ExecStopPost=/usr/bin/python3 -I /opt/picasso-wifi/wifi-auto-service.py --cleanup','Restart=no','WatchdogSec=8s','TimeoutStopSec=45s','MemoryMax=256M','RuntimeDirectoryPreserve=yes'):self.assertIn(x,body)
 def test_pinned_worker_is_original_native_probation_code(self):
  self.assertEqual(hashlib.sha256((ROOT/'tools/wifi-auto-service.py').read_bytes()).hexdigest(),R.WORKER_SHA)
  self.assertEqual(len(R.FDTS),2)
 def test_no_arbitrary_child_or_dependency_units(self):
  with self.assertRaises(RuntimeError):R.props('sshd.service')
  with self.assertRaises(RuntimeError):R.props('picasso-wifi-session-../../x.service')
 def test_owner_stop_does_not_stop_uncreated_colliding_name(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'budget.json';name='picasso-wifi-session-2f080316-0123456789ab.service';p.write_text(json.dumps({'boot_id':'boot','current_unit':name,'attempts':[{'unit':name}]}))
   with patch.object(R,'budget_path',return_value=('boot',p)),patch.object(R,'clean_ready') as clean,patch.object(R,'props') as props:
    self.assertEqual(R.cleanup_owned()['status'],'planned_child_not_created_no_stop');clean.assert_called_once();props.assert_not_called()
 def test_no_stop_if_unit_file_inode_owner_changed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'budget.json';name='picasso-wifi-session-2f080316-0123456789ab.service';p.write_text(json.dumps({'boot_id':'boot','current_unit':name,'attempts':[{'unit':name,'definition_identity':[0,0]}]}))
   fake=SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_uid=1000,st_nlink=1,st_dev=0,st_ino=0)
   with patch.object(R,'budget_path',return_value=('boot',p)),patch.object(Path,'lstat',return_value=fake),patch.object(R,'props') as props:
    with self.assertRaises(RuntimeError):R.cleanup_owned()
    props.assert_not_called()
 def test_durable_intent_is_exclusive_never_deletes_markers(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'intent.json';R.durable(p,{'attempts':[1]},True)
   with self.assertRaises(FileExistsError):R.durable(p,{'attempts':[]},True)
   self.assertEqual(json.loads(p.read_text())['attempts'],[1])
 def run_fake(self,outcome):
  o=R.Supervisor.__new__(R.Supervisor);o.budget={'attempts':[]};o.lock=os.open(os.devnull,os.O_RDONLY);o.tick=lambda:{'sensor':35000};o.save=lambda phase,**kw:o.budget.update(phase=phase,**kw)
  def attempt():o.budget['attempts'].append({'unit':'fake'});return outcome
  o.attempt=attempt
  with patch.object(R,'fixed_assets'),patch.object(R,'clean_ready'),patch.object(R,'notify'),patch.object(R,'cleanup_owned',return_value={'status':'clean'}):rc=o.execute()
  return o,rc
 def test_simulated_clean_ordinary_failures_stop_after_four_attempts(self):
  o,rc=self.run_fake('retryable');self.assertEqual(rc,1);self.assertEqual(len(o.budget['attempts']),4);self.assertIn('exhausted',o.budget['error'])
 def test_simulated_safety_failure_does_not_consume_retry(self):
  o,rc=self.run_fake('safety_or_unknown_failure');self.assertEqual(rc,1);self.assertEqual(len(o.budget['attempts']),1)
 def test_supervisor_sandbox_and_failed_history_preservation(self):
  text=(ROOT/'tools/picasso-wifi-reconnect.service').read_text();code=(ROOT/'tools/wifi-reconnect-service.py').read_text()
  for x in ('Restart=no','WatchdogSec=8s','ExecStopPost=','CapabilityBoundingSet=','RestrictAddressFamilies=AF_UNIX','@module','DevicePolicy=closed'):self.assertIn(x,text)
  for x in ('reset-failed','--collect','restart always','modemst1.bin','/dev/mem','--show-secrets','systemctl reboot'):self.assertNotIn(x,code)
  self.assertIn("digest(p)==expected",code);self.assertIn("not (WIFI/'dirty.json').exists()",code);self.assertIn('definition_identity',code)
 def test_clean_stop_resume_preserves_consumed_budget(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'budget.json';p.write_text(json.dumps({'schema':1,'boot_id':'boot','phase':'operator_stopped_clean','attempts':[{'unit':'first'},{'unit':'second'}]}))
   with patch.object(R,'STATE',root/'state'),patch.object(R,'RUN',root/'run'),patch.object(R,'budget_path',return_value=('boot',p)),patch.object(R.os,'open',return_value=123),patch.object(R.fcntl,'flock'):
    o=R.Supervisor();self.assertEqual(len(o.budget['attempts']),2);self.assertEqual(R.retry_delay(len(o.budget['attempts'])),30)
 def test_halted_or_exhausted_boot_budget_cannot_be_replayed(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'budget.json'
   for phase,count in (('halted_safety_or_budget',1),('operator_stopped_clean',4),('online',1)):
    p.write_text(json.dumps({'schema':1,'boot_id':'boot','phase':phase,'attempts':[{}]*count}))
    with patch.object(R,'STATE',root/'state'),patch.object(R,'RUN',root/'run'),patch.object(R,'budget_path',return_value=('boot',p)),patch.object(R.os,'open',return_value=123),patch.object(R.fcntl,'flock'):
     with self.assertRaises(RuntimeError):R.Supervisor()
 def test_supervisor_ready_is_explicitly_not_wlan_readiness(self):
  code=(ROOT/'tools/wifi-reconnect-service.py').read_text();self.assertIn('WLAN not yet connected',code)
  self.assertLess(code.index('READY=1\\nSTATUS=Guarded reconnect'),code.index('outcome=self.attempt()'))


if __name__=='__main__':unittest.main()
