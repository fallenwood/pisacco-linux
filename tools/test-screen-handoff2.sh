#!/usr/bin/env bash
set -euo pipefail
[[ -t 0 && -t 1 ]] || { printf '%s\n' '请在本地交互终端运行，无需密码。' >&2; exit 1; }
[[ $# == 0 ]] || exit 1
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT"
D=picasso/out/display-visual2-20261028
[[ ! -e "$D/visual-local-run.log" && ! -L "$D/visual-local-run.log" ]] || { printf '%s\n' '已有试验日志，请检查既有结果，不重复启动。' >&2; exit 1; }
printf '%s\n' '这是修补解空白后重绘的visual2新试验（约一分钟），不是重跑visual1。' \
 '请保持USB连接，看着手机；只在提示息屏后短按一次【音量上】。' \
 '本轮不测试电源/音量下；不要长按电源。无需输入或重新保存Wi-Fi密码。'
read -r -p '准备好观察后按回车；Ctrl-C取消：' answer
ssh -F /dev/null -i picasso/out/fedora-server-test/id_ed25519 \
 -o BatchMode=yes -o IdentitiesOnly=yes \
 -o UserKnownHostsFile=picasso/out/confirmation-20261027/known_hosts \
 -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
 picasso@192.168.7.2 'sudo -n python3 -I /opt/picasso-display-trial/run-screen-visual2.py' | tee "$D/visual-local-run.log"
printf '%s\n' '请回复：是否看见三色色条、是否确实关灯、短按音量上后是否亮屏。'
