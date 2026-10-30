#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Reconstruct the user-supplied full-OTA vendor image, offline and read-only.

No installer scripts, mounting, phone commands, or target ELF execution. Uses a
native brotli executable. Only full-OTA new/zero/erase commands are accepted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BLOCK = 4096
MAX_BLOCKS = 1 << 20


def parse_transfer(text):
    lines = text.splitlines()
    if len(lines) < 5 or lines[0] not in {'3', '4'}:
        raise ValueError('Expected full OTA transfer list v3/v4')
    declared = int(lines[1])
    if int(lines[2]) or int(lines[3]):
        raise ValueError('Stash/incremental transfer lists are not supported')
    operations, extents = [], []
    for line in lines[4:]:
        words = line.split()
        if len(words) != 2 or words[0] not in {'new', 'zero', 'erase'}:
            raise ValueError('Only full-OTA new/zero/erase operations are allowed')
        cells = [int(x) for x in words[1].split(',')]
        if not cells or cells[0] != len(cells)-1 or cells[0] % 2 or not cells[0]:
            raise ValueError('Invalid transfer ranges')
        for start, end in zip(cells[1::2], cells[2::2]):
            if not 0 <= start < end <= MAX_BLOCKS:
                raise ValueError('Transfer range outside image bound')
            operations.append((words[0], start, end))
            extents.append((start, end))
    previous = 0
    for start, end in sorted(extents):
        if start < previous:
            raise ValueError('Overlapping full-OTA ranges are not accepted')
        previous = end
    new_blocks = sum(e-s for op, s, e in operations if op == 'new')
    if not operations or not declared or new_blocks != declared:
        raise ValueError('New-data count differs from transfer header')
    return operations, max(e for _, _, e in operations)


def reconstruct(operations, blocks, source, target):
    target.truncate(blocks*BLOCK)
    for op, start, end in operations:
        if op != 'new':
            continue  # fresh sparse file is already zero in these disjoint ranges
        target.seek(start*BLOCK)
        remaining = (end-start)*BLOCK
        while remaining:
            data = source.read(min(1 << 20, remaining))
            if not data:
                raise ValueError('Truncated vendor new-data stream')
            target.write(data)
            remaining -= len(data)
    if source.read(1):
        raise ValueError('Extra bytes after vendor new-data stream')


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'downloads/crdroid-9.12/vendor.img')
    a = p.parse_args()
    device = json.loads((ROOT/'device.json').read_text())
    archive = (ROOT/device['rom_package']['file']).resolve()
    if digest(archive) != device['rom_package']['sha256']:
        raise SystemExit('ROM archive hash mismatch')
    if a.output.exists():
        raise SystemExit('Output already exists; refusing to overwrite')
    brotli = shutil.which('brotli')
    if not brotli:
        raise SystemExit('Native brotli executable required; no QEMU is used')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vendor-extract-', dir=a.output.parent) as td:
        work = Path(td)
        with zipfile.ZipFile(archive) as z:
            operations, blocks = parse_transfer(z.read('vendor.transfer.list').decode())
            member = z.getinfo('vendor.new.dat.br')
            if member.file_size > 1 << 30:
                raise ValueError('Unexpected vendor compressed size')
            compressed = work/'vendor.new.dat.br'
            with z.open(member) as src, compressed.open('wb') as dst:
                shutil.copyfileobj(src, dst, 1 << 20)  # zipfile verifies member CRC
        temporary = work/'vendor.img'
        with (work/'brotli.log').open('wb') as errors:
            process = subprocess.Popen([brotli, '--decompress', '--stdout', str(compressed)],
                                       stdout=subprocess.PIPE, stderr=errors)
            try:
                with temporary.open('w+b') as target:
                    reconstruct(operations, blocks, process.stdout, target)
                if process.wait(timeout=30):
                    raise ValueError('Brotli decoder failed')
            finally:
                process.stdout.close()
                if process.poll() is None:
                    process.kill()
                    process.wait()
        report = {'archive_sha256': device['rom_package']['sha256'],
                  'compressed_member_crc32': f'{member.CRC:08x}',
                  'compressed_member_sha256': digest(compressed),
                  'image_bytes': temporary.stat().st_size, 'image_sha256': digest(temporary),
                  'method': 'native brotli + validated full-OTA ranges; no mount, phone IO or QEMU'}
        temporary.replace(a.output)
        a.output.with_suffix('.source.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
