# SPDX-License-Identifier: GPL-2.0-only
import hashlib,importlib.util,struct,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'tools/provision-wlan-mac.py'
s=importlib.util.spec_from_file_location('wlan_mac',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
# Synthetic unit-test bytes only. Never used as a device fallback.
MAC=bytes.fromhex('001122334455')
def record(mac=MAC):
 return {'source':'libqmi DMS Get MAC Address WLAN, same-device modem using authorized private NV copies','returncode':0,'query_read_only':True,'persist_read':False,'mac':':'.join(f'{v:02x}' for v in mac)}
class WlanMac(unittest.TestCase):
 def test_valid_device_checkpoint(self):self.assertEqual(m.address_from_record(record(),hashlib.sha256(MAC).hexdigest()),MAC)
 def test_no_random_zero_multicast_or_local_fallback(self):
  for v in ('000000000000','ffffffffffff','021122334455','011122334455'):
   mac=bytes.fromhex(v)
   with self.subTest(v=v),self.assertRaises(ValueError):m.address_from_record(record(mac),hashlib.sha256(mac).hexdigest())
 def test_wrong_checkpoint(self):
  with self.assertRaises(ValueError):m.address_from_record(record(),'0'*64)
 def test_provenance_required(self):
  for k,v in [('returncode',1),('source','guessed'),('persist_read',True),('query_read_only',False)]:
   r=record();r[k]=v
   with self.subTest(k=k),self.assertRaises(ValueError):m.address_from_record(r,hashlib.sha256(MAC).hexdigest())
 def test_no_extra_array_count_in_request(self):
  packet=m.request(MAC);self.assertEqual(m.HEADER.unpack_from(packet),(0,m.TXN,0x33,9))
  self.assertEqual(packet[7:],b'\x10\x06\0'+MAC)
 def test_success_only(self):
  payload=m.HEADER.pack(2,m.TXN,0x33,7)+struct.pack('<BHHH',2,4,0,0)
  self.assertFalse(m.response(payload)['random_or_derived_mac_used'])
  for p in (payload[:-1],payload+b'\0',m.HEADER.pack(2,m.TXN+1,0x33,7)+payload[7:],m.HEADER.pack(2,m.TXN,0x33,7)+struct.pack('<BHHH',2,4,1,0x5e)):
   with self.assertRaises(ValueError):m.response(p)
if __name__=='__main__':unittest.main()
