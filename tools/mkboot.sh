#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
STOCK=${1:?usage: tools/mkboot.sh /path/to/your-picasso-stock-boot.img}
OUT=$ROOT/out
for file in "$STOCK" "$OUT/Image" "$OUT/picasso.dtb" "$OUT/kernel.config"; do
    [[ -f $file ]] || { echo "Missing input: $file" >&2; exit 1; }
done
# When a current-ROM baseline is configured, refuse an old/mismatched boot or
# a stale offline DTBO/memory audit BEFORE touching generated image outputs.
python3 - "$ROOT" "$STOCK" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
profile = root/'out/dtb-profile.txt'
if profile.exists() and profile.read_text().strip() in ('wifi','wifi-rmtfs'):
    audit_path = root/'out/wifi-audit.json'
    if not audit_path.exists():
        raise SystemExit('Wi-Fi audit missing; run tools/audit-wifi.py before packing')
    radio = json.loads(audit_path.read_text())
    if not (radio.get('status') == 'passed_offline_only' and
            radio.get('mpss_auto_boot') is False and
            radio.get('modem_mdt_within_reserved_memory') is True):
        raise SystemExit('Wi-Fi offline audit incomplete; refusing trial image')
    if profile.read_text().strip() == 'wifi-rmtfs' and radio.get('rmtfs',{}).get('checked') is not True:
        raise SystemExit('RMTFS memory audit missing; rerun audit-wifi.py --require-rmtfs')
    for name,key in (('Image','image_sha256'),('picasso.dtb','candidate_dtb_sha256'),('kernel.config','kernel_config_sha256')):
        if digest(root/'out'/name) != radio.get(key):
            raise SystemExit('Stale Wi-Fi audit input: ' + name)
if (root/'device.json').exists():
    device = json.loads((root/'device.json').read_text())
    baseline = device.get('boot_baseline')
    if baseline:
        if digest(pathlib.Path(sys.argv[2])) != baseline['boot_sha256']:
            raise SystemExit('Refusing boot input: it is not the configured current-ROM baseline')
        audit = json.loads((root/baseline['audit_file']).read_text())
        if audit.get('offline_overlay_applied') is not True or audit.get('uncovered_fixed_regions') != []:
            raise SystemExit('ROM overlay/fixed-memory audit has not passed; run tools/inspect-rom.py')
        if audit['archive']['sha256'] != device['rom_package']['sha256']:
            raise SystemExit('ROM audit belongs to a different archive')
        if any(audit['selected_indices'][key] != baseline[key + '_index'] for key in ('dtb', 'dtbo')):
            raise SystemExit('ROM audit indices differ from the configured baseline')
        for relative in (baseline['boot_file'], baseline['dtbo_file'], 'out/picasso.dtb'):
            if digest(root/relative) != audit['inputs_sha256'][relative]:
                raise SystemExit('Stale ROM audit input: ' + relative + '; rerun tools/inspect-rom.py')
        if digest(root/baseline['dtbo_file']) != baseline['dtbo_sha256']:
            raise SystemExit('Configured DTBO hash mismatch')
PY
# External Android ramdisks are intentionally discarded: /init must be built in.
grep -q '^CONFIG_INITRAMFS_SOURCE=".' "$OUT/kernel.config"
grep -qx '# CONFIG_EFI is not set' "$OUT/kernel.config"
clang --target=aarch64-linux-gnu -c -x assembler-with-cpp \
    "-DIMAGE_PATH=\"$OUT/Image\"" "-DDTB_PATH=\"$OUT/picasso.dtb\"" \
    "$ROOT/shim/copydown.S" -o "$OUT/shim.o"
ld.lld --image-base=0 -Ttext=0 --entry=_start "$OUT/shim.o" -o "$OUT/shim.elf"
llvm-objcopy -O binary "$OUT/shim.elf" "$OUT/shim.bin"
llvm-nm -n "$OUT/shim.elf" > "$OUT/shim.symbols"
python3 - "$OUT" <<'PY'
from pathlib import Path
import struct, sys
out = Path(sys.argv[1])
symbols = {}
for line in (out / 'shim.symbols').read_text().splitlines():
    fields = line.split()
    if len(fields) == 3: symbols[fields[2]] = int(fields[0], 16)
shim = (out / 'shim.bin').read_bytes()
image = (out / 'Image').read_bytes()
dtb = (out / 'picasso.dtb').read_bytes()
checks = {
    'arm64_header': shim[56:60] == b'ARMd',
    'payload_size': struct.unpack_from('<Q', shim, 16)[0] == len(shim),
    'image_source_alignment': symbols['linux_image'] == 0x200000,
    'trampoline_outside_destination': symbols['copy_entry'] >= len(image),
    'image_matches': shim[symbols['linux_image']:symbols['linux_end']] == image,
    'dtb_matches': shim[symbols['runtime_dtb']:symbols['runtime_dtb_end']] == dtb,
    'dtb_alignment': symbols['runtime_dtb'] % 8 == 0,
}
for key, ok in checks.items():
    print(f'{key}: {ok}')
