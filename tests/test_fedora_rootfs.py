# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FedoraServerPosttrans(unittest.TestCase):
    """Execute only the native Python rootfs setup, never DNF or target ELF."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('etc/selinux', 'etc/firewalld', 'usr/share/polkit-1/actions'):
            (self.root/directory).mkdir(parents=True)
        (self.root/'etc/firewalld/firewalld-server.conf').write_text('DefaultZone=FedoraServer\n')
        (self.root/'usr/share/polkit-1/actions/org.fedoraproject.FirewallD1.server.policy.choice').write_text('server policy\n')
        source = (ROOT/'tools/mkrootfs-fedora.sh').read_text()
        self.setup = source.split('python3 - "$TARGET" <<\'PY\'\n', 1)[1].split('\nPY\n', 1)[0]

    def run_setup(self):
        return subprocess.run([sys.executable, '-c', self.setup, str(self.root)],
                              capture_output=True, text=True)

    def test_server_ghost_links_created_without_target_execution(self):
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        config = self.root/'etc/firewalld/firewalld.conf'
        self.assertEqual(config.readlink(), Path('firewalld-server.conf'))
        policy = self.root/'usr/share/polkit-1/actions/org.fedoraproject.FirewallD1.policy'
        self.assertEqual(policy.readlink(), Path('org.fedoraproject.FirewallD1.server.policy.choice'))
        self.assertIn('SELINUX=permissive', (self.root/'etc/selinux/config').read_text())
        self.assertEqual(result.stderr, '')

    def test_existing_firewall_config_preserved(self):
        config = self.root/'etc/firewalld/firewalld.conf'
        config.write_text('custom config\n')
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(config.is_symlink())
        self.assertEqual(config.read_text(), 'custom config\n')

    def test_missing_server_payload_rejected(self):
        (self.root/'etc/firewalld/firewalld-server.conf').unlink()
        result = self.run_setup()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing Fedora Server firewalld payload:', result.stderr)
        self.assertFalse((self.root/'etc/firewalld/firewalld.conf').is_symlink())


if __name__ == '__main__':
    unittest.main()
