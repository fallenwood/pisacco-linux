# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
UUID = '32684d05-1c3b-836e-c936-7d4638bf1be9'


class DiskRootGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'diskroot'
        for name in ('etc', 'dev', 'proc', 'sys', 'run', 'usr/lib/systemd'):
            (self.root/name).mkdir(parents=True, exist_ok=True)
        (self.root/'etc/os-release').write_text('ID=fedora\nVERSION_ID=44\nVARIANT_ID=server\n')
        self.fstype = 'ext4'
        (self.root/'etc/picasso-fedora-root').write_text('PICASSO_FEDORA44_DISKROOT_V2\n')
        (self.root/'etc/picasso-install-fstype').write_text(self.fstype+'\n')
        (self.root/'etc/picasso-install-partuuid').write_text(UUID+'\n')
        (self.root/'etc/picasso-native-init.done').write_text('PICASSO_NATIVE_INIT_V1\n')
        (self.root/'usr/lib/systemd/systemd').write_text('not executed by the guard\n')
        (self.root/'usr/lib/systemd/systemd').chmod(0o755)
        self.mounts = self.base/'mounts'
        self.mounts.write_text(f'/dev/fixture {self.root} ext4 ro,noload 0 0\n')
        source = (ROOT/'initramfs/init').read_text()
        body = source.split('diskroot_valid() {', 1)[1].split('\n}\n', 1)[0]
        self.guard = ('diskroot_valid() {'+body+'\n}\n').replace('/newroot', str(self.root)).replace('/proc/mounts', str(self.mounts))

    def accepted(self):
        p = subprocess.run(['sh', '-c', f'ROOTARG=PARTUUID={UUID}\nROOTFSTYPE={self.fstype}\n'+self.guard+'diskroot_valid'], capture_output=True)
        return p.returncode == 0

    def test_completed_ext4_server_root_accepted(self):
        self.assertTrue(self.accepted())

    def test_completed_xfs_server_root_accepted(self):
        self.fstype = 'xfs'
        (self.root/'etc/picasso-install-fstype').write_text('xfs\n')
        self.mounts.write_text(f'/dev/fixture {self.root} xfs ro,norecovery 0 0\n')
        self.assertTrue(self.accepted())

    def test_xfs_marker_on_ext4_rejected(self):
        self.fstype = 'xfs'
        (self.root/'etc/picasso-install-fstype').write_text('xfs\n')
        self.assertFalse(self.accepted())

    def test_mismatched_fstype_marker_rejected(self):
        (self.root/'etc/picasso-install-fstype').write_text('xfs\n')
        self.assertFalse(self.accepted())

    def test_fstype_marker_required(self):
        (self.root/'etc/picasso-install-fstype').unlink()
        self.assertFalse(self.accepted())

    def test_unsupported_fstype_rejected(self):
        self.fstype = 'btrfs'
        self.assertFalse(self.accepted())

    def test_v1_marker_rejected(self):
        (self.root/'etc/picasso-fedora-root').write_text('PICASSO_FEDORA44_DISKROOT_V1\n')
        self.assertFalse(self.accepted())

    def test_no_replay_readonly_options_are_filesystem_specific(self):
        source = (ROOT/'initramfs/init').read_text()
        self.assertIn('ext4) ROOTRO=ro,noload', source)
        self.assertIn('xfs) ROOTRO=ro,norecovery', source)
        self.assertIn('mount -t "$ROOTFSTYPE" -o "$ROOTRO"', source)

    def test_tmpfs_rejected(self):
        self.mounts.write_text(f'tmpfs {self.root} tmpfs rw 0 0\n')
        self.assertFalse(self.accepted())

    def test_generic_old_marker_rejected(self):
        (self.root/'etc/picasso-fedora-root').write_text('generic Fedora marker\n')
        self.assertFalse(self.accepted())

    def test_other_partuuid_rejected(self):
        (self.root/'etc/picasso-install-partuuid').write_text('00000000-0000-0000-0000-000000000000\n')
        self.assertFalse(self.accepted())

    def test_incomplete_native_init_rejected(self):
        (self.root/'etc/picasso-native-init.done').unlink()
        self.assertFalse(self.accepted())

    def test_wrong_edition_rejected(self):
        (self.root/'etc/os-release').write_text('ID=fedora\nVERSION_ID=44\nVARIANT_ID=container\n')
        self.assertFalse(self.accepted())

    def test_symlink_api_mountpoint_rejected(self):
        (self.root/'dev').rmdir()
        (self.root/'dev').symlink_to(self.base)
        self.assertFalse(self.accepted())


if __name__ == '__main__':
    unittest.main()
