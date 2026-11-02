#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build a fresh RAM-only, transition-blocked loader image. No device I/O."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import tarfile

from bootimg import pack, parse_stock
from fdt import dtbo_entries, fixed_regions, nodes, region_covered, split_fdts

ROOT = Path(__file__).resolve().parents[1]
PIN_DIR = ROOT / 'petitboot'
RELEASE = '7.3.1-picasso-petitboot2'
SPEC = importlib.util.spec_from_file_location('petitboot_userspace', ROOT / 'tools/build-petitboot.py')
USERSPACE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(USERSPACE)
digest = USERSPACE.digest


def new_output(path):
    """Reject symlink redirects, existing paths and writes outside ignored out/."""
    path = Path(os.path.abspath(path))
    out = ROOT / 'out/petitboot-1.15'
    if path == out or not path.is_relative_to(out):
        raise ValueError('Output must be a fresh directory below out/petitboot-1.15/')
    for parent in (path, *path.parents):
        if parent == ROOT:
            break
        if parent.is_symlink():
            raise ValueError(f'Symlinked output path: {parent}')
    if path.exists():
        raise ValueError('Output already exists; choose a fresh directory')
    return path


def check_file(path, expected):
    if (not path.is_file() or path.stat().st_size != expected['size'] or
            digest(path) != expected['sha256']):
        raise ValueError(f'Missing or changed retained input: {path}')


def retained_targets():
    targets = []
    for relative in ('out', 'out/linux-7.3.1'):
        directory = ROOT / relative
        manifest_path = directory / 'boot-manifest.json'
        manifest = json.loads(manifest_path.read_text())
        files = {}
        for name, data in manifest['inputs_and_outputs'].items():
            path = Path(name)
            # The original 6.18 receipt used a repository-directory prefix.
            if not path.is_absolute() and path.parts[0] == ROOT.name:
                path = Path(*path.parts[1:])
            path = (ROOT / path).resolve()
            if not path.is_relative_to(ROOT):
                raise ValueError('Retained receipt references a file outside this repository')
            files[path] = data
        for path, data in files.items():
            check_file(path, data)
        for name in ('Image', 'picasso.dtb', 'kernel.config', 'boot-picasso.img'):
            if (directory / name).resolve() not in files:
                raise ValueError(f'Retained receipt missing {relative}/{name}')
        config = (directory / 'kernel.config').read_text()
        local = next(line.split('=', 1)[1].strip('"') for line in config.splitlines()
                     if line.startswith('CONFIG_LOCALVERSION='))
        targets.append({
            'directory': directory,
            'release': manifest['sources']['kernel_version'] + local,
            'manifest_sha256': digest(manifest_path),
        })
    rescue = json.loads((ROOT / 'out/boot-manifest.json').read_text())
    if not rescue.get('hardware_test_matches_image'):
        raise ValueError('Retained 6.18 image does not match its native acceptance receipt')
    current = json.loads((ROOT / 'out/linux-7.3.1/offline-candidate.json').read_text())
    if not (current.get('authorized_startup_scope_acceptance_complete') and
            current.get('default_switch_acceptance_complete') and
            current.get('verified_618_rescue_preserved') and
            current.get('boot_image_prefix_readback_matches')):
        raise ValueError('Missing current/default and retained-rescue acceptance')
    return targets


def initramfs_list(root, destination):
    lines = []
    for path in sorted(root.rglob('*'), key=lambda p: (len(p.parts), p)):
        relative = '/' + path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.lstat().st_mode)
        if any(c.isspace() for c in str(path)):
            raise ValueError('gen_init_cpio paths must not contain whitespace')
        if path.is_symlink():
            target = str(path.readlink())
            if target.startswith('/') or '..' in Path(target).parts:
                raise ValueError('Unexpected initramfs symlink')
            lines.append(f'slink {relative} {target} {mode:o} 0 0')
        elif path.is_dir():
            lines.append(f'dir {relative} {mode:o} 0 0')
        elif path.is_file():
            lines.append(f'file {relative} {path} {mode:o} 0 0')
        else:
            raise ValueError(f'Unexpected initramfs file type: {path}')
    lines += ['nod /dev/console 0600 0 0 c 5 1', 'nod /dev/null 0666 0 0 c 1 3',
              'nod /dev/kmsg 0600 0 0 c 1 11']
    destination.write_text('\n'.join(lines) + '\n')


