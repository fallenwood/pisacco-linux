#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Create a fresh LTS source tree, applying the local series, without root."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'sources.json').read_text())
    ver = manifest['kernel_version']
    dest = ROOT / 'src' / f'linux-{ver}'
    if dest.exists():
        raise SystemExit(f'{dest} already exists; will not overwrite source work')
    archive = ROOT / 'downloads' / f'linux-{ver}.tar.xz'
    expected = next(x['sha256'] for x in manifest['downloads'] if x['file'] == archive.name)
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
            raise SystemExit('Kernel tarball checksum mismatch')
    dest.parent.mkdir(parents=True, exist_ok=True)
    series = ROOT / 'kernel/patches/series'
    names = [x.strip() for x in series.read_text().splitlines() if x.strip() and not x.startswith('#')]
    with tarfile.open(archive) as tar:
        # Kernel.org archives have one top-level directory. Reject unexpected roots.
        if any(not x.name.startswith(f'linux-{ver}/') and x.name != f'linux-{ver}' for x in tar):
            raise SystemExit('Unexpected top-level tarball member')
        tar.extractall(dest.parent, filter='data')
    for name in names:
        patch = ROOT / 'kernel/patches' / name
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=dest, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=dest, check=True)
    (dest / '.picasso-source.json').write_text(json.dumps({
        'kernel_version': ver,
        'patches': {name: hashlib.sha256((ROOT / 'kernel/patches' / name).read_bytes()).hexdigest() for name in names},
    }, indent=2) + '\n')
    print(dest)


if __name__ == '__main__':
    main()
