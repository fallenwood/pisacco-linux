#!/usr/bin/env bash
set -euo pipefail
# Entry ONLY: explicit persistent-secret consent, never start radio by itself.
[[ -t 0 && -t 1 ]] || { printf '%s\n' '请在本地交互终端运行；禁止管道/密码参数。' >&2; exit 1; }
[[ $# == 0 ]] || { printf '%s\n' '此命令不接受密码参数。' >&2; exit 1; }
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
exec ssh -F /dev/null -tt -i "$ROOT/picasso/out/fedora-server-test/id_ed25519" \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile="$ROOT/picasso/out/confirmation-20261027/known_hosts" \
  -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
  picasso@192.168.7.2 'sudo -n python3 -I /opt/picasso-wifi/enter-wifi-autoconnect.py'