def check_config(config):
    lines = set(config.splitlines())
    required = ('NET', 'UNIX', 'BLK_DEV_INITRD', 'DEVTMPFS', 'TMPFS', 'PROC_FS',
                'SYSFS', 'MODULES', 'MODULE_UNLOAD', 'KEXEC', 'KEXEC_FILE', 'SYSCTL',
                'INPUT_EVDEV', 'INPUT_PM8941_PWRKEY', 'BACKLIGHT_CLASS_DEVICE',
                'THERMAL', 'QCOM_TSENS', 'DRM_SIMPLEDRM', 'FRAMEBUFFER_CONSOLE',
                'CMDLINE_FORCE', 'CPU_FREQ_DEFAULT_GOV_POWERSAVE', 'PRINTK',
                'USB_G_SERIAL', 'U_SERIAL_CONSOLE', 'USB_U_SERIAL', 'USB_F_ACM',
                'USB_DWC3', 'USB_DWC3_QCOM', 'PHY_QCOM_USB_SNPS_FEMTO_V2')
    prohibited = ('BLOCK', 'INET', 'IPV6', 'PACKET', 'WLAN', 'BT', 'REMOTEPROC',
                  'RPMSG', 'QRTR', 'QCOM_PD_MAPPER', 'QCOM_RMTFS_MEM', 'EFI',
                  'LOCALVERSION_AUTO', 'MAGIC_SYSRQ', 'USB_CONFIGFS',
                  'USB_U_ETHER', 'USB_F_NCM', 'USB_F_ECM', 'USB_F_RNDIS',
                  'USB_F_MASS_STORAGE', 'USB_F_FS')
    for symbol in required:
        if f'CONFIG_{symbol}=y' not in lines:
            raise ValueError(f'Loader requires built-in CONFIG_{symbol}')
    for symbol in prohibited:
        if f'CONFIG_{symbol}=y' in lines or f'CONFIG_{symbol}=m' in lines:
            raise ValueError(f'Loader forbids CONFIG_{symbol}')
    cmdline = next(line for line in lines if line.startswith('CONFIG_CMDLINE='))
    if 'root=' in cmdline or 'rdinit=/init' not in cmdline:
        raise ValueError('Loader command line must enter RAM-only /init without a disk root')
    if f'CONFIG_LOCALVERSION="{RELEASE.removeprefix("7.3.1")}"' not in lines:
        raise ValueError('Loader release must not collide with retained kernels')
    if 'CONFIG_MODPROBE_PATH=""' not in lines:
        raise ValueError('Loader must have no kernel module-autoload executable')
    if int(next((line.split('=', 1)[1] for line in lines
                 if line.startswith('CONFIG_LOG_BUF_SHIFT=')), '0')) < 20:
        raise ValueError('USB diagnostics require at least a 1 MiB kernel log buffer')
    for argument in ('console=ttyGS0', 'g_serial.use_acm=1', 'g_serial.use_obex=0',
                     'g_serial.n_ports=1', 'g_serial.iSerialNumber=picasso-menu-diagnostics',
                     'printk.devkmsg=on'):
        if argument not in cmdline.strip('"').split():
            raise ValueError(f'USB diagnostic command line requires {argument}')


