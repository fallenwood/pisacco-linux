#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build isolated 7.3.1 screen/PON and opt-in Wi-Fi modules, never install them."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from kernel_profile import select_profile


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    profile = select_profile(ROOT)
    if profile.version != '7.3.1':
        raise SystemExit('Explicit KERNEL_VERSION=7.3.1 required; existing modules are protected')
    release = (profile.output / 'kbuild/include/config/kernel.release').read_text().strip()
    if not release.startswith('7.3.1-picasso-wifi'):
        raise SystemExit('Build the matching isolated Wi-Fi kernel first')
    baseline = profile.output / 'modules/lib/modules' / release
    before = {str(p.relative_to(baseline)): digest(p) for p in baseline.rglob('*.ko')}
    if not before:
        raise SystemExit('Matching baseline module installation missing')
    output = profile.output / 'extra-modules'
    output.mkdir(mode=0o700)
    make = ['make', '-s', '-C', str(profile.source),
            'O=' + str(profile.output / 'kbuild'), 'ARCH=arm64', 'LLVM=1',
            'LOCALVERSION=', '-j' + os.environ.get('JOBS', '6')]
    artifacts = {}
    for kind in ('display', 'power'):
        stage = output / kind
        stage.mkdir()
        for path in (ROOT / 'kernel' / kind).iterdir():
            if path.name == 'Makefile' or path.suffix == '.c' and not path.name.endswith('.mod.c'):
                shutil.copyfile(path, stage / path.name)
        if kind == 'power':
            path = stage / 'picasso-pon-reason-audit.c'
            text = path.read_text()
            old = '"6.18.58-picasso-lts-wifi2"'
            if text.count(old) != 1:
                raise ValueError('PON exact-release guard changed; review the port')
            path.write_text(text.replace(old, json.dumps(release)))
        subprocess.run(make + ['M=' + str(stage), 'modules'], check=True)
        for path in stage.glob('*.ko'):
            artifacts[path.name] = path
    stage = output / 'wifi-source'
    ath = stage / 'drivers/net/wireless/ath'
    shutil.copytree(profile.source / 'drivers/net/wireless/ath', ath)
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(stage.parent))
    patches = ('ath10k-picasso-ht20-only.patch', 'ath10k-picasso-mgmt-observer.patch')
    for name in patches:
        patch = ROOT / 'kernel/diagnostics' / name
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=stage, env=env, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=stage, env=env, check=True)
    subprocess.run(make + ['M=' + str(ath / 'ath10k'), 'modules'], check=True)
    for name in ('ath10k_core', 'ath10k_snoc'):
        artifacts[name + '.ko'] = ath / 'ath10k' / (name + '.ko')
    for name, path in artifacts.items():
        vermagic = subprocess.check_output(['modinfo', '-F', 'vermagic', str(path)], text=True).strip()
        if vermagic.split()[0] != release:
            raise ValueError('Module ABI mismatch: ' + name)
    core = baseline / 'kernel/drivers/net/wireless/ath/ath10k/ath10k_core.ko'
    plain = subprocess.check_output(['modinfo', '-p', str(core)], text=True)
    custom = subprocess.check_output(['modinfo', '-p', str(artifacts['ath10k_core.ko'])], text=True)
    if 'picasso_ht20_only:' in plain or not all(
            name + ':' in custom for name in ('picasso_ht20_only', 'picasso_mgmt_status')):
        raise ValueError('Normal and conservative ath10k variants are not isolated')
    after = {str(p.relative_to(baseline)): digest(p) for p in baseline.rglob('*.ko')}
    if after != before:
        raise ValueError('Baseline module bytes changed during isolated diagnostic build')
    manifest = {
        'status': 'built_offline_not_loaded_or_hardware_tested',
        'kernel_release': release,
        'baseline_modules_unchanged': True,
        'baseline_module_sha256': before,
        'artifacts': {name: {'file': str(path.relative_to(ROOT)), 'sha256': digest(path)}
                      for name, path in sorted(artifacts.items())},
        'diagnostic_patches': {name: digest(ROOT / 'kernel/diagnostics' / name) for name in patches},
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Isolated screen/PON and conservative ath10k modules built; not installed or loaded')


if __name__ == '__main__':
    main()
