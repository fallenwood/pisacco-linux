# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
from pathlib import Path
import struct
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('picasso_board',ROOT/'tools/pack-picasso-board.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class BoardWrapper(unittest.TestCase):
    def test_roundtrip_preserves_every_factory_byte(self):
        data=bytes(i%251 for i in range(26328));self.assertEqual(m.unpack(m.pack(data)),data)
    def test_single_exact_hex_identity(self):
        b=m.pack(bytes(26328));self.assertEqual(b.count(m.NAME),1)
        self.assertIn(b'qmi-board-id=ff,qmi-chip-id=320,variant=Xiaomi-Picasso',b)
    def test_wrong_payload_size_rejected(self):
        for n in (0,26327,26329):
            with self.assertRaises(ValueError):m.pack(bytes(n))
    def test_bad_magic_rejected(self):
        b=bytearray(m.pack(bytes(26328)));b[0]=0
        with self.assertRaises(ValueError):m.unpack(b)
    def test_wrong_identity_rejected(self):
        b=m.pack(bytes(26328)).replace(b'qmi-chip-id=320',b'qmi-chip-id=321')
        with self.assertRaises(ValueError):m.unpack(b)
    def test_truncated_payload_rejected(self):
        with self.assertRaises(ValueError):m.unpack(m.pack(bytes(26328))[:-4])
    def test_no_generic_board_fallback_entry(self):
        b=m.pack(bytes(26328));self.assertNotIn(b'bus=snoc,qmi-board-id=ff\0',b)
if __name__=='__main__':unittest.main()
