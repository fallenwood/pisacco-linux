#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
SRC=$ROOT/src/linux-6.18.58
OUT=$ROOT/out
KB=$OUT/kbuild
[[ -f $SRC/Makefile ]] || { echo 'Run tools/prepare-kernel.py first' >&2; exit 1; }
[[ -x $ROOT/downloads/busybox ]] || { echo 'Run tools/fetch-sources.py first' >&2; exit 1; }
for tool in clang ld.lld llvm-ar llvm-objcopy make flex bison bc python3; do
    command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
mkdir -p "$KB"
# gen_init_cpio makes device nodes without root or a host-architecture executable.
python3 - "$ROOT" <<'PY'
import pathlib, struct, sys
root = pathlib.Path(sys.argv[1])
bb = root / 'downloads/busybox'
hdr = bb.read_bytes()[:64]
if hdr[:5] != b'\x7fELF\x02' or struct.unpack_from('<H', hdr, 18)[0] != 183:
    sys.exit('busybox must be an AArch64 ELF64 executable')
lines = [f'dir /{d} 0755 0 0' for d in ('bin','sbin','dev','proc','sys','run','tmp','etc','usr','usr/bin','usr/sbin','newroot')]
lines += [f'file /bin/busybox {bb} 0755 0 0', f'file /init {root}/initramfs/init 0755 0 0',
          'nod /dev/console 0600 0 0 c 5 1', 'nod /dev/null 0666 0 0 c 1 3']
(root / 'out/initramfs.list').write_text('\n'.join(lines) + '\n')
PY
M=(make -C "$SRC" O="$KB" ARCH=arm64 LLVM=1 LOCALVERSION=)
"${M[@]}" defconfig >/dev/null
# Drop non-Qualcomm platforms, independently of defconfig's current platform list.
while IFS= read -r symbol; do
    [[ $symbol = ARCH_QCOM ]] || "$SRC/scripts/config" --file "$KB/.config" -d "$symbol"
done < <(grep -o '^config ARCH_[A-Z0-9_]*' "$SRC/arch/arm64/Kconfig.platforms" | cut -d' ' -f2)
EXTRA=()
if [[ ${DTS_PROFILE:-server} = wifi || ${DTS_PROFILE:-server} = wifi-rmtfs ]]; then
    EXTRA+=("$ROOT/kernel/picasso-wifi.config")
    DEFAULT_WIFI_VERSION=-picasso-lts-wifi1
    if [[ ${DTS_PROFILE:-server} = wifi-rmtfs ]]; then
        EXTRA+=("$ROOT/kernel/picasso-wifi-rmtfs.config")
        DEFAULT_WIFI_VERSION=-picasso-lts-wifi2
    fi
    # Never collide with modules of the installed, known-bootable server kernel.
    KERNEL_LOCALVERSION=${KERNEL_LOCALVERSION:-$DEFAULT_WIFI_VERSION}
    [[ $KERNEL_LOCALVERSION =~ ^-picasso-lts-wifi[0-9]+$ ]] || { echo 'Wi-Fi trial requires a distinct -picasso-lts-wifiN release' >&2; exit 1; }
fi
ARCH=arm64 "$SRC/scripts/kconfig/merge_config.sh" -m -O "$KB" "$KB/.config" \
    "$ROOT/kernel/picasso.config" "$ROOT/kernel/fedora-server.config" "${EXTRA[@]}" > "$OUT/config-merge.log"
if [[ -n ${KERNEL_LOCALVERSION:-} ]]; then
    "$SRC/scripts/config" --file "$KB/.config" --set-str LOCALVERSION "$KERNEL_LOCALVERSION"
