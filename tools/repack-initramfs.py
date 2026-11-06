#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline, pinned boot-v2 repack: change only /init within its existing gzip slot.

Does not compile kernel code, contact a device, authorize services or flash. The
new image is unverified. Kernel code, configuration, shim and both DTBs remain
byte-identical outside the compressed initramfs; all other cpio members remain
identical. Refuse rather than grow the slot or relocate any linked kernel data.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import zlib

from bootimg import pack, parse_stock

MAX_CPIO = 16 << 20


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_cpio(raw):
    entries, seen, offset = [], set(), 0
    while True:
        require(raw[offset:offset + 6] == b'070701', 'Expected bounded newc cpio')
        header = raw[offset:offset + 110]
        require(len(header) == 110, 'Truncated cpio header')
        fields = [int(header[6 + i * 8:14 + i * 8], 16) for i in range(13)]
        length, namesize = fields[6], fields[11]
        require(0 < namesize <= 4096 and length <= MAX_CPIO, 'Invalid cpio lengths')
        namebytes = raw[offset + 110:offset + 110 + namesize]
        require(len(namebytes) == namesize and namebytes[-1:] == b'\0', 'Invalid cpio name')
        name = namebytes[:-1].decode('utf-8')
        require(name and name not in seen and not name.startswith('/') and
                '..' not in name.split('/'), 'Duplicate or unsafe cpio name')
        seen.add(name)
        start = (offset + 110 + namesize + 3) & ~3
        end = start + length
        require(end <= len(raw), 'Truncated cpio data')
        entries.append({'header': header, 'namebytes': namebytes, 'name': name,
                        'data': raw[start:end]})
        offset = (end + 3) & ~3
        if name == 'TRAILER!!!':
            require(not length and not any(raw[offset:]), 'Invalid cpio trailer/padding')
            break
    return entries


def encode_cpio(entries):
    raw = bytearray()
    for e in entries:
        header = bytearray(e['header'])
        header[54:62] = f"{len(e['data']):08X}".encode()
        raw.extend(header)
        raw.extend(e['namebytes'])
        raw.extend(b'\0' * (-len(raw) % 4))
        raw.extend(e['data'])
        raw.extend(b'\0' * (-len(raw) % 4))
    raw.extend(b'\0' * (-len(raw) % 512))
    return bytes(raw)


def find_initramfs(kernel):
    found = []
    for match in re.finditer(b'\x1f\x8b\x08', kernel):
        offset = match.start()
        try:
            stream = zlib.decompressobj(31)
            raw = stream.decompress(kernel[offset:], MAX_CPIO + 1)
            if not stream.eof or len(raw) > MAX_CPIO or not raw.startswith(b'070701'):
                continue
            entries = parse_cpio(raw)
            size = len(kernel) - offset - len(stream.unused_data)
            found.append((offset, size, raw, entries))
        except (zlib.error, ValueError, UnicodeError):
            continue
    require(len(found) == 1, 'Expected exactly one valid gzip/newc initramfs')
    return found[0]


def repack(original, expected_init, replacement_init):
    require(replacement_init.startswith(b'#!/bin/busybox sh\n'), 'Unexpected replacement init interpreter')
    info = parse_stock(original)
    start = info['page_size']
    length = struct.unpack_from('<I', original, 8)[0]
    kernel = original[start:start + length]
    require(pack(original, kernel) == original, 'Baseline must reproduce exactly with the existing packer')
    offset, size, raw, entries = find_initramfs(kernel)
    require(encode_cpio(entries) == raw, 'Cannot reproduce original cpio metadata/layout')
    init = [e for e in entries if e['name'] == 'init']
    require(len(init) == 1 and init[0]['data'] == expected_init, 'Original init does not match pinned source')
    mode = int(init[0]['header'][14:22], 16)
    require(stat.S_ISREG(mode) and mode & 0o111, 'Original init must be an executable regular file')
    old_members = {e['name']: (e['header'], e['namebytes'], e['data']) for e in entries}
    init[0]['data'] = replacement_init
    compressed = gzip.compress(encode_cpio(entries), compresslevel=9, mtime=0)
    require(len(compressed) <= size, 'New initramfs does not fit its original linked gzip slot')
    changed_kernel = (kernel[:offset] + compressed.ljust(size, b'\0') +
                      kernel[offset + size:])
    require(len(changed_kernel) == len(kernel), 'Kernel layout changed')
    after = find_initramfs(changed_kernel)[3]
    for e in after:
        if e['name'] != 'init':
            require((e['header'], e['namebytes'], e['data']) == old_members[e['name']],
                    'Other cpio member changed: ' + e['name'])
        else:
            require(e['data'] == replacement_init, 'Replacement init readback mismatch')
    result = pack(original, changed_kernel)
    require(len(result) == len(original) and parse_stock(result)['dtb'] == info['dtb'],
            'Boot layout or ABL DTB changed')
    allowed = ((576, 608), (start + offset, start + offset + size))
    cursor = 0
    for left, right in allowed:
        require(result[cursor:left] == original[cursor:left], 'Unexpected boot byte change')
        cursor = right
    require(result[cursor:] == original[cursor:], 'Unexpected trailing boot byte change')
    receipt = {'status': 'offline_only_unverified_initramfs_repack_no_device_IO',
               'original_boot_sha256': sha(original), 'candidate_boot_sha256': sha(result),
               'boot_size': len(result), 'original_init_sha256': sha(expected_init),
               'candidate_init_sha256': sha(replacement_init),
               'kernel_gzip_offset': offset, 'original_gzip_slot_bytes': size,
               'candidate_gzip_bytes': len(compressed),
               'all_other_cpio_members_identical': True,
               'only_boot_ID_and_existing_gzip_slot_changed': True,
               'kernel_code_config_shim_ABL_and_runtime_DTB_preserved': True,
               'no_compilation_module_ABI_change_flash_or_activation': True}
    return result, receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--boot', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--original-init', type=Path, required=True)
    p.add_argument('--init', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True,
                   help='Fresh directory under repository out/; must not exist')
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.absolute()
    require(output.resolve() == output and output.is_relative_to(root / 'out') and
            not output.exists(), 'Output must be a fresh non-symlink repository out/ subdirectory')
    original = args.boot.read_bytes()
    require(re.fullmatch('[0-9a-f]{64}', args.expected_sha256) and
            sha(original) == args.expected_sha256, 'Pinned baseline boot digest mismatch')
    result, receipt = repack(original, args.original_init.read_bytes(), args.init.read_bytes())
    output.mkdir(mode=0o700, parents=True)
    (output / 'boot-f45-trial.img').write_bytes(result)
    (output / 'repack.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
