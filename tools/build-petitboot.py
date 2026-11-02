#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build an isolated Petitboot userspace bundle; never install or boot it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PIN_DIR = ROOT / 'petitboot'
GUARD = '/usr/libexec/picasso-petitboot/blocked-transition'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def archive_source(source, pin, dest):
    head = subprocess.check_output(
        ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if head != pin['commit']:
        raise ValueError(f"{source}: expected {pin['commit']}, found {head}")
    dest.mkdir()
    with subprocess.Popen(
            ['git', '-C', str(source), 'archive', '--format=tar', head],
            stdout=subprocess.PIPE) as archive:
        with tarfile.open(fileobj=archive.stdout, mode='r|') as tar:
            tar.extractall(dest, filter='data')
        if archive.wait():
            raise RuntimeError(f'git archive failed: {source}')


def run(command, cwd, env, log):
    with log.open('wb') as stream:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'{command[0]} failed ({result.returncode}); see {log}')


def root_file(root, path):
    """Resolve target symlinks inside the sysroot, not against the host root."""
    parts = list(Path(path).parts)
    resolved = root
    for _ in range(64):
        if not parts:
            if not resolved.exists():
                raise FileNotFoundError(resolved)
            if not resolved.is_file():
                raise ValueError(f'Not a regular sysroot file: {resolved}')
            return resolved
        part = parts.pop(0)
        if part in ('/', '.'):
            continue
        if part == '..':
            if resolved == root:
                raise ValueError('Sysroot symlink escapes root')
            resolved = resolved.parent
            continue
        resolved /= part
        if resolved.is_symlink():
            target = resolved.readlink()
            resolved = root if target.is_absolute() else resolved.parent
            parts = list(target.parts) + parts
    raise ValueError(f'Too many sysroot path components or symlinks: {path}')


