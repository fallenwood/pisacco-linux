#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fail closed unless this exact offline bundle has new device-phase consent."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def private_json(path):
    value = path.lstat()
    require(stat.S_ISREG(value.st_mode) and value.st_uid == 0 and value.st_nlink == 1
            and stat.S_IMODE(value.st_mode) == 0o400, 'Root0400 candidate policy required')
    return json.loads(path.read_text())


def validate_identity(authorization, build, feature, release, config_sha256, fdt_sha256):
    require(authorization.get('allow_' + feature) is True,
            'New explicit candidate activation consent required: ' + feature)
    for key in ('kernel_release', 'config_sha256', 'fdt_sha256', 'boot_image_sha256'):
        require(authorization.get(key) == build[key], 'Candidate authorization mismatch: ' + key)
    require(release == build['kernel_release'], 'Different running kernel')
    require(config_sha256 == build['config_sha256'], 'Different running kernel configuration')
    require(fdt_sha256 == build['fdt_sha256'], 'Different live device tree')


def validate_screen_backlight_ownership(mask):
    require(mask.is_symlink() and os.readlink(mask) == '/dev/null',
            'Mask systemd-backlight@backlight:picasso-screen.service '
            'before starting the PID-leased screen owner')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feature', choices=('screen', 'wifi', 'wifi_probation', 'power'), required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0, 'Native root required')
    base = Path(__file__).resolve().parent
    manifest_path = base / 'runtime-manifest.json'
    manifest = private_json(manifest_path)
    authorization = private_json(base / 'activation.json')
    require(authorization.get('runtime_manifest_sha256') == digest(manifest_path),
            'Activation does not authorize this exact runtime bundle')
    validate_identity(
        authorization, manifest['build'], args.feature, os.uname().release,
        hashlib.sha256(gzip.decompress(Path('/proc/config.gz').read_bytes())).hexdigest(),
        digest(Path('/sys/firmware/fdt')),
    )
    if args.feature == 'screen':
        validate_screen_backlight_ownership(
            Path('/etc/systemd/system/systemd-backlight@backlight:picasso-screen.service'))
    for path, sha256 in {**manifest['shared_files'], **manifest['files']}.items():
        require(digest(Path(path)) == sha256, 'Candidate dependency changed: ' + path)
    print('Exact candidate identity/assets/feature consent verified; hardware not armed', flush=True)


if __name__ == '__main__':
    main()
