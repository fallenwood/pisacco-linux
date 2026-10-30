#!/usr/bin/env bash
# Audited RAM boot and real KEY_POWER OBSERVATION ONLY; never flash/off.
# --resume-fastboot skips ALL phone reboot/preparation commands.
set -euo pipefail
[[ -t 0 && -t 1 ]] || { printf '%s\n' '请在正常主机本地交互终端运行。' >&2; exit 1; }
MODE=normal
case $# in
 0) ;;
 1) [[ $1 == --resume-fastboot ]] || { echo 'usage: test-power-input.sh [--resume-fastboot]' >&2; exit 2; }; MODE=resume ;;
 *) echo 'usage: test-power-input.sh [--resume-fastboot]' >&2; exit 2 ;;
esac
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
D=picasso/out/power-key-preparation-20261028
FB=/home/vbox/.local/opt/android/platform-tools/fastboot
[[ -x "$FB" && ! -e "$D/observer-local-result.json" && ! -e "$D/fastboot-boot-request.json" ]] || { printf '%s\n' '缺少fastboot或已有本次试验/boot请求记录；请检查既有结果，不重复启动。' >&2; exit 1; }
if [[ $MODE == normal ]]; then
 [[ ! -e "$D/observer-launch.json" ]] || { printf '%s\n' '已做过重启准备，不重复重启。如当前已是fastboot，请用 --resume-fastboot。' >&2; exit 1; }
else
 [[ -f "$D/observer-launch.json" && ! -L "$D/observer-launch.json" ]] || { printf '%s\n' '缺少原始重启准备记录，拒绝无来源resume。' >&2; exit 1; }
fi
SSH=(ssh -F /dev/null -i picasso/out/fedora-server-test/id_ed25519
 -o BatchMode=yes -o IdentitiesOnly=yes
 -o UserKnownHostsFile=picasso/out/confirmation-20261027/known_hosts
 -o StrictHostKeyChecking=yes -o ConnectTimeout=10 picasso@192.168.7.2)
python3 - "$MODE" <<'PY'
import hashlib,json,sys
from pathlib import Path
D=Path('picasso/out/power-key-preparation-20261028');r=json.loads((D/'build-result.json').read_text());p=D/'boot-power-key-trial.img'
assert hashlib.sha256(p.read_bytes()).hexdigest()==r['artifacts'][p.name]['sha256']=='002147068dd9a03b467e27cf95398b3147bf5452af411f3e6a90c443e92b2c5f'
assert r['audit']['all_existing_nodes_byte_properties_preserved'] and not r['audit']['hardware_tested']
if sys.argv[1]=='resume':
 old=json.loads((D/'observer-launch.json').read_text());assert old['observe_only'] is True and len(old['old_boot_id'])==36
PY
printf '%s\n' '本次只临时启动电源键候选并记录按键，不关机、不刷boot、不改NV。' \
 'USB fastboot节点需本地sudo权限；若需要认证，只在此本地终端输入，不在聊天中输入。'
# Authenticate in the operator terminal, not through cached Wi-Fi credentials
# or a privileged-container/NoNewPrivs workaround.
sudo -v
if [[ $MODE == normal ]]; then
 printf '%s\n' '正常重启期间按住【音量下】进入fastboot，不长按电源。失败会停止，不循环重启。'
 read -r -p '准备好按住【音量下】并保持到fastboot后，按回车；Ctrl-C取消：' answer
 "${SSH[@]}" 'sudo -n python3 -c '\''import hashlib,json,os;from pathlib import Path;assert hashlib.sha256(Path("/sys/firmware/fdt").read_bytes()).hexdigest()=="62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388";assert max(int(p.read_text()) for p in Path("/sys/class/thermal").glob("thermal_zone*/temp"))<40000;assert Path("/etc/systemd/logind.conf.d/90-picasso-power-trial.conf").read_text().splitlines()==["[Login]","HandlePowerKey=ignore","HandlePowerKeyLongPress=ignore"];p=Path("/var/lib/picasso-power/observer-launch.json");fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);data=json.dumps({"old_boot_id":Path("/proc/sys/kernel/random/boot_id").read_text().strip(),"observe_only":True}).encode();os.write(fd,data);os.fsync(fd);os.close(fd);os.sync();print(data.decode())'\''' > "$D/observer-launch.json"
 "${SSH[@]}" 'sudo -n systemctl reboot' || true