def copy_libraries(binaries, sysroot, bundle):
    pending = list(binaries)
    copied = set()
    while pending:
        binary = pending.pop()
        dynamic = subprocess.check_output(['readelf', '-d', str(binary)], text=True)
        program = subprocess.check_output(['readelf', '-l', str(binary)], text=True)
        names = re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic)
        interpreters = re.findall(r'Requesting program interpreter: (.*?)\]', program)
        for name in names + interpreters:
            if name in copied:
                continue
            candidates = ([name] if name.startswith('/') else
                          [f'/usr/lib64/{name}', f'/lib64/{name}',
                           f'/usr/lib/{name}', f'/lib/{name}'])
            for candidate in candidates:
                try:
                    source = root_file(sysroot, candidate)
                except FileNotFoundError:
                    continue
                break
            else:
                raise ValueError(f'Missing target dependency {name} for {binary}')
            relative = name.lstrip('/') if name.startswith('/') else f'usr/lib64/{name}'
            target = bundle / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o755)
            copied.add(name)
            pending.append(target)
    return sorted(copied)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arch', choices=('native', 'aarch64'), required=True)
    parser.add_argument('--sysroot', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--jobs', type=int, default=min(os.cpu_count() or 1, 8))
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    if args.arch == 'aarch64' and args.sysroot is None:
        parser.error('--sysroot is required for aarch64')
    if args.arch == 'native' and args.sysroot is not None:
        parser.error('--sysroot is only supported for aarch64')

    pins = json.loads((PIN_DIR / 'sources.json').read_text())
    output = (args.output or ROOT / 'out' / 'petitboot-1.15' / args.arch).resolve()
    if not output.is_relative_to(ROOT / 'out'):
        parser.error('--output must be a new directory below repository out/')
    if output.exists():
        parser.error(f'{output} already exists; choose a fresh output directory')
    sysroot = args.sysroot.resolve() if args.sysroot else Path('/')
    if not (sysroot / 'usr/include/stdlib.h').is_file():
        parser.error('sysroot is missing libc development headers')
    output.mkdir(parents=True)

    env = dict(os.environ)
    for name in ('CC', 'CPP', 'CXX', 'CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'LIBS',
                 'PKG_CONFIG_PATH', 'PKG_CONFIG_LIBDIR', 'PKG_CONFIG_SYSROOT_DIR',
                 'CONFIG_SITE', 'LD_LIBRARY_PATH'):
        env.pop(name, None)
    env['CONFIG_SITE'] = '/dev/null'
    env['LC_ALL'] = 'C.UTF-8'
    env['CFLAGS'] = '-std=gnu99'
    env['PETITBOOT_VERSION'] = pins['petitboot']['version'] + '-picasso1'
    env['GIT_CEILING_DIRECTORIES'] = str(output)
    host = []
    if args.arch == 'aarch64':
        compiler_libs = sysroot / 'usr/lib/gcc/aarch64-redhat-linux'
        versions = [path for path in compiler_libs.glob('*') if path.is_dir()]
        if len(versions) != 1:
            raise ValueError('sysroot must have exactly one target GCC runtime directory')
        env.update({
            'CC': f'clang --target=aarch64-linux-gnu --sysroot={sysroot} '
                  f'--gcc-install-dir={versions[0]}',
            'AR': 'aarch64-linux-gnu-ar',
            'LD': 'aarch64-linux-gnu-ld',
            'OBJCOPY': 'aarch64-linux-gnu-objcopy',
            'STRIP': 'aarch64-linux-gnu-strip',
            'CFLAGS': '-O2 -std=gnu99',
            'LDFLAGS': f'-fuse-ld=lld -L{versions[0]} '
                       f'-Wl,-rpath-link,{sysroot}/usr/lib64',
            'PKG_CONFIG_LIBDIR': f'{sysroot}/usr/lib64/pkgconfig:{sysroot}/usr/share/pkgconfig',
            'PKG_CONFIG_SYSROOT_DIR': str(sysroot),
        })
        host = ['--host=aarch64-linux-gnu']

    sources = {}
    for name, pin in pins.items():
        dest = output / name
        archive_source(ROOT / 'src' / f"{name}-{pin['version']}", pin, dest)
        sources[name] = dest
    pb = sources['petitboot']
    patches = sorted((PIN_DIR / 'patches').glob('*.patch'))
    if not patches:
        raise ValueError('Missing Petitboot patch series')
    patch_env = dict(env, GIT_CEILING_DIRECTORIES=str(output))
    for index, patch in enumerate(patches):
        run(['git', 'apply', '--check', str(patch)], pb, patch_env,
            output / f'patch-{index}-check.log')
        run(['git', 'apply', str(patch)], pb, patch_env,
            output / f'patch-{index}.log')
    run(['./bootstrap'], pb, env, output / 'petitboot-bootstrap.log')
    pb_build = output / 'petitboot-build'
    pb_build.mkdir()
    run([str(pb / 'configure'), *host, '--disable-platform-auto',
         '--disable-platform-arm64', '--disable-nls', '--without-twin-x11',
         '--with-ncurses', f'HOST_PROG_KEXEC={GUARD}', f'HOST_PROG_SHUTDOWN={GUARD}'],
        pb_build, env, output / 'petitboot-configure.log')
    run(['make', '-s', f'-j{args.jobs}'], pb_build, env, output / 'petitboot-make.log')
    if args.arch == 'native':
        run(['make', '-s', f'-j{args.jobs}', 'check'], pb_build, env,
            output / 'petitboot-check.log')

    kexec = sources['kexec-tools']
    run(['./bootstrap'], kexec, env, output / 'kexec-bootstrap.log')
    kexec_build = output / 'kexec-build'
    kexec_build.mkdir()
    run([str(kexec / 'configure'), *host, '--without-xen', '--without-zlib',
         '--without-lzma', '--without-zstd'], kexec_build, env,
        output / 'kexec-configure.log')
    run(['make', '-s', f'-j{args.jobs}'], kexec_build, env, output / 'kexec-make.log')

    bundle = output / 'rootfs'
    programs = {
        'usr/sbin/pb-discover': pb_build / 'discover/pb-discover',
        'usr/sbin/pb-event': pb_build / 'utils/pb-event',
        'usr/sbin/petitboot-nc': pb_build / 'ui/ncurses/petitboot-nc',
        'usr/libexec/picasso-petitboot/kexec.unvalidated': kexec_build / 'build/sbin/kexec',
        GUARD.lstrip('/'): PIN_DIR / 'blocked-transition',
    }
    binaries = []
    for name, source in programs.items():
        target = bundle / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o755)
        if name != GUARD.lstrip('/'):
            header = subprocess.check_output(['readelf', '-h', str(target)], text=True)
            if args.arch == 'aarch64' and 'AArch64' not in header:
                raise ValueError(f'Not an ARM64 ELF: {target}')
            binaries.append(target)
    libraries = copy_libraries(binaries, sysroot, bundle)
    for name in ('run/petitboot', 'var/log/petitboot', 'tmp', 'dev'):
        (bundle / name).mkdir(parents=True, exist_ok=True)
    (bundle / 'tmp').chmod(0o1777)
    terminfo = sysroot / 'usr/share/terminfo/l/linux'
    if not terminfo.is_file():
        raise ValueError(f'Missing Linux-console terminfo: {terminfo}')
    (bundle / 'usr/share/terminfo/l').mkdir(parents=True)
    shutil.copyfile(terminfo, bundle / 'usr/share/terminfo/l/linux')
    shutil.copyfile(pb / 'COPYING', bundle / 'COPYING.petitboot')
    shutil.copyfile(kexec / 'COPYING', bundle / 'COPYING.kexec-tools')
    receipt = {
        'arch': args.arch, 'sources': pins,
        'patches': {path.name: digest(path) for path in patches},
        'programs': {name: digest(bundle / name) for name in programs},
        'libraries': libraries,
        'native_tests': args.arch == 'native',
        'bootable_image': False,
        'hardware_validated': False,
        'transitions': 'blocked; no phone deployment or boot authorization',
    }
    (output / 'build.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(output / 'build.json')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error
