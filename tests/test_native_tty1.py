# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('select_native_tty1', ROOT / 'tools/select-native-tty1.py')
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


class NativeTty1SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.units = self.root / 'system'
        self.wants = self.units / 'getty.target.wants'
        self.wants.mkdir(parents=True)
        (self.wants / 'getty@tty1.service').symlink_to(selector.GETTY)
        (self.wants / 'kmsconvt@tty1.service').symlink_to(selector.KMSCON)
        (self.units / 'autovt@.service').symlink_to(selector.KMSCON)
        (self.wants / 'kmsconvt@tty2.service').symlink_to(selector.KMSCON)
        self.backup = self.root / 'backup'

    def select(self):
        return selector.select_native_tty1(self.units, self.backup)

    def test_selects_only_tty1_preserving_other_vts_and_global_alias(self):
        result = self.select()
        self.assertEqual(result['after']['getty_want'], selector.GETTY)
        self.assertEqual((self.units / 'kmsconvt@tty1.service').readlink(), Path('/dev/null'))
        self.assertFalse((self.wants / 'kmsconvt@tty1.service').is_symlink())
        self.assertEqual((self.units / 'autovt@tty1.service').readlink(), Path(selector.GETTY))
        self.assertEqual((self.units / 'autovt@.service').readlink(), Path(selector.KMSCON))
        self.assertEqual((self.wants / 'kmsconvt@tty2.service').readlink(), Path(selector.KMSCON))
        self.assertEqual(json.loads((self.backup / 'before.json').read_text()), result['before'])
        self.assertTrue(result['no_service_start_or_hardware_operation'])

    def test_wrong_mask_or_regular_file_refused_before_any_mutation(self):
        mask = self.units / 'kmsconvt@tty1.service'
        for kind in ('wrong_symlink', 'file'):
            with self.subTest(kind=kind):
                if kind == 'wrong_symlink':
                    mask.symlink_to(selector.KMSCON)
                else:
                    mask.write_text('custom unit')
                with self.assertRaises(RuntimeError):
                    self.select()
                self.assertTrue((self.wants / 'kmsconvt@tty1.service').is_symlink())
                self.assertFalse(self.backup.exists())
                mask.unlink()

    def test_missing_native_getty_or_unexpected_competitor_refused(self):
        for name in ('getty@tty1.service', 'kmsconvt@tty1.service'):
            with self.subTest(name=name):
                path = self.wants / name
                old = path.readlink()
                path.unlink()
                path.symlink_to('/unexpected/template')
                with self.assertRaises(RuntimeError):
                    self.select()
                self.assertFalse(self.backup.exists())
                path.unlink()
                path.symlink_to(old)

    def test_unreviewed_tty1_alias_is_refused_before_any_mutation(self):
        (self.units / 'autovt@tty1.service').symlink_to(selector.KMSCON)
        with self.assertRaises(RuntimeError):
            self.select()
        self.assertFalse(self.backup.exists())
        self.assertFalse((self.units / 'kmsconvt@tty1.service').is_symlink())
        self.assertTrue((self.wants / 'kmsconvt@tty1.service').is_symlink())

    def test_existing_backup_cannot_be_overwritten(self):
        self.select()
        before = (self.backup / 'before.json').read_bytes()
        with self.assertRaises(RuntimeError):
            self.select()
        self.assertEqual((self.backup / 'before.json').read_bytes(), before)

    def test_already_selected_layout_is_checked_without_unmasking(self):
        self.select()
        result = selector.select_native_tty1(self.units, self.root / 'second-backup')
        self.assertEqual(result['before'], result['after'])

    def test_symlinked_system_directory_is_not_followed(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.units)
        with self.assertRaises(RuntimeError):
            selector.select_native_tty1(alias, self.backup)


if __name__ == '__main__':
    unittest.main()