fi
"$SRC/scripts/config" --file "$KB/.config" --set-str INITRAMFS_SOURCE "$OUT/initramfs.list"
if [[ -n ${ROOT_PARTUUID:-} ]]; then
    [[ $ROOT_PARTUUID =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]] || { echo 'Invalid ROOT_PARTUUID' >&2; exit 1; }
    CMDLINE=$(python3 - "$ROOT/kernel/picasso.config" <<'PY'
import sys
for line in open(sys.argv[1]):
    if line.startswith('CONFIG_CMDLINE='): print(line.split('=',1)[1].strip().strip('"'))
PY
)
    ROOT_FSTYPE=${ROOT_FSTYPE:-ext4}
    [[ $ROOT_FSTYPE = ext4 || $ROOT_FSTYPE = xfs ]] || { echo 'ROOT_FSTYPE must be ext4 or xfs' >&2; exit 1; }
    "$SRC/scripts/config" --file "$KB/.config" --set-str CMDLINE "$CMDLINE root=PARTUUID=$ROOT_PARTUUID rootfstype=$ROOT_FSTYPE"
fi
"${M[@]}" olddefconfig >/dev/null
for symbol in SM_GCC_7250 PINCTRL_SM7250 INTERCONNECT_QCOM_SM7250 QCOM_CLK_RPMH QCOM_SMEM \
    QCOM_PDC QCOM_GENI_SE SERIAL_QCOM_GENI SERIAL_QCOM_GENI_CONSOLE REGULATOR_QCOM_RPMH \
    SCSI_UFS_QCOM PHY_QCOM_QMP_UFS USB_DWC3_QCOM PHY_QCOM_USB_SNPS_FEMTO_V2 \
    USB_CONFIGFS_NCM USB_CONFIGFS_ACM EXT4_FS XFS_FS XFS_POSIX_ACL XFS_QUOTA SECURITY_SELINUX DEVTMPFS \
    NF_TABLES NF_TABLES_INET NFT_CT NFT_FIB_INET NFT_REJECT_INET \
    ZRAM ZRAM_BACKEND_ZSTD ZRAM_DEF_COMP_ZSTD; do
    grep -qx "CONFIG_$symbol=y" "$KB/.config" || { echo "CONFIG_$symbol was lost to dependencies" >&2; exit 1; }
done
grep -qx '# CONFIG_ZRAM_WRITEBACK is not set' "$KB/.config" || { echo 'ZRAM writeback must stay disabled' >&2; exit 1; }
if [[ ${DTS_PROFILE:-server} = wifi || ${DTS_PROFILE:-server} = wifi-rmtfs ]]; then
    WIFI_DEPS=(ATH10K_SNOC QCOM_Q6V5_PAS QCOM_PD_MAPPER QRTR QRTR_SMD RPMSG_QCOM_GLINK_SMEM)
    [[ ${DTS_PROFILE:-server} != wifi-rmtfs ]] || WIFI_DEPS+=(QCOM_RMTFS_MEM)
    for symbol in "${WIFI_DEPS[@]}"; do
        grep -qx "CONFIG_$symbol=m" "$KB/.config" || { echo "Wi-Fi dependency CONFIG_$symbol=m lost" >&2; exit 1; }
    done
fi
"${M[@]}" -j"${JOBS:-$(nproc)}" Image modules
# Explicit DT profile; PM telemetry stays opt-in, never enables charging.
bash "$ROOT/tools/build-dtb.sh" "${DTS_PROFILE:-server}"
cp "$KB/arch/arm64/boot/Image" "$OUT/Image"
# Only remove this script's generated module staging tree, never a system path.
rm -rf -- "$OUT/modules"
"${M[@]}" INSTALL_MOD_PATH="$OUT/modules" INSTALL_MOD_STRIP=1 modules_install > "$OUT/modules-install.log"
find "$OUT/modules" -type l \( -name build -o -name source \) -delete
cp "$KB/.config" "$OUT/kernel.config"
sha256sum "$OUT/Image" "$OUT/picasso.dtb" "$OUT/kernel.config" > "$OUT/SHA256SUMS"
echo 'Built Image, picasso.dtb and modules. NOT hardware tested; no boot image or flash performed.'
