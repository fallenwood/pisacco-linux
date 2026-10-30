# Picasso Fedora 持久安装方案（已授权并完成 XFS 重装） / Picasso Fedora Persistent Installation Plan (Authorized; XFS Reinstallation Completed)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录；“当前”等状态按原记录时间理解，反引号中的代码及证据路径相对于仓库根目录。 / Historical stage record; “current” refers to the recorded stage. Code and evidence paths in backticks are relative to the repository root.

## 中文

用户已接受永久删除个人数据和实验性限制，并进一步明确要求：**“使用xfs重新安装fedora”**。

2026-10-27 最终状态：

- `userdata` 已从 ext4 试装重新安装为约 107 GiB 的 XFS Fedora，原个人数据和 Android 已放弃。
- 用户物理进入 fastboot 后，临时启动 XFS 根及 15,285 个静态文件读回通过，才写入 boot。
- boot 完整 128 MiB 读回及第一次正常重启/文件保留通过，才清空 super 的全部 8.5 GiB。
- 第二次正常重启、文件保留、boot/受保护分区/GPT 校验通过；GPT、DTBO、recovery、vbmeta 不变。
- 当前保留 Fedora USB SSH，不是仍等待 fastboot 或运行 tmpfs；功能和安全限制仍在。

最终结论、登录及恢复边界见 [INSTALL-XFS.md](INSTALL-XFS.md)，证据为
`out/install-xfs-20261027/result.json`（目录 0700）；先前 ext4 试装证据保留在
`out/install-20261027/`，不混作 XFS 硬件验收。

## 已确认的物理布局

设备为 Redmi K30 5G / Picasso，非 A/B。以下设备名仅是此次 Linux 的观察值；实际执行前
必须再次由唯一 GPT PARTNAME、PARTUUID 和大小定位，不能仅按 `/dev/sdaNN` 猜测。

| 用途 | GPT PARTNAME | 本次设备名 | 精确大小 | PARTUUID |
| --- | --- | --- | ---: | --- |
| Fedora 根（已为 XFS） | userdata | /dev/sda34 | 114,936,492,032 B（约 107.04 GiB） | ${PARTUUID_USERDATA} |
| 启动内核（已写入） | boot | /dev/sde55 | 134,217,728 B（128 MiB） | ${PARTUUID_BOOT} |
| Android 系统（已清零） | super | /dev/sda33 | 9,126,805,504 B（8.5 GiB） | ${PARTUUID_SUPER} |
| 保留恢复入口 | recovery | /dev/sda29 | 134,217,728 B | ${PARTUUID_RECOVERY} |
| 保留 ABL 使用的 overlay | dtbo | /dev/sde45 | 33,554,432 B | ${PARTUUID_DTBO} |

不调整 GPT，不将整个 UFS LUN 当作系统盘覆盖。不执行全盘 erase、blkdiscard 或固件降级。

## 已按顺序完成的破坏性范围（历史执行方案，不是待执行命令）

1. 将 **userdata** 重新格式化为 **XFS**，安装持久 Fedora rootfs。
   - 内核内置 XFS、POSIX ACL 和 quota；显式 `rootfstype=xfs`，首次只读挂载使用
     `ro,norecovery` 禁止日志回放，校验 V2 安装标记、文件系统类型及 PARTUUID 后才读写。
   - XFS 使用 xfsprogs 的 `lts_6.18` 兼容配置、4 KiB 扇区/块；fstab 不启用 discard，
     `fsck` pass 为 0。不承诺能缩小文件系统，也不把元数据 CRC 说成文件内容校验和。
   - 主机仅用受限 loop 挂载构造普通镜像文件（nodev/nosuid/noexec），不执行 ARM 程序；
     复用已原生初始化的快照，增加签名验证的 aarch64 XFS RPM，不绕过 tmpfs 初始化保护。
   - Android 的应用、照片、下载、账号数据及其他用户数据会丢失。
   - 此处是“放弃个人数据”的安装，不是无损迁移，也不是取证级安全擦除承诺。
2. 用新建的持久根镜像替换 **boot**。
   - 当前已测试的 `59784cc4…` 镜像默认是救援，不能直接当成自动磁盘启动成品。
   - 新镜像必须用明确的 root PARTUUID，保持 stock 12-DTB blob 和现有 dtbo。
   - 先通过 `fastboot boot` 临时验证磁盘根，再允许写 boot；新字节不能继承 RAM 镜像验收。
