# Picasso：Fedora 44 XFS 持久安装完成（实验性，原#8阶段） / Picasso: Fedora 44 XFS Persistent Installation Completed (Experimental, Original #8 Stage)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录；“当前”等状态按原记录时间理解，反引号中的代码及证据路径相对于仓库根目录。 / Historical stage record; “current” refers to the recorded stage. Code and evidence paths in backticks are relative to the repository root.

## 中文

**后续用户授权把已验证的wifi2 #10写入boot，并通过正常重启；XFS根和原文件保留，不是重新格式化。
当前默认#10、精确新哈希及#8回退边界见 [WIFI-INSTALL.md](WIFI-INSTALL.md)。以下为原#8安装时的历史快照。**

2026-10-27，用户先接受删除全部个人数据和实验性限制，再明确要求 **“使用xfs重新安装fedora”**。
本机已完成安装；不是仍运行 tmpfs，也不需要每次由电脑执行 `fastboot boot`。

## 已完成并在真机验证

- Redmi K30 5G / Picasso / SM7250 / 6 GB；内核 `6.18.58-picasso-lts #8`。
- Fedora Server 44 minimal aarch64：真正 systemd PID 1，虚拟化检测 `none`，277 个软件包、
  278 条 RPM 记录；8 CPU 在线。最终快照 MemAvailable 约 4.89 GiB，不是内存完整性验收。
- `userdata` 为 XFS 根：约 107 GiB，最终快照可用约 104.3 GiB。
- 临时启动 XFS 根后，15,285 个静态文件的长度、SHA256、UID/GID 和权限全部读回一致。
- 写入 `boot` 后校验整个 128 MiB；第一次**正常重启**成功，256 KiB `fsync` 测试文件保留。
- 清空 `super` 的全部 8.5 GiB，缓存 flush 后完整物理读回全零；然后第二次正常重启成功。
  第二次重启再次校验静态文件、测试文件、boot、受保护分区及 GPT。两次均未使用 fastboot boot。
- 在最终新镜像上重新执行 firewalld USB 阻断→放行→阻断、32 MiB ZRAM 换出/读回测试，均通过；
  临时端口、规则和监听进程已清理。ZRAM 为 1 GiB zstd，无磁盘后备/writeback。
- 原生 SELinux 标签初始化通过；省略主机安全 xattr 导致的 7 个 RPM file capabilities 已在手机
  按 RPM 元数据恢复并 `setcap -v` 验证，另一次重启后再次验证保留。未来镜像构造脚本已补齐此步骤。
- 最终采集时 systemd `running`，没有失败 unit；这**不表示已经解决无互联网、DNS、NTP 的限制**。
  未执行 reset-failed，也没有为掩盖问题停用服务。原先 RAM 阶段的 DNF 失败证据继续保留。
- 78 项测试：77 通过，1 个可选 QEMU BusyBox 测试跳过。实际构建和手机运行均未使用 QEMU。

## 实际写入范围

执行时均由唯一 PARTNAME、PARTUUID 和精确长度确认，不把 `/dev/sd*` 编号作为唯一身份。

| 分区 | PARTUUID | 字节数 | 最终用途 |
| --- | --- | ---: | --- |
| userdata | ${PARTUUID_USERDATA} | 114936492032 | Fedora XFS 根；先前 ext4 试装已被替换 |
| boot | ${PARTUUID_BOOT} | 134217728 | Fedora 内核/内建 initramfs，镜像后补零 |
| super | ${PARTUUID_SUPER} | 9126805504 | 全部清零，不另改 GPT 回收容量 |

**Android 个人数据和系统已放弃。** 这是普通安装/逻辑清空，不承诺 UFS 物理介质的取证级安全擦除。

没有重分区、整 LUN 覆盖、全盘 discard、固件降级、解锁或 vbmeta 写入。六个 LUN 的保护 MBR、
主备 GPT header 和 entries 与备份逐字节一致。DTBO、recovery 和五个 vbmeta 分区的完整 SHA256
仍与备份相同。启动链、基带/DSP、校准/EFS、persist 等其余分区不在安装写入范围；不要把这一
写入范围约束夸大为已为所有固件做了全量内容备份/读回。

## XFS 与启动

- XFS 内置于内核，包含 POSIX ACL、quota；当前根挂载未启用 quota。
- xfsprogs 7.1.1，`lts_6.18` mkfs 配置，扇区和块均为 4096 B。
- 显式内核参数：`root=PARTUUID=${PARTUUID_USERDATA} rootfstype=xfs`。
- initramfs 先 `ro,norecovery` 挂载，禁止校验阶段日志回放；核验 V2 安装标记、文件系统类型、
  PARTUUID、Fedora Server 44 和原生初始化标记，才切换读写并交给 systemd。失配则进入救援。