else
 printf '%s\n' '从现有fastboot继续：不再次重启、不重新准备手机。'
fi
python3 - "$FB" "$MODE" <<'PY'
import json,subprocess,sys,time
from pathlib import Path
fb,mode=sys.argv[1:];deadline=time.monotonic()+(45 if mode=='normal' else 8)
while time.monotonic()<deadline:
 try:
  p=subprocess.run(['sudo','-n',fb,'-s','79b5ecfc','getvar','product'],capture_output=True,text=True,timeout=3)
  if p.returncode==0 and 'product: picasso' in p.stdout+p.stderr:
   found=[]
   for n in Path('/sys/bus/usb/devices').iterdir():
    if not (n/'idVendor').exists() or not (n/'idProduct').exists():continue
    if (n/'idVendor').read_text().strip()=='18d1' and (n/'idProduct').read_text().strip()=='d00d' and (n/'serial').exists() and (n/'serial').read_text().strip()=='79b5ecfc':found.append(n.name)
   assert len(found)==1,'Expected one original serial/VID/PID target'
   D=Path('picasso/out/power-key-preparation-20261028');(D/'fastboot-product-check.json').write_text(json.dumps({'product':'picasso','serial':'79b5ecfc','vid':'18d1','pid':'d00d','usb_port':found[0],'mode':mode,'read_only_product_stdout':p.stdout,'read_only_product_stderr':p.stderr},indent=2)+'\n')
   break
  if 'sudo:' in p.stderr:raise SystemExit(p.stderr)
 except subprocess.TimeoutExpired:pass
 time.sleep(.5)
else:raise SystemExit('未确认目标fastboot，已停止；不再次重启/刷写。检查USB权限与sudo认证。')
PY
read -r -p '已确认原picasso fastboot。请松开所有按键，按回车仅临时启动候选；Ctrl-C取消：' answer
python3 - "$MODE" <<'PY'
import json,os,sys
from pathlib import Path
p=Path('picasso/out/power-key-preparation-20261028/fastboot-boot-request.json');fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
try:os.write(fd,json.dumps({'method':'fastboot boot only','mode':sys.argv[1],'serial':'79b5ecfc','reboot_skipped':sys.argv[1]=='resume','image_sha256':'002147068dd9a03b467e27cf95398b3147bf5452af411f3e6a90c443e92b2c5f','completion':'pending actual boot/SSH evidence'}).encode());os.fsync(fd)
finally:os.close(fd)
PY
sudo -n "$FB" -s 79b5ecfc boot "$D/boot-power-key-trial.img"
printf '%s\n' '等待手机USB重新出现后，恢复仅USB静态地址……'
python3 - <<'PY'
import json,subprocess,time
until=time.monotonic()+90
while time.monotonic()<until:
 if any(x.get('address')=='02:50:49:00:00:01' for x in json.loads(subprocess.check_output(['ip','-j','link','show'],text=True))):break
 time.sleep(1)
else:raise SystemExit('手机USB未返回；停止，不重复boot或flash。')
time.sleep(8)
PY
# The USB restore can finish before sshd; wait boundedly without another boot.
if ! ./picasso/tools/restore-screen-usb.sh; then
 printf '%s\n' 'USB恢复或首次SSH检查未完成；只等待同一手机SSH，不重复启动候选。'
fi
READY=no
for attempt in {1..15}; do
 if "${SSH[@]}" true; then READY=yes; break; fi
 sleep 2
done
[[ $READY == yes ]] || { printf '%s\n' 'SSH未返回，保留boot请求记录，请检查；不要重复启动。' >&2; exit 1; }
printf '%s\n' '即将启动60秒【只观察、不关机】记录。等待ready提示后，电源键只按住约2秒后松开，不超过3秒。'
OBSERVE=0
"${SSH[@]}" 'sudo -n python3 -I /opt/picasso-power/power-key-service.py' || OBSERVE=$?
# Preserve observer evidence even if it failed; do not treat exit0 as hardware success.
"${SSH[@]}" 'sudo -n python3 -c '\''from pathlib import Path;p=Path("/run/picasso-power-observe/result.json");print(p.read_text() if p.exists() else "{\"status\":\"observer_result_missing\"}")'\''' > "$D/observer-local-result.json"
printf '%s\n' '观察结果已保存。不要重跑、不长按超过3秒。回复“电源键试验完成”（如有错误请附终端最后几行）。'
exit "$OBSERVE"
