# SPDX-License-Identifier: GPL-2.0-only
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bootimg', ROOT / 'tools/bootimg.py')
bootimg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootimg)


def fdt(payload=b''):
    # Structurally sufficient for the concatenation/bounds validator.
    return struct.pack('>10I', 0xd00dfeed, 40 + len(payload), 40, 40, 40, 17, 16, 0, 0, 0) + payload


def image(payload=b''):
    data = bytearray(64)
    data[56:60] = b'ARMd'
    struct.pack_into('<Q', data, 16, len(data) + len(payload))
    return bytes(data) + payload


def stock(page=4096, recovery=b'', second=b''):
    header = bytearray(1660)
    header[:8] = b'ANDROID!'
    dtbs = fdt(b'one') + fdt(b'two')
    kernel, ramdisk = b'STOCK-KERNEL', b'STOCK-RAMDISK'
    for off, value in {8: len(kernel), 12: 0x8000, 16: len(ramdisk), 20: 0x1000000,
                       24: len(second), 36: page, 40: 2, 1632: len(recovery),
                       1644: 1660, 1648: len(dtbs)}.items():
        struct.pack_into('<I', header, off, value)
    struct.pack_into('<Q', header, 1652, 0x1f00000)
    result = bytes(header).ljust(page, b'\0')
    for part in (kernel, ramdisk, second):
        result += part.ljust(bootimg.align(len(part), page), b'\0')
    if recovery:
        header = bytearray(result[:page])
        struct.pack_into('<Q', header, 1636, len(result))
        result = bytes(header) + result[page:]
        result += recovery.ljust(bootimg.align(len(recovery), page), b'\0')
    return result + dtbs


class BootImageTests(unittest.TestCase):
    def test_parse(self):
        info = bootimg.parse_stock(stock())
        self.assertEqual(info['dtb_offset'], 3 * 4096)
        self.assertEqual(info['dtb_count'], 2)

    def test_roundtrip_preserves_stock_dtb_and_addresses(self):
        original = stock()
        packed = bootimg.pack(original, image(b'linux'))
        before, after = bootimg.parse_stock(original), bootimg.parse_stock(packed)
        self.assertEqual(before['dtb'], after['dtb'])
        self.assertEqual(after['dtb_offset'], 2 * 4096)
        for start, end in ((12,16), (20,24), (28,40), (1652,1660)):
            self.assertEqual(original[start:end], packed[start:end])
        self.assertEqual(struct.unpack_from('<I', packed, 16)[0], 0)

    def test_legacy_id(self):
        kernel = image(b'linux')
        original = stock()
        packed = bootimg.pack(original, kernel)
        h = hashlib.sha1()
        for payload in (kernel, b'', b'', b'', bootimg.parse_stock(original)['dtb']):
            h.update(payload + struct.pack('<I', len(payload)))
        self.assertEqual(packed[576:608], h.digest().ljust(32,b'\0'))

    def test_page_sizes(self):
        for page in (2048, 4096, 8192, 16384):
            with self.subTest(page=page):
                packed = bootimg.pack(stock(page), image())
                self.assertEqual(len(packed) % page, 0)
                self.assertEqual(bootimg.parse_stock(packed)['dtb_count'], 2)

    def test_second_and_recovery_removed(self):
        original = stock(second=b'second', recovery=b'overlay')
        self.assertEqual(bootimg.parse_stock(original)['dtb_offset'], 5 * 4096)
        packed = bootimg.pack(original, image())
        self.assertEqual(bootimg.parse_stock(packed)['dtb_offset'], 2 * 4096)
        self.assertEqual(struct.unpack_from('<I', packed, 24)[0], 0)
        self.assertEqual(struct.unpack_from('<I', packed, 1632)[0], 0)
        self.assertEqual(struct.unpack_from('<Q', packed, 1636)[0], 0)

    def test_wrong_magic(self):
        with self.assertRaises(ValueError): bootimg.parse_stock(b'bad')

    def test_v3_rejected(self):
        data = bytearray(stock())
        struct.pack_into('<I', data, 40, 3)
        with self.assertRaises(ValueError): bootimg.parse_stock(data)

    def test_invalid_pages_rejected(self):
        for page in (0, 1024, 3000, 131072):
            data = bytearray(stock())
            struct.pack_into('<I', data, 36, page)
            with self.subTest(page=page), self.assertRaises(ValueError): bootimg.parse_stock(data)

    def test_truncated_dtb_rejected(self):
        with self.assertRaises(ValueError): bootimg.parse_stock(stock()[:-1])

    def test_invalid_fdt_sizes_rejected(self):
        for size in (0, 39, 0xffffffff):
            data = bytearray(fdt())
            struct.pack_into('>I', data, 4, size)
            with self.subTest(size=size), self.assertRaises(ValueError): bootimg.fdt_count(data)

    def test_empty_fdt_rejected(self):
        with self.assertRaises(ValueError): bootimg.fdt_count(bytes(40))

    def test_non_image_rejected(self):
        with self.assertRaises(ValueError): bootimg.pack(stock(), bytes(64))

    def test_image_size_mismatch_rejected(self):
        with self.assertRaises(ValueError): bootimg.pack(stock(), image() + b'junk')

    def test_partition_size_limit(self):
        with self.assertRaises(ValueError): bootimg.pack(stock(), image(), max_size=4096)

    def test_bad_recovery_offset_rejected(self):
        data = bytearray(stock(recovery=b'recovery'))
        struct.pack_into('<Q', data, 1636, 100)
        with self.assertRaises(ValueError): bootimg.parse_stock(data)


if __name__ == '__main__':
    unittest.main()
