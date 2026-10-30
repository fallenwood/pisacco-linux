# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
import os
from pathlib import Path
import struct
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rmtfs_proxy',ROOT/'tools/rmtfs-private-proxy.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def u32(n):return struct.pack('<I',n)
def request(msg,fields):
    body=b''.join(m.tlv(k,v) for k,v in fields)
    return m.HEADER.pack(0,7,msg,len(body))+body

def result(reply):return struct.unpack_from('<HH',reply,10)


class PrivateProxy(unittest.TestCase):
    def setUp(self):
        self.fds=[]
        for size in (m.MEMORY_SIZE,m.IMAGE_SIZE,m.IMAGE_SIZE,m.IMAGE_SIZE):
            fd=os.memfd_create('synthetic-offline-test');os.ftruncate(fd,size);self.fds.append(fd)
        self.b=m.Backend(self.fds[0],dict(zip(m.PATHS.values(),self.fds[1:])),0xff000000)
        reply,_=self.b.handle(request(1,[(1,b'/boot/modem_fs1')]))
        self.assertEqual(result(reply),(0,0));self.h=1
        self.b.handle(request(4,[(1,u32(self.h)),(2,u32(2*1024**2))]))
    def tearDown(self):
        for fd in self.fds:os.close(fd)
    def call(self,msg,fields,node=0):return self.b.handle(request(msg,fields),node)[0]
    def vector(self,direction,entries,force=0):
        data=bytes([len(entries)])+b''.join(struct.pack('<III',*e) for e in entries)
        return self.call(3,[(1,u32(self.h)),(2,bytes([direction])),(3,data),(4,bytes([force]))])
    def test_reads_real_copy_bytes_to_shared_buffer(self):
        os.pwrite(self.fds[1],b'A'*512,0)
        self.assertEqual(result(self.vector(0,[(0,self.b.base,1)])),(0,0))
        self.assertEqual(os.pread(self.fds[0],512,0),b'A'*512)
    def test_writes_only_private_working_copy(self):
        os.pwrite(self.fds[0],b'B'*512,0)
        self.assertEqual(result(self.vector(1,[(1,self.b.base,1)])),(0,0))
        self.assertEqual(os.pread(self.fds[1],512,512),b'B'*512)
        self.assertEqual(os.pread(self.fds[2],512,512),bytes(512))
    def test_client_buffer_is_shared_across_files(self):
        reply=self.call(1,[(1,b'/boot/modem_fs2')]);self.assertEqual(result(reply),(0,0))
        self.h=2;os.pwrite(self.fds[2],b'D'*512,0)
        self.assertEqual(result(self.vector(0,[(0,self.b.base,1)])),(0,0))
        self.assertEqual(os.pread(self.fds[0],512,0),b'D'*512)
    def test_closing_one_file_does_not_revoke_global_buffer(self):
        self.call(1,[(1,b'/boot/modem_fs2')]);self.call(2,[(1,u32(1))]);self.h=2
        self.assertEqual(result(self.vector(0,[(0,self.b.base,1)])),(0,0))
    def test_source_data_never_in_metadata(self):
        secret=b'NV-not-to-be-logged'*28
        os.pwrite(self.fds[1],secret,0)
        reply,meta=self.b.handle(request(3,[(1,u32(1)),(2,b'\0'),(3,b'\x01'+struct.pack('<III',0,self.b.base,1)),(4,b'\0')]))
        self.assertNotIn('NV-not',repr(meta));self.assertNotIn(b'NV-not',reply)
    def test_unknown_partition_rejected_without_open(self):
        p=b'/boot/modem_fsc'
        with patch('builtins.open',side_effect=AssertionError('No requested path open')):
            reply=self.call(1,[(1,p)])
        self.assertNotEqual(result(reply),(0,0));self.assertEqual(len(self.b.handles),1)
    def test_raw_absolute_nv_path_rejected(self):
        p=b'/dev/sdf2';self.assertNotEqual(result(self.call(1,[(1,p)])),(0,0))
    def test_traversal_rejected(self):
        p=b'/boot/../persist';self.assertNotEqual(result(self.call(1,[(1,p)])),(0,0))
    def test_wrong_node_denied(self):
        self.assertNotEqual(result(self.call(5,[(1,u32(1))],node=1)),(0,0))
    def test_bad_cookie_denied(self):
        for n in (0,0xffffffff,4):self.assertNotEqual(result(self.call(5,[(1,u32(n))])),(0,0))
    def test_closed_cookie_denied(self):
        self.assertEqual(result(self.call(2,[(1,u32(1))])),(0,0))
        self.assertNotEqual(result(self.call(5,[(1,u32(1))])),(0,0))
    def test_oversized_allocations_denied(self):
        for n in (0,m.MEMORY_SIZE+1,0xffffffff):self.assertNotEqual(result(self.call(4,[(1,u32(1)),(2,u32(n))])),(0,0))
    def test_buffer_underflow_denied(self):
        self.assertNotEqual(result(self.vector(0,[(0,self.b.base-512,1)])),(0,0))
    def test_buffer_overflow_denied(self):
        self.assertNotEqual(result(self.vector(0,[(0,self.b.base+2*1024**2,1)])),(0,0))
    def test_disk_out_of_bounds_denied(self):
        for sector in (m.IMAGE_SIZE//512,0xffffffff):self.assertNotEqual(result(self.vector(0,[(sector,self.b.base,1)])),(0,0))
    def test_prevalidates_all_vectors_before_writes(self):
        os.pwrite(self.fds[0],b'C'*512,0)
        self.assertNotEqual(result(self.vector(1,[(0,self.b.base,1),(0,self.b.base-512,1)])),(0,0))
        self.assertEqual(os.pread(self.fds[1],512,0),bytes(512))
    def test_huge_sector_count_denied(self):
        self.assertNotEqual(result(self.vector(1,[(0,self.b.base,0xffffffff)])),(0,0))
    def test_bad_direction_denied(self):
        self.assertNotEqual(result(self.vector(2,[(0,self.b.base,1)])),(0,0))
    def test_duplicate_tlv_rejected_before_io(self):
        with self.assertRaises(ValueError):self.b.handle(request(5,[(1,u32(1)),(1,u32(1))]))
    def test_short_tlv_rejected(self):
        with self.assertRaises(ValueError):m.parse(m.HEADER.pack(0,7,1,3)+b'\1\xff\xff')
    def test_truncated_array_rejected(self):
        self.assertNotEqual(result(self.call(3,[(1,u32(1)),(2,b'\0'),(3,b'\xff'),(4,b'\0')])),(0,0))
    def test_dev_error_valid_cookie_success(self):
        self.assertEqual(result(self.call(5,[(1,u32(1))])),(0,0))
    def test_short_reads_not_zero_padded(self):
        os.ftruncate(self.fds[1],1)
        self.assertNotEqual(result(self.vector(0,[(0,self.b.base,1)])),(0,0))
    def test_unauthorized_backing_set_rejected(self):
        with self.assertRaises(ValueError):m.Backend(self.fds[0],{'persist':self.fds[1]},self.b.base)
    def test_wrong_physical_range_rejected(self):
        for base in (1,0x100000000):
            with self.assertRaises(ValueError):m.Backend(self.fds[0],self.b.images,base)


class DescriptorGuard(unittest.TestCase):
    def test_block_devices_rejected_for_private_images(self):
        # The production guard uses real fstat; a regular test FD also cannot
        # stand in for the required kernel shared-memory character device.
        fd=os.memfd_create('not-a-kernel-device')
        try:
            with patch.dict(os.environ,{'LISTEN_PID':str(os.getpid()),'LISTEN_FDS':'4','LISTEN_FDNAMES':'rmtfs_mem:modem_fs1:modem_fs2:modem_fsg'}):
                fake=os.stat_result((0o060600,0,0,1,0,0,m.IMAGE_SIZE,0,0,0))
                with patch.object(m.os,'fstat',return_value=fake),patch.object(m.fcntl,'fcntl',return_value=os.O_RDWR):
                    with self.assertRaises(ValueError):m.inherited_fds(250,1)
        finally:os.close(fd)
    def specs(self):
        return [SimpleNamespace(st_mode=stat.S_IFCHR|0o600,st_rdev=os.makedev(250,1))]+[SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_size=m.IMAGE_SIZE,st_nlink=1,st_uid=0,st_dev=42,st_ino=i) for i in range(3)]
    def guard(self,specs):
        with patch.dict(os.environ,{'LISTEN_PID':str(os.getpid()),'LISTEN_FDS':'4','LISTEN_FDNAMES':'rmtfs_mem:modem_fs1:modem_fs2:modem_fsg'}):
            with patch.object(m.os,'fstat',side_effect=specs),patch.object(m.fcntl,'fcntl',return_value=os.O_RDWR):
                return m.inherited_fds(250,1)
    def test_valid_four_descriptor_layout(self):
        self.assertEqual(self.guard(self.specs())['modem_fsg'],6)
    def test_nv_raw_block_fd_denied(self):
        s=self.specs();s[1].st_mode=stat.S_IFBLK|0o600
        with self.assertRaises(ValueError):self.guard(s)
    def test_readonly_master_image_denied(self):
        s=self.specs();s[1].st_mode=stat.S_IFREG|0o400
        with self.assertRaises(ValueError):self.guard(s)
    def test_aliased_image_fds_denied(self):
        s=self.specs();s[2].st_ino=s[1].st_ino
        with self.assertRaises(ValueError):self.guard(s)
    def test_other_memory_char_device_denied(self):
        s=self.specs();s[0].st_rdev=os.makedev(1,1)
        with self.assertRaises(ValueError):self.guard(s)
    def test_activation_missing_rejected(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):m.inherited_fds(250,1)


if __name__=='__main__':unittest.main()
