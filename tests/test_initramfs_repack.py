# SPDX-License-Identifier: GPL-2.0-only
import gzip
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
SPEC = importlib.util.spec_from_file_location('repack_initramfs', ROOT / 'tools/repack-initramfs.py')
REPACK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPACK)
from test_bootimg import stock, image
from bootimg import pack, parse_stock


def member(name, data=b'', mode=0o100755):
    fields = [1, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(name) + 1, 0]
    return {'header': b'070701' + b''.join(f'{v:08X}'.encode() for v in fields),
            'namebytes': name.encode() + b'\0', 'name': name, 'data': data}


def archive(init, extra=None):
    entries = [member('bin/busybox', b'unchanged ELF fixture'), member('init', init)]
    if extra:
        entries.extend(extra)
    entries.append(member('TRAILER!!!', mode=0))
    return REPACK.encode_cpio(entries)


def boot(init, extra=None):
    raw = archive(init, extra)
    stream = gzip.compress(raw, compresslevel=0, mtime=0)
    return pack(stock(), image(b'kernel code prefix' + stream + b'linked suffix'))


class InitramfsRepack(unittest.TestCase):
    old = b'#!/bin/busybox sh\ngrep -qx VERSION_ID=44 /newroot/etc/os-release\n'
    new = b"#!/bin/busybox sh\ngrep -qx 'VERSION_ID=4[45]' /newroot/etc/os-release\n"

    def test_only_slot_and_boot_id_changed(self):
        original = boot(self.old)
        changed, receipt = REPACK.repack(original, self.old, self.new)
        self.assertEqual(len(changed), len(original))
        info = parse_stock(changed)
        self.assertEqual(info['dtb'], parse_stock(original)['dtb'])
        kernel = changed[info['page_size']:info['page_size'] + struct.unpack_from('<I', changed, 8)[0]]
        entries = REPACK.find_initramfs(kernel)[3]
        self.assertEqual(next(e['data'] for e in entries if e['name'] == 'init'), self.new)
        self.assertEqual(next(e['data'] for e in entries if e['name'] == 'bin/busybox'), b'unchanged ELF fixture')
        slot = info['page_size'] + receipt['kernel_gzip_offset']
        for i, (a, b) in enumerate(zip(original, changed)):
            if a != b:
                self.assertTrue(576 <= i < 608 or slot <= i < slot + receipt['original_gzip_slot_bytes'])
        self.assertEqual(receipt['status'], 'offline_only_unverified_initramfs_repack_no_device_IO')

    def test_old_init_identity_required(self):
        with self.assertRaisesRegex(ValueError, 'Original init'):
            REPACK.repack(boot(self.old), b'not the original init', self.new)

    def test_replacement_interpreter_required(self):
        with self.assertRaisesRegex(ValueError, 'interpreter'):
            REPACK.repack(boot(self.old), self.old, b'#!/bin/sh\n')

    def test_oversized_new_stream_refused_not_relocated(self):
        large = b'#!/bin/busybox sh\n' + bytes(range(256)) * 100
        info = parse_stock(boot(self.old))
        original = pack(stock(), image(gzip.compress(archive(self.old), compresslevel=9, mtime=0)))
        with self.assertRaisesRegex(ValueError, 'does not fit'):
            REPACK.repack(original, self.old, large)

    def test_duplicate_init_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            REPACK.repack(boot(self.old, [member('init', self.old)]), self.old, self.new)

    def test_multiple_initramfs_rejected(self):
        stream = gzip.compress(archive(self.old), mtime=0)
        original = pack(stock(), image(stream + b'\0' * 8 + stream))
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            REPACK.repack(original, self.old, self.new)

    def test_missing_initramfs_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            REPACK.repack(pack(stock(), image(b'no archive')), self.old, self.new)

    def test_truncated_cpio_rejected(self):
        with self.assertRaises(ValueError):
            REPACK.parse_cpio(archive(self.old)[:180])

    def test_unsafe_member_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            REPACK.parse_cpio(archive(self.old, [member('../escape')]))

    def test_original_metadata_survives_round_trip(self):
        raw = archive(self.old)
        self.assertEqual(REPACK.encode_cpio(REPACK.parse_cpio(raw)), raw)

    def test_nonzero_trailing_archive_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, 'trailer'):
            REPACK.parse_cpio(archive(self.old) + b'junk')


if __name__ == '__main__':
    unittest.main()
