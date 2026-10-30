#!/usr/bin/env bash
# Restore only the independently identified Picasso USB link after enumeration.
# Run by the operator in a normal local terminal, not the NNP agent sandbox.
set -euo pipefail
[[ -t 0 && -t 1 ]] || { printf '%s\n' '请在主机本地交互终端执行；不要在聊天中输入密码。' >&2; exit 1; }
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
DEV=$(python3 - <<'PY'
import json,subprocess
from pathlib import Path
links=json.loads(subprocess.check_output(['ip','-j','address','show'],text=True))
found=[p for p in links if p.get('address')=='02:50:49:00:00:01']
assert len(found)==1,'Expected one Picasso USB Ethernet MAC'
name=found[0]['ifname'];p=Path('/sys/class/net')/name/'device'
assert (p/'driver').resolve().name=='cdc_ncm','Wrong USB Ethernet driver'
parents=(p.resolve(),*p.resolve().parents)
usb=next(x for x in parents if (x/'idVendor').exists() and (x/'idProduct').exists())
assert (usb/'idVendor').read_text().strip()=='1d6b' and (usb/'idProduct').read_text().strip()=='0104','Wrong USB gadget'
print(name)
PY
)
printf '仅恢复已核对的手机USB接口：%s\n' "$DEV"
printf '%s\n' '不修改Wi-Fi、默认路由、DNS或NAT。sudo若需认证，请只在此本地终端输入。'
sudo nmcli device set "$DEV" managed no
sudo ip link set "$DEV" up
sudo ip address replace 192.168.7.1/24 dev "$DEV"
ssh -F /dev/null -i picasso/out/fedora-server-test/id_ed25519 \
 -o BatchMode=yes -o IdentitiesOnly=yes \
 -o UserKnownHostsFile=picasso/out/confirmation-20261027/known_hosts \
 -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
 picasso@192.168.7.2 \
 'sudo -n python3 -c '\''import json,subprocess;from pathlib import Path;r=Path("/run/picasso-screen/session.json");print(json.dumps({"boot_id":Path("/proc/sys/kernel/random/boot_id").read_text().strip(),"screen_enabled":subprocess.check_output(["systemctl","is-enabled","picasso-screen.service"],text=True).strip(),"screen_state":subprocess.check_output(["systemctl","show","picasso-screen.service","-p","ActiveState","-p","SubState","-p","Result"],text=True),"session":json.loads(r.read_text()) if r.exists() else None},indent=2))'\'''
printf '%s\n' 'USB已恢复；请回复“已恢复”，以便继续核对重启后状态与完整性。'
