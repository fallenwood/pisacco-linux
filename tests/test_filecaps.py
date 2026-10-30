# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('restore_caps', Path(__file__).resolve().parents[1]/'tools/fedora-restore-filecaps.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class RpmFileCaps(unittest.TestCase):
    def test_only_nonempty_records(self):
        self.assertEqual(mod.parse_filecaps('/usr/bin/a\t\n/usr/bin/b\t(none)\n/usr/bin/c\tcap_net_raw=p\n'), {'/usr/bin/c':'cap_net_raw=p'})

    def test_nonusr_target_rejected(self):
        with self.assertRaises(ValueError):
            mod.parse_filecaps('/dev/sda\tcap_net_raw=p\n')

    def test_traversal_rejected(self):
        with self.assertRaises(ValueError):
            mod.parse_filecaps('/usr/../dev/sda\tcap_net_raw=p\n')

    def test_conflicting_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            mod.parse_filecaps('/usr/bin/a\tcap_net_raw=p\n/usr/bin/a\tcap_setuid=ep\n')

    def test_malformed_record_rejected(self):
        with self.assertRaises(ValueError):
            mod.parse_filecaps('/usr/bin/a cap_setuid=ep\n')


if __name__ == '__main__':
    unittest.main()
