#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# HOST ONLY: build userdata ext4 from an already natively initialized RAM root.
# No Android/phone block device is opened or written by this tool.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
[[ $# == 2 ]] || { echo 'Usage: podman unshare bash tools/prepare-diskroot.sh SNAPSHOT WORKDIR' >&2; exit 2; }
SNAPSHOT=$(realpath "$1")
WORK=$(realpath "$2")
[[ $WORK == "$ROOT"/out/* && -f $SNAPSHOT && -d $WORK ]]
# Preserve target ownership without using host root or executing ARM programs.
[[ $(id -u) == 0 ]]
awk '$1 == 0 && $2 != 0 { ok=1 } END { exit !ok }' /proc/self/uid_map
PARTUUID=32684d05-1c3b-836e-c936-7d4638bf1be9
BYTES=114936492032
STAGE=$WORK/diskroot-stage
IMAGE=$WORK/fedora-userdata.ext4
[[ ! -e $STAGE && ! -e $IMAGE ]]
mkdir -m 700 "$STAGE"
tar --no-selinux --no-xattrs --numeric-owner --same-owner -xzf "$SNAPSHOT" -C "$STAGE"
[[ $(< "$STAGE/etc/picasso-native-init.done") == PICASSO_NATIVE_INIT_V1 ]]
grep -qx 'ID=fedora' "$STAGE/etc/os-release"
grep -qx 'VERSION_ID=44' "$STAGE/etc/os-release"
grep -qx 'VARIANT_ID=server' "$STAGE/etc/os-release"
for d in dev proc sys run mnt tmp; do
    [[ ! -L $STAGE/$d ]]
    mkdir -p "$STAGE/$d"
    chmod 755 "$STAGE/$d"
done
chmod 1777 "$STAGE/tmp"
# This is only this script's new host staging tree, never the source/RAM root.
rm -rf -- "$STAGE/usr/lib/modules"
cp -a "$ROOT/out/modules/lib/modules" "$STAGE/usr/lib/modules"
rm -f -- "$STAGE/etc/picasso-fedora-ramroot" "$STAGE/.autorelabel"
printf '%s\n' PICASSO_FEDORA44_DISKROOT_V2 > "$STAGE/etc/picasso-fedora-root"
printf '%s\n' ext4 > "$STAGE/etc/picasso-install-fstype"
printf '%s\n' "$PARTUUID" > "$STAGE/etc/picasso-install-partuuid"
printf 'PARTUUID=%s / ext4 defaults,noatime 0 1\n' "$PARTUUID" > "$STAGE/etc/fstab"
# PID 1 uses this timestamp as a trusted lower bound; no fake NTP/RTC claim.
touch "$STAGE/usr/lib/clock-epoch"
# Host SELinux xattrs are deliberately not imported into the ARM image. Label
# natively in the guest (permissive kernel) before SSH/firewalld on first boot.
install -Dm755 "$ROOT/tools/fedora-restore-filecaps.py" "$STAGE/usr/libexec/picasso-restore-filecaps.py"
cat > "$STAGE/usr/lib/systemd/system/picasso-disk-label.service" <<'EOF'
[Unit]
Description=Label the explicitly installed Picasso Fedora disk root
After=local-fs.target
Before=sshd.service firewalld.service multi-user.target
ConditionPathExists=!/etc/picasso-disk-label.done

[Service]
Type=oneshot
ExecStartPre=/usr/bin/python3 /usr/libexec/picasso-restore-filecaps.py
ExecStart=/usr/sbin/setfiles -F -e /dev -e /proc -e /sys -e /run -e /tmp /etc/selinux/targeted/contexts/files/file_contexts /
ExecStartPost=/usr/bin/touch /etc/picasso-disk-label.done
RemainAfterExit=yes
TimeoutStartSec=180

[Install]
WantedBy=multi-user.target
EOF
mkdir -p "$STAGE/etc/systemd/system/multi-user.target.wants"
ln -s /usr/lib/systemd/system/picasso-disk-label.service "$STAGE/etc/systemd/system/multi-user.target.wants/picasso-disk-label.service"
python3 - "$STAGE" "$WORK" "$PARTUUID" "$BYTES" "$ROOT" <<'PY'
import hashlib,json,os,stat,sys,uuid
from pathlib import Path
stage,work,partuuid,size,root=map(Path,sys.argv[1:])
# Compare public key material, never print private host keys.
known=(root/'out/confirmation-20261027/known_hosts').read_text().split()
pub=(stage/'etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
assert known[1:3]==pub[:2], 'snapshot host key differs from physically pinned key'
assert stat.S_IMODE((stage/'etc/ssh/ssh_host_ed25519_key').stat().st_mode)==0o600
assert (stage/'etc/firewalld/firewalld.conf').readlink()==Path('firewalld-server.conf')
files={}
for prefix in ('usr','etc/ssh','etc/firewalld','home/picasso/.ssh'):
 for base,dirs,names in os.walk(stage/prefix,followlinks=False):
  dirs.sort(); names.sort()
  for name in names:
   p=Path(base)/name
   s=p.lstat()
   if stat.S_ISREG(s.st_mode):
    with p.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    files[str(p.relative_to(stage))]={'bytes':s.st_size,'sha256':digest,'uid':s.st_uid,'gid':s.st_gid,'mode':stat.S_IMODE(s.st_mode)}
manifest={'source':'natively initialized and hardware-tested Fedora RAM root; updated matching modules and disk-only config',
          'target_partname':'userdata','target_partuuid':str(partuuid),'target_bytes':int(str(size)),
          'filesystem_uuid':str(uuid.uuid4()),'native_arm_binaries_executed_on_host':False,
          'host_selinux_xattrs_copied':False,'firstboot_native_label_service':True,'files':files}
(work/'diskroot-files-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared',len(files),'static files; public SSH host key matches physical serial pin.')
PY
UUID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["filesystem_uuid"])' "$WORK/diskroot-files-manifest.json")
truncate -s "$BYTES" "$IMAGE"
mke2fs -q -t ext4 -F -b 4096 -i 65536 -m 1 -L fedora-root -U "$UUID" \
    -E nodiscard,no_copy_xattrs,lazy_itable_init=0,lazy_journal_init=0 \
    -d "$STAGE" "$IMAGE"
e2fsck -fn "$IMAGE"
echo "Built host-only ext4 userdata image: $IMAGE (not flashed)"
