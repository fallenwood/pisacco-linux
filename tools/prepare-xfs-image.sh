#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# HOST ONLY: populate a new regular-file XFS image using a scoped loop mount.
# Never opens a phone block device; never executes target AArch64 programs.
set -euo pipefail
umask 077
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
[[ $# == 1 ]] || { echo 'Usage: bash tools/prepare-xfs-image.sh WORKDIR' >&2; exit 2; }
WORK=$(realpath "$1")
[[ $WORK == "$ROOT"/out/install-xfs-* && -d $WORK && ! -L $WORK ]]
STAGE=$WORK/rootfs-stage
IMAGE=$WORK/fedora-userdata-xfs.raw
MOUNT=$WORK/host-image-mount
[[ -f $WORK/packages-prepared && -d $STAGE && ! -L $STAGE ]]
[[ ! -e $IMAGE && ! -e $MOUNT ]]
BYTES=114936492032
PARTUUID=32684d05-1c3b-836e-c936-7d4638bf1be9
for symbol in XFS_FS XFS_POSIX_ACL XFS_QUOTA; do grep -qx "CONFIG_$symbol=y" "$ROOT/out/kernel.config"; done
grep -q "root=PARTUUID=$PARTUUID rootfstype=xfs" "$ROOT/out/kernel.config"
# All staging ownership changes are made inside the existing rootless mapping.
podman unshare python3 - "$ROOT" "$WORK" <<'PY'
import hashlib,json,os,shutil,stat,sys,uuid
from pathlib import Path
r,w=map(Path,sys.argv[1:]); s=w/'rootfs-stage'
assert os.geteuid()==0
assert s.is_dir() and not s.is_symlink()
assert (s/'etc/picasso-native-init.done').read_text().strip()=='PICASSO_NATIVE_INIT_V1'
assert 'VARIANT_ID=server\n' in (s/'etc/os-release').read_text()
assert 'VERSION_ID=44\n' in (s/'etc/os-release').read_text()
shutil.rmtree(s/'usr/lib/modules')
shutil.copytree(r/'out/modules/lib/modules',s/'usr/lib/modules',symlinks=True,copy_function=shutil.copy2)
for name in ('etc/picasso-fedora-ramroot','etc/picasso-disk-label.done','.autorelabel'):
 (s/name).unlink(missing_ok=True)
(s/'etc/picasso-fedora-root').write_text('PICASSO_FEDORA44_DISKROOT_V2\n')
(s/'etc/picasso-install-partuuid').write_text('32684d05-1c3b-836e-c936-7d4638bf1be9\n')
(s/'etc/picasso-install-fstype').write_text('xfs\n')
(s/'etc/fstab').write_text('PARTUUID=32684d05-1c3b-836e-c936-7d4638bf1be9 / xfs defaults,noatime 0 0\n')
(s/'usr/lib/clock-epoch').touch()
helper=s/'usr/libexec/picasso-restore-filecaps.py'
shutil.copy2(r/'tools/fedora-restore-filecaps.py',helper); helper.chmod(0o755)
unit=s/'usr/lib/systemd/system/picasso-disk-label.service'
u=unit.read_text()
pre='ExecStartPre=/usr/bin/python3 /usr/libexec/picasso-restore-filecaps.py'
if pre not in u:
 assert u.count('Type=oneshot\n')==1
 unit.write_text(u.replace('Type=oneshot\n','Type=oneshot\n'+pre+'\n'))
seed=s/'var/lib/systemd/random-seed'
seed.write_bytes(os.urandom(512)); seed.chmod(0o600)
known=(r/'out/confirmation-20261027/known_hosts').read_text().split()
pub=(s/'etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
assert known[1:3]==pub[:2], 'SSH host key differs from physical serial pin'
assert stat.S_IMODE((s/'etc/ssh/ssh_host_ed25519_key').stat().st_mode)==0o600
assert (s/'etc/firewalld/firewalld.conf').readlink()==Path('firewalld-server.conf')
# DNF creates an empty runtime directory even with all target scriptlets off.
# Remove only that known empty directory; reject any other runtime contents.
if (s/'run/dnf').exists():
 (s/'run/dnf').rmdir()
for d in ('dev','proc','sys','run'):
 p=s/d; assert p.is_dir() and not p.is_symlink(); assert not any(p.iterdir())
files={}
for prefix in ('usr','etc/ssh','etc/firewalld','home/picasso/.ssh'):
 for base,dirs,names in os.walk(s/prefix,followlinks=False):
  dirs.sort(); names.sort()
  for name in names:
   p=Path(base)/name; info=p.lstat()
   if stat.S_ISREG(info.st_mode):
    with p.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    files[str(p.relative_to(s))]={'bytes':info.st_size,'sha256':digest,'uid':info.st_uid,'gid':info.st_gid,'mode':stat.S_IMODE(info.st_mode)}
m={'target_partname':'userdata','target_partuuid':'32684d05-1c3b-836e-c936-7d4638bf1be9',
   'target_bytes':114936492032,'fstype':'xfs','filesystem_uuid':str(uuid.uuid4()),
   'source':'native-initialized Fedora 44 Server snapshot; signed aarch64 XFS packages added without host target execution',
   'host_selinux_xattrs_copied':False,'firstboot_native_label_service':True,'native_arm_binaries_executed_on_host':False,
   'kernel_config_sha256':hashlib.sha256((r/'out/kernel.config').read_bytes()).hexdigest(),'files':files}
(w/'diskroot-files-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print('Prepared',len(files),'static files; native initialization and pinned SSH key preserved.')
PY
UUID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["filesystem_uuid"])' "$WORK/diskroot-files-manifest.json")
cp /usr/share/xfsprogs/mkfs/lts_6.18.conf "$WORK/mkfs-lts_6.18.conf"
truncate -s "$BYTES" "$IMAGE"
mkfs.xfs -f -K -c "options=$WORK/mkfs-lts_6.18.conf" -b size=4096 -s size=4096 \
    -m "uuid=$UUID" -L fedora-root "$IMAGE"
mkdir -m 700 "$MOUNT"
LOOP=
MOUNTED=0
cleanup() {
    if [[ $MOUNTED == 1 ]]; then sudo -n umount "$MOUNT"; fi
    if [[ -n $LOOP ]]; then sudo -n losetup -d "$LOOP"; fi
}
trap cleanup EXIT
LOOP=$(sudo -n losetup --find --show "$IMAGE")
[[ $(sudo -n losetup -n -O BACK-FILE "$LOOP") == "$IMAGE" ]]
printf 'Scoped host loop: %s -> %s\n' "$LOOP" "$IMAGE"
# noexec prevents accidental target execution; a temporary host-only SELinux
# mount context avoids importing host policy labels into the ARM filesystem.
sudo -n mount -t xfs -o nodev,nosuid,noexec,noatime,context=system_u:object_r:tmp_t:s0 "$LOOP" "$MOUNT"
MOUNTED=1
podman unshare tar --numeric-owner --no-selinux --no-xattrs -cpf - -C "$STAGE" . |
    sudo -n tar --numeric-owner --same-owner --no-selinux --no-xattrs -xpf - -C "$MOUNT"
sudo -n sync -f "$MOUNT"
sudo -n xfs_info "$MOUNT"
sudo -n umount "$MOUNT"
MOUNTED=0
sudo -n losetup -d "$LOOP"
LOOP=
rmdir "$MOUNT"
xfs_repair -n "$IMAGE"
# Decode and byte-compare the complete logical image before any phone flash.
TOOLS=$ROOT/out/install-20261027/native-tools/usr/bin
"$TOOLS/img2simg" -s "$IMAGE" "$WORK/fedora-userdata-xfs.sparse.img"
"$TOOLS/simg2img" "$WORK/fedora-userdata-xfs.sparse.img" "$WORK/fedora-userdata-xfs.roundtrip.raw"
cmp "$IMAGE" "$WORK/fedora-userdata-xfs.roundtrip.raw"
xfs_repair -n "$WORK/fedora-userdata-xfs.roundtrip.raw"
python3 - "$WORK" <<'PY'
import datetime,hashlib,json,struct,sys
from pathlib import Path
w=Path(sys.argv[1]); p=w/'fedora-userdata-xfs.sparse.img'
with p.open('rb') as f:
 h=struct.unpack('<I4H4I',f.read(28))
assert h[:5]==(0xed26ff3a,1,0,28,12)
assert h[5]==4096 and h[5]*h[6]==114936492032
with p.open('rb') as f: sha=hashlib.file_digest(f,'sha256').hexdigest()
x={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'android_sparse_header':h,
   'logical_bytes':h[5]*h[6],'image_bytes':p.stat().st_size,'sha256':sha,'fstype':'xfs',
   'simg2img_full_byte_comparison_passed':True,'roundtrip_xfs_repair_readonly_passed':True,
   'target_partition':'userdata','flashed':False,'contains_private_ssh_host_keys':True,
   'mkfs_profile':'xfsprogs lts_6.18; sector and block size 4096; no discard'}
(w/'sparse-image-validation.json').write_text(json.dumps(x,indent=2)+'\n')
print(json.dumps(x,indent=2))
PY
echo 'XFS image built and validated ON HOST ONLY. No phone formatting/flash performed.'
