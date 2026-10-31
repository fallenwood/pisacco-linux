#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fetch hash-pinned inputs; extract ONLY the static AArch64 BusyBox executable."""
import hashlib
from pathlib import Path
import struct
import tarfile
import urllib.request

from kernel_profile import select_profile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    manifest = select_profile(ROOT).sources()
    dl = ROOT / 'downloads'
    dl.mkdir(exist_ok=True)
    for item in manifest['downloads']:
        dest = dl / item['file']
        if not dest.exists():
            temporary = dest.with_suffix(dest.suffix + '.part')
            print('Downloading', item['url'], flush=True)
            urllib.request.urlretrieve(item['url'], temporary)
            if digest(temporary) != item['sha256']:
                temporary.unlink()
                raise SystemExit(f'Checksum mismatch: {dest.name}')
            temporary.replace(dest)
        if digest(dest) != item['sha256']:
            raise SystemExit(f'Checksum mismatch: {dest}; move it aside and retry')
        print(dest.name, 'SHA256 OK')
    # APK v2 is concatenated gzip/tar streams. Never extract arbitrary archive paths.
    with tarfile.open(dl / 'busybox-static.apk', 'r:gz', ignore_zeros=True) as archive:
        member = archive.getmember('bin/busybox.static')
        if not member.isfile():
            raise SystemExit('BusyBox archive member is not a regular file')
        blob = archive.extractfile(member).read()
    if blob[:5] != b'\x7fELF\x02' or struct.unpack_from('<H', blob, 18)[0] != 183:
        raise SystemExit('BusyBox is not AArch64 ELF64')
    executable = dl / 'busybox'
    if executable.exists():
        if executable.read_bytes() != blob or executable.stat().st_mode & 0o777 != 0o755:
            raise SystemExit('Existing BusyBox executable differs; refusing to overwrite it')
    else:
        executable.write_bytes(blob)
        executable.chmod(0o755)


if __name__ == '__main__':
    main()
