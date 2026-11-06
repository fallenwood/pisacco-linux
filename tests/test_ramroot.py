# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rescue_console', ROOT/'tools/rescue-console.py')
console = importlib.util.module_from_spec(spec)
spec.loader.exec_module(console)


class SerialMarkers(unittest.TestCase):
    def test_crlf_body(self):
        self.assertEqual(console.extract(b'\r\nBEGIN\r\nhello\r\nEND\r\nprompt', b'BEGIN', b'END'), b'hello')

    def test_echo_does_not_count_as_completion(self):
        self.assertIsNone(console.extract(b"printf '\\nBEGIN\\n'; echo hi; printf '\\nEND\\n'\r\n", b'BEGIN', b'END'))

    def test_partial_capture_rejected(self):
        self.assertIsNone(console.extract(b'\nBEGIN\npartial', b'BEGIN', b'END'))

    def test_large_line_refused_before_any_serial_write(self):
        instance = console.Console.__new__(console.Console)
        instance.send = lambda data: self.fail('Oversized command reached the device')
        with self.assertRaisesRegex(ValueError, 'use chunks'):
            instance.command('x' * 1800)


class RamRootGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'root'
        for name in ('etc', 'dev', 'proc', 'sys', 'run', 'usr/lib/systemd'):
            (self.root/name).mkdir(parents=True, exist_ok=True)
        (self.root/'etc/os-release').write_text('ID=fedora\nVERSION_ID=44\nVARIANT_ID=server\n')
        (self.root/'etc/picasso-fedora-ramroot').write_text('PICASSO_FEDORA44_RAMROOT_V1\n')
        (self.root/'etc/picasso-native-init.done').write_text('PICASSO_NATIVE_INIT_V1\n')
        systemd = self.root/'usr/lib/systemd/systemd'
        systemd.write_text('not executed by the guard\n')
        systemd.chmod(0o755)
        self.request = self.base/'request'
        self.request.write_text('PICASSO_RAMROOT_V1\n')
        self.mounts = self.base/'mounts'
        self.mounts.write_text(f'tmpfs {self.root} tmpfs rw 0 0\n')
        source = (ROOT/'initramfs/init').read_text()
        self.guard = 'ramroot_valid() {'+source.split('ramroot_valid() {', 1)[1].split('\nwhile :', 1)[0]
        self.guard = self.guard.replace('/newroot', str(self.root)).replace('/run/picasso-ramroot.request', str(self.request)).replace('/proc/mounts', str(self.mounts))

    def accepted(self):
        return subprocess.run(['sh', '-c', self.guard+'\nramroot_valid'], capture_output=True).returncode == 0

    def test_valid_ram_server(self):
        self.assertTrue(self.accepted())

    def test_unmounted_directory_rejected(self):
        self.mounts.write_text('')
        self.assertFalse(self.accepted())

    def test_block_filesystem_rejected(self):
        self.mounts.write_text(f'/dev/sda34 {self.root} ext4 rw 0 0\n')
        self.assertFalse(self.accepted())

    def test_native_initialization_required(self):
        (self.root/'etc/picasso-native-init.done').unlink()
        self.assertFalse(self.accepted())

    def test_fedora45_not_implicitly_accepted_as_ramroot(self):
        (self.root/'etc/os-release').write_text('ID=fedora\nVERSION_ID=45\nVARIANT_ID=server\n')
        self.assertFalse(self.accepted())

    def test_server_release_required(self):
        (self.root/'etc/os-release').write_text('ID=fedora\nVERSION_ID=44\nVARIANT_ID=container\n')
        self.assertFalse(self.accepted())

    def test_symlink_mountpoint_rejected(self):
        (self.root/'dev').rmdir()
        (self.root/'dev').symlink_to(self.base)
        self.assertFalse(self.accepted())


if __name__ == '__main__':
    unittest.main()
