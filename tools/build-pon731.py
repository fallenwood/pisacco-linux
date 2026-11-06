#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build a separate, inert 7.3.1 PON module offline; no phone I/O or installation."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RELEASE = '7.3.1-picasso-wifi2'
# These metadata/input-path changes do not change enabled kernel features.
CONFIG_METADATA = {
    'CONFIG_CC_VERSION_TEXT', 'CONFIG_INITRAMFS_SOURCE',
    # Rust is disabled in this C-only reference. Its detected toolchain metadata
    # may differ on the host without changing a compiled feature or C ABI.
    'CONFIG_RUSTC_VERSION', 'CONFIG_RUSTC_VERSION_TEXT',
    'CONFIG_RUSTC_LLVM_VERSION', 'CONFIG_RUSTC_LLVM_MAJOR_VERSION',
    'CONFIG_RUSTC_CLANG_LLVM_COMPATIBLE', 'CONFIG_RUSTC_HAS_SPAN_FILE',
    'CONFIG_RUSTC_HAS_UNNECESSARY_TRANSMUTES', 'CONFIG_RUSTC_HAS_FILE_WITH_NUL',
    'CONFIG_RUSTC_HAS_FILE_AS_C_STR',
    'CONFIG_RUSTC_HAS_SUSPICIOUS_RUNTIME_SYMBOL_DEFINITIONS',
}
FORBIDDEN_IMPORTS = ('write', 'update_bits', 'register_driver', 'device_add',
                     'device_alloc', 'notifier', 'irq', 'reboot', 'restart',
                     'poweroff', 'regcache', 'regmap_init')
REQUIRED_IMPORTS = {'regmap_read', 'dev_get_regmap', 'device_is_bound',
                    'spmi_find_device_by_of_node'}
ALLOWED_IMPORTS = {
    '__stack_chk_fail', 'dev_get_regmap', 'device_is_bound', 'kernel_kobj',
    'kobject_create_and_add', 'kobject_put', 'ktime_get_with_offset',
    'mutex_trylock', 'mutex_unlock', 'of_device_is_available',
    'of_device_is_compatible', 'of_find_node_opts_by_path',
    'of_machine_compatible_match', 'of_node_put', 'param_ops_bool',
    'put_device', 'regmap_read', 'spmi_find_device_by_of_node', 'strcmp',
    'sysfs_create_file_ns', 'sysfs_emit', 'sysfs_emit_at', 'sysfs_remove_file_ns',
}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def config_entries(text):
    entries = {}
    for line in text.splitlines():
        if line.startswith('CONFIG_') and '=' in line:
            key, value = line.split('=', 1)
            entries[key] = value
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
            entries[line[2:-11]] = 'n'
    return entries


def check_config(reference, prepared):
    before, after = config_entries(reference), config_entries(prepared)
    if before.get('CONFIG_RUST', 'n') != 'n' or after.get('CONFIG_RUST', 'n') != 'n':
        raise ValueError('This reviewed build supports only the native C-only configuration')
    changed = {key for key in before.keys() | after.keys()
               if before.get(key) != after.get(key)}
    if changed - CONFIG_METADATA:
        raise ValueError('Kernel feature/config drift: ' + ', '.join(sorted(changed - CONFIG_METADATA)))
    for key, value in {'CONFIG_LOCALVERSION': '"-picasso-wifi2"',
                       'CONFIG_CLANG_VERSION': '220108', 'CONFIG_AS_VERSION': '220108',
                       'CONFIG_LLD_VERSION': '220108', 'CONFIG_MODULES': 'y',
                       'CONFIG_MODVERSIONS': 'n', 'CONFIG_LTO_NONE': 'y',
                       'CONFIG_CFI': 'n', 'CONFIG_RANDSTRUCT_NONE': 'y'}.items():
        if before.get(key) != value:
            raise ValueError('Unreviewed native configuration: ' + key)
    return sorted(changed)


