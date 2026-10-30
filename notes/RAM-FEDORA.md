# Fedora Server 44 minimal：真机 RAM 运行 / Fedora Server 44 Minimal: Running in RAM on the Actual Phone

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录；“当前”等状态按原记录时间理解，反引号中的代码及证据路径相对于仓库根目录。 / Historical stage record; “current” refers to the recorded stage. Code and evidence paths in backticks are relative to the repository root.

## 中文

最新新内核功能确认见 [CONFIRMATION.md](CONFIRMATION.md)（2026-10-27）。本文保留 RAM
构建和交接流程；10 月 26 日首轮旧镜像的缺 NF_TABLES/ZRAM 故障已由新镜像修复。

## 当前结果

不是只运行 chroot，也不是在手机上跑容器/模拟器：

- `cat /proc/1/comm` → `systemd`；PID 1 executable 为 `/usr/lib/systemd/systemd`。
- `/etc/os-release` → Fedora Linux 44 (Server Edition)，aarch64 GNU/Linux。
- `systemd-detect-virt` → `none`；`multi-user.target` active。
- USB SSH 公钥登录 UID 1000 `${DEVICE_USER}`、wheel、无密码 sudo 已验证。
- sshd、dbus、systemd-networkd、NetworkManager active；DNF ${IP_ADDRESS} 可原生执行。
- 实际软件包 274 个；RPM 数据库 275 条，含 1 条 Fedora GPG key。
- 根为 tmpfs（3 GiB 上限）；可用内存约 4.36 GiB，另有 1 GiB 逻辑 zstd ZRAM swap，
  无磁盘后备，32 MiB pageout/readback SHA256 验证通过。
- 8 CPU 在线；最后温度快照约 33.1–34.4°C，不等于温控/压力验收。
- SELinux **Permissive**，策略已加载、RAM 文件已标记，SSH/PAM 有正常 SELinux context。
- Linux 的挂载表只有内存/API 文件系统，没有 Android 块设备文件系统。

**systemd 状态为 degraded，不能当作健康的生产服务器：**

1. nftables/firewalld 和 ZRAM 已通过真机功能测试；剩余失败项是 `dnf-makecache.service`，
   原因是没有互联网/DNS 出口，没有清除失败状态。
2. 跳过 RPM 脚本遗漏的 firewalld Server/Polkit ghost 链接已在 RAM 中补齐并 reload；
   构建脚本已修复，但本次测试的原始 rootfs 归档未重建。重现时仍需完成这一初始化。
3. 系统时钟曾落后，导致 RPM 签名“尚未生效”；已从主机校时，无 RTC 写入或 NTP 验收。
4. 装载对齐、PSCI、UFS 供电/对齐及 watchdog/ignore-unused 限制仍在。qcom_rng 报
   `TRNG support not detected`，不认为硬件熵源通过。
5. 没有验证持久写入、充电、休眠、完整内存或长期温控。只有可信 USB 直连；不要开放到公网。

## 当前主机如何登录

在 `${REPO_ROOT}` 执行：

```sh
ssh -F /dev/null -i ${SSH_PRIVATE_KEY} \
  -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=${SSH_KNOWN_HOSTS} \
  -o StrictHostKeyChecking=yes ${DEVICE_USER}@${PHONE_USB_IP}
```

手机地址 `${PHONE_USB_IP}/24`，主机当前 USB NCM 地址 `${HOST_USB_IP}/24`。没有配置手机互联网
网关、NAT 或代理；DNF CLI/RPM 数据库已测试，不代表手机已能访问互联网仓库。

当前测试专用私钥只在主机 `${SSH_KEY_DIR}/`（0700）中，不写到手机、文档或 HTTP 目录。
主机 known_hosts 的公钥在切换前从物理 USB 救援串口读取，不使用关闭主机密钥校验的做法。
每次 RAM 启动会重新生成 SSH host keys，应重新从可信串口取得并固定公钥。

进入 Fedora 前，PID 1 已终止全部无密码救援 shell。USB gadget 的名称仍是 Picasso LTS
rescue，但 Fedora 串口是需要认证的 getty，不再是 root shell；账号未设置控制台密码，
请用公钥 SSH。`tools/rescue-console.py` 只用于切换前的空闲救援 shell，不能当 Fedora 登录工具。

## 构建与交接流程（必须另行授权物理启动）