- fstab：`PARTUUID=${PARTUUID_USERDATA} / xfs defaults,noatime 0 0`。
  不启用 discard，不自动探测/挂载其他 Android 分区。XFS 不能原地缩小。
- 保留 ROM 的完整 12-DTB blob 供 ABL 使用，DTBO 未写入；主线 runtime DTB 未替换成 vendor merged DT。

## 当前产物与证据

证据目录：`out/install-xfs-20261027/`，权限 0700。`result.json` 是最终结论；
`preparation-status.json`、`boot-xfs-manifest.json` 是准备阶段快照，不是最终状态。
最终打包状态为 `out/boot-manifest.json` 和 `out/install-xfs-20261027/boot-installed-manifest.json`。

| 产物 | SHA256 |
| --- | --- |
| boot 镜像，33,820,672 B | `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c` |
| boot 完整分区，含零 padding | `312e42f3c590faa3c7988b8e02e15f7bee1952dee785a0d0acb218f088a1a696` |
| 初始 XFS sparse 镜像，574,804,228 B | `${PRIVATE_ROOT_IMAGE_SHA256}` |
| 运行内核配置 | `78d5a451ed01af58807e1add0cc42506255b5fd03bd46e974a7db595b1813589` |
| 最终 result.json | `43e1690717251494b433eab417e3e5d7e11438389a0bee612f1b1c897f524206` |

原始 XFS 镜像和 sparse 还原图均通过 `xfs_repair -n`，整个 114,936,492,032 B 逻辑镜像相同。
镜像包括手机的私有 SSH host keys，**不可公开分发**。原始镜像与运行根的原生 filecap、SELinux
标签、时间种子、日志和测试文件等运行期调整分开记录，不把初始文件摘要说成整个活动文件系统摘要。

## USB SSH 登录

在 `${REPO_ROOT}` 下：

```sh
ssh -F /dev/null -i "${SSH_PRIVATE_KEY}" \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile="${SSH_KNOWN_HOSTS}" \
  -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
  "${DEVICE_USER}@${PHONE_USB_IP}"
```

账号 `${DEVICE_USER}`，可 `sudo -n`。Host key 原先由物理 USB 串口固定，并与构造镜像的公钥比较一致；
没有关闭 host-key 检查。不要公开客户端私钥或镜像内的 host 私钥。

主机 USB 地址为 `${HOST_USB_IP}/24`，MAC `${USB_HOST_MAC}`。若 USB 重枚举或主机重启后地址丢失，
先识别该 MAC 对应的接口；本次为 `${HOST_USB_INTERFACE}`。只对核对后的 USB 接口临时取消主机 NetworkManager
管理并配置地址，避免其 DHCP 清除手工地址；不能误改 Wi-Fi，也没有配置 NAT/默认路由。

```sh
IF="${HOST_USB_INTERFACE}"
[ "$(cat "/sys/class/net/$IF/address")" = "${USB_HOST_MAC}" ] || exit 1
sudo nmcli device set "$IF" managed no
sudo ip link set "$IF" up
sudo ip addr replace "${HOST_USB_IP}/24" dev "$IF"
```

## 恢复材料与限制

原 boot/recovery/DTBO/vbmeta 及六个 LUN GPT 备份位于 `out/install-preflight-20261027/`，
302,817,280 B tar 的 SHA256 为 `${PRIVATE_RECOVERY_ARCHIVE_SHA256}`。
这不是个人数据或整机备份，也不含 super/EFS/persist；恢复 Android 可能需要完整 ROM 重装和重新
格式化 userdata，不能认为只恢复原 boot 就能恢复被删除的 Android/个人文件。恢复步骤未全部验收。

仍是 headless 实验系统：显示/GPU/触摸、Wi-Fi、音频、蜂窝、相机等未验收；Linux 电池/充电遥测为空。
本次 fastboot 读取 4297 mV，电量百分比不提供；不能用旧 99% 记录声称当前电量或充电正常。
全 super 读回 SHA256 后观测到 46.8°C，随后降到 40°C 以下；最终快照 34.4–36.8°C，
**不是闭环温控、长期压力或充电安全验收**。watchdog、完整内存/原始 ABL RAM map、关机、挂起、
掉电恢复和耐久仍未验收；对齐/PSCI/UFS/TRNG 告警没有消失。SELinux 为 Permissive。

无互联网/DNS 出口和持续 NTP；校时只来自可信 USB 主机，并保存 PID 1 的下次启动时间下限，
没有写 RTC。启动时回退到保存时间、journal 因时钟回退轮转仍是已观察到的限制。
不能当作日常手机、公网生产或无人值守充电服务器。