def initramfs_data(path):
    data = path.read_bytes()
    if len(data) > 32 * 1024 * 1024:
        raise ValueError('Oversized ordinary initramfs input')
    if data.startswith(b'\x1f\x8b'):
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            unpacked = stream.read(32 * 1024 * 1024 + 1)
    else:
        unpacked = data
    if len(unpacked) > 32 * 1024 * 1024 or not unpacked.startswith(b'070701'):
        raise ValueError('Expected an ordinary newc CPIO archive, optionally gzip compressed')
    return data, data.startswith(b'\x1f\x8b')


def check_imports(symbols):
    if not REQUIRED_IMPORTS <= symbols:
        raise ValueError('Required existing-device APIs missing')
    if symbols - ALLOWED_IMPORTS:
        raise ValueError('Unreviewed kernel import: ' + ', '.join(sorted(symbols - ALLOWED_IMPORTS)))
    forbidden = {s for s in symbols if any(part in s.lower() for part in FORBIDDEN_IMPORTS)}
    if forbidden:
        raise ValueError('Unexpected write/probe/power/IRQ API: ' + ', '.join(sorted(forbidden)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-config', type=Path, required=True)
    parser.add_argument('--initramfs', type=Path, required=True,
                        help='Existing ordinary CPIO[.gz] inside the repository, ABI rebuild only')
    parser.add_argument('--output', type=Path, required=True, help='Fresh directory under out/')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--reuse-kbuild', type=Path,
                        help='Reuse a reviewed matching build under out/; still validate and rebuild normally')
    args = parser.parse_args()
    os.umask(0o077)
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'out') or not args.initramfs.resolve().is_relative_to(ROOT):
        parser.error('Output and relocated initramfs must remain inside this repository')
    if not 1 <= args.jobs <= 16:
        parser.error('Jobs must be between 1 and 16')
    reference = args.reference_config.read_text()
    check_config(reference, reference)
    ramfs_data, compressed = initramfs_data(args.initramfs)
    source = ROOT / 'src/linux-7.3.1'
    manifest = json.loads((ROOT / 'sources-7.3.1.json').read_text())
    archive = ROOT / 'downloads/linux-7.3.1.tar.xz'
    expected = next(d['sha256'] for d in manifest['downloads'] if d['file'] == archive.name)
    if digest(archive) != expected:
        raise ValueError('Pinned upstream source archive differs')
    source_receipt = json.loads((source / '.picasso-source.json').read_text())
    series = ROOT / 'kernel/patches/7.3/series'
    patches = {name: digest(series.parent / name) for name in series.read_text().splitlines()
               if name and not name.startswith('#')}
    if source_receipt != {'kernel_version': '7.3.1', 'patches': patches}:
        raise ValueError('Prepared source patch receipt differs')
    version = subprocess.check_output(['clang', '--version'], text=True).splitlines()[0]
    if 'clang version 22.1.8 ' not in version:
        raise ValueError('Use the native compiler major/minor/patch, clang 22.1.8')
    resources = Path(subprocess.check_output(['clang', '--print-resource-dir'], text=True).strip())
    if not (resources / 'include/stddef.h').is_file():
        raise ValueError('Matching clang builtin resource headers are missing')
    for tool in ('ld.lld', 'llvm-ar', 'llvm-nm', 'llvm-objcopy', 'flex', 'bison', 'bc', 'openssl'):
        if shutil.which(tool) is None:
            raise ValueError('Missing offline build tool: ' + tool)
    out.mkdir(mode=0o700)  # Exclusive: never clean or overwrite a prior build.
    kb = args.reuse_kbuild.resolve() if args.reuse_kbuild else out / 'kbuild'
    stage = out / 'module'
    if args.reuse_kbuild:
        if (not kb.is_relative_to(ROOT / 'out') or not (kb / 'vmlinux.o').is_file()
                or not (kb / 'vmlinux.symvers').is_file()):
            raise ValueError('Reuse requires a reviewed complete kernel build inside out/')
        check_config(reference, (kb / '.config').read_text())
    else:
        kb.mkdir()
    stage.mkdir()
    (out / 'reference.config').write_text(reference)
    # gen_initramfs.sh recognizes *.cpio[.*], not arbitrary names ending in .gz.
    # Normalize the suffix so compressed bytes can never be parsed as a file list.
    ramfs = out / ('reference-initramfs.cpio.gz' if compressed else 'reference-initramfs.cpio')
    ramfs.write_bytes(ramfs_data)
    relocated = reference.replace(config_entries(reference)['CONFIG_INITRAMFS_SOURCE'],
                                  json.dumps(str(ramfs)))
    if not args.reuse_kbuild:
        (kb / '.config').write_text(relocated)
    make = ['make', '-s', '-C', str(source), 'O=' + str(kb), 'ARCH=arm64',
            'LLVM=1', 'LOCALVERSION=', '-j' + str(args.jobs)]
    env = dict(os.environ, KBUILD_BUILD_USER='offline', KBUILD_BUILD_HOST='offline',
               RUSTUP_TOOLCHAIN='stable')
    for bad in ('KBUILD_MODPOST_WARN', 'KBUILD_EXTRA_SYMBOLS', 'KBUILD_NSDEPS',
                'KCFLAGS', 'KCPPFLAGS', 'CFLAGS_MODULE', 'KCONFIG_CONFIG',
                'KCONFIG_ALLCONFIG', 'MAKEFLAGS', 'MFLAGS'):
        if env.get(bad):
            raise ValueError('Unreviewed build override: ' + bad)
    subprocess.run(make + ['olddefconfig'], env=env, check=True)
    changed = check_config(reference, (kb / '.config').read_text())
    # Genuine built-in export table, not a fabricated symvers or ignored modpost errors.
    # This ABI-reference vmlinux is never installed or packed into a boot image.
    subprocess.run(make + ['vmlinux', 'modules_prepare'], env=env, check=True)
    if (kb / 'include/config/kernel.release').read_text().strip() != RELEASE:
        raise ValueError('Wrong prepared kernel release')
    shutil.copyfile(kb / 'vmlinux.symvers', kb / 'Module.symvers')
    for name in ('Makefile', 'picasso-pon-reason-audit731.c'):
        shutil.copyfile(ROOT / 'kernel/power-7.3.1' / name, stage / name)
    subprocess.run(make + ['M=' + str(stage), 'modules'], env=env, check=True)
    module = stage / 'picasso-pon-reason-audit731.ko'
    vermagic = subprocess.check_output(['modinfo', '-F', 'vermagic', str(module)], text=True).strip()
    if vermagic != RELEASE + ' SMP preempt mod_unload aarch64':
        raise ValueError('Unexpected module ABI: ' + vermagic)
    undefined = subprocess.check_output(['llvm-nm', '-u', str(module)], text=True)
    symbols = {line.split()[-1] for line in undefined.splitlines() if line.strip()}
    check_imports(symbols)
    exports = {line.split()[1] for line in (kb / 'vmlinux.symvers').read_text().splitlines()}
    if symbols - exports:
        raise ValueError('Unresolved import(s) absent from real built-in export table')
    check_config(reference, (kb / '.config').read_text())
    receipt = {'status': 'built_offline_not_loaded_or_hardware_tested',
               'kernel_release': RELEASE, 'vermagic': vermagic, 'compiler': version,
               'reference_config_sha256': digest(args.reference_config),
               'prepared_config_sha256': digest(kb / '.config'),
               'config_metadata_changes_only': changed,
               'source_archive_sha256': expected, 'patch_sha256': patches,
               'module_sha256': digest(module),
               'module_file': str(module.relative_to(ROOT)),
               'source_sha256': digest(stage / 'picasso-pon-reason-audit731.c'),
               'decoder_sha256': digest(ROOT / 'tools/power-pon-reasons.py'),
               'undefined_symbols': sorted(symbols), 'built_in_exports_verified': True,
               'reused_reviewed_kbuild': bool(args.reuse_kbuild),
               'baseline_runtime_assets_modified': False, 'phone_io': False,
               'PMIC_register_reads': False, 'PMIC_register_writes': False,
               'power_actions': False}
    (out / 'manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
