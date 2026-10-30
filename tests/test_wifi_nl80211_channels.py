import importlib.util,json,struct,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('raw_phy_get',ROOT/'tools/wifi-nl80211-channels.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
def attr(k,p=b''):return M.attribute(k,p)
def integer(x):return struct.pack('=I',x)
def frequency(indoor=True,power=2300,disabled=False):
 return attr(1,integer(5180))+attr(6,integer(power))+(attr(14) if indoor else b'')+(attr(2) if disabled else b'')
def message(channel,phy=0):
 bands=attr(1,attr(1,attr(1,channel)))
 return bytes([3,1,0,0])+attr(1,integer(phy))+attr(2,b'phy0\0')+attr(22,bands)

class FakeSocket:
 def __init__(self,interrupted=False):self.pending=None;self.commands=[];self.interrupted=interrupted
 def bind(self,x):pass
 def getsockname(self):return (4242,0)
 def settimeout(self,x):pass
 def close(self):pass
 def sendto(self,data,dest):
  length,family,flags,seq,pid=struct.unpack_from('=IHHII',data);cmd=data[16];self.commands.append((family,cmd,flags))
  if family==16 and cmd==3:payload=bytes([1,2,0,0])+attr(1,struct.pack('=H',40));kind=16;fl=0
  elif cmd==95:payload=bytes([95,1,0,0])+attr(173,integer(1));kind=family;fl=0
  elif cmd==1:payload=integer(0);kind=3;fl=16 if self.interrupted else 0
  else:raise AssertionError('Unexpected command')
  self.pending=struct.pack('=IHHII',16+len(payload),kind,fl,seq,pid)+payload
 def recvmsg(self,limit):return self.pending,[],0,(0,0)

def client(sock):
 c=M.ReadOnlyNetlink.__new__(M.ReadOnlyNetlink);c.sock=sock;c.port=4242;c.sequence=100;c.deadline=time.monotonic()+8;c.bytes=0;c.messages=0;c.family=None;return c

class RawPhyEvidence(unittest.TestCase):
 def test_exact_indoor_attribute_preserved(self):
  r=M.decode_frequency(frequency());self.assertTrue(r['indoor_only']);self.assertIn(14,r['observed_attribute_ids']);self.assertEqual(r['max_tx_power_mbm'],2300)
 def test_absence_not_replaced_by_iw_text_assumption(self):
  r=M.decode_frequency(frequency(False));self.assertFalse(r['indoor_only']);self.assertNotIn(14,r['observed_attribute_ids'])
 def test_nonempty_flag_rejected(self):
  with self.assertRaises(ValueError):M.decode_frequency(frequency(False)+attr(14,b'\x01'))
 def test_disabled_channel_need_not_have_power(self):
  r=M.decode_frequency(attr(1,integer(5500))+attr(2));self.assertTrue(r['disabled']);self.assertIsNone(r['max_tx_power_mbm'])
 def test_enabled_channel_missing_power_rejected(self):
  with self.assertRaises(ValueError):M.decode_frequency(attr(1,integer(5180))+attr(14))
 def test_truncation_duplicate_or_malformed_padding_rejected(self):
  for data in (b'\x03\x00\x01\x00',attr(1,integer(5180))[:-1],attr(1,integer(5180))*2,b'\x05\x00\x01\x00a\x01\0\0'):
   with self.assertRaises(ValueError):M.attributes(data)
 def test_merge_split_PHY_and_duplicate_consistency(self):
  phys={};M.merge_wiphy(phys,message(frequency()));M.merge_wiphy(phys,message(frequency()));self.assertTrue(next(iter(phys[0]['channels'].values()))['indoor_only'])
  with self.assertRaises(ValueError):M.merge_wiphy(phys,message(frequency(False)))
 def test_wrong_response_command_rejected(self):
  with self.assertRaises(ValueError):M.merge_wiphy({},bytes([2,1,0,0])+attr(1,integer(0)))
 def test_only_three_fixed_GETs_and_empty_dump_not_live_proof(self):
  sock=FakeSocket();r=client(sock).collect();self.assertEqual([x[1] for x in sock.commands],[3,95,1]);self.assertEqual(sock.commands[-1][2],0x301);self.assertEqual(r['phys'],[]);self.assertTrue(r['complete_dump']);self.assertTrue(r['no_PHYS_does_not_prove_live_indoor_flags'])
 def test_requested_missing_PHY_rejected(self):
  with self.assertRaises(ValueError):client(FakeSocket()).collect(0)
 def test_dump_interruption_is_not_complete_evidence(self):
  with self.assertRaisesRegex(ValueError,'Interrupted'):client(FakeSocket(True)).collect()
 def test_SET_or_scan_not_permitted_by_transport(self):
  c=client(FakeSocket());c.family=40
  for command in (2,33,34,103):
   with self.assertRaisesRegex(ValueError,'Only fixed GET'):c.exchange(40,command)
if __name__=='__main__':unittest.main()