1. Fedora 44 主机执行 `tools/mkrootfs-fedora.sh key.pub`。它进入 **Podman rootless user
   namespace**，用主机原生 DNF `--installroot` / `--forcearch=aarch64` 从签名 RPM 构建
   `@core` + `fedora-release-server`。不需要 OCI ARM 容器或 QEMU，不修改主机 RPM 数据库。
   普通 RPM scripts/triggers 跳过；RPM sysusers helper 从 chroot 外用原生 `--root` 操作。
   脚本预置 usr-merge 链接，避免跳过 filesystem pretrans 后 `/lib64` 变成真实目录。
2. 构建内核并用匹配 crDroid boot 打包。当前 `/init` 默认仍只进救援，**不会自己联网下载
   或自动选择磁盘根**。10 月 26 日启动阶段从旧救援正常重启回 Android，再经 ADB reboot bootloader，
   核对 product/unlocked 后仅执行 `fastboot boot`，没有 flash/unlock/erase。
3. 主机 HTTP 只绑定 USB 地址，并使用专用目录，只提供 rootfs gzip 和初始化脚本，
   **不能把包含 SSH 私钥的目录当 HTTP root**。手机下载到 `/run` tmpfs，核对主机给定的
   SHA256，然后挂载 `tmpfs /newroot`（size=3G），用 `tar -xzpf` 解包并删除压缩包。
   峰值内存远低于本机可用量；没有 loop image、分区格式化或 Android 文件系统挂载。
4. 验证脚本 hash 后在手机原生执行 `tools/fedora-native-init.sh`：仅接受 `/newroot` tmpfs、
   Fedora Server 44 marker。创建 RPM ghost API mountpoints，临时 bind dev/proc/sys；依次
   ldconfig、sysusers、authselect **local**、crypto policies、CA trust、SSH keys、SELinux
   load_policy/setfiles、sshd -t。清除临时 bind 后写 native-init 成功标记。
   普通 chroot 只是这个初始化阶段，不是最终运行方式。
5. 从串口取 SSH public host key，确认没有块设备挂载，再显式提交：

   ```sh
   printf 'PICASSO_RAMROOT_V1\n' > /run/picasso-ramroot.request
   ```

   PID 1 会再核对 tmpfs、marker、Fedora 44/Server、systemd 可执行文件、非 symlink API
   目录。任何校验失败都保留救援并删除请求；通过才停止所有救援用户进程、移动 API
   挂载、`exec switch_root /newroot /usr/lib/systemd/systemd`。没有无密码 shell 跨入 Fedora。
6. 用固定的 SSH host key 登录，检查 PID 1、multi-user、failed units、mounts、内存、温度。
   本轮临时 HTTP 服务已停止；SSH 和当前 Fedora RAM 系统继续运行。

普通脚本没有执行设备命令的隐式权限。先确认用户允许重启/RAM boot；失败不能改用刷写。
Android SELinux 没有修改，也不需要给 Android 安装 root。Fedora udev 可能探测块设备元数据；
没有挂载 Android 文件系统或手工访问用户文件/EFS，不应把它扩大为“所有块设备零读取”。

## 固定证据

- 当前 Kernel boot image：32,899,072 bytes，SHA256
  `59784cc401cad3d1b245e8a403b80abd0176e02e9f6891b31daabe9423a1e801`。
- 当前实际传输的 rootfs gzip SHA256：
  `${PRIVATE_ROOTFS_SHA256_1}`。
- `out/confirmation-20261027/result.json` 记录相应 hash、已测结果、已知失败及证据文件 hash，
  同目录包含测试镜像、初始化脚本、串口和功能 probe 证据。旧 `out/fedora-ramtest/result.json`
  保留首轮缺 nftables/ZRAM 的历史结果，不覆盖、不继承旧镜像的通过状态。
- 构建来源：`out/fedora-rootfs-build.json`、`out/fedora-packages.txt`、`out/fedora-rootfs.sha256`。
- 最新 unit tests：59 个，58 通过，1 个 QEMU applet 测试默认跳过；BusyBox 所需 applets 已在
  手机原生查询。可选模拟器测试需显式 `PICASSO_RUN_QEMU_TESTS=1`，本轮未运行。

