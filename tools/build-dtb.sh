#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Build one explicit mainline DT variant; no phone IO or firmware loading.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
SRC=$ROOT/src/linux-6.18.58
OUT=$ROOT/out
case ${1:-server} in
    server) DTS=$ROOT/dts/sm7250-xiaomi-picasso-fedora.dts ;;
    pm-telemetry) DTS=$ROOT/dts/sm7250-xiaomi-picasso-pm-telemetry.dts ;;
    wifi) DTS=$ROOT/dts/sm7250-xiaomi-picasso-wifi.dts ;;
    wifi-rmtfs) DTS=$ROOT/dts/sm7250-xiaomi-picasso-wifi-rmtfs.dts ;;
    *) echo 'usage: tools/build-dtb.sh [server|pm-telemetry|wifi|wifi-rmtfs]' >&2; exit 1 ;;
esac
[[ -x $OUT/kbuild/scripts/dtc/dtc ]] || { echo 'Build the kernel first' >&2; exit 1; }
if [[ ${1:-server} = pm-telemetry ]]; then
    grep -Eq '^CONFIG_QCOM_SPMI_ADC5=(y|m)$' "$OUT/kbuild/.config" || {
        echo 'Matching kernel lacks the ADC5 driver' >&2; exit 1;
    }
fi
clang -E -P -nostdinc -undef -D__DTS__ -x assembler-with-cpp \
    -I "$SRC/arch/arm64/boot/dts/qcom" -I "$SRC/include" \
    "$DTS" -o "$OUT/picasso.dts.pp"
"$OUT/kbuild/scripts/dtc/dtc" -I dts -O dtb -o "$OUT/picasso.dtb" \
    "$OUT/picasso.dts.pp" 2> "$OUT/dtc-warnings.log"
printf '%s\n' "${1:-server}" > "$OUT/dtb-profile.txt"
echo "DTB built from $DTS; not hardware validated. Rerun inspect-rom.py before packing."