3. 持久启动及重启后文件保留验证通过，才清除 **super** 中的 Android 系统内容。
   - 保留 super 的 GPT 槽位，不为回收额外 8.5 GiB 冒险改分区。
   - 在这一步之前保留原系统内容，避免同时破坏所有恢复线索。

**明确保留：** bootloader / XBL / ABL、TrustZone、RPMh/AOP、基带/DSP 等设备固件、
DTBO、vbmeta 系列、recovery、persist/persistbak、modemst1/2、fsg/fsc、keystore、FRP、
设备校准与其余未知分区。这里“删除 Android”不表示删除手机启动链和 OEM 固件。
未列入三项覆盖范围的分区不顺手擦除。若 boot 验证提示 AVB 问题，停止诊断，不能临时
扩展成盲刷 vbmeta 或解锁命令。

## 当前已保存的恢复材料

`out/install-preflight-20261027/` 权限 0700：

- `storage-readonly.json`：本机 GPT/sysfs 布局、当前挂载和温度。
- `system-recovery-backup.tar`：302,817,280 字节。
- SHA256：`${PRIVATE_RECOVERY_ARCHIVE_SHA256}`。
- 备份 6 个 LUN 的保护 MBR、主/备 GPT header 和 partition entries；header/table CRC 验证，
  主/备 entries 一致。
- 完整原始 boot、DTBO、recovery、5 个 vbmeta 分区，共 38 个成员文件，逐个核对 SHA256。
- 备份中的原 boot 完整分区 hash 为 `f82a7bf0…`，DTBO 为 `6e285dbd…`，与安装前测量一致。
  当前 boot 已是 Fedora，完整分区 hash 为 `312e42f3…`，不能再与原 boot 混称。
  使用这份真实 boot 备份，而不是把 ROM 包里 padding 不同的 boot 当作同一分区。

**这不是个人数据备份，也不是整机备份。** 该备份不包含 userdata、super、EFS 或 persist
的内容。已有 crDroid ROM ZIP 可作重装材料，但回到 Android 仍可能需要重装/清数据。
恢复入口材料不等于已验证所有恢复步骤，更不能保证恢复被格式化的个人文件。

## 执行记录与仍未解除的限制

- 个人数据放弃及 XFS 重装授权已取得；不再等待原来的授权，但不扩大三项分区范围。
- 07:55 CST 左右曾重新进入 Android 读到 99%、4.413 V、30.1°C、外部供电/充电状态正常，
  证据在 `out/install-20261027/battery-preflight.json`。这比旧基线新，但仍不是实时 Linux
  电量遥测；`/sys/class/power_supply` 仍为空。XFS 覆盖前 fastboot 另读到 4297 mV，
  百分比/状态查询不支持；未知项没有伪装成已测值。
- 新 XFS boot SHA256：`81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c`。
  完成独立 XFS 真机验收后才绑定新结果；准备阶段 false 的 manifest 作为历史证据保留。
- XFS sparse SHA256：`${PRIVATE_ROOT_IMAGE_SHA256}`，
  文件 574,804,228 B，逻辑长度 114,936,492,032 B。原图及还原图均通过 `xfs_repair -n`，
  完整逻辑镜像逐字节相同；镜像包含私有 SSH host key，只保存在受限目录，不能公开分发。
- 最终测试 78 项，77 通过、1 可选 QEMU BusyBox 测试跳过；实际 XFS 启动、
  15,285 个静态文件及权限、原分区/GPT 保留、两次正常重启和 filecap 持久化均通过。
- 已有一次 ext4 写入/读回验证不等于 XFS、长期 UFS 写入、掉电或耐久验收。正常 boot
  启动、文件 fsync 及重启保留验证通过后才允许清除 super；异常立即停止。

## 用户必须知道的运行限制

当前是 headless Fedora：主要通过 USB SSH 使用。Wi-Fi、原生显示/GPU/触摸、音频、
蜂窝等未验收；电池/充电驱动、闭环温控和 watchdog 也未完成，不能作为日常手机或
无人值守充电服务器。SELinux Permissive，尚无互联网/DNS 出口；旧 RAM 阶段的 DNF
makecache 失败证据保留，最终 snapshot running 不等于已解决 DNF 互联网刷新。
持久安装不会自动修复这些问题。内存原始布局、启动对齐/PSCI/UFS 告警也仍在。

