#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail
[[ -t 0 && -t 2 ]] || { printf '%s\n' '请在本地交互终端运行；不要通过聊天、管道或命令参数传入密码。' >&2; exit 1; }
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
exec ssh -F /dev/null \
  -i "$ROOT/out/fedora-server-test/id_ed25519" \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile="$ROOT/out/confirmation-20261027/known_hosts" \
  -o StrictHostKeyChecking=yes -o ConnectTimeout=10 -t \
  picasso@192.168.7.2 sudo -n python3 \
  /opt/picasso-wifi-trial/enter-chaldea-secret.py
