import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('only_chaldea',ROOT/'tools/wifi-chaldea-only.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class ChaldeaOnlyTests(unittest.TestCase):
 def test_exact_primary_request_only(self):
  M.allowed_request('Chaldea','a',20)
  for args in (('Chaldea-2.4G','bg',25),('Chaldea','bg',20),('Chaldea','a',21),('other','a',20)):
   with self.assertRaises(RuntimeError):M.allowed_request(*args)
 def test_failed_primary_cannot_delegate_to_fallback(self):
  calls=[]
  class Base:
   def activate(self,*args):calls.append(args);return False
  o=M.service_type(SimpleNamespace(Service=Base))();self.assertFalse(o.activate('Chaldea','a',20))
  with self.assertRaises(RuntimeError):o.activate('Chaldea-2.4G','bg',25)
  self.assertEqual(calls,[('Chaldea','a',20)])
 def test_runtime_fallback_is_also_blocked_without_replacing_monitor(self):
  class Base:
   def activate(self,*args):raise AssertionError('Forbidden call reached original worker')
   def monitor(self):return self.activate('Chaldea-2.4G','bg',25)
  o=M.service_type(SimpleNamespace(Service=Base))()
  with self.assertRaises(RuntimeError):o.monitor()
 def test_native_safety_and_cleanup_methods_not_overridden(self):
  class Base:pass
  cls=M.service_type(SimpleNamespace(Service=Base));self.assertEqual({k for k in cls.__dict__ if not k.startswith('__')},{'activate'})
  self.assertEqual(hashlib.sha256((ROOT/'tools/wifi-auto-service.py').read_bytes()).hexdigest(),M.SOURCE_SHA)


if __name__=='__main__':unittest.main()
