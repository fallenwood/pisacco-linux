#!/usr/bin/env bash
# Real, user-confirmed orderly poweroff/on trial; no flash/reboot/reset/suspend.
set -euo pipefail
[[ -t 0 && -t 1 && $# == 0 ]] || { printf '%s\n' '请在正常主机本地交互终端运行，无需参数。' >&2; exit 1; }
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
D=picasso/out/power-shutdown-trial-20261028
mkdir -p "$D"
[[ ! -e "$D/operator-launch.json" && ! -L "$D/operator-launch.json" ]] || { printf '%s\n' '已有本次关机请求记录，不重复试验；先检查结果。' >&2; exit 1; }
SSH=(ssh -F /dev/null -i picasso/out/fedora-server-test/id_ed25519
 -o BatchMode=yes -o IdentitiesOnly=yes
 -o UserKnownHostsFile=picasso/out/confirmation-20261027/known_hosts
 -o StrictHostKeyChecking=yes -o ConnectTimeout=8 picasso@192.168.7.2)
cancel_trial() {
 trap - INT HUP TERM
 printf '%s\n' '取消：正在请求终止已核对的远端等待进程；暂勿再按电源。已提交给PID1的关机请求不能靠取消撤销。' >&2
 timeout 10 "${SSH[@]}" 'sudo -n python3 -I /opt/picasso-power/power-shutdown-cancel.py' || true
 exit 130
}
trap cancel_trial INT HUP TERM
printf '%s\n' '注意：这次会真正请求系统正常关机，不是息屏演示，SSH/USB应断开。' \
 '只在ready之后，电源键按住约2秒后松开，不超过3秒。不要拔USB或长按强制复位。' \
 '关机后先不要按键：脚本将静候USB无自动返回20秒，再提示你开机。' \
 '若设备自行重启，会停止并保存异常，不把它当作关机通过。' \
 '本次仍为临时RAM试验：后续开机返回原默认#10，尚未把电源键DTB写入boot。'
read -r -p '准备好做真实关机试验时输入 POWER OFF；其他输入取消：' answer
[[ $answer == 'POWER OFF' ]] || { echo '已取消，没有启动关机试验。'; exit 0; }
"${SSH[@]}" 'sudo -n python3 -c '\''import hashlib,json;from pathlib import Path;p=Path("/var/lib/picasso-power/observations-20261028/acceptance.json");a=json.loads(p.read_text());boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip();assert a["boot_id"]==boot and not a["armed"] and not a["shutdown_requested"];assert hashlib.sha256(Path("/sys/firmware/fdt").read_bytes()).hexdigest()=="ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c";assert not Path("/run/picasso-power-armed/observer-consumed").exists();print(json.dumps({"status":"operator_explicitly_confirmed_real_shutdown_trial","old_boot_id":boot,"observed_acceptance":a,"not_physical_shutdown_proof":True},indent=2))'\''' > "$D/operator-launch.json"
RC=0
"${SSH[@]}" 'sudo -n python3 -I /opt/picasso-power/power-shutdown-current.py --confirmed-local-shutdown-test' | tee "$D/armed-transcript.log" || RC=$?
printf '关机请求连接返回码=%s；这本身不代表关机成功。\n' "$RC"
python3 - "$RC" <<'PY'
import json,sys,time
from pathlib import Path
D=Path('picasso/out/power-shutdown-trial-20261028')
def present():
 result=[]
 for n in Path('/sys/bus/usb/devices').iterdir():
  try:
   vid=(n/'idVendor').read_text().strip();pid=(n/'idProduct').read_text().strip()
   if (vid,pid)==('1d6b','0104') and (n/'serial').read_text().strip()=='picasso-bringup':result.append('linux_gadget')
   if (vid,pid)==('18d1','d00d') and (n/'serial').read_text().strip()=='79b5ecfc':result.append('fastboot')
  except FileNotFoundError:pass
 return result
record={'ssh_exit_code':int(sys.argv[1]),'usb_disconnect_seen':False,'usb_absent_20s_without_key_press':False,'automatic_return_without_power_press':False,'physical_complete_power_removal_proven':False}
until=time.monotonic()+60
while time.monotonic()<until:
 if not present():record['usb_disconnect_seen']=True;break
 time.sleep(.5)
if not record['usb_disconnect_seen']:
 (D/'usb-after-request.json').write_text(json.dumps(record,indent=2)+'\n');raise SystemExit('USB未消失，不能确认关机。停止；不要重复请求或长按复位，请报告日志。')
print('USB已消失。现在静候20秒，请不要按任何键；稍后会提示手动开机。',flush=True)
until=time.monotonic()+20
while time.monotonic()<until:
 found=present()
 if found:
  record.update(automatic_return_without_power_press=True,returned_mode=found);(D/'usb-after-request.json').write_text(json.dumps(record,indent=2)+'\n');raise SystemExit('未按键USB却自行返回：可能重启/自动开机，不算正常关机通过。停止并报告，不重复试验。')
 time.sleep(.5)
record['usb_absent_20s_without_key_press']=True;(D/'usb-after-request.json').write_text(json.dumps(record,indent=2)+'\n')
PY
read -r -p 'USB已断开并静候20秒。若你也确认手机未自行重启、已关机，输入 OFF；否则其他输入停止：' off
[[ $off == OFF ]] || { echo '未确认关机，停止；不执行其他电源操作。'; exit 1; }
python3 - <<'PY'
import json
from pathlib import Path
Path('picasso/out/power-shutdown-trial-20261028/user-off-confirmed.json').write_text(json.dumps({'user_confirmed_device_off_no_spontaneous_restart':True,'user_confirmation':'OFF','usb_observation_separate_from_electrical_off_proof':True},indent=2)+'\n')
PY
printf '%s\n' '现在请按住电源约2秒后松开，不超过3秒，观察是否开机。不要按音量下。'
read -r -p '按键后松开，再按回车等待系统USB；不要反复按电源，异常则Ctrl-C停止并报告：' answer
python3 - <<'PY'
import json,time
from pathlib import Path
until=time.monotonic()+120
while time.monotonic()<until:
 for n in Path('/sys/bus/usb/devices').iterdir():
  try:
   if (n/'idVendor').read_text().strip()=='1d6b' and (n/'idProduct').read_text().strip()=='0104' and (n/'serial').read_text().strip()=='picasso-bringup':raise SystemExit(0)
  except FileNotFoundError:pass
 time.sleep(1)
raise SystemExit('正常Linux USB未返回，停止，不重复boot/flash/重启。')
PY
printf '%s\n' '下一段USB恢复是子步骤，请等脚本最终结果，不在“USB已恢复”提示处提前结束。'
if ! ./picasso/tools/restore-screen-usb.sh; then echo '仅等待同一设备SSH，不再次重启。'; fi
READY=no
for attempt in {1..15}; do if "${SSH[@]}" true; then READY=yes; break; fi; sleep 2; done
[[ $READY == yes ]] || { echo 'SSH未返回，停止并报告，不重复关机。' >&2; exit 1; }
"${SSH[@]}" 'sudo -n python3 -c '\''import hashlib,json,subprocess;from pathlib import Path;boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip();base=Path("/var/lib/picasso-power/shutdown-trial-20261028");records={p.name:json.loads(p.read_text()) for p in base.glob("*.json")};r=Path("/run/picasso-screen/session.json");print(json.dumps({"new_boot_id":boot,"fdt_sha256":hashlib.sha256(Path("/sys/firmware/fdt").read_bytes()).hexdigest(),"durable_shutdown_records":records,"screen_unit_state":subprocess.check_output(["systemctl","show","picasso-screen.service","-p","ActiveState","-p","SubState","-p","Result"],text=True),"screen_session":json.loads(r.read_text()) if r.exists() else None},indent=2))'\''' > "$D/after-manual-power-on.json"
python3 - <<'PY'
import json
from pathlib import Path
D=Path('picasso/out/power-shutdown-trial-20261028');before=json.loads((D/'operator-launch.json').read_text());after=json.loads((D/'after-manual-power-on.json').read_text());assert after['new_boot_id']!=before['old_boot_id'],'Boot ID unchanged'
assert after['fdt_sha256']=='62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388','Default boot DTB unexpected; inspect without flashing'
print('新的正常启动已返回原默认#10。请回复“关机开机试验完成”，我会核对持久请求、USB与人工观察，不自动刷写boot。')
PY
