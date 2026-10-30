# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('rmtfs_mem_audit',ROOT/'tools/audit-wifi.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def cells(*v):return struct.pack('>'+str(len(v))+'I',*v)
class MemoryAudit(unittest.TestCase):
    def setUp(self):
        self.n={'compatible':b'qcom,rmtfs-mem\0','size':cells(0,0x282000),'alignment':cells(0,4096),'alloc-ranges':cells(0,0x80000000,0,0x80000000),'no-map':b'','qcom,use-guard-pages':b'','qcom,client-id':cells(1),'qcom,vmid':cells(15)}
        self.t={'/reserved-memory/rmtfs':self.n}
    def test_dynamic_payload_and_two_guards(self):
        r=m.audit_rmtfs(self.t);self.assertEqual(r['reserved_bytes']-r['guard_bytes'],0x280000)
    def test_guessed_fixed_address_rejected(self):
        self.n['reg']=cells(0,0xff000000,0,0x282000)
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
    def test_missing_guards_rejected(self):
        del self.n['qcom,use-guard-pages']
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
    def test_missing_no_map_rejected(self):
        del self.n['no-map']
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
    def test_wrong_client_rejected(self):
        self.n['qcom,client-id']=cells(0)
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
    def test_wrong_vmid_rejected(self):
        self.n['qcom,vmid']=cells(3)
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
    def test_high_memory_allocation_rejected(self):
        self.n['alloc-ranges']=cells(1,0,1,0)
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
    def test_wrong_payload_size_rejected(self):
        self.n['size']=cells(0,0x280000)
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
    def test_unaligned_region_rejected(self):
        self.n['alignment']=cells(0,1)
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
    def test_duplicate_shared_regions_rejected(self):
        self.t['/reserved-memory/other']=dict(self.n)
        with self.assertRaises(ValueError):m.audit_rmtfs(self.t)
if __name__=='__main__':unittest.main()
