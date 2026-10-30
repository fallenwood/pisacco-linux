#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Restore only Fedora RPM file capabilities, natively, without changing modes.

Host filesystem images deliberately omit host security xattrs. Unlike rpm's
legacy --setcaps aliases, this does not restore unrelated package attributes.
"""
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess


def parse_filecaps(output):
    result = {}
    for line in output.splitlines():
        name, sep, caps = line.rpartition('\t')
        if not sep:
            raise ValueError('Malformed RPM file capability record')
        if not caps or caps == '(none)':
            continue
        p = PurePosixPath(name)
        if not name.startswith('/usr/') or '..' in p.parts or not caps.startswith('cap_'):
            raise ValueError('Unexpected capability target or syntax: '+name)
        if name in result and result[name] != caps:
            raise ValueError('Conflicting RPM capabilities: '+name)
        result[name] = caps
    return result


def main():
    if os.geteuid() != 0 or platform.machine() != 'aarch64':
        raise SystemExit('Run only as native root on the AArch64 Fedora phone')
    release = Path('/etc/os-release').read_text()
    if not all(line in release.splitlines() for line in ('ID=fedora', 'VERSION_ID=44', 'VARIANT_ID=server')):
        raise SystemExit('Require Fedora Server 44')
    records = subprocess.check_output(['rpm', '-qa', '--filecaps'], text=True)
    caps = parse_filecaps(records)
    for name, value in sorted(caps.items()):
        p = Path(name)
        if p.is_symlink() or not p.is_file():
            raise SystemExit('Refusing nonregular capability target: '+name)
        subprocess.run(['setcap', value, name], check=True)
        subprocess.run(['setcap', '-v', value, name], check=True, stdout=subprocess.DEVNULL)
    print(json.dumps({'status':'passed','file_capabilities_restored_and_verified':caps,
                      'file_contents_modes_owners_unchanged':True}))


if __name__ == '__main__':
    main()