## English

**The user subsequently authorized writing the verified wifi2 #10 to boot, and a normal reboot passed.
The XFS root and original files were retained; this was not a reformat. For the default #10, exact new
hashes, and #8 fallback boundaries at that later stage, see [WIFI-INSTALL.md](WIFI-INSTALL.md).
What follows is the historical snapshot from the original #8 installation.**

On 2026-10-27, the user first accepted deletion of all personal data and the experimental limitations,
then explicitly requested **“使用xfs重新安装fedora” (“Reinstall Fedora using xfs”).**
Installation on this device was completed; it was no longer running from tmpfs and no longer needed
the computer to execute `fastboot boot` every time.

## Completed and verified on the actual phone

- Redmi K30 5G / Picasso / SM7250 / 6 GB; kernel `6.18.58-picasso-lts #8`.
- Fedora Server 44 minimal aarch64: real systemd PID 1, virtualization detection `none`,
  277 packages, 278 RPM records, and 8 CPUs online. Final snapshot MemAvailable was approximately
  4.89 GiB; this was not memory-integrity acceptance.
- `userdata` was the XFS root: approximately 107 GiB, with approximately 104.3 GiB available
  in the final snapshot.
- After temporarily booting the XFS root, the lengths, SHA256, UID/GID, and permissions of all
  15,285 static files matched on readback.
- After writing `boot`, the entire 128 MiB was verified. The first **normal reboot** succeeded,
  retaining the 256 KiB `fsync` test file.
- All 8.5 GiB of `super` was cleared; after a cache flush, full physical readback was all zero.
  The second normal reboot then succeeded. Static files, the test file, boot, protected partitions,
  and GPT were verified again after that reboot. Neither reboot used fastboot boot.
- On the final new image, firewalld USB block→allow→block and 32 MiB ZRAM swap-out/readback
  tests were repeated and passed. Temporary ports, rules, and listener processes were cleaned up.
  ZRAM was 1 GiB zstd, with no disk backing/writeback.
- Native SELinux label initialization passed. Seven RPM file capabilities omitted because host
  security xattrs were excluded were restored on the phone from RPM metadata and verified using
  `setcap -v`; another reboot verified their retention. The future image-construction script was
  updated with this step.
- At final collection, systemd was `running` with no failed unit; this **did not mean the lack of
  Internet, DNS, or NTP was resolved**. reset-failed was not executed and services were not disabled
  to conceal problems. Earlier RAM-stage DNF failure evidence remained.
- 78 tests: 77 passed, 1 optional QEMU BusyBox test skipped. Neither the actual build nor the
  phone runtime used QEMU.

## Actual write scope

At execution time, each partition was confirmed by unique PARTNAME, PARTUUID, and exact length;
`/dev/sd*` numbering was not used as its sole identity.

| Partition | PARTUUID | Bytes | Final purpose |
| --- | --- | ---: | --- |
| userdata | ${PARTUUID_USERDATA} | 114936492032 | Fedora XFS root; replaced the earlier ext4 trial installation |
| boot | ${PARTUUID_BOOT} | 134217728 | Fedora kernel/built-in initramfs, zero-padded after the image |
| super | ${PARTUUID_SUPER} | 9126805504 | Fully zeroed; GPT was not separately changed to reclaim capacity |

**Android personal data and the system were relinquished.** This was an ordinary installation/logical
clearing operation, not a promise of forensic-grade secure erasure of the UFS physical medium.

No repartitioning, whole-LUN overwrite, whole-disk discard, firmware downgrade, unlocking, or vbmeta
write occurred. Protective MBRs and primary/backup GPT headers and entries for all six LUNs matched
the backups byte-for-byte. Full SHA256 of DTBO, recovery, and five vbmeta partitions still matched
the backups. The boot chain, baseband/DSP, calibration/EFS, persist, and other partitions were outside
the installation write scope; do not exaggerate that constraint into a claim that all firmware contents
had been fully backed up or read back.

## XFS and boot

- XFS was built into the kernel, including POSIX ACL and quota; the root mount did not enable quota.
- xfsprogs 7.1.1, `lts_6.18` mkfs profile, sectors and blocks both 4096 B.
- Explicit kernel parameters:
  `root=PARTUUID=${PARTUUID_USERDATA} rootfstype=xfs`.
- initramfs first mounts using `ro,norecovery`, prohibiting log replay during verification. It verifies
  the V2 installation marker, filesystem type, PARTUUID, Fedora Server 44, and native-initialization
  marker before switching to read/write and handing over to systemd. A mismatch enters rescue.
