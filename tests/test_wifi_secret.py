# SPDX-License-Identifier: GPL-2.0-only
import importlib.util,os,stat,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1]/'tools/enter-chaldea-secret.py'
s=importlib.util.spec_from_file_location('wifi_secret',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Secret(unittest.TestCase):
 def test_no_plaintext_in_passwd_value(self):
  # Synthetic test credential, never a deployment default.
  v=m.psk_value('unit-test-only-passphrase');self.assertEqual(len(v),64);self.assertNotIn('unit-test',v)
 def test_raw_psk(self):self.assertEqual(m.psk_value('A'*64),'a'*64)
 def test_invalid_input_rejected(self):
  for v in ('short','x'*64,'line\nbreak','nul\0data','x'*65):
   with self.assertRaises(ValueError):m.psk_value(v)
 def test_no_overwrite_symlink_or_existing_file(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'secret';p.write_text('sentinel')
   # Parent owner check intentionally requires root in production.
   fake=os.stat(d)
   parent=type('S',(),{'st_uid':0,'st_mode':fake.st_mode})()
   original=Path.stat
   def controlled(path,*a,**kw):return parent if path==Path(d) else original(path,*a,**kw)
   with patch.object(m,'DEST',p),patch.object(Path,'stat',controlled):
    with self.assertRaises(FileExistsError):m.save('unit-test-only-passphrase')
   self.assertEqual(p.read_text(),'sentinel')
 def test_pinned_wrapper_and_no_argv_secret(self):
  s=(P.parent/'enter-chaldea-password.sh').read_text();self.assertIn('StrictHostKeyChecking=yes',s)
  self.assertIn('UserKnownHostsFile=',s);self.assertNotIn('StrictHostKeyChecking=no',s)
  self.assertIn('[[ -t 0 && -t 2 ]]',s)
 def test_same_passphrase_uses_target_specific_ssid_and_destination(self):
  old=m.psk_value('unit-test-only-passphrase')
  with patch.object(m,'SSID',m.SSID),patch.object(m,'DEST',m.DEST):
   m.configure_target('Chaldea-2.4G')
   self.assertEqual(m.SSID,b'Chaldea-2.4G')
   self.assertEqual(m.DEST,Path('/run/picasso-chaldea-2g.passwd'))
   value=m.psk_value('unit-test-only-passphrase')
   self.assertNotEqual(value,old)
   self.assertEqual(value,m.hashlib.pbkdf2_hmac('sha1',b'unit-test-only-passphrase',b'Chaldea-2.4G',4096,32).hex())
 def test_target_allowlist_rejects_others_without_mutating_state(self):
  old=(m.SSID,m.DEST)
  for name in ('Other','Chaldea-2.4G\n','Chaldea-2.4G;id'):
   with self.assertRaises(ValueError):m.configure_target(name)
   self.assertEqual((m.SSID,m.DEST),old)
 def test_2g_wrapper_uses_explicit_ssid_and_pinned_local_terminal(self):
  s=(P.parent/'enter-chaldea-2g-password.sh').read_text()
  self.assertIn('--ssid Chaldea-2.4G',s)
  self.assertIn('StrictHostKeyChecking=yes',s)
  self.assertIn('UserKnownHostsFile=',s)
  self.assertIn('[[ -t 0 && -t 2 ]]',s)
  self.assertNotIn('--show-secrets',s)
 def test_one_shot_test_is_explicit_tty_and_pinned_and_checks_actual_result(self):
  s=(P.parent/'test-chaldea-2g.sh').read_text()
  self.assertIn('[[ -t 0 && -t 2 ]]',s)
  self.assertIn('StrictHostKeyChecking=yes',s)
  self.assertIn('UserKnownHostsFile=',s)
  self.assertIn('enter-chaldea-2g-password.sh',s)
  self.assertIn('run-connect.py',s)
  self.assertIn("startswith('passed_')",s)
  self.assertIn('test ! -e /run/picasso-chaldea-2g.passwd',s)
  self.assertNotIn('--show-secrets',s)
  self.assertNotIn('reset-failed',s)
 def test_one_shot_cold_native_preflight_precedes_local_secret_entry(self):
  s=(P.parent/'test-chaldea-2g.sh').read_text()
  self.assertIn('wifi-chaldea-2g-connect4-20261028',s)
  self.assertNotIn('wifi-chaldea-2g-connect3',s)
  self.assertLess(s.index("<40000"),s.index('"$ROOT/tools/enter-chaldea-2g-password.sh"'))
  self.assertLess(s.index("=='offline'"),s.index('"$ROOT/tools/enter-chaldea-2g-password.sh"'))
if __name__=='__main__':unittest.main()
