# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
import fcntl
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import socket
import struct
import subprocess
import tempfile
import termios
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('build_petitboot', ROOT / 'tools/build-petitboot.py')
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class PetitbootPreparation(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_target_absolute_symlinks_stay_inside_sysroot(self):
        root = self.root / 'sysroot'
        (root / 'usr/lib64').mkdir(parents=True)
        library = root / 'usr/lib64/runtime.so.1'
        library.write_bytes(b'target runtime')
        (root / 'lib64').symlink_to('/usr/lib64')
        (root / 'usr/lib64/runtime.so').symlink_to('runtime.so.1')
        self.assertEqual(BUILD.root_file(root, '/lib64/runtime.so'), library)
        with self.assertRaises(FileNotFoundError):
            BUILD.root_file(root, '/usr/lib64/not-present.so')

    def test_relative_symlink_cannot_escape_sysroot(self):
        root = self.root / 'sysroot'
        root.mkdir()
        (root / 'escape').symlink_to('../outside')
        (self.root / 'outside').write_bytes(b'host data')
        with self.assertRaisesRegex(ValueError, 'escapes root'):
            BUILD.root_file(root, '/escape')

    def test_source_pin_rejects_mismatch_and_preserves_dirty_work(self):
        source = self.root / 'source'
        source.mkdir()
        subprocess.run(['git', 'init', '--quiet', str(source)], check=True)
        original = source / 'payload'
        original.write_text('pinned source\n')
        subprocess.run(['git', '-C', str(source), 'add', 'payload'], check=True)
        subprocess.run(
            ['git', '-C', str(source), '-c', 'user.name=Fixture',
             '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet',
             '-m', 'fixture'], check=True)
        commit = subprocess.check_output(
            ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        original.write_text('uncommitted source work\n')
        destination = self.root / 'staged'
        with self.assertRaisesRegex(ValueError, 'expected'):
            BUILD.archive_source(source, {'commit': '0' * 40}, destination)
        self.assertFalse(destination.exists())
        BUILD.archive_source(source, {'commit': commit}, destination)
        self.assertEqual((destination / 'payload').read_text(), 'pinned source\n')
        self.assertEqual(original.read_text(), 'uncommitted source work\n')

    def test_all_transition_variants_remain_blocked(self):
        for args in (('-l', '/unvalidated/Image'), ('-s', '/unvalidated/Image'),
                     ('-e',), ('-e', '-f'), ('-r', 'now')):
            with self.subTest(args=args):
                result = subprocess.run(
                    ['sh', str(ROOT / 'petitboot/blocked-transition'), *args],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 125)
                self.assertIn('not validated or authorized', result.stderr)

    @unittest.skipUnless(os.environ.get('PETITBOOT_NATIVE_BUILD'),
                         'requires an explicitly selected native bundle')
    def test_isolated_daemon_reinit_menu_and_blocked_load(self):
        build = ROOT / os.environ['PETITBOOT_NATIVE_BUILD']
        with tempfile.TemporaryDirectory(dir=ROOT / 'out',
                                          prefix='petitboot-runtime.') as temporary:
            root = Path(temporary) / 'rootfs'
            shutil.copytree(build / 'rootfs', root)
            (root / 'bin').mkdir()
            shell = root / 'bin/sh'
            shutil.copyfile(BUILD.root_file(Path('/'), '/bin/sh'), shell)
            shell.chmod(0o755)
            BUILD.copy_libraries([shell], Path('/'), root)
            (root / 'menu.conf').write_text(
                'LABEL linux-new\nKERNEL file:///kernels/new/Image\n'
                'FDT file:///kernels/new/board.dtb\nAPPEND console=tty0\n'
                'LABEL linux-rescue\nKERNEL file:///kernels/rescue/Image\n'
                'DTB file:///kernels/rescue/board.dtb\nAPPEND console=tty0\n')
            for entry in ('new', 'rescue'):
                directory = root / 'kernels' / entry
                directory.mkdir(parents=True)
                (directory / 'Image').write_bytes(b'not a bootable kernel\n')
                (directory / 'board.dtb').write_bytes(b'not a bootable DTB\n')
            command = ['unshare', '--user', '--map-root-user', '--mount',
                       '--net', 'chroot', str(root)]
            log = Path(temporary) / 'discover.log'
            master, slave = pty.openpty()
            ui = None
            with log.open('wb') as stream:
                daemon = subprocess.Popen(
                    [*command, '/usr/sbin/pb-discover', '--local-only',
                     '--log', '-', '--verbose'],
                    stdout=stream, stderr=subprocess.STDOUT)
                try:
                    def wait_for(predicate):
                        deadline = time.monotonic() + 10
                        while time.monotonic() < deadline:
                            self.assertIsNone(daemon.poll(), log.read_text())
                            if predicate():
                                return
                            time.sleep(0.02)
                        self.fail('Timed out waiting for isolated daemon:\n' + log.read_text())

                    wait_for(lambda: (root / 'tmp/petitboot.ev').exists())
                    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as event:
                        def send_event(*parts):
                            event.sendto(('\0'.join(parts) + '\0').encode(),
                                         str(root / 'tmp/petitboot.ev'))

                        send_event('url@local', 'url=https://example.invalid/menu.conf')
                        wait_for(lambda: 'Local-only mode requires a local config file'
                                 in log.read_text())
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                            client.connect(str(root / 'tmp/petitboot.ui'))
                            client.settimeout(5)

                            def receive_action(expected):
                                def receive_exact(size):
                                    data = b''
                                    while len(data) < size:
                                        chunk = client.recv(size - len(data))
                                        self.assertTrue(chunk, log.read_text())
                                        data += chunk
                                    return data

                                for _ in range(32):
                                    action, size = struct.unpack('!II', receive_exact(8))
                                    payload = receive_exact(size)
                                    if action == expected:
                                        return payload
                                self.fail(f'Missing protocol action {expected}')

                            send_event('url@local', 'url=file:///menu.conf')
                            self.assertIn(b'linux-new', receive_action(0x2))
                            self.assertIn(b'linux-rescue', receive_action(0x2))
                            for _ in range(3):
                                client.sendall(struct.pack('!II', 0xA, 0))
                                receive_action(0xD)
                            send_event('url@local', 'url=file:///menu.conf')
                            self.assertIn(b'linux-new', receive_action(0x2))
                            self.assertIn(b'linux-rescue', receive_action(0x2))

                            fcntl.ioctl(slave, termios.TIOCSWINSZ,
                                        struct.pack('HHHH', 40, 100, 0, 0))
                            ui = subprocess.Popen(
                                [*command, '/usr/sbin/petitboot-nc', '--menu-only', '--log', '-'],
                                stdin=slave, stdout=slave, stderr=stream,
                                env=dict(os.environ, TERM='linux', LC_ALL='C.UTF-8'))
                            rendered = b''
                            deadline = time.monotonic() + 10
                            while time.monotonic() < deadline:
                                if select.select([master], [], [], 0.1)[0]:
                                    rendered += os.read(master, 65536)
                                if b'linux-new' in rendered and b'linux-rescue' in rendered:
                                    break
                                self.assertIsNone(ui.poll(), log.read_text())
                            self.assertIn(b'linux-new', rendered)
                            self.assertIn(b'linux-rescue', rendered)
                            for action in (b'Exit to shell', b'Reboot', b'System configuration',
                                           b'Retrieve config from URL', b'Plugins ('):
                                self.assertNotIn(action, rendered)
                            os.write(master, b'xnegl\r')
                            time.sleep(0.1)
                            self.assertIsNone(ui.poll(), log.read_text())
                            send_event('boot@local', 'name=linux-new')
                            wait_for(lambda: 'Petitboot transition blocked' in log.read_text())
                            self.assertIsNone(daemon.poll())
                    self.assertIn('block/network discovery disabled', log.read_text())
                    self.assertIn('set autoboot: disabled', log.read_text())
                    self.assertNotIn('scsi-rescan', log.read_text())
                finally:
                    if ui is not None:
                        ui.send_signal(signal.SIGTERM)
                        ui.wait(timeout=5)
                    daemon.send_signal(signal.SIGINT)
                    daemon.wait(timeout=5)
                    os.close(master)
                    os.close(slave)


if __name__ == '__main__':
    unittest.main()
