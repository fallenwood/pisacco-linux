#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Android boot v2 parser/packer. Preserve the stock DTB blob for ABL's DTBO.

This does not sign AVB images and is only for an already-unlocked bootloader.
It never talks to a phone. Addresses/page size are read, not guessed.
"""
import argparse
import hashlib
from pathlib import Path
import struct

MAGIC = b'ANDROID!'
HEADER_SIZE = 1660


def align(value, page):
    return (value + page - 1) // page * page


def fdt_count(blob):
    offset = count = 0
    while offset < len(blob):
        if not any(blob[offset:]):
            break  # allow final zero padding, not arbitrary intervening junk
        if len(blob) - offset < 40 or blob[offset:offset + 4] != b'\xd0\x0d\xfe\xed':
            raise ValueError('stock DTB field is not concatenated FDTs')
        size = struct.unpack_from('>I', blob, offset + 4)[0]
        if size < 40 or offset + size > len(blob):
            raise ValueError('truncated/invalid FDT')
        offset += size
        count += 1
    if not count:
        raise ValueError('empty DTB field')
    return count


def parse_stock(blob):
    if len(blob) < HEADER_SIZE or blob[:8] != MAGIC:
        raise ValueError('not an Android boot image')
    u32 = lambda off: struct.unpack_from('<I', blob, off)[0]
    page = u32(36)
    if u32(40) != 2:
        raise ValueError('Picasso packer requires a stock header-v2 boot image')
    if page < 2048 or page > 65536 or page & (page - 1):
        raise ValueError('invalid boot page size')
    if u32(1644) != HEADER_SIZE or page < HEADER_SIZE:
        raise ValueError('invalid v2 header size')
    if not u32(8):
        raise ValueError('stock image has no kernel')
    # Header + kernel + ramdisk + second + recovery_dtbo + dtb, page-aligned.
    before_recovery = page + sum(align(u32(off), page) for off in (8, 16, 24))
    recovery_size = u32(1632)
    recovery_offset = struct.unpack_from('<Q', blob, 1636)[0]
    if recovery_size and recovery_offset != before_recovery:
        raise ValueError('unexpected recovery DTBO offset')
    dtb_offset = before_recovery + align(recovery_size, page)
    dtb_size = u32(1648)
    if not dtb_size or dtb_offset + dtb_size > len(blob):
        raise ValueError('missing/truncated stock DTB field')
    dtb = blob[dtb_offset:dtb_offset + dtb_size]
    return {'page_size': page, 'dtb': dtb, 'dtb_offset': dtb_offset,
            'dtb_count': fdt_count(dtb), 'header': blob[:HEADER_SIZE]}


def pack(stock, kernel, max_size=128 << 20):
    info = parse_stock(stock)
    if len(kernel) < 64 or kernel[56:60] != b'ARMd':
        raise ValueError('kernel field must be an uncompressed ARM64 Image/shim')
    if struct.unpack_from('<Q', kernel, 16)[0] != len(kernel):
        raise ValueError('shim Image header size does not cover its payload')
    header = bytearray(info['header'])
    struct.pack_into('<I', header, 8, len(kernel))
    for off in (16, 24, 1632):  # external ramdisk, second and recovery_dtbo removed
        struct.pack_into('<I', header, off, 0)
    struct.pack_into('<Q', header, 1636, 0)
    # Legacy Android boot ID includes each component followed by its u32 size.
    sha = hashlib.sha1()
    for payload in (kernel, b'', b'', b'', info['dtb']):
        sha.update(payload)
        sha.update(struct.pack('<I', len(payload)))
    header[576:608] = sha.digest().ljust(32, b'\0')
    page = info['page_size']
    result = bytes(header).ljust(page, b'\0')
    result += kernel.ljust(align(len(kernel), page), b'\0')
    result += info['dtb'].ljust(align(len(info['dtb']), page), b'\0')
    if len(result) > max_size:
        raise ValueError('boot image exceeds the configured partition size')
    if parse_stock(result)['dtb'] != info['dtb']:
        raise ValueError('internal error: stock DTB changed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', required=True, type=Path)
    parser.add_argument('--kernel', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--extract-dtb', type=Path)
    parser.add_argument('--max-size', type=int, default=128 << 20)
    args = parser.parse_args()
    stock = args.stock.read_bytes()
    info = parse_stock(stock)
    print(f"v2, page={info['page_size']}, stock DTBs={info['dtb_count']}, offset={info['dtb_offset']:#x}")
    if args.extract_dtb:
        args.extract_dtb.write_bytes(info['dtb'])
    if args.kernel or args.output:
        if not args.kernel or not args.output:
            parser.error('--kernel and --output must be used together')
        if args.output.resolve() in {args.stock.resolve(), args.kernel.resolve()}:
            parser.error('output must not overwrite an input')
        image = pack(stock, args.kernel.read_bytes(), args.max_size)
        args.output.write_bytes(image)
        print(hashlib.sha256(image).hexdigest(), args.output)


if __name__ == '__main__':
    main()