if not all(checks.values()): raise SystemExit('Shim layout validation failed')
PY
python3 "$ROOT/tools/bootimg.py" --stock "$STOCK" --kernel "$OUT/shim.bin" --output "$OUT/boot-picasso.img"
python3 - "$ROOT" "$STOCK" <<'PY'
import hashlib, json, pathlib, struct, sys
root = pathlib.Path(sys.argv[1]); out = root / 'out'
sys.path.insert(0, str(root/'tools'))
from bootimg import parse_stock
stock_path = pathlib.Path(sys.argv[2])
stock = stock_path.read_bytes()
info = parse_stock(stock)
device = json.loads((root/'device.json').read_text()) if (root/'device.json').exists() else None
files = [stock_path, out/'Image', out/'picasso.dtb', out/'kernel.config', out/'shim.bin', out/'boot-picasso.img']
baseline = device.get('boot_baseline') if device else None
if baseline:
    files += [root/baseline['dtbo_file'], root/baseline['audit_file']]
manifest = {'status': 'experimental; not hardware tested', 'sources': json.loads((root/'sources.json').read_text()),
            'device': device,
            'stock_header': {'version': 2, 'page_size': info['page_size'], 'dtb_count': info['dtb_count'],
                             'dtb_offset': info['dtb_offset'], 'dtb_size': len(info['dtb']),
                             'kernel_addr': struct.unpack_from('<I', stock, 12)[0],
                             'ramdisk_addr': struct.unpack_from('<I', stock, 20)[0],
                             'dtb_addr': struct.unpack_from('<Q', stock, 1652)[0]},
            'inputs_and_outputs': {str(p): {'size': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
if device:
    # A matching download pin does NOT prove compatibility with installed firmware.
    expected = baseline['boot_sha256'] if baseline else device['stock_boot']['sha256']
    manifest['stock_matches_device_pin'] = hashlib.sha256(stock).hexdigest() == expected
    if baseline:
        manifest['boot_baseline'] = baseline
        manifest['offline_overlay_audit'] = str(root/baseline['audit_file'])
    manifest['boot_test_status'] = device.get('current_os', {}).get('boot_test_status',
        device.get('current_rom', {}).get('boot_test_status', 'unverified'))
    # A previous phone boot validates only that exact image, never a rebuild
    # with different Image/DTB/initramfs/shim bytes. This script stays offline.
    tested = device.get('hardware_test', {})
    image_hash = hashlib.sha256((out/'boot-picasso.img').read_bytes()).hexdigest()
    booted_statuses = {'passed_rescue_ram_boot', 'passed_fedora_ram_boot_with_known_service_failures',
                      'passed_fedora_persistent_xfs_boot_with_known_limitations'}
    manifest['hardware_test_matches_image'] = (
        tested.get('status') in booted_statuses and
        tested.get('status') == manifest['boot_test_status'] and
        tested.get('image_sha256') == image_hash and
        tested.get('image_size') == (out/'boot-picasso.img').stat().st_size)
    if manifest['boot_test_status'] in booted_statuses:
        if manifest['hardware_test_matches_image']:
            if manifest['boot_test_status'] == 'passed_rescue_ram_boot':
                manifest['status'] = 'EXPERIMENTAL: exact image rescue RAM-boot tested; Fedora/stability/peripheral validation incomplete'
            elif manifest['boot_test_status'] == 'passed_fedora_persistent_xfs_boot_with_known_limitations':
                manifest['status'] = 'EXPERIMENTAL: exact image Fedora Server XFS disk-root tested, flashed boot and two normal reboots verified; Android super removed, stability/power/peripheral validation incomplete'
            else:
                manifest['status'] = 'EXPERIMENTAL: exact image Fedora Server RAM-boot tested; known service failures, persistence/stability/peripheral validation incomplete'
        else:
            manifest['boot_test_status'] = 'unverified_image_differs_from_tested_candidate'
    if manifest['boot_test_status'].startswith('blocked_'):
        manifest['status'] = 'OFFLINE ONLY: remaining device checks/boot approval are required; see boot_test_status'
        print('WARNING: boot testing blocked: ' + manifest['boot_test_status'])
(out/'boot-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY
(cd "$OUT" && sha256sum boot-picasso.img > boot-picasso.sha256)
echo 'Experimental boot-picasso.img packed. No flash/erase/repartition commands have been run.'