**所有 Fedora 修改和主机密钥都只在 RAM 中，关机/重启即丢失。** 持久系统仍是原 Android；
本轮已观察过从旧救援正常重启回 Android，但当前 Fedora systemd 的关机路径尚未专项验收。
持久安装需要独立的分区方案、备份和授权，不要格式化 userdata 或把 tar 当磁盘镜像 dd。

## English

See [CONFIRMATION.md](CONFIRMATION.md) (2026-10-27) for the latest new-kernel functional confirmation
at this stage. This document preserves the RAM build and handover process; the missing NF_TABLES/ZRAM
failures in the first October 26 old-image run were fixed by the new image.

## Results at this stage

This was not merely a chroot, nor a container/emulator running on the phone:

- `cat /proc/1/comm` → `systemd`; PID 1 executable was `/usr/lib/systemd/systemd`.
- `/etc/os-release` → Fedora Linux 44 (Server Edition), aarch64 GNU/Linux.
- `systemd-detect-virt` → `none`; `multi-user.target` active.
- USB SSH public-key login as UID 1000 `${DEVICE_USER}`, wheel membership, and passwordless sudo
  were verified.
- sshd, dbus, systemd-networkd, and NetworkManager were active; DNF ${IP_ADDRESS} ran natively.
- 274 actual packages; 275 RPM database records, including 1 Fedora GPG key.
- Root was tmpfs capped at 3 GiB; approximately 4.36 GiB of memory was available, plus 1 GiB of
  logical zstd ZRAM swap with no disk backing. 32 MiB pageout/readback SHA256 verification passed.
- 8 CPUs online; the final temperature snapshot was approximately 33.1–34.4°C, not thermal-control
  or stress acceptance.
- SELinux **Permissive**, policy loaded, RAM files labeled, and normal SELinux contexts for SSH/PAM.
- Linux's mount table contained only memory/API filesystems, with no Android block-device filesystem.

**systemd was degraded; this could not be treated as a healthy production server:**

1. nftables/firewalld and ZRAM passed functional tests on the actual phone. The remaining failed unit
   was `dnf-makecache.service`, caused by no Internet/DNS egress; the failure state was not cleared.
2. The firewalld Server/Polkit ghost links omitted by skipping RPM scripts were created in RAM,
   followed by reload. The build script was fixed, but the original rootfs archive tested in this session
   was not rebuilt. Reproduction still requires this initialization.
3. The system clock was previously behind, causing RPM signatures to be “not yet valid.”
   It was set from the host; no RTC write or NTP acceptance occurred.
4. Load alignment, PSCI, UFS power/alignment, and watchdog/ignore-unused limitations remained.
   qcom_rng reported `TRNG support not detected`; the hardware entropy source was not considered
   to have passed.
5. Persistent writes, charging, suspend, complete memory, and long-term thermal control were
   unverified. Only a trusted direct USB connection was available; do not expose this to the public Internet.

## How the host logged in at this stage

Run from `${REPO_ROOT}`:

```sh
ssh -F /dev/null -i ${SSH_PRIVATE_KEY} \
  -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=${SSH_KNOWN_HOSTS} \
  -o StrictHostKeyChecking=yes ${DEVICE_USER}@${PHONE_USB_IP}
```

Phone address `${PHONE_USB_IP}/24`; host USB NCM address at this stage `${HOST_USB_IP}/24`.
No phone Internet gateway, NAT, or proxy was configured. DNF CLI/RPM database testing does not
mean the phone could access Internet repositories.

The dedicated test private key existed only in host `${SSH_KEY_DIR}/` (0700), not on the phone,
in documentation, or in the HTTP directory. The public key in the host's known_hosts was read through
the physical USB rescue serial console before handover; host-key verification was not disabled.
Each RAM boot generates fresh SSH host keys, so obtain and pin the public key again through a
trusted serial console.

Before entering Fedora, PID 1 terminated every passwordless rescue shell. The USB gadget was still
named Picasso LTS rescue, but Fedora's serial console was an authenticated getty, no longer a root
shell. The account had no console password; use public-key SSH. `tools/rescue-console.py` is only for
the idle rescue shell before handover, not a Fedora login tool.

## Build and handover process (physical boot requires separate authorization)

1. On the Fedora 44 host, run `tools/mkrootfs-fedora.sh key.pub`. It enters a **Podman rootless user
   namespace** and uses host-native DNF `--installroot` / `--forcearch=aarch64` to build
   `@core` + `fedora-release-server` from signed RPMs. No OCI ARM container or QEMU is needed,
   and the host RPM database is not modified. Ordinary RPM scripts/triggers are skipped;
   the RPM sysusers helper runs natively with `--root` outside the chroot. The script precreates
   usr-merge links so `/lib64` does not become a real directory when filesystem pretrans is skipped.
