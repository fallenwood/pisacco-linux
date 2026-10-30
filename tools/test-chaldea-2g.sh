#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Explicit attended one-shot TEST: local secret entry, then immediate bounded trial.
# Unlike enter-chaldea-2g-password.sh alone, THIS command starts the radio/test.
set -euo pipefail
[[ -t 0 && -t 2 ]] || { printf '%s\n' '请在本地交互终端运行；不要通过聊天、管道或参数传入密码。' >&2; exit 1; }
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
TRIAL="$ROOT/out/wifi-chaldea-2g-connect4-20261028"
[[ -f "$TRIAL/run-connect.py" ]] || { printf '%s\n' '缺少本次已准备的试验控制器；未录入密码或启动无线。' >&2; exit 1; }
# Refuse a reused exclusive trial or an existing pending secret before prompting.
ssh -F /dev/null -i "$ROOT/out/fedora-server-test/id_ed25519" \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile="$ROOT/out/confirmation-20261027/known_hosts" \
  -o StrictHostKeyChecking=yes -o ConnectTimeout=10 picasso@192.168.7.2 \
  'sudo -n test ! -e /run/picasso-wifi-chaldea-2g-connect4 && sudo -n test ! -e /run/picasso-chaldea-2g.passwd && sudo -n test ! -L /run/picasso-chaldea-2g.passwd' \
  || { printf '%s\n' '已有试验目录或待用凭据，或手机不可达；未覆盖/重新录入。请告知助手核对。' >&2; exit 1; }
# Nonsecret native preflight before asking the operator for a password.
ssh -F /dev/null -i "$ROOT/out/fedora-server-test/id_ed25519" \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile="$ROOT/out/confirmation-20261027/known_hosts" \
  -o StrictHostKeyChecking=yes -o ConnectTimeout=10 picasso@192.168.7.2 \
  sudo -n python3 - <<'PY'
import os
from pathlib import Path
assert os.uname().release=='6.18.58-picasso-lts-wifi2','Expected native temporary wifi2 session'
assert Path('/sys/class/remoteproc/remoteproc0/state').read_text().strip()=='offline','DSP must be offline before starting a new trial'
assert max(int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp'))<40000,'Cool below 40C before local entry/trial'
print('Native kernel/offline DSP/cold temperature preflight passed; no credential read.')
PY
printf '%s\n' '本命令将本地录入 Chaldea-2.4G 密码后立即执行最多90秒的联网试验；不是持久启用。' >&2
"$ROOT/tools/enter-chaldea-2g-password.sh"
printf '%s\n' '现在自动开始试验；请等待整个命令结束，不要同时重复启动。结束后回复已完成。' >&2
cd -- "$ROOT/.."
python3 "$TRIAL/run-connect.py"
# Report the structured result, not a successful SSH/Python launch, as acceptance.
python3 - "$TRIAL/connect-result.json" <<'PY'
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
print('Bounded test result:',r.get('status'))
sys.exit(0 if str(r.get('status','')).startswith('passed_') else 1)
PY
