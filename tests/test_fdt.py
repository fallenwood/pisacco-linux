# SPDX-License-Identifier: GPL-2.0-only
import hashlib
import importlib.util
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import fdt
spec = importlib.util.spec_from_file_location('inspect_rom', ROOT/'tools/inspect-rom.py')
inspect_rom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspect_rom)


def make_fdt(props=None, children=None):
    strings, offsets = bytearray(), {}

    def pad(data):
        return data + b'\0' * (-len(data) % 4)

    def node(name, properties, descendants):
        result = struct.pack('>I', 1) + pad(name.encode() + b'\0')
        for key, value in properties.items():
            if key not in offsets:
                offsets[key] = len(strings)
                strings.extend(key.encode() + b'\0')
            result += struct.pack('>III', 3, len(value), offsets[key]) + pad(value)
        for child in descendants:
            result += node(*child)
        return result + struct.pack('>I', 2)

    body = node('', props or {}, children or []) + struct.pack('>I', 9)
    return (struct.pack('>10I', fdt.FDT_MAGIC, 56 + len(body) + len(strings),
                        56, 56 + len(body), 40, 17, 16, 0, len(strings), len(body))
            + bytes(16) + body + bytes(strings))


def make_table(*blobs):
    offset = 32 + len(blobs) * 32
    entries = b''
    for blob in blobs:
        entries += struct.pack('>8I', len(blob), offset, 0, 0, 0, 0, 0, 0)
        offset += len(blob)
    return struct.pack('>8I', fdt.DTBO_MAGIC, offset, 32, 32, len(blobs), 32, 4096, 0) + entries + b''.join(blobs)


class FdtTests(unittest.TestCase):
    def test_nodes_and_properties(self):
        blob = make_fdt({'model': b'Picasso\0'}, [('memory', {'reg': bytes(16)}, [])])
        tree = fdt.nodes(blob)
        self.assertEqual(tree['/']['model'], b'Picasso\0')
        self.assertEqual(tree['/memory']['reg'], bytes(16))

    def test_split_preserves_indices_and_bytes(self):
        first, second = make_fdt({'model': b'first\0'}), make_fdt({'model': b'second\0'})
        self.assertEqual(fdt.split_fdts(first + second + bytes(100)), [first, second])

    def test_bad_fdt_headers(self):
        for index, value in ((0, 0), (1, 0xffffffff), (2, 1), (3, 0xffffffff), (4, 1), (4, 0xfffffff8), (5, 18), (8, 0xffffffff)):
            blob = bytearray(make_fdt())
            struct.pack_into('>I', blob, index * 4, value)
            with self.subTest(index=index), self.assertRaises(ValueError):
                fdt.nodes(blob)
        with self.assertRaises(ValueError): fdt.header(bytes(20))

    def test_bad_structure_token(self):
        blob = bytearray(make_fdt())
        struct.pack_into('>I', blob, 56, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'token'): fdt.nodes(blob)

    def test_property_bounds(self):
        for relative in (12, 16):  # size and string offset of first root property
            blob = bytearray(make_fdt({'model': b'x\0'}))
            struct.pack_into('>I', blob, 56 + relative, 0xffffffff)
            with self.subTest(relative=relative), self.assertRaises(ValueError): fdt.nodes(blob)

    def test_dtbo_entries(self):
        blobs = [make_fdt({'model': b'one\0'}), make_fdt({'model': b'two\0'})]
        entries = fdt.dtbo_entries(make_table(*blobs) + bytes(100))
        self.assertEqual([e['data'] for e in entries], blobs)
        self.assertEqual(entries[1]['index'], 1)

    def test_bad_dtbo_headers(self):
        for offset, value in ((0, 0), (4, 0xffffffff), (12, 1), (16, 0), (20, 0), (24, 3), (28, 1)):
            blob = bytearray(make_table(make_fdt()))
            struct.pack_into('>I', blob, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError): fdt.dtbo_entries(blob)
        with self.assertRaises(ValueError): fdt.dtbo_entries(bytes(20))

    def test_dtbo_entry_outside_table(self):
        for offset, value in ((32, 0xffffffff), (36, 0), (36, 0xffffffff)):
            blob = bytearray(make_table(make_fdt()))
            struct.pack_into('>I', blob, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError): fdt.dtbo_entries(blob)

    def test_reserved_memory_cells_and_no_map(self):
        cells = struct.pack('>I', 2)
        blob = make_fdt(children=[('reserved-memory', {'#address-cells': cells, '#size-cells': cells},
                      [('secure@80000000', {'reg': struct.pack('>QQ', 0x80000000, 0x600000), 'no-map': b''}, [])])])
        regions = fdt.fixed_regions(fdt.nodes(blob))
        self.assertEqual(regions[0]['start'], 0x80000000)
        self.assertEqual(regions[0]['size'], 0x600000)
        self.assertTrue(regions[0]['no_map'])

    def test_wrong_reserved_memory_cells(self):
        tree = {'/reserved-memory': {'#address-cells': struct.pack('>I', 1)}}
        with self.assertRaises(ValueError): fdt.fixed_regions(tree)

    def test_coverage_union_gap_and_no_map(self):
        required = {'start': 100, 'size': 100, 'no_map': True}
        available = [{'start': 100, 'size': 50, 'no_map': True}, {'start': 150, 'size': 50, 'no_map': True}]
        self.assertTrue(fdt.region_covered(required, available))
        available[1]['start'] = 151
        self.assertFalse(fdt.region_covered(required, available))
        available[1]['start'] = 150
        available[1]['no_map'] = False
        self.assertFalse(fdt.region_covered(required, available))


class RomInspectionTests(unittest.TestCase):
    def test_metadata_match_and_wrong_device(self):
        pin = {'metadata': {'post-sdk-level': '33', 'post-build-incremental': '123'}}
        text = 'pre-device=picasso\npost-sdk-level=33\npost-build-incremental=123\n'
        self.assertEqual(inspect_rom.validate_metadata(text, pin, 'picasso')['post-sdk-level'], '33')
        with self.assertRaises(ValueError): inspect_rom.validate_metadata(text, pin, 'sunstone')

    def test_metadata_wrong_incremental(self):
        with self.assertRaises(ValueError):
            inspect_rom.validate_metadata('pre-device=picasso\npost-build-incremental=old\n',
                                          {'metadata': {'post-build-incremental': 'new'}}, 'picasso')

    def test_extract_and_preserve_existing_file(self):
        data = b'synthetic boot image'
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z: z.writestr('boot.img', data)
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as z, tempfile.TemporaryDirectory() as td:
            info = z.getinfo('boot.img')
            pin = {'size': len(data), 'zip_crc32': f'{info.CRC:08x}', 'sha256': hashlib.sha256(data).hexdigest()}
            target = Path(td)/'boot.img'
            inspect_rom.extract_member(z, 'boot.img', target, pin)
            self.assertEqual(target.read_bytes(), data)
            target.write_bytes(b'existing file')
            with self.assertRaises(ValueError): inspect_rom.extract_member(z, 'boot.img', target, pin)
            self.assertEqual(target.read_bytes(), b'existing file')

    def test_hash_failure_cleans_output(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z: z.writestr('boot.img', b'data')
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as z, tempfile.TemporaryDirectory() as td:
            info = z.getinfo('boot.img')
            pin = {'size': 4, 'zip_crc32': f'{info.CRC:08x}', 'sha256': '0'*64}
            with self.assertRaises(ValueError): inspect_rom.extract_member(z, 'boot.img', Path(td)/'boot.img', pin)
            self.assertEqual(list(Path(td).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