2. Build the kernel and package it using the matching crDroid boot. At this stage `/init` still defaulted
   to rescue only; it **did not download over the network itself or automatically select a disk root**.
   During the October 26 boot stage, the phone normally rebooted from the old rescue environment
   back into Android, then used ADB reboot bootloader. After checking product/unlocked, only
   `fastboot boot` was executed; no flash/unlock/erase occurred.
3. Host HTTP binds only to the USB address and uses a dedicated directory serving only the rootfs
   gzip and initialization script. **Never use a directory containing SSH private keys as the HTTP root.**
   The phone downloads to `/run` tmpfs, verifies the SHA256 supplied by the host, mounts
   `tmpfs /newroot` (size=3G), extracts with `tar -xzpf`, and removes the compressed archive.
   Peak memory use is far below this device's available amount; no loop image, partition formatting,
   or Android filesystem mount is used.
4. After verifying the script hash, run `tools/fedora-native-init.sh` natively on the phone. It accepts
   only `/newroot` tmpfs with the Fedora Server 44 marker. It creates RPM ghost API mountpoints,
   temporarily binds dev/proc/sys, then runs ldconfig, sysusers, authselect **local**, crypto policies,
   CA trust, SSH keys, SELinux load_policy/setfiles, and sshd -t in sequence. After clearing temporary
   binds, it writes the native-init success marker. An ordinary chroot is used only for this
   initialization stage, not as the final runtime.
5. Obtain the SSH public host key from the serial console, confirm no block-device mounts,
   then explicitly submit:

   ```sh
   printf 'PICASSO_RAMROOT_V1\n' > /run/picasso-ramroot.request
   ```

   PID 1 rechecks tmpfs, the marker, Fedora 44/Server, the systemd executable, and non-symlink API
   directories. Any verification failure preserves rescue and deletes the request. Only after passing
   does it stop all rescue user processes, move API mounts, and
   `exec switch_root /newroot /usr/lib/systemd/systemd`. No passwordless shell crosses into Fedora.
6. Log in using the pinned SSH host key and check PID 1, multi-user, failed units, mounts, memory,
   and temperatures. This round's temporary HTTP server was stopped; SSH and the Fedora RAM
   system were left running.

Ordinary scripts have no implicit permission to execute device commands. First confirm the user
allows reboot/RAM boot; failure does not authorize switching to flashing. Android SELinux was not
modified, and installing Android root was unnecessary. Fedora udev may probe block-device metadata.
No Android filesystem was mounted and no user files/EFS were manually accessed; this must not be
expanded into a claim of “zero reads from all block devices.”

## Pinned evidence

- Kernel boot image at this stage: 32,899,072 bytes, SHA256
  `59784cc401cad3d1b245e8a403b80abd0176e02e9f6891b31daabe9423a1e801`.
- Rootfs gzip actually transferred at this stage, SHA256:
  `${PRIVATE_ROOTFS_SHA256_1}`.
- `out/confirmation-20261027/result.json` records the corresponding hashes, tested results,
  known failures, and evidence-file hashes. The same directory contains the tested image,
  initialization script, serial output, and functional-probe evidence.
  The old `out/fedora-ramtest/result.json` retains the first-round historical results missing
  nftables/ZRAM; it is not overwritten, and pass status from an old image is not inherited.
- Build provenance: `out/fedora-rootfs-build.json`, `out/fedora-packages.txt`,
  `out/fedora-rootfs.sha256`.
- Latest unit tests: 59 total, 58 passed, 1 QEMU applet test skipped by default. Required BusyBox
  applets were queried natively on the phone. The optional emulator test requires explicit
  `PICASSO_RUN_QEMU_TESTS=1` and was not run in this round.

**All Fedora modifications and host keys existed only in RAM and would be lost on shutdown/reboot.**
The persistent system at this stage was still the original Android. A normal reboot from the old rescue
environment back to Android had been observed, but the current Fedora systemd shutdown path had
not undergone a dedicated acceptance test. Persistent installation needs its own partition plan,
backups, and authorization; do not format userdata or dd a tar archive as if it were a disk image.
