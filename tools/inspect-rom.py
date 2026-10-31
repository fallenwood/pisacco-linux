#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Inspect the pinned local ROM, extract only boot data and apply its DTBO offline.

Never executes update-binary/updater-script, connects to adb, mounts images,
changes a bootloader, or writes phone partitions. This is not a live DT dump.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile

from bootimg import parse_stock
from fdt import dtbo_entries, fixed_regions, nodes, region_covered, split_fdts
from kernel_profile import select_profile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_metadata(text, pin, codename):
    fields = dict(line.split('=', 1) for line in text.splitlines() if '=' in line)
    expected = dict(pin['metadata'], **{'pre-device': codename})
    for key, value in expected.items():
        if fields.get(key) != str(value):
            raise ValueError(f'ROM metadata mismatch: {key}')
    return fields


def extract_member(archive, name, target, pin):
    infos = [i for i in archive.infolist() if i.filename == name]
    if len(infos) != 1:
        raise ValueError(f'missing/ambiguous member: {name}')
    info = infos[0]
    if info.file_size != pin['size'] or f'{info.CRC:08x}' != pin['zip_crc32']:
        raise ValueError(f'member metadata mismatch: {name}')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.stat().st_size != pin['size'] or sha256(target) != pin['sha256']:
            raise ValueError(f'existing extracted file differs: {target}')
        return
    temporary = None
    try:
        with archive.open(info) as source, tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
            temporary = Path(output.name)
            while chunk := source.read(1 << 20):
                output.write(chunk)
        if sha256(temporary) != pin['sha256']:
            raise ValueError(f'extracted member SHA256 mismatch: {name}')
        temporary.chmod(0o644)
        temporary.replace(target)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def describe(blob):
    root = nodes(blob)['/']
    result = {'model': root.get('model', b'').rstrip(b'\0').decode(errors='replace'),
              'compatible': [s.decode(errors='replace') for s in root.get('compatible', b'').split(b'\0') if s]}
    for key in ('qcom,msm-id', 'qcom,board-id'):
        data = root.get(key, b'')
        if len(data) % 4:
            raise ValueError('invalid Qualcomm ID property')
        result[key] = [hex(v[0]) for v in struct.iter_unpack('>I', data)]
    return result


def inspect(archive_path):
    profile = select_profile(ROOT)
    device = json.loads((ROOT/'device.json').read_text())
    pin, baseline = device['rom_package'], device['boot_baseline']
    before = archive_path.stat()
    if before.st_size != pin['size'] or sha256(archive_path) != pin['sha256']:
        raise ValueError('ROM archive does not match the device.json pin')
    with zipfile.ZipFile(archive_path) as archive:
        metadata = validate_metadata(archive.read('META-INF/com/android/metadata').decode(), pin, device['codename'])
        for name, member in pin['members'].items():
            extract_member(archive, name, ROOT/member['file'], member)
    after = archive_path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise ValueError('ROM archive changed while inspecting it')
    boot_path, dtbo_path = ROOT/baseline['boot_file'], ROOT/baseline['dtbo_file']
    boot, dtbo = boot_path.read_bytes(), dtbo_path.read_bytes()
    info = parse_stock(boot)
    bases, overlays = split_fdts(info['dtb']), dtbo_entries(dtbo)
    base_index, overlay_index = baseline['dtb_index'], baseline['dtbo_index']
    if not 0 <= base_index < len(bases) or not 0 <= overlay_index < len(overlays):
        raise ValueError('ADB-reported DTB/DTBO index not present in ROM')
    out = profile.output/'rom-audit'
    out.mkdir(parents=True, exist_ok=True)
    base_path, overlay_path = out/f'base-{base_index:02d}.dtb', out/f'overlay-{overlay_index:02d}.dtbo'
    merged_path = out/f'merged-{base_index:02d}-{overlay_index:02d}.dtb'
    base_path.write_bytes(bases[base_index])
    overlay_path.write_bytes(overlays[overlay_index]['data'])
    tools = profile.output/'kbuild/scripts/dtc'
    for program in ('fdtoverlay', 'dtc'):
        if not (tools/program).is_file():
            raise ValueError('build the LTS kernel first; its dtc/fdtoverlay is needed')
    subprocess.run([str(tools/'fdtoverlay'), '-i', str(base_path), '-o', str(merged_path), str(overlay_path)], check=True)
    for path in (base_path, overlay_path, merged_path):
        with path.with_suffix('.dtc.log').open('w') as log:
            subprocess.run([str(tools/'dtc'), '-I', 'dtb', '-O', 'dts', '-o', str(path.with_suffix('.dts')), str(path)], stderr=log, check=True)
    runtime_path = profile.output/'picasso.dtb'
    merged = nodes(merged_path.read_bytes())
    required = fixed_regions(merged)
    available = fixed_regions(nodes(runtime_path.read_bytes()))
    missing = [region for region in required if not region_covered(region, available)]
    ram_regs = [props.get('reg', b'') for props in merged.values() if props.get('device_type') == b'memory\0']
    report = {
        'scope': 'ROM-package offline overlay and fixed-memory audit; not a dump of installed partitions or live DT',
        'archive': {'file': str(archive_path), 'size': pin['size'], 'sha256': pin['sha256']},
        'metadata': metadata,
        'boot': {'header_version': 2, 'page_size': info['page_size'], 'dtb_count': len(bases),
                 'dtb_field_offset': info['dtb_offset'], 'dtb_field_size': len(info['dtb'])},
        'base_dtbs': [dict(index=i, **describe(b)) for i, b in enumerate(bases)],
        'dtbo_entry_count': len(overlays),
        'selected_indices': {'dtb': base_index, 'dtbo': overlay_index, 'source': 'ADB ro.boot.* properties'},
        'selected_overlay': describe(overlays[overlay_index]['data']),
        'offline_overlay_applied': True,
        'fixed_region_count': len(required),
        'uncovered_fixed_regions': missing,
        'merged_fixed_regions': required,
        'runtime_fixed_regions': available,
        'memory_reg_is_placeholder': bool(ram_regs) and all(raw and not any(raw) for raw in ram_regs),
        'live_memory_verified': False,
        'installed_partition_hashes_verified': False,
        'bootloader_lock_state_verified': False,
        'inputs_sha256': {str(p.relative_to(ROOT)): sha256(p) for p in (boot_path, dtbo_path, base_path, overlay_path, merged_path, runtime_path)},
    }
    (out/'compatibility.json').write_text(json.dumps(report, indent=2) + '\n')
    if missing:
        raise ValueError('runtime DT leaves ROM fixed/no-map regions uncovered; see compatibility.json')
    print(f'ROM metadata and member hashes OK; {len(bases)} DTBs, {len(overlays)} DTBOs')
    print(f'DTB {base_index} + DTBO {overlay_index}: libfdt offline apply OK')
    print(f'All {len(required)} fixed reserved regions covered; live RAM/bootloader still NOT verified')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', nargs='?', type=Path)
    args = parser.parse_args()
    pin = json.loads((ROOT/'device.json').read_text())['rom_package']
    inspect(args.archive or (ROOT/pin['file']).resolve())


if __name__ == '__main__':
    main()
