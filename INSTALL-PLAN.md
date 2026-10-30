# Picasso Fedora 持久安装方案（已授权并完成 XFS 重装）

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
| Fedora 根（已为 XFS） | userdata | /dev/sda34 | 114,936,492,032 B（约 107.04 GiB） | 32684d05-1c3b-836e-c936-7d4638bf1be9 |
| 启动内核（已写入） | boot | /dev/sde55 | 134,217,728 B（128 MiB） | 4aadcdf3-3aad-3318-a158-46642b851943 |
| Android 系统（已清零） | super | /dev/sda33 | 9,126,805,504 B（8.5 GiB） | f045b7f2-f351-5ead-1c36-47aefbfa6e16 |
| 保留恢复入口 | recovery | /dev/sda29 | 134,217,728 B | bcc905f9-4a28-e11f-b627-db9ff3235a7e |
| 保留 ABL 使用的 overlay | dtbo | /dev/sde45 | 33,554,432 B | 3bed3992-b3d6-771c-70af-40ffcf622fa3 |

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
- SHA256：`319051e3cdb5d6d050a2c6096d536b2a4960325e6eb81cda55ae8de806b184d4`。
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
- XFS sparse SHA256：`9b83521354c27f181042b8d053ad72deb055563cba29479a1a6f479707adfa54`，
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
