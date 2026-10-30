#!/usr/bin/env bash
# Continue ONLY in the already-running candidate: no reboot/boot/flash/off.
set -euo pipefail
[[ -t 0 && -t 1 && $# == 0 ]] || { printf '%s\n' '请在正常主机本地交互终端运行，无需参数。' >&2; exit 1; }
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
D=picasso/out/power-key-cooldown-20261028
mkdir -p "$D"
STAMP=$(date -u +%Y%m%dT%H%M%S)-$$
SSH=(ssh -F /dev/null -i picasso/out/fedora-server-test/id_ed25519
 -o BatchMode=yes -o IdentitiesOnly=yes
 -o UserKnownHostsFile=picasso/out/confirmation-20261027/known_hosts
 -o StrictHostKeyChecking=yes -o ConnectTimeout=10 picasso@192.168.7.2)
printf '%s\n' '只在当前候选启动中继续：不重启、不fastboot、不刷写、不关机。' \
 '先最多等待120秒，所有传感器连续低于40°C才进入观察。达到45°C会拒绝。' \
 '等待观察器提示 ready 后，电源键按住约2秒后松开，不超过3秒。'
RC=0
"${SSH[@]}" 'sudo -n python3 -I /opt/picasso-power/power-observe-current.py' || RC=$?
# Keep every attempt/refusal separate, never erase the initial failed result.
"${SSH[@]}" 'sudo -n python3 -c '\''import json;from pathlib import Path;r=Path("/run/picasso-power-observe");print(json.dumps({"boot_id":Path("/proc/sys/kernel/random/boot_id").read_text().strip(),"observer_consumed":(r/"observer-consumed").exists(),"records":{n:json.loads((r/n).read_text()) for n in ("result.json","startup-last.json","cooldown-last.json") if (r/n).exists()}},indent=2))'\''' > "$D/observer-current-$STAMP.json"
if [[ $RC == 0 ]]; then
 printf '%s\n' '按键观察记录已另存，本轮未关机。请回复“电源键试验完成”，再核对实际事件。'
else
 printf '%s\n' '本轮未通过，只保存拒绝/错误记录，不算观察完成。请附终端最后几行，不要重新boot或删除marker。'
fi
exit "$RC"
