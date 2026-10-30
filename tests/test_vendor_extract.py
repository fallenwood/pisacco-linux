# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import importlib.util
import io
import tempfile
import unittest

p = Path(__file__).resolve().parents[1]/'tools/extract-vendor.py'
spec = importlib.util.spec_from_file_location('extract_vendor', p)
vendor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vendor)


class VendorTransferTests(unittest.TestCase):
    def test_reconstruct_sparse_full_image(self):
        ops, blocks = vendor.parse_transfer('4\n2\n0\n0\nnew 2,0,2\nzero 2,2,3\n')
        with tempfile.TemporaryFile() as out:
            vendor.reconstruct(ops, blocks, io.BytesIO(b'A'*(2*vendor.BLOCK)), out)
            out.seek(0)
            self.assertEqual(out.read(), b'A'*(2*vendor.BLOCK)+b'\0'*vendor.BLOCK)

    def test_incremental_commands_rejected(self):
        with self.assertRaises(ValueError):
            vendor.parse_transfer('4\n1\n0\n0\nmove abc 2,0,1\n')

    def test_overlapping_ranges_rejected(self):
        with self.assertRaises(ValueError):
            vendor.parse_transfer('4\n2\n0\n0\nnew 2,0,2\nzero 2,1,3\n')

    def test_invalid_range_count_rejected(self):
        with self.assertRaises(ValueError):
            vendor.parse_transfer('4\n1\n0\n0\nnew 4,0,1\n')

    def test_header_count_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            vendor.parse_transfer('4\n9\n0\n0\nnew 2,0,1\n')

    def test_truncated_or_extra_stream_rejected(self):
        ops, blocks = vendor.parse_transfer('4\n1\n0\n0\nnew 2,0,1\n')
        for data in (b'A', b'A'*(vendor.BLOCK+1)):
            with self.subTest(length=len(data)), tempfile.TemporaryFile() as out:
                with self.assertRaises(ValueError):
                    vendor.reconstruct(ops, blocks, io.BytesIO(data), out)


if __name__ == '__main__':
    unittest.main()