def check_dtb(baseline, candidate):
    old, new = nodes(baseline), nodes(candidate)
    power = '/soc@0/spmi@c440000/pmic@0/pon@800/pwrkey'
    resin = power.rsplit('/', 1)[0] + '/resin'
    expected = {path: dict(props) for path, props in old.items()}
    expected[power]['compatible'] = b'xiaomi,picasso-pwrkey-input\0'
    for name in ('debounce', 'bias-pull-up'):
        expected[power].pop(name)
    expected[resin] = {
        'compatible': b'xiaomi,picasso-resin-input\0',
        'interrupts': struct.pack('>4I', 0, 8, 1, 3),
        'linux,code': struct.pack('>I', 114),
    }
    if new != expected:
        changed = sorted(path for path in old.keys() | new.keys()
                         if old.get(path) != new.get(path) and path not in (power, resin))
        raise ValueError(f'DTB exceeds input-only changes; unexpected nodes: {changed}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--userspace', type=Path, required=True)
    parser.add_argument('--sysroot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=min(os.cpu_count() or 1, 6))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    output = new_output(args.output)
    if any(c.isspace() for c in str(output)):
        parser.error('Output path must not contain whitespace')
    bundle = args.userspace.resolve()
    sysroot = args.sysroot.resolve()
    if output.is_relative_to(bundle) or output.is_relative_to(sysroot):
        raise ValueError('Output must not be nested inside userspace/sysroot inputs')
    receipt = json.loads((bundle / 'build.json').read_text())
    pins = json.loads((PIN_DIR / 'sources.json').read_text())
    patches = sorted((PIN_DIR / 'patches').glob('*.patch'))
    if (receipt['arch'] != 'aarch64' or receipt['sources'] != pins or
            receipt['patches'] != {p.name: digest(p) for p in patches}):
        raise ValueError('ARM64 userspace receipt does not match current pins/patches')
    for name, expected in receipt['programs'].items():
        if digest(bundle / 'rootfs' / name) != expected:
            raise ValueError(f'Changed userspace program: {name}')
    targets = retained_targets()
    source_files = [PIN_DIR / name for name in
                    ('init', 'loader.config', 'loader.dts', 'console-check.c', 'usb-log.c')]
    source_files += [ROOT / 'kernel/display/picasso-wled-service.c', ROOT / 'shim/copydown.S',
                     bundle / 'build.json']
    source_snapshot = {str(p): digest(p) for p in source_files}
    sources = json.loads((ROOT / 'sources-7.3.1.json').read_text())
    for item in sources['downloads']:
        if digest(ROOT / 'downloads' / item['file']) != item['sha256']:
            raise ValueError(f"Pinned download changed: {item['file']}")
    with tarfile.open(ROOT / 'downloads/busybox-static.apk', 'r:gz',
                      ignore_zeros=True) as archive:
        busybox = archive.extractfile('bin/busybox.static').read()
    if busybox != (ROOT / 'downloads/busybox').read_bytes():
        raise ValueError('BusyBox executable differs from the pinned APK')
    if busybox[:5] != b'\x7fELF\x02' or struct.unpack_from('<H', busybox, 18)[0] != 183:
        raise ValueError('BusyBox must be AArch64 ELF64')
    versions = sorted((sysroot / 'usr/lib/gcc/aarch64-redhat-linux').glob('*'))
    if len(versions) != 1:
        raise ValueError('Expected exactly one target GCC runtime directory')
    device = json.loads((ROOT / 'device.json').read_text())
    baseline = device['boot_baseline']
    stock, dtbo = ((ROOT / baseline[name]).read_bytes()
                   for name in ('boot_file', 'dtbo_file'))
    if (hashlib.sha256(stock).hexdigest() != baseline['boot_sha256'] or
            hashlib.sha256(dtbo).hexdigest() != baseline['dtbo_sha256']):
        raise ValueError('Stock boot/DTBO does not match configured ROM baseline')

    output.mkdir(parents=True, mode=0o700)
    env = dict(os.environ, LC_ALL='C.UTF-8', GIT_CEILING_DIRECTORIES=str(output))
    for name in ('ARCH', 'CROSS_COMPILE', 'KCONFIG_CONFIG', 'KBUILD_OUTPUT',
                 'KBUILD_SRC', 'LOCALVERSION', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS'):
        env.pop(name, None)

    def run(command, log, cwd=output):
        USERSPACE.run([str(x) for x in command], cwd, env, output / log)

    archive_path = ROOT / 'downloads/linux-7.3.1.tar.xz'
    print('Extracting a separate pinned Linux source; retained outputs are read-only', flush=True)
    with tarfile.open(archive_path) as archive:
        if any(m.name != 'linux-7.3.1' and not m.name.startswith('linux-7.3.1/')
               for m in archive):
            raise ValueError('Unexpected kernel archive root')
        archive.extractall(output, filter='data')
    source = output / 'linux-7.3.1'
    series = ROOT / 'kernel/patches/7.3/series'
    base_patches = [series.parent / line.strip() for line in series.read_text().splitlines()
                    if line.strip() and not line.startswith('#')]
    input_patches = sorted((PIN_DIR / 'kernel-patches').glob('*.patch'))
    if len(input_patches) != 1:
        raise ValueError('Expected exactly one input-only kernel patch')
    base_receipt = json.loads((ROOT / 'src/linux-7.3.1/.picasso-source.json').read_text())
    if base_receipt['patches'] != {p.name: digest(p) for p in base_patches}:
        raise ValueError('Base patch series differs from retained 7.3.1 source receipt')
    for index, patch in enumerate(base_patches + input_patches):
        run(['git', 'apply', '--check', patch], f'kernel-patch-{index}-check.log', source)
        run(['git', 'apply', patch], f'kernel-patch-{index}.log', source)

    root = output / 'rootfs'
    shutil.copytree(bundle / 'rootfs', root)
    (root / 'usr/libexec/picasso-petitboot/kexec.unvalidated').unlink()
    for name in ('bin', 'sbin', 'etc/petitboot', 'proc', 'sys', 'dev', 'run', 'tmp'):
        (root / name).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'downloads/busybox', root / 'bin/busybox')
    (root / 'bin/busybox').chmod(0o755)
    (root / 'bin/sh').symlink_to('busybox')
    shutil.copyfile(PIN_DIR / 'init', root / 'init')
    (root / 'init').chmod(0o755)
    menu = []
    for target in reversed(targets):
        name = target['release']
        directory = root / 'kernels' / name
        directory.mkdir(parents=True)
        for filename in ('Image', 'picasso.dtb'):
            shutil.copyfile(target['directory'] / filename, directory / filename)
        menu += [f'LABEL {name}', f'MENU LABEL {name} [transition blocked]',
                 f'KERNEL file:///kernels/{name}/Image',
                 f'FDT file:///kernels/{name}/picasso.dtb', '']
    (root / 'etc/petitboot/menu.conf').write_text('\n'.join(menu))
    helper = root / 'usr/libexec/picasso-petitboot/console-check'
    run(['clang', '--target=aarch64-linux-gnu', f'--sysroot={sysroot}',
         f'--gcc-install-dir={versions[0]}', '-fuse-ld=lld', '-O2',
         '-Wall', '-Wextra', '-Werror', PIN_DIR / 'console-check.c', '-o', helper],
        'console-check-build.log')
    USERSPACE.copy_libraries([helper], sysroot, root)
    usb_log = root / 'usr/libexec/picasso-petitboot/usb-log'
    run(['clang', '--target=aarch64-linux-gnu', f'--sysroot={sysroot}',
         f'--gcc-install-dir={versions[0]}', '-fuse-ld=lld', '-O2',
         '-Wall', '-Wextra', '-Werror', PIN_DIR / 'usb-log.c', '-o', usb_log],
        'usb-log-build.log')
    USERSPACE.copy_libraries([usb_log], sysroot, root)
    initlist = output / 'initramfs.list'
    initramfs_list(root, initlist)
    kbuild = output / 'kbuild'
    kbuild.mkdir()
    shutil.copyfile(ROOT / 'out/linux-7.3.1/kernel.config', kbuild / '.config')
    config_tool = source / 'scripts/config'
    run([config_tool, '--file', kbuild / '.config',
         *sum((['-d', 'CPU_FREQ_DEFAULT_GOV_' + governor] for governor in
               ('PERFORMANCE', 'USERSPACE', 'SCHEDUTIL', 'CONSERVATIVE', 'ONDEMAND')), [])],
        'governor-config.log')
    run([source / 'scripts/kconfig/merge_config.sh', '-m', '-O', kbuild,
         kbuild / '.config', PIN_DIR / 'loader.config'], 'config-merge.log')
    run([config_tool, '--file', kbuild / '.config', '--set-str',
         'INITRAMFS_SOURCE', initlist], 'initramfs-config.log')
    make = ['make', '-s', '-C', source, f'O={kbuild}', 'ARCH=arm64', 'LLVM=1',
            'LOCALVERSION=']
    run([*make, 'olddefconfig'], 'olddefconfig.log')
    check_config((kbuild / '.config').read_text())
    release = subprocess.check_output([str(x) for x in [*make, 'kernelrelease']],
                                      env=env, text=True).strip()
    if release != RELEASE:
        raise ValueError(f'Unexpected loader release: {release}')
    print('Building RAM-only loader kernel and matching leased display module', flush=True)
    run([*make, f'-j{args.jobs}', 'Image', 'modules'], 'kernel-build.log')
    modules = output / 'display-module'
    modules.mkdir()
    shutil.copyfile(ROOT / 'kernel/display/picasso-wled-service.c',
                    modules / 'picasso-wled-service.c')
    (modules / 'Makefile').write_text(
        'obj-m += picasso_wled_service.o\n'
        'picasso_wled_service-y := picasso-wled-service.o\n')
    run([*make, f'M={modules}', f'-j{args.jobs}', 'modules'], 'display-module-build.log')
    shutil.copyfile(modules / 'picasso_wled_service.ko',
                    root / 'usr/libexec/picasso-petitboot/picasso-wled-service.ko')
    initramfs_list(root, initlist)
    run([*make, f'-j{args.jobs}', 'Image'], 'kernel-final-image.log')
    shutil.copyfile(kbuild / 'arch/arm64/boot/Image', output / 'Image')
    shutil.copyfile(kbuild / '.config', output / 'kernel.config')
    run(['clang', '-E', '-P', '-nostdinc', '-undef', '-D__DTS__',
         '-x', 'assembler-with-cpp', '-I', source / 'include',
         '-I', source / 'arch/arm64/boot/dts/qcom', '-I', ROOT / 'dts',
         PIN_DIR / 'loader.dts', '-o', output / 'loader.pp.dts'], 'dtb-preprocess.log')
    dtc = kbuild / 'scripts/dtc'
    run([dtc / 'dtc', '-I', 'dts', '-O', 'dtb', '-o', output / 'picasso.dtb',
         output / 'loader.pp.dts'], 'dtb-build.log')
    check_dtb((ROOT / 'out/linux-7.3.1/picasso.dtb').read_bytes(),
              (output / 'picasso.dtb').read_bytes())
    bases = split_fdts(parse_stock(stock)['dtb'])
    overlays = dtbo_entries(dtbo)
    base_path, overlay_path, merged_path = (output / name for name in
                                           ('stock-base.dtb', 'stock-overlay.dtbo', 'stock-merged.dtb'))
    base_path.write_bytes(bases[baseline['dtb_index']])
    overlay_path.write_bytes(overlays[baseline['dtbo_index']]['data'])
    run([dtc / 'fdtoverlay', '-i', base_path, '-o', merged_path, overlay_path],
        'stock-overlay.log')
    required = fixed_regions(nodes(merged_path.read_bytes()))
    available = fixed_regions(nodes((output / 'picasso.dtb').read_bytes()))
    if not required or not all(region_covered(r, available) for r in required):
        raise ValueError('Loader DTB leaves stock fixed/no-map memory uncovered')
    run(['clang', '--target=aarch64-linux-gnu', '-c', '-x', 'assembler-with-cpp',
         f'-DIMAGE_PATH="{output}/Image"', f'-DDTB_PATH="{output}/picasso.dtb"',
         ROOT / 'shim/copydown.S', '-o', output / 'shim.o'], 'shim-compile.log')
    run(['ld.lld', '--image-base=0', '-Ttext=0', '--entry=_start',
         output / 'shim.o', '-o', output / 'shim.elf'], 'shim-link.log')
    run(['llvm-objcopy', '-O', 'binary', output / 'shim.elf', output / 'shim.bin'],
        'shim-binary.log')
    symbols = subprocess.check_output(['llvm-nm', '-n', str(output / 'shim.elf')],
                                      text=True)
    (output / 'shim.symbols').write_text(symbols)
    addresses = {fields[2]: int(fields[0], 16) for line in symbols.splitlines()
                 if len(fields := line.split()) == 3}
    shim, image, dtb = ((output / name).read_bytes() for name in
                        ('shim.bin', 'Image', 'picasso.dtb'))
    layout = {
        'arm64_header': shim[56:60] == b'ARMd',
        'payload_size': struct.unpack_from('<Q', shim, 16)[0] == len(shim),
        'image_source_alignment': addresses['linux_image'] == 0x200000,
        'trampoline_outside_destination': addresses['copy_entry'] >= len(image),
        'image_matches': shim[addresses['linux_image']:addresses['linux_end']] == image,
        'dtb_matches': shim[addresses['runtime_dtb']:addresses['runtime_dtb_end']] == dtb,
        'dtb_alignment': addresses['runtime_dtb'] % 8 == 0,
        'dtb_outside_kernel_memory': addresses['runtime_dtb'] >=
            struct.unpack_from('<Q', image, 16)[0],
    }
    if not all(layout.values()):
        raise ValueError(f'Loader shim layout failed: {layout}')
    (output / 'boot-petitboot-menu.img').write_bytes(pack(stock, shim, 128 << 20))
    retained_targets()
    if source_snapshot != {str(p): digest(p) for p in source_files}:
        raise ValueError('Loader inputs changed during this build; no acceptance receipt written')
    files = ('Image', 'picasso.dtb', 'kernel.config', 'shim.bin', 'boot-petitboot-menu.img')
    record = {
        'status': 'offline-only USB diagnostic menu candidate; no native boot authorization',
        'kernel_release': RELEASE, 'boot_image_packed': True, 'hardware_validated': False,
        'transitions': 'blocked helper and irreversible per-boot kexec_load_disabled=1',
        'menu_window_seconds': 120, 'usb_or_network_diagnostics': True,
        'usb_diagnostics': {
            'transport': 'built-in CDC ACM ttyGS0 console and output-only kernel-log relay',
            'host_input_commands': False, 'network': False, 'shell': False,
            'relay_survives_menu_failure': True, 'hardware_validated': False,
            'relay_sha256': digest(usb_log),
        },
        'kernel_archive_sha256': digest(archive_path),
        'kernel_patches': {p.name: digest(p) for p in base_patches + input_patches},
        'userspace_receipt': str(bundle / 'build.json'),
        'userspace_receipt_sha256': digest(bundle / 'build.json'),
        'display_module_source_sha256': digest(ROOT / 'kernel/display/picasso-wled-service.c'),
        'loader_sources': {name: digest(PIN_DIR / name) for name in
                           ('init', 'loader.config', 'loader.dts', 'console-check.c', 'usb-log.c')},
        'retained_targets': [{k: str(v) for k, v in t.items()} for t in targets],
        'fixed_regions_covered': len(required), 'input_only_dtb_diff': True,
        'shim_layout': layout, 'phone_io_performed': False,
        'files': {name: {'size': (output / name).stat().st_size,
                         'sha256': digest(output / name)} for name in files},
    }
    (output / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(output / 'build.json')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
