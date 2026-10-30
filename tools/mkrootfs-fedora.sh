#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Native cross-install in Podman's rootless user namespace. NO QEMU, phone IO,
# target-architecture execution, filesystem formatting, or host RPM installation.
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
KEYFILE=$(realpath "${1:?usage: tools/mkrootfs-fedora.sh /path/to/key.pub}")
if [[ ${PICASSO_BUILD_USERNS:-} != 1 ]]; then
    command -v podman >/dev/null
    exec podman unshare env PICASSO_BUILD_USERNS=1 "$0" "$KEYFILE"
fi
[[ $(id -u) = 0 ]] || { echo 'Expected Podman user namespace' >&2; exit 1; }
for tool in dnf rpm systemd-sysusers systemctl useradd tar gzip python3; do command -v "$tool" >/dev/null; done
KEY=$(<"$KEYFILE")
[[ $KEY != *$'\n'* && $KEY =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-[^[:space:]]+)[[:space:]] ]] || { echo 'Expected one OpenSSH public key' >&2; exit 1; }
OUT=$ROOT/out
mkdir -p "$OUT"
WORK=${FEDORA_WORK_DIR:-$(mktemp -d "$OUT/fedora-cross.XXXXXX")}
[[ $WORK = "$OUT"/fedora-cross.* && ! -L $WORK ]] || { echo 'Unsafe build work directory' >&2; exit 1; }
TARGET=$WORK/rootfs
mkdir -p "$TARGET" "$WORK/repos" "$WORK/logs"
# filesystem's pretrans normally prepares usr-merge. With scriptlets skipped,
# seed it ourselves before any RPM can create /lib64 as a real directory.
mkdir -p "$TARGET/usr/bin" "$TARGET/usr/lib" "$TARGET/usr/lib64"
for spec in usr/sbin:bin bin:usr/bin sbin:usr/sbin lib:usr/lib lib64:usr/lib64; do
    name=${spec%:*}; link=${spec#*:}
    if [[ ! -e $TARGET/$name && ! -L $TARGET/$name ]]; then
        ln -s "$link" "$TARGET/$name"
    fi
done
echo "Native cross-build work directory: $WORK"
# Fixed HTTPS mirrors avoid slow/unreachable metalink choices; signatures remain
# checked against Fedora's release key installed on this Fedora build host.
MIRROR=${FEDORA_MIRROR:-https://mirrors.ustc.edu.cn/fedora}
GPG=/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-44-primary
[[ -f $GPG ]] || { echo 'Fedora 44 signing key missing on build host' >&2; exit 1; }
cat > "$WORK/repos/fedora-cross.repo" <<EOF
[fedora-cross]
name=Fedora 44 aarch64
baseurl=$MIRROR/releases/44/Everything/aarch64/os/
enabled=1
gpgcheck=1
gpgkey=file://$GPG
[updates-cross]
name=Fedora 44 updates aarch64
baseurl=$MIRROR/updates/44/Everything/aarch64/
enabled=1
gpgcheck=1
gpgkey=file://$GPG
EOF
DNF=(dnf -y --installroot="$TARGET" --releasever=44 --forcearch=aarch64 --use-host-config
    --setopt="reposdir=$WORK/repos" --setopt="cachedir=$WORK/cache" --setopt="logdir=$WORK/logs"
    --setopt=tsflags=noscripts,notriggers,nocontexts --setopt=install_weak_deps=False
    --setopt=timeout=30 --setopt=retries=2 --repo=fedora-cross,updates-cross
    --exclude='kernel*' --exclude='grub2*' --exclude='shim*' --exclude='*firmware*')
# RPM payloads and their dependency graph are real Fedora Server/Core packages.
# Scriptlets/triggers are deliberately not executed on this foreign-arch root.
"${DNF[@]}" install @core fedora-release-server systemd systemd-udev systemd-networkd \
    dbus-broker openssh-server openssh-clients NetworkManager NetworkManager-wifi \
    wpa_supplicant iw wireless-regdb shadow-utils sudo \
    util-linux e2fsprogs kmod iproute iputils selinux-policy-targeted policycoreutils \
    procps-ng less vim-minimal tar gzip ca-certificates passwd crypto-policies-scripts
# All following helpers are native HOST programs operating on an explicit root.
# Never chroot into the aarch64 tree on the x86 host (which would invoke binfmt).
systemd-sysusers --root="$TARGET"
grep -q '^picasso:' "$TARGET/etc/passwd" || useradd --prefix "$TARGET" -m -G wheel -p '*' -s /bin/bash picasso
install -d -m 0700 "$TARGET/home/picasso/.ssh"
printf '%s\n' "$KEY" > "$TARGET/home/picasso/.ssh/authorized_keys"
chown -R 1000:1000 "$TARGET/home/picasso"
chmod 0600 "$TARGET/home/picasso/.ssh/authorized_keys"
install -d "$TARGET/etc/sudoers.d" "$TARGET/etc/ssh/sshd_config.d" \
    "$TARGET/etc/systemd/network" "$TARGET/etc/NetworkManager/conf.d" \
    "$TARGET/etc/systemd/system-generators" "$TARGET/etc/systemd/system"
printf 'picasso ALL=(ALL) NOPASSWD: ALL\n' > "$TARGET/etc/sudoers.d/picasso"
chmod 0440 "$TARGET/etc/sudoers.d/picasso"
printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\n' > "$TARGET/etc/ssh/sshd_config.d/10-picasso.conf"
cat > "$TARGET/etc/systemd/network/10-picasso-usb.network" <<'EOF'
[Match]
MACAddress=02:50:49:00:00:02
[Network]
Address=192.168.7.2/24
LinkLocalAddressing=no
IPv6AcceptRA=no
EOF
printf '[keyfile]\nunmanaged-devices=mac:02:50:49:00:00:02\n' > "$TARGET/etc/NetworkManager/conf.d/10-picasso-usb.conf"
printf 'picasso-fedora\n' > "$TARGET/etc/hostname"
printf '127.0.0.1 localhost\n127.0.1.1 picasso-fedora\n::1 localhost\n' > "$TARGET/etc/hosts"
printf '# RAM-only root; no automatic disk mounts.\n' > "$TARGET/etc/fstab"
# Match the actual custom kernel. A 1 GiB logical ZRAM device is RAM only;
# CONFIG_ZRAM_WRITEBACK is disabled, with no Android-backed swap files/devices.
if grep -Eq '^CONFIG_ZRAM=(y|m)$' "$OUT/kernel.config"; then
    printf '[zram0]\nzram-size = 1024\ncompression-algorithm = zstd\n' > "$TARGET/etc/systemd/zram-generator.conf"
else
    printf '# Kernel has no ZRAM; do not wait for a nonexistent device.\n' > "$TARGET/etc/systemd/zram-generator.conf"
fi
install -d "$TARGET/etc/firewalld/zones"
cat > "$TARGET/etc/firewalld/zones/picasso-usb.xml" <<'EOF'
<?xml version="1.0" encoding="utf-8"?>
<zone>
  <short>Picasso trusted USB host</short>
  <description>Temporary directly-attached host; SSH key authentication only.</description>
  <source address="192.168.7.1/32"/>
  <service name="ssh"/>
</zone>
EOF
printf 'PICASSO_FEDORA44_RAMROOT_V1\n' > "$TARGET/etc/picasso-fedora-ramroot"
printf 'Picasso Fedora 44 root; persistent PARTUUID requires separate authorization\n' > "$TARGET/etc/picasso-fedora-root"
# Keep SELinux installed/permissive for bring-up. Do NOT request /.autorelabel:
# its automatic reboot would throw away a RAM root. Native policy initialization
# is completed on the phone before PID 1 handoff; enforcing is not yet validated.
python3 - "$TARGET" <<'PY'
from pathlib import Path
import sys
r = Path(sys.argv[1])
# Fedora firewalld creates these ghost links in posttrans, which this cross
# install deliberately skips. Reproduce Server defaults without running ARM.
for relative, target in (
    ('etc/firewalld/firewalld.conf', 'firewalld-server.conf'),
    ('usr/share/polkit-1/actions/org.fedoraproject.FirewallD1.policy',
     'org.fedoraproject.FirewallD1.server.policy.choice'),
):
    p = r/relative
    if not (p.parent/target).is_file():
        raise SystemExit('Missing Fedora Server firewalld payload: ' + str(p.parent/target))
    if not p.exists() and not p.is_symlink():
        p.symlink_to(target)
p = r/'etc/selinux/config'
s = p.read_text() if p.exists() else 'SELINUX=permissive\nSELINUXTYPE=targeted\n'
s = '\n'.join('SELINUX=permissive' if x.startswith('SELINUX=') else x for x in s.splitlines())+'\n'
p.write_text(s)
for name in ('.autorelabel', '.dockerenv', 'run/.containerenv', 'etc/machine-id', 'var/lib/dbus/machine-id'):
    p = r/name
    if p.exists() or p.is_symlink(): p.unlink()
(r/'etc/machine-id').touch()
PY
# No discoverable-partition auto-mounting, repartitioning, LVM activation, or
# firstboot/relabel reboots during this RAM-only trial.
ln -sfn /dev/null "$TARGET/etc/systemd/system-generators/systemd-gpt-auto-generator"
systemctl --root="$TARGET" preset-all
systemctl --root="$TARGET" enable sshd systemd-networkd NetworkManager serial-getty@ttyGS0.service
systemctl --root="$TARGET" set-default multi-user.target
systemctl --root="$TARGET" mask systemd-networkd-wait-online.service NetworkManager-wait-online.service \
    systemd-repart.service systemd-growfs-root.service systemd-firstboot.service \
    selinux-autorelabel.service selinux-autorelabel-mark.service \
    lvm2-monitor.service lvm2-pvscan@.service lvm2-lvmpolld.socket dm-event.socket mdmonitor.service \
    fwupd.service fwupd-refresh.service fwupd-refresh.timer fstrim.timer \
    sssd.service sssd-kcm.socket systemd-homed.service
if [[ -d $OUT/modules/lib/modules ]]; then
    # Do not retain stale .ko files when a previous module became built-in.
    rm -rf -- "$TARGET/usr/lib/modules"
    cp -a "$OUT/modules/lib/modules" "$TARGET/usr/lib/"
fi
rpm --root "$TARGET" -qa --qf '%{NAME} %{VERSION}-%{RELEASE} %{ARCH}\n' | sort > "$OUT/fedora-packages.txt"
python3 - "$TARGET" "$WORK" "$OUT" "$GPG" <<'PY'
from pathlib import Path
import hashlib,json,platform,sys
r,w,o,key=map(Path,sys.argv[1:]); release=(r/'usr/lib/os-release').read_text()
assert 'VARIANT_ID=server' in release and 'VERSION_ID=44' in release,release
packages=(o/'fedora-packages.txt').read_text().splitlines()
assert all(p.split()[-1] in {'aarch64','noarch'} or p.startswith('gpg-pubkey ') for p in packages)
(o/'fedora-rootfs-build.json').write_text(json.dumps({
 'method':'podman unshare; native DNF forcearch=aarch64; RPM scriptlets/triggers skipped',
 'qemu_used':False,'host_arch':platform.machine(),'target_arch':'aarch64','release':44,
 'variant':'server','package_group':'core',
 'package_count':sum(not p.startswith('gpg-pubkey ') for p in packages),
 'rpm_record_count':len(packages),
 'work_dir':str(w),'root_dir':str(r),'repo_config':(w/'repos/fedora-cross.repo').read_text(),
 'fedora_signing_key_sha256':hashlib.sha256(key.read_bytes()).hexdigest(),
 'native_phone_initialization_required':True,'storage_mode':'RAM only',
 'kernel':'custom 6.18.58-picasso-lts; no Fedora kernel RPM'},indent=2)+'\n')
PY
ARCHIVE=$OUT/fedora-44-aarch64-rootfs.tar
tar --numeric-owner -cpf "$ARCHIVE.tmp" -C "$TARGET" .
mv "$ARCHIVE.tmp" "$ARCHIVE"
gzip -1 -c "$ARCHIVE" > "$ARCHIVE.gz.tmp"
mv "$ARCHIVE.gz.tmp" "$ARCHIVE.gz"
sha256sum "$ARCHIVE" "$ARCHIVE.gz" > "$OUT/fedora-rootfs.sha256"
echo 'Fedora Server/Core archive built without QEMU; native phone initialization still required.'
echo "Root kept for inspection: $TARGET; no phone commands or host package installation performed."
