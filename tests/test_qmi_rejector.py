# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qmi_rejector',ROOT/'tools/qmi-rejector.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


def packet(msg=1,body=b''):
    return struct.pack('<BHHH',0,42,msg,len(body))+body


class RejectOnly(unittest.TestCase):
    def test_only_failure_no_handle_or_address(self):
        reply,meta=mod.reject(packet())
        self.assertEqual(reply,struct.pack('<BHHH',2,42,1,7)+struct.pack('<BHHH',2,4,1,0x5e))
        self.assertFalse(meta['storage_access'])
    def test_open_factory_path_only_logged_not_opened(self):
        path=b'/boot/modem_fs1';body=struct.pack('<BH',1,len(path)+1)+bytes([len(path)])+path
        with patch('builtins.open',side_effect=AssertionError('No file I/O')):
            reply,meta=mod.reject(packet(body=body))
        self.assertEqual(meta['fields'][0]['known_factory_path'],'/boot/modem_fs1')
        self.assertEqual(meta['reply'],'NOT_SUPPORTED')
    def test_unknown_data_not_logged(self):
        secret=b'private-NV-payload'
        _,meta=mod.reject(packet(msg=3,body=struct.pack('<BH',2,len(secret))+secret))
        self.assertNotIn('private',repr(meta));self.assertNotIn('payload',repr(meta))
    def test_short_header_rejected(self):
        for n in range(7):self.assertIsNone(mod.reject(bytes(n)))
    def test_wrong_length_rejected(self):
        self.assertIsNone(mod.reject(packet()+b'\0'))
    def test_indication_not_replied_to(self):
        p=bytearray(packet());p[0]=4;self.assertIsNone(mod.reject(p))
    def test_truncated_tlv_rejected(self):
        self.assertIsNone(mod.reject(packet(body=b'\x01\x08\x00bad')))
        self.assertIsNone(mod.reject(packet(body=b'\x01')))
    def test_all_message_ids_get_failure(self):
        for msg in (1,2,3,4,5,0xffff):
            reply,_=mod.reject(packet(msg));self.assertEqual(struct.unpack_from('<H',reply,12)[0],0x5e)


if __name__=='__main__':unittest.main()
