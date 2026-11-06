#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Select native getty on tty1 only; never start services or touch hardware."""
import argparse
import json
import os
from pathlib import Path
import subprocess


GETTY = '/usr/lib/systemd/system/getty@.service'
KMSCON = '/usr/lib/systemd/system/kmsconvt@.service'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def link_target(path):
    if path.is_symlink():
        return os.readlink(path)
    require(not path.exists(), 'Refuse non-symlink console configuration: ' + str(path))
    return None


def select_native_tty1(unit_dir, backup_dir):
    """Change only tty1 selection/mask/alias links after an exclusive backup."""
    wants = unit_dir / 'getty.target.wants'
    require(unit_dir.is_dir() and not unit_dir.is_symlink()
            and wants.is_dir() and not wants.is_symlink(), 'Real systemd directories required')
    paths = {'getty_want': wants / 'getty@tty1.service',
             'kmscon_want': wants / 'kmsconvt@tty1.service',
             'kmscon_mask': unit_dir / 'kmsconvt@tty1.service',
             'autovt_instance': unit_dir / 'autovt@tty1.service',
             'autovt_alias': unit_dir / 'autovt@.service'}
    before = {name: link_target(path) for name, path in paths.items()}
    require(before['getty_want'] == GETTY, 'Existing native tty1 getty selection required')
    require(before['kmscon_want'] in (None, KMSCON), 'Unexpected kmscon tty1 selection')
    require(before['kmscon_mask'] in (None, '/dev/null'), 'Unexpected kmscon tty1 override')
    require(before['autovt_instance'] in (None, GETTY), 'Unexpected autovt tty1 override')
    require(not backup_dir.exists() and not backup_dir.is_symlink(), 'Do not overwrite/replay backup')
    backup_dir.mkdir(mode=0o700)
    with (backup_dir / 'before.json').open('x') as stream:
        json.dump(before, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    for directory in (backup_dir, backup_dir.parent):
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    if before['kmscon_mask'] is None:
        paths['kmscon_mask'].symlink_to('/dev/null')
    if before['kmscon_want'] is not None:
        require(link_target(paths['kmscon_want']) == KMSCON, 'Console link changed during selection')
        paths['kmscon_want'].unlink()
    if before['autovt_instance'] is None:
        paths['autovt_instance'].symlink_to(GETTY)
    after = {name: link_target(path) for name, path in paths.items()}
    require(after == {**before, 'kmscon_want': None, 'kmscon_mask': '/dev/null',
                     'autovt_instance': GETTY},
            'Unexpected console selection result')
    for directory in (wants, unit_dir, backup_dir.parent):
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return {'status': 'native_getty_tty1_selected_kmscon_instance_masked',
            'before': before, 'after': after, 'no_service_start_or_hardware_operation': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', required=True)
    parser.add_argument('--backup-directory', type=Path, required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0 and os.uname().release == '7.3.1-picasso-wifi2',
            'Explicit native root on the installed kernel required')
    require(Path('/etc/picasso-fedora-root').read_text().strip() == 'PICASSO_FEDORA44_DISKROOT_V2',
            'Completed native disk installation required')
    subprocess.run(['/usr/bin/python3', '-I',
                    '/opt/picasso-kernel-7.3.1/kernel-candidate-activation.py',
                    '--feature', 'screen'], check=True, capture_output=True, timeout=30)
    os.umask(0o077)
    print(json.dumps(select_native_tty1(Path('/etc/systemd/system'), args.backup_directory), indent=2))


if __name__ == '__main__':
    main()