## English

The user accepted permanent deletion of personal data and the experimental limitations, then
explicitly requested: **“使用xfs重新安装fedora” (“Reinstall Fedora using xfs”).**

Final state on 2026-10-27:

- `userdata` had been reinstalled from the ext4 trial installation to approximately 107 GiB of
  XFS-backed Fedora; the original personal data and Android had been relinquished.
- After the user physically entered fastboot, the XFS root was temporarily booted and all 15,285
  static files passed readback verification before boot was written.
- The full 128 MiB boot readback, first normal reboot, and file retention passed before all 8.5 GiB
  of super was cleared.
- A second normal reboot, file retention, and boot/protected-partition/GPT verification passed;
  GPT, DTBO, recovery, and vbmeta remained unchanged.
- Fedora USB SSH was left available; this was no longer awaiting fastboot or running from tmpfs.
  Functional and safety limitations remained.

See [INSTALL-XFS.md](INSTALL-XFS.md) for the final conclusion, login, and recovery boundaries.
Evidence is `out/install-xfs-20261027/result.json` in a directory with permissions 0700.
Earlier ext4 trial-installation evidence remains in `out/install-20261027/` and must not be treated
as XFS hardware acceptance.

## Confirmed physical layout

The device is a Redmi K30 5G / Picasso, non-A/B. Device names below were observations from this
Linux session only. Before actual execution, identify partitions again by unique GPT PARTNAME,
PARTUUID, and size; never guess solely from `/dev/sdaNN`.

| Purpose | GPT PARTNAME | Device name in this session | Exact size | PARTUUID |
| --- | --- | --- | ---: | --- |
| Fedora root, now XFS | userdata | /dev/sda34 | 114,936,492,032 B, approximately 107.04 GiB | ${PARTUUID_USERDATA} |
| Boot kernel, written | boot | /dev/sde55 | 134,217,728 B, 128 MiB | ${PARTUUID_BOOT} |
| Android system, zeroed | super | /dev/sda33 | 9,126,805,504 B, 8.5 GiB | ${PARTUUID_SUPER} |
| Retained recovery entry point | recovery | /dev/sda29 | 134,217,728 B | ${PARTUUID_RECOVERY} |
| Retained overlay used by ABL | dtbo | /dev/sde45 | 33,554,432 B | ${PARTUUID_DTBO} |

Do not modify GPT or overwrite an entire UFS LUN as a system disk. Do not perform whole-disk erase,
blkdiscard, or firmware downgrades.

## Destructive scope completed in order (historical execution plan, not pending commands)

1. Reformat **userdata** as **XFS** and install the persistent Fedora rootfs.
   - The kernel includes XFS, POSIX ACL, and quota. Explicit `rootfstype=xfs` is used; the initial
     read-only mount uses `ro,norecovery` to prohibit log replay. Read/write access is allowed only
     after verifying the V2 installation marker, filesystem type, and PARTUUID.
   - XFS uses the xfsprogs `lts_6.18` compatibility profile with 4 KiB sectors/blocks. fstab does
     not enable discard; the `fsck` pass is 0. Filesystem shrinking is not promised, and metadata
     CRCs are not described as file-content checksums.
   - The host constructs a regular image file using only a restricted loop mount
     (nodev/nosuid/noexec), without executing ARM programs. It reuses the natively initialized
     snapshot and adds signature-verified aarch64 XFS RPMs, without bypassing the tmpfs
     initialization safeguard.
   - Android applications, photos, downloads, account data, and other user data will be lost.
   - This installation “relinquishes personal data”; it is neither a lossless migration nor a promise
     of forensic-grade secure erasure.
2. Replace **boot** with the newly constructed persistent-root boot image.
   - The tested `59784cc4…` image defaults to rescue and cannot directly be treated as a finished
     automatic disk-boot image.
   - The new image must specify the root PARTUUID and preserve the stock 12-DTB blob and
     existing dtbo.
   - Temporarily verify the disk root through `fastboot boot` before permitting boot writes.
     New bytes cannot inherit RAM-image acceptance.