- fstab: `PARTUUID=${PARTUUID_USERDATA} / xfs defaults,noatime 0 0`.
  discard is not enabled; other Android partitions are not automatically detected or mounted.
  XFS cannot be shrunk in place.
- The ROM's complete 12-DTB blob was retained for ABL; DTBO was not written. The mainline
  runtime DTB was not replaced with the merged vendor DT.

## Artifacts and evidence at this stage

Evidence directory: `out/install-xfs-20261027/`, permissions 0700. `result.json` is the final conclusion;
`preparation-status.json` and `boot-xfs-manifest.json` are preparation-stage snapshots, not the final state.
Final packaging status is in `out/boot-manifest.json` and
`out/install-xfs-20261027/boot-installed-manifest.json`.

| Artifact | SHA256 |
| --- | --- |
| Boot image, 33,820,672 B | `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c` |
| Complete boot partition, including zero padding | `312e42f3c590faa3c7988b8e02e15f7bee1952dee785a0d0acb218f088a1a696` |
| Initial XFS sparse image, 574,804,228 B | `${PRIVATE_ROOT_IMAGE_SHA256}` |
| Running kernel configuration | `78d5a451ed01af58807e1add0cc42506255b5fd03bd46e974a7db595b1813589` |
| Final result.json | `43e1690717251494b433eab417e3e5d7e11438389a0bee612f1b1c897f524206` |

Both the original XFS image and the reconstructed sparse image passed `xfs_repair -n`; the entire
114,936,492,032 B logical images were identical. The image contains the phone's private SSH host keys
and **must not be publicly distributed**. Runtime changes to native filecaps, SELinux labels, time seed,
logs, test files, and other items on the running root were recorded separately from the original image.
The initial file digests are not described as a digest of the entire active filesystem.

## USB SSH login

From `${REPO_ROOT}`:

```sh
ssh -F /dev/null -i "${SSH_PRIVATE_KEY}" \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile="${SSH_KNOWN_HOSTS}" \
  -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
  "${DEVICE_USER}@${PHONE_USB_IP}"
```

Account `${DEVICE_USER}`, with `sudo -n` available. The host key was originally pinned through the physical
USB serial console and matched the public key in the constructed image; host-key checking was not
disabled. Do not disclose the client private key or the image's private host keys.

The host USB address was `${HOST_USB_IP}/24`, MAC `${USB_HOST_MAC}`. If the address disappears after USB
re-enumeration or a host reboot, first identify the interface with that MAC; it was `${HOST_USB_INTERFACE}` in this
session. Temporarily disable host NetworkManager management and configure the address only on
that verified USB interface, preventing DHCP from clearing the manual address. Do not accidentally
modify Wi-Fi; NAT/default routes were not configured.

```sh
IF="${HOST_USB_INTERFACE}"
[ "$(cat "/sys/class/net/$IF/address")" = "${USB_HOST_MAC}" ] || exit 1
sudo nmcli device set "$IF" managed no
sudo ip link set "$IF" up
sudo ip addr replace "${HOST_USB_IP}/24" dev "$IF"
```

## Recovery materials and limitations

Original boot/recovery/DTBO/vbmeta and six-LUN GPT backups are in `out/install-preflight-20261027/`.
The 302,817,280 B tar has SHA256
`${PRIVATE_RECOVERY_ARCHIVE_SHA256}`.
This is not a personal-data or full-device backup and does not include super/EFS/persist.
Restoring Android may require a full ROM reinstall and reformatting userdata; merely restoring the
original boot cannot be assumed to restore deleted Android/personal files. Not all recovery steps
had passed acceptance.

This remained a headless experimental system: display/GPU/touch, Wi-Fi, audio, cellular, cameras,
and other features were unaccepted; Linux battery/charging telemetry was empty. This session's
fastboot read reported 4297 mV, with no percentage available; the old 99% record cannot establish
current battery level or normal charging. After full super readback SHA256, 46.8°C was observed,
followed by cooling below 40°C; the final snapshot was 34.4–36.8°C. **This was not acceptance of
closed-loop thermal control, long-term stress behavior, or charging safety.** watchdog, complete
memory/original ABL RAM map, shutdown, suspend, power-loss recovery, and endurance remained
unaccepted; alignment/PSCI/UFS/TRNG warnings had not disappeared. SELinux was Permissive.

There was no Internet/DNS egress or continuous NTP. Time came only from the trusted USB host,
and a lower bound for PID 1's next boot time was saved; the RTC was not written. Falling back to
saved time at boot and journal rotation caused by the clock moving backward remained observed
limitations. This was not suitable as a daily-use phone, public-Internet production system, or
unattended charging server.
