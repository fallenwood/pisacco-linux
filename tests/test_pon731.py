"""Offline source/build checks and execution of the actual C register plan.

The C harness supplies synthetic bytes only; it performs no PMIC/phone access.
"""
import ctypes
import errno
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'kernel/power-7.3.1/picasso-pon-reason-audit731.c'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load('pon731_builder', ROOT / 'tools/build-pon731.py')
D = load('pon731_decoder', ROOT / 'tools/power-pon-reasons.py')


def reference_config():
    return '\n'.join(('CONFIG_LOCALVERSION="-picasso-wifi2"',
                      'CONFIG_CLANG_VERSION=220108', 'CONFIG_AS_VERSION=220108',
                      'CONFIG_LLD_VERSION=220108', 'CONFIG_MODULES=y',
                      '# CONFIG_MODVERSIONS is not set', 'CONFIG_LTO_NONE=y',
                      '# CONFIG_CFI is not set', 'CONFIG_RANDSTRUCT_NONE=y',
                      'CONFIG_CC_VERSION_TEXT="clang version 22.1.8 (reference)"',
                      'CONFIG_INITRAMFS_SOURCE="fixture.cpio.gz"'))


class Pon731SourceTests(unittest.TestCase):
    def test_exact_release_confirmation_existing_topology_and_no_probe(self):
        text = SOURCE.read_text()
        for required in ('"7.3.1-picasso-wifi2"', '!confirm_readonly',
                         'of_machine_is_compatible("xiaomi,picasso")',
                         '"qcom,pm8150"', '"qcom,pm8150l"', '"qcom,spmi-pmic"',
                         'primary->usid != 0', 'anchor->usid != 5',
                         'primary->ctrl != anchor->ctrl',
                         'primary->ctrl->dev.of_node != node'):
            self.assertIn(required, text)
        for forbidden in ('spmi_device_alloc(', 'spmi_device_add(', 'spmi_ext_register_',
                          'regmap_write(', 'regmap_update_bits(', 'regmap_init(',
                          'regcache_', 'writel(', 'register_reboot_notifier(',
                          'request_irq(', 'enable_irq(', 'disable_irq(', 'module_spmi_driver('):
            self.assertNotIn(forbidden, text)
        self.assertEqual(text.count('module_param('), 1)

    def test_existing_map_lifetime_is_locked_no_wait_or_reconfiguration(self):
        text = SOURCE.read_text()
        guards = ('device_trylock(&primary->dev)', 'device_is_bound(&primary->dev)',
                  'strcmp(primary->dev.driver->name, "pmic-spmi")',
                  'dev_get_regmap(&primary->dev, NULL)', 'capture_from_regmap(map)',
                  'device_unlock(&primary->dev)')
        self.assertEqual([text.index(g) for g in guards], sorted(text.index(g) for g in guards))
        self.assertNotIn('device_lock(', text)
        self.assertIn('spmi_device_put(primary)', text)
        self.assertIn('spmi_device_put(anchor)', text)

    def test_whitelist_and_cached_root_only_distinct_module(self):
        text = SOURCE.read_text()
        block = text.split('static const u16 addresses[] = {', 1)[1].split('};', 1)[0]
        self.assertEqual({f'{int(s, 16):04x}' for s in re.findall(r'0x[0-9a-f]+', block)}, D.ADDRESSES)
        show = text.split('static ssize_t snapshot_show', 1)[1].split('static struct kobj_attribute', 1)[0]
        self.assertNotIn('regmap', show.replace('existing-primary-regmap', ''))
        self.assertNotIn('capture_from_regmap', show)
        self.assertIn('__ATTR(snapshot, 0400', text)
        self.assertIn('kobject_create_and_add("picasso_pon_reason_audit731"', text)
        self.assertIn('obj-m += picasso-pon-reason-audit731.o', (SOURCE.parent / 'Makefile').read_text())

    def test_builder_only_allows_metadata_drift(self):
        ref = reference_config()
        self.assertEqual(B.check_config(ref, ref), [])
        changed = ref.replace('(reference)', '(different package build)').replace('fixture.cpio.gz', 'relocated.cpio.gz')
        self.assertEqual(B.check_config(ref, changed), ['CONFIG_CC_VERSION_TEXT', 'CONFIG_INITRAMFS_SOURCE'])
        self.assertEqual(B.check_config(ref, ref + '\nCONFIG_RUSTC_VERSION=109901'), ['CONFIG_RUSTC_VERSION'])
        with self.assertRaises(ValueError):
            B.check_config(ref, ref + '\nCONFIG_RUST=y')
        with self.assertRaises(ValueError):
            B.check_config(ref, ref + '\nCONFIG_SOME_FEATURE=y')
        for change in (('CONFIG_CLANG_VERSION=220108', 'CONFIG_CLANG_VERSION=230104'),
                       ('# CONFIG_MODVERSIONS is not set', 'CONFIG_MODVERSIONS=y'),
                       ('CONFIG_LTO_NONE=y', '# CONFIG_LTO_NONE is not set')):
            with self.assertRaises(ValueError):
                bad = ref.replace(*change)
                B.check_config(bad, bad)

    def test_builder_preserves_strict_export_checks_and_rejects_power_imports(self):
        B.check_imports(B.REQUIRED_IMPORTS | {'mutex_trylock', 'mutex_unlock'})
        for bad in ('regmap_write', 'spmi_ext_register_writel', 'register_reboot_notifier',
                    'regcache_cache_bypass', 'request_threaded_irq', 'spmi_device_alloc',
                    'call_usermodehelper'):
            with self.assertRaises(ValueError):
                B.check_imports(B.REQUIRED_IMPORTS | {bad})
        with self.assertRaises(ValueError):
            B.check_imports({'regmap_read'})
        text = (ROOT / 'tools/build-pon731.py').read_text()
        self.assertNotIn('KBUILD_MODPOST_WARN=1', text)
        self.assertIn("['vmlinux', 'modules_prepare']", text)
        for bad in ("['insmod'", "['rmmod'", "['ssh'", "['fastboot'", '/dev/mem'):
            self.assertNotIn(bad, text)

    def test_initramfs_magic_validation_not_filename_or_binary_filelist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'not-a-cpio-suffix.gz'
            raw = b'070701offline-fixture-not-a-hardware-measurement'
            for data, compressed in ((raw, False), (gzip.compress(raw), True)):
                path.write_bytes(data)
                self.assertEqual(B.initramfs_data(path), (data, compressed))
            for data in (b'file /init not-an-archive', gzip.compress(b'not-newc')):
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    B.initramfs_data(path)
        text = (ROOT / 'tools/build-pon731.py').read_text()
        self.assertIn('reference-initramfs.cpio.gz', text)

    def test_future_extra_build_selects_new_port_not_legacy_release_substitution(self):
        text = (ROOT / 'tools/build-extra-modules.py').read_text()
        self.assertIn("('power', 'power-7.3.1')", text)
        self.assertIn("release != '7.3.1-picasso-wifi2'", text)
        self.assertIn('picasso-pon-reason-audit731.c', text)
        self.assertNotIn('text.replace(old, json.dumps(release))', text)

    def test_optional_built_module_receipt_matches_current_source(self):
        receipt = ROOT / 'out/pon-731/build-accepted/manifest.json'
        if not receipt.exists():
            self.skipTest('Optional offline 7.3.1 module build not present')
        value = json.loads(receipt.read_text())
        self.assertEqual(value['status'], 'built_offline_not_loaded_or_hardware_tested')
        self.assertEqual(value['source_sha256'], hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        module = ROOT / value['module_file']
        self.assertEqual(value['module_sha256'], hashlib.sha256(module.read_bytes()).hexdigest())
        self.assertTrue(value['built_in_exports_verified'])
        self.assertFalse(value['phone_io'])


class Pon731CPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which('cc')
        if not compiler:
            raise unittest.SkipTest('Native C compiler unavailable for offline harness')
        cls.tmp = tempfile.TemporaryDirectory()
        text = SOURCE.read_text()
        plan = text[text.index('static const u16 addresses[]'):text.index('static int capture(void)')]
        harness = r'''
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint64_t u64;
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define BIT(n) (1U << (n))
struct regmap { unsigned int off; int fail, bad_id, nonbyte; int calls[10]; };
static int regmap_read(struct regmap *, unsigned int, unsigned int *);
''' + plan + r'''
static int regmap_read(struct regmap *map, unsigned int addr, unsigned int *value)
{
    const unsigned int ids[] = {0x51, 0x1e, 4};
    int i;
    for (i = 0; i < 10; i++)
        if (addresses[i] == addr) break;
    if (i == 10) return -EINVAL;
    map->calls[i]++;
    if (map->fail == i) return -EIO;
    *value = i < 3 ? ids[i] : (i == 5 ? map->off : 0);
    if (map->bad_id == i) *value ^= 1;
    if (map->nonbyte == i) *value = 256;
    return 0;
}
int exercise(unsigned int off, int fail, int bad_id, int nonbyte, int *calls, int *seen)
{
    struct regmap map = {.off = off, .fail = fail, .bad_id = bad_id, .nonbyte = nonbyte};
    int ret, i;
    memset(values, 0, sizeof(values)); memset(valid, 0, sizeof(valid));
    ret = capture_from_regmap(&map);
    for (i = 0; i < 10; i++) {calls[i] = map.calls[i]; seen[i] = valid[i];}
    return ret;
}
int invalid_or_duplicate(int slot, int *count)
{
    struct regmap map = {.fail = -1, .bad_id = -1, .nonbyte = -1};
    int ret;
    memset(valid, 0, sizeof(valid));
    if (slot == 0) read_slot(&map, 0);
    ret = read_slot(&map, slot); *count = map.calls[0]; return ret;
}
'''
        cpath, so = Path(cls.tmp.name) / 'plan.c', Path(cls.tmp.name) / 'plan.so'
        cpath.write_text(harness)
        subprocess.run([compiler, '-shared', '-fPIC', '-O2', '-o', str(so), str(cpath)], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(so))
        cls.lib.exercise.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        cls.lib.exercise.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_plan(self, off, fail=-1, bad_id=-1, nonbyte=-1):
        calls, seen = (ctypes.c_int * 10)(), (ctypes.c_int * 10)()
        ret = self.lib.exercise(off, fail, bad_id, nonbyte, calls, seen)
        return ret, list(calls), list(seen)

    def test_all_256_off_bytes_select_only_the_expected_banks_once(self):
        for off in range(256):
            with self.subTest(off=off):
                ret, calls, seen = self.run_plan(off)
                expected = [1] * 6 + [int(bool(off & 0x80)), int(bool(off & 0x40)),
                                      int(bool(off & 0x40)), int(bool(off & 0x20))]
                self.assertEqual((ret, calls, seen), (0, expected, expected))

    def test_each_identity_mismatch_stops_before_reason_registers(self):
        for slot in range(3):
            ret, calls, seen = self.run_plan(0xe0, bad_id=slot)
            self.assertEqual((ret, calls, seen), (-errno.ENODEV, [1] * 3 + [0] * 7, [1] * 3 + [0] * 7))

    def test_every_bus_failure_aborts_without_retry_or_later_reads(self):
        for slot in range(10):
            ret, calls, seen = self.run_plan(0xe0, fail=slot)
            self.assertEqual(ret, -errno.EIO)
            self.assertEqual(calls, [1] * (slot + 1) + [0] * (9 - slot))
            self.assertEqual(seen, [1] * slot + [0] * (10 - slot))

    def test_nonbyte_is_rejected_without_truncation(self):
        for slot in range(10):
            ret, calls, seen = self.run_plan(0xe0, nonbyte=slot)
            self.assertEqual(ret, -errno.ERANGE)
            self.assertEqual(calls, [1] * (slot + 1) + [0] * (9 - slot))
            self.assertEqual(seen[slot], 0)

    def test_out_of_range_and_duplicate_slot_never_issue_extra_reads(self):
        for slot, expected_count in ((10, 0), (0, 1)):
            count = ctypes.c_int()
            self.assertEqual(self.lib.invalid_or_duplicate(slot, ctypes.byref(count)), -errno.EINVAL)
            self.assertEqual(count.value, expected_count)


if __name__ == '__main__':
    unittest.main()
