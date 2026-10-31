#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Select isolated kernel inputs and outputs without changing the LTS defaults."""
import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path


@dataclass(frozen=True)
class KernelProfile:
    version: str
    source: Path
    output: Path
    manifest: Path
    series: Path
    config: Path | None

    def sources(self):
        value = json.loads(self.manifest.read_text())
        if value['kernel_version'] != self.version:
            raise ValueError('Kernel profile and source manifest versions differ')
        return value


def select_profile(root, version=None):
    root = Path(root).resolve()
    version = os.environ.get('KERNEL_VERSION', '6.18.58') if version is None else version
    if version == '6.18.58':
        return KernelProfile(version, root / 'src/linux-6.18.58', root / 'out',
                             root / 'sources.json', root / 'kernel/patches/series', None)
    if version == '7.3.1':
        profile = KernelProfile(version, root / 'src/linux-7.3.1', root / 'out/linux-7.3.1',
                                root / 'sources-7.3.1.json', root / 'kernel/patches/7.3/series',
                                root / 'kernel/picasso-7.3.config')
        for path in (profile.source, profile.output):
            if path.resolve() != path:
                raise ValueError('Parallel kernel paths must not redirect through symlinks')
        for name in ('kbuild', 'modules', 'rom-audit', 'Image', 'kernel.config',
                     'picasso.dtb', 'boot-picasso.img', 'initramfs.list'):
            if not (profile.output / name).resolve().is_relative_to(profile.output):
                raise ValueError('Parallel kernel output redirects outside its profile')
        return profile
    raise ValueError(f'Unsupported KERNEL_VERSION: {version!r}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('field', choices=('version', 'source', 'output', 'manifest', 'series', 'config'))
    args = parser.parse_args()
    try:
        profile = select_profile(Path(__file__).resolve().parents[1])
        profile.sources()
    except (ValueError, KeyError) as exc:
        parser.error(str(exc))
    print(getattr(profile, args.field) or '')


if __name__ == '__main__':
    main()
