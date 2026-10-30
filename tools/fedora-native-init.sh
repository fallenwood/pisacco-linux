#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Run ONLY on the phone, before the explicit PID-1 RAM-root handoff.
# All persistent-looking paths below are inside the verified /newroot tmpfs.
set -eu
[ "$(uname -m)" = aarch64 ]
awk '$2 == "/newroot" && $3 == "tmpfs" { ok=1 } END { exit !ok }' /proc/mounts
[ "$(cat /newroot/etc/picasso-fedora-ramroot)" = PICASSO_FEDORA44_RAMROOT_V1 ]
grep -qx 'ID=fedora' /newroot/etc/os-release
grep -qx 'VERSION_ID=44' /newroot/etc/os-release
grep -qx 'VARIANT_ID=server' /newroot/etc/os-release
# RPM filesystem marks some API mountpoints as ghost entries, so a cross
# payload-only install may not contain them yet. Create them only on this tmpfs.
for d in dev proc sys run; do
    [ ! -L /newroot/$d ] || exit 1
    mkdir -p /newroot/$d
    [ -d /newroot/$d ] || exit 1
done
step() { echo "fedora-native-init: $*"; }
step 'initializing aarch64 Fedora natively, not using QEMU'
# qcom-rng was a module in the rescue build. Its DT node is enabled; load
# the matching driver to resolve probe dependencies. This board reports no TRNG:
# do not claim this PRNG driver supplies trusted hardware entropy to the CRNG.
RNG=/newroot/usr/lib/modules/$(uname -r)/kernel/drivers/crypto/qcom-rng.ko
if [ -f "$RNG" ] && [ ! -d /sys/module/qcom_rng ]; then
    insmod "$RNG"
fi
BOUND=
SELINUX_BOUND=0
cleanup() {
    if [ "$SELINUX_BOUND" = 1 ]; then umount /newroot/sys/fs/selinux || return 1; SELINUX_BOUND=0; fi
    for d in $BOUND; do umount /newroot/$d || return 1; done
    BOUND=
}
trap 'cleanup' EXIT
for d in dev proc sys; do
    mount --bind /$d /newroot/$d
    BOUND="$d $BOUND"
done
step ldconfig
chroot /newroot /usr/sbin/ldconfig
step sysusers
chroot /newroot /usr/bin/systemd-sysusers
step 'local PAM/NSS profile'
chroot /newroot /usr/bin/authselect select local --force
step 'crypto policies and certificate trust'
chroot /newroot /usr/bin/update-crypto-policies --set DEFAULT
chroot /newroot /usr/bin/update-ca-trust extract
step 'SSH host keys (kept only in RAM)'
chroot /newroot /usr/bin/ssh-keygen -A
step 'load Fedora SELinux policy without enabling enforcement'
if ! grep -qs ' /sys/fs/selinux selinuxfs ' /proc/mounts; then
    mkdir -p /sys/fs/selinux
    mount -t selinuxfs selinuxfs /sys/fs/selinux
fi
mount --bind /sys/fs/selinux /newroot/sys/fs/selinux
SELINUX_BOUND=1
chroot /newroot /usr/sbin/load_policy -i
step 'label only the RAM root; never Android storage or pseudo filesystems'
chroot /newroot /usr/sbin/setfiles -F -e /dev -e /proc -e /sys -e /run \
    /etc/selinux/targeted/contexts/files/file_contexts /
step 'validate SSH configuration and Fedora identity'
mkdir -p /newroot/run/sshd
chroot /newroot /usr/sbin/sshd -t
chroot /newroot /usr/bin/cat /etc/os-release
chroot /newroot /usr/bin/getenforce
cleanup
trap - EXIT
printf 'PICASSO_NATIVE_INIT_V1\n' > /newroot/etc/picasso-native-init.done
step 'complete; still rescue PID 1 until a separate explicit RAM-root request'