3. Clear Android system contents in **super** only after persistent boot and post-reboot file
   retention have passed verification.
   - Retain super's GPT slot rather than risk repartitioning to reclaim another 8.5 GiB.
   - Keep the original system contents until this step to avoid destroying every recovery clue
     simultaneously.

**Explicitly retained:** bootloader / XBL / ABL, TrustZone, RPMh/AOP, baseband/DSP and other device
firmware, DTBO, the vbmeta family, recovery, persist/persistbak, modemst1/2, fsg/fsc, keystore, FRP,
device calibration, and all other unknown partitions. “Deleting Android” here does not mean deleting
the phone's boot chain or OEM firmware. Partitions outside the three overwrite targets must not be
erased incidentally. If boot verification reports an AVB problem, stop for diagnosis; do not broaden
the operation into blind vbmeta flashing or unlocking commands.

## Recovery materials saved at this stage

`out/install-preflight-20261027/`, permissions 0700:

- `storage-readonly.json`: this device's GPT/sysfs layout, current mounts, and temperatures.
- `system-recovery-backup.tar`: 302,817,280 bytes.
- SHA256: `${PRIVATE_RECOVERY_ARCHIVE_SHA256}`.
- Backups of protective MBRs, primary/backup GPT headers, and partition entries for 6 LUNs;
  header/table CRCs verified, with primary and backup entries matching.
- Complete original boot, DTBO, recovery, and 5 vbmeta partitions: 38 member files in total,
  with SHA256 checked individually.
- The backed-up original boot full-partition hash is `f82a7bf0…`, and DTBO is `6e285dbd…`,
  matching pre-installation measurements. The installed boot is now Fedora, with full-partition
  hash `312e42f3…`, and must not be conflated with the original boot. Use this actual boot backup
  rather than treating the ROM package's differently padded boot as the same partition.

**This is neither a personal-data backup nor a full-device backup.** It does not include userdata,
super, EFS, or persist contents. The available crDroid ROM ZIP can serve as reinstallation material,
but returning to Android may still require reinstalling/clearing data. Recovery-entry materials do not
mean all recovery steps have been verified, much less guarantee recovery of formatted personal files.

## Execution record and remaining limitations

- Authorization to relinquish personal data and reinstall using XFS was obtained. The original
  authorization was no longer pending, but the scope remained the three specified partitions.
- At approximately 07:55 CST, the phone re-entered Android and reported 99%, 4.413 V, 30.1°C,
  and normal external-power/charging status, recorded in
  `out/install-20261027/battery-preflight.json`. This was newer than the old baseline but still
  not live Linux battery telemetry; `/sys/class/power_supply` remained empty. Before the XFS
  overwrite, fastboot separately reported 4297 mV; percentage/status queries were unsupported.
  Unknown values were not presented as measured.
- New XFS boot SHA256:
  `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c`.
  New results were bound only after independent XFS hardware acceptance; the preparation-stage
  manifest containing false was retained as historical evidence.
- XFS sparse SHA256:
  `${PRIVATE_ROOT_IMAGE_SHA256}`,
  file size 574,804,228 B, logical length 114,936,492,032 B. Both the original and reconstructed
  images passed `xfs_repair -n`, and the entire logical images were byte-for-byte identical.
  The image contains private SSH host keys and is stored only in a restricted directory;
  it must not be publicly distributed.
- Final tests: 78 total, 77 passed, 1 optional QEMU BusyBox test skipped. Actual XFS boot,
  15,285 static files and their permissions, original-partition/GPT preservation, two normal reboots,
  and filecap persistence all passed.
- A prior ext4 write/readback check does not constitute XFS, long-term UFS write, power-loss,
  or endurance acceptance. Clearing super was allowed only after normal boot startup, file fsync,
  and reboot retention passed; any abnormality required an immediate stop.

## Operating limitations the user must know

This was headless Fedora, used mainly through USB SSH. Wi-Fi, native display/GPU/touch, audio,
cellular, and other features had not passed acceptance; battery/charging drivers, closed-loop thermal
control, and watchdog were also unfinished. It was unsuitable as a daily-use phone or unattended
charging server. SELinux was Permissive, with no Internet/DNS egress. Evidence of the old RAM-stage
DNF makecache failure was retained; a final running snapshot did not mean DNF Internet refresh had
been resolved. Persistent installation does not automatically fix these issues. The original memory
layout and boot-alignment/PSCI/UFS warnings also remained outstanding.
