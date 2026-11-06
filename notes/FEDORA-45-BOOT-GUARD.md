# Fedora 45 启动拒绝诊断 / Fedora 45 Boot-Guard Refusal

> 2026-11-06 UTC 只读诊断快照；未修复或授权重放。代码及 `out/` 路径相对于仓库根目录，
> 同级文档链接相对于 `notes/`。私有网络、主机、分区与会话标识不公开。
> Initial read-only diagnostic snapshot dated 2026-11-06 UTC; neither a repair
> nor replay authorization. Code and `out/` paths are repository-root-relative;
> peer links are relative to `notes/`. Private network, host, partition and
> session IDs are withheld.

最新阶段 / Latest phase：另按新授权修复 kmscon/getty tty1 冲突及实例别名，
新增一次正常重启后屏幕/Wi-Fi 均自启动通过，running/零 failed；监管稳定性仍未根治。
见 [屏幕自启动修复](FEDORA-45-SCREEN-AUTOSTART.md)。下文各旧状态保留为阶段快照。
/ A later explicit grant fixed kmscon/getty tty1 conflict/instance alias and
verified screen/Wi-Fi autostart after one additional normal reboot, running/zero
failed. Regulatory stability remains unresolved. See
[screen-autostart repair](FEDORA-45-SCREEN-AUTOSTART.md); older states below remain staged snapshots.

此前普通重启阶段 / Earlier normal-reboot stage：在后续明确的一次“正常重启”授权下，永久引导及 Wi-Fi 自启动
通过；新启动 running、零 failed，屏幕未自启动，已手动恢复但未修复自启动。
见 [普通重启验收](FEDORA-45-NORMAL-REBOOT.md)。此前“未重启、degraded、仅临时”
均为各阶段快照，不是本阶段留置状态。
/ A later explicit one-normal-reboot grant verified permanent boot and Wi-Fi
autostart. New boot is running with zero failed units; screen failed to autostart
and was manually restored, not fixed. See [normal-reboot acceptance](FEDORA-45-NORMAL-REBOOT.md).
Unverified reboot, degraded and temporary-only below belong to earlier stages.

此前永久安装阶段 / Earlier permanent-installation phase：另一次明确授权后，屏幕/Wi-Fi 原生验收、真实音量上亮屏及
用户终端显示确认通过，随后仅写 boot 并完成全分区独立直接读回，恢复两服务。
两个旧 RMTFS 辅助进程退出租约超时失败保留，整体为 degraded；未新增普通重启。
详见 [永久安装与功能验收](FEDORA-45-INSTALL-ACCEPTANCE.md)。下文“永久 boot 未改、
功能关闭、NTP 未同步”均为此前阶段快照，不是新阶段留置状态。
/ Under a separate later explicit grant, native screen/Wi-Fi acceptance, real
volume-UP wake and operator terminal confirmation passed; write only boot, fully
independently direct-read back and restore both services. Two historical RMTFS
exit-lease failures remain, making global state degraded. No new normal reboot.
See [permanent installation and features](FEDORA-45-INSTALL-ACCEPTANCE.md).
Unchanged boot, inhibited features and unsynchronized NTP below are earlier snapshots.

此前临时启动阶段 / Earlier temporary-boot stage: 用户回复“继续”，授权准备修复候选并受控临时启动，不授权永久写 boot。
随后用户确认已进入原厂 Fastboot，精确候选已成功临时启动 Fedora 45，USB SSH 和
基本系统/提前降温验收通过。仍未写永久 boot，四个实验功能继续关闭；再重启仍会回到
旧 44 专用引导。各阶段与失败见下文；后续 RW 挂载不属于此前只读诊断。
/ “Continue” authorized candidate preparation and controlled temporary boot, not
permanent boot writing. After confirmed physical stock Fastboot entry, the exact
candidate booted Fedora 45 with USB SSH and core/early-cooling acceptance. No
permanent boot write; four experimental features remain off. Another reboot
still returns to the old 44-only guard. Stages/failures follow; later RW mounting
is separate from initial read-only diagnosis.

## 中文

### 已确认的原因

用户在手机上通过 DNF 升级到 Fedora 45 后报告启动似乎卡住。USB NCM/ACM 已枚举，
LAN SSH 超时，USB SSH 拒绝连接。通过精确识别的物理 USB 串口确认：

- 运行内核仍为 `7.3.1-picasso-wifi2`，PID 1 是内建 BusyBox `/init`，不是 systemd。
- 启动日志先以 `ro,norecovery` 挂载 XFS，随后明确打印
  `root is not a completed Picasso Fedora Server 44 disk install; refusing it`，
  卸载根分区并进入救援 shell。没有自动再次重启。
- 仓库 `initramfs/init` 的 `diskroot_valid()` 固定检查 `VERSION_ID=44`；
  内建引导逻辑不会因根文件系统内的 DNF 发行版升级自动变更。
- 只读查看根系统得到 `ID=fedora`、`VERSION_ID=45`、`VARIANT_ID=server`。
  `PICASSO_FEDORA44_DISKROOT_V2`、XFS、精确 PARTUUID 与
  `PICASSO_NATIVE_INIT_V1` 安装标记仍存在。systemd 文件也存在。
- DNF 日志末尾在 07:13:37 UTC 记录
  `Transaction complete! Cleaning up and rebooting...` 和 `DNF5 finished`。
  这不是仍在运行的升级事务，也不表示已经逐包审计整个升级的完整性。

因此当前阻塞点是 **44 专用 initramfs 拒绝 45 根系统交接**，不是已观察到的内核
死锁，也不是 Wi-Fi 或屏幕软件门槛拒启。Fedora 尚未启动，SSH/Wi-Fi/屏幕/NTP
以及提前降温服务都没有执行；此前[65°C 策略](THERMAL-LIMIT-65.md)和
[自动校时](DNF-CLOCK-SIGNATURE.md)的在线结果是此前 Fedora 44 的历史快照，
不能当作此刻运行状态。CPU 温度采样为 31.7–32.7°C，非高温验收。

### 本次只读范围与当前留置

只从内核显式 `root=PARTUUID=... rootfstype=xfs` 解析候选，核验 sysfs 分区元数据
中的唯一匹配、userdata 名称及既有精确长度；未探测其他块分区的内容。
只用 `ro,norecovery` 挂载明确的根分区查看版本、安装标记、systemd、默认 target、
Wi-Fi 生命周期文件及 DNF 日志，随后成功卸载。没有日志回放或根文件写入。
XFS 的 no-recovery 提示意味着这不是完整文件系统一致性验收，不能仅凭可读
就保证全部文件完好。观察时没有 `dirty.json`，有普通工作 checkpoint；
没有删除标记或恢复工作文件，也没有验证/启用 RF。

主机 USB helper 仅临时添加/移除自己的 IPv4，保留已有链路本地 IPv6；SSH
仍使用固定主机密钥，不关闭安全检查。串口证据保存在受保护的 `out/` 中。
本助手没有执行本次升级、重启、关机、kexec、刷写、RW 挂载、NV 或 PMIC/PON 操作，
没有修改 initramfs 源码、内建镜像或根系统版本声明。手机仍留在救援模式，根分区未挂载。

### 修复边界

需要为原生磁盘根明确适配 Fedora 45 的引导校验，保留唯一分区、安装完成标记、
文件系统、原生初始化和 Fedora Server 身份检查，并重新构建、测试候选。
不能伪装 `/etc/os-release` 为 44、直接取消验证、强行使用 RAM-root 通路、
重装/格式化根分区，或把保留的 6.18 救援镜像默认视为兼容 45。

受控临时启动、重启及永久写 `boot` 都需要另外明确授权；临时验证成功也不自动
授权永久写入。Fedora 45 的 systemd、服务资产 pin、屏幕、Wi-Fi 与热策略仍需重新
核验，当前没有成功启动或联网结论。

## English

### Confirmed cause

The operator reported an apparently stuck boot after upgrading the phone through
DNF to Fedora 45. USB NCM/ACM enumerated; LAN SSH timed out and USB SSH refused.
The explicitly identified physical USB serial console established:

- The kernel is still `7.3.1-picasso-wifi2`; PID 1 is built-in BusyBox `/init`,
  not systemd.
- Boot logs mount XFS `ro,norecovery`, print
  `root is not a completed Picasso Fedora Server 44 disk install; refusing it`,
  unmount the root and enter a rescue shell. No automatic reboot follows.
- Repository `initramfs/init` `diskroot_valid()` requires `VERSION_ID=44`;
  upgrading userspace through DNF does not automatically change this embedded guard.
- Read-only root inspection shows `ID=fedora`, `VERSION_ID=45`,
  `VARIANT_ID=server`. The `PICASSO_FEDORA44_DISKROOT_V2`, XFS, exact PARTUUID and
  `PICASSO_NATIVE_INIT_V1` installation markers remain. The systemd file exists.
- At 07:13:37 UTC the DNF log ends with
  `Transaction complete! Cleaning up and rebooting...` and `DNF5 finished`.
  This is not an upgrade transaction still running, nor an exhaustive package audit.

The current blocker is therefore the **44-only initramfs refusing handoff to a 45
root**, not an observed kernel deadlock or Wi-Fi/screen temperature refusal.
Fedora has not started: SSH/Wi-Fi/screen/NTP and early cooling services have not
run. Earlier online [65°C policy](THERMAL-LIMIT-65.md) and
[automatic time-sync](DNF-CLOCK-SIGNATURE.md) results describe the prior Fedora 44
snapshot, not current running services. CPU samples were 31.7–32.7°C, not a
high-temperature acceptance.

### Read-only scope and state left behind

Derive a candidate only from explicit kernel `root=PARTUUID=... rootfstype=xfs`;
verify unique sysfs partition metadata, userdata name and previously established
exact length. No content probing of other block partitions. Mount only that root
`ro,norecovery` to inspect release, install markers, systemd/default target, Wi-Fi
lifecycle files and DNF logs, then successfully unmount. No log replay or root
writes. XFS no-recovery output is not filesystem-consistency qualification;
readability alone cannot guarantee every file intact. `dirty.json` was absent
and an ordinary-work checkpoint present. No marker deletion, work recovery or
RF verification/enablement.

The host USB helper temporarily added/removed only its own IPv4, retaining
existing link-local IPv6. SSH kept pinned host-key verification. Protected serial
evidence stays in `out/`. The agent did not perform this upgrade, reboot,
poweroff, kexec, flashing, RW mount, NV or PMIC/PON operation, and did not modify
initramfs source, embedded images or the root's release declaration. The phone
remains in rescue with the disk root unmounted.

### Repair boundary

Explicitly adapt native disk-root validation for Fedora 45 while preserving
unique partition, completed-install marker, filesystem, native initialization and
Fedora Server identity checks; rebuild and test a candidate. Do not impersonate
44 in `/etc/os-release`, remove validation, force the RAM-root path, reinstall/
format the root or assume retained 6.18 rescue images already support 45.

Controlled temporary boot, reboot and permanent `boot` writes each require
additional explicit authorization; successful temporary validation does not grant
permanent flashing. Fedora 45 systemd, service asset pins, screen, Wi-Fi and
thermal policy need fresh checks. No successful Fedora 45 boot/network result yet.

## 后续授权准备 / Subsequently Authorized Preparation

### 中文

用户在上述边界说明后回复“继续”。本阶段允许准备修复和一次受控临时启动，
不允许永久写 boot、重装、格式化、RTC/PMIC/PON 操作或放宽 RF/NV 检查。

- 当前主机缺少此前构建缓存与恢复产物；历史“已保留”不能被当作本机现有文件。
  从唯一、名称/长度确认的 boot 分区**只读**回收完整 128 MiB，在主机保存压缩及
  原始备份。镜像前缀与既有运行时固定摘要一致，尾部全零；配置、现场 FDT、原 `/init`
  也与既有基线逐字节/摘要匹配。未接触其他分区内容或原始 NV。
- 修改 `initramfs/init`：磁盘根明确允许 44/45，保留 V2 安装标记、PARTUUID、
  文件系统、Fedora Server、原生初始化及 API 目录检查；RAM-root 仍只允许 44。
- `tools/repack-initramfs.py` 不重新编译内核、不改地址/布局。它要求固定原镜像摘要、
  原 `/init` 一致、唯一可解析 gzip/newc 档案与完整 metadata round-trip；仅把新 `/init`
  重压缩进原 gzip 槽，不够空间则拒绝。候选只有现有 gzip 槽和 Android boot ID 改变，
  其他 CPIO 成员、内核机器码、配置、shim、ABL DTB 和运行时 DTB 保留；模块 ABI 不变。
  新镜像不能继承旧镜像的实机成功状态。
- 在实际只读挂载的 45 根上执行两个校验函数：原函数拒绝，新函数接受完整标记。
  这只验收接管前的 admission，不表示 Fedora 45 PID 1/服务已启动。
- 为阻止未验收的服务自动启动，先只读复核，再按本次授权以 RW 挂载明确 XFS 根，
  允许其正常日志回放。已有 Fedora 45 Python 的 chroot 执行成功；归档原激活策略、
  manifest、证明和 checkpoint 后，只把四个 `allow_*` 开关设为 false 并绑定候选摘要。
  原证明、源码、模块、普通 NV 工作副本及 checkpoint 不改，三个 8 MiB 普通副本
  摘要均匹配 checkpoint，dirty 不存在。原子写入并保留 activation xattrs，随后卸载根。
  备份在手机通用目录 `/var/lib/picasso-fedora45-boot-review/`；不是自动恢复或重放指令。
  结果字段 `no_service_start_or_partition_write` 仅指未启动服务或直接写块设备，
  不能解读为没有上述普通文件/文件系统写入。
- 首次 2,400 字节编码块因救援 ash 长行截断缺失结束标记而停止；未盲目重放。
  独立检查确认 RAM spool 为零、根未挂载、PID 1 仍是救援，RW 阶段尚未发生。
  保留失败后，把 `tools/rescue-console.py` 线上限保守降到 1,800 字节，增加发送前
  拒绝回归，改用新 RAM 文件与 768 字节分块，并读回整体摘要后才执行上述阶段。
- 最新主机检查 **503 项：481 通过、21 跳过、1 错误**。唯一错误仍是缺少未生成的
  `kernel/power/picasso-pon-reason-audit.ko`，没有删除测试掩盖它。
- 当前仍是救援、根未挂载、四个实验功能授权关闭。主机 Fastboot 工具可用，但尚无
  Fastboot 设备；需用户现场进入原厂模式，再重新核验唯一设备、产品、解锁状态、
  boot 大小和候选摘要，只执行临时 boot。现有设备树没有可靠软件 bootloader 目标，
  不臆造重启指令或写 IMEM。没有永久写 boot 或完成 Fedora 45 启动/联网验收。

### English

After the boundary explanation above, “continue” authorized preparation and one
controlled temporary boot, not permanent boot writing, reinstall/format,
RTC/PMIC/PON operations or relaxed RF/NV checks.

- This host lacks the former build caches/recovery artifacts; historical retention
  is not proof of present files. **Read-only** recover the complete 128 MiB boot
  partition after unique name/length checks, saving compressed/raw host backups.
  Its image prefix matches the existing runtime pin, its tail is zero, and config,
  live FDT and original `/init` match the established baseline. No other partition
  content or raw NV access.
- Update `initramfs/init` disk admission to explicitly allow 44/45, preserving V2
  installation, PARTUUID, filesystem, Fedora Server, native-init and API-directory
  checks. RAM-root remains 44 only.
- `tools/repack-initramfs.py` recompiles no kernel and relocates nothing. Require
  pinned baseline image, matching original `/init`, unique parseable gzip/newc
  archive and exact metadata round-trip. Recompress only the new `/init` into the
  original gzip slot; refuse if it does not fit. Only that slot and Android boot
  ID change; other CPIO members, kernel code/config, shim, ABL/runtime DTBs and
  module ABI remain unchanged. The new image inherits no native success status.
- Run old/new admission functions on the actual read-only 45 root: old refuses,
  new accepts complete markers. This accepts only pre-handoff admission, not a
  running Fedora 45 PID 1 or services.
- Inhibit unqualified autostart: after read-only checks, use this authorization to
  mount the explicit XFS root RW, allowing normal journal replay. Existing Fedora
  45 Python ran successfully in chroot. Archive activation/manifest/proof/checkpoint,
  then atomically set only four `allow_*` feature switches false with candidate
  digest binding and preserved activation xattrs. Source/modules/proof, ordinary
  work and checkpoint remain unchanged; three 8 MiB work digests match checkpoint,
  dirty absent. Unmount afterward. Phone backup is in generic
  `/var/lib/picasso-fedora45-boot-review/`, not an automatic recovery/replay command.
  The recorded `no_service_start_or_partition_write` field means no service start
  or direct block-device write, not absence of the ordinary filesystem writes above.
- First 2,400-byte encoded chunk lost its end marker through rescue ash long-line
  truncation. Stop, do not blindly retry. Independent inspection found zero-byte
  RAM spool, unmounted root and rescue PID 1; RW stage had not occurred. Retain
  failure, lower `tools/rescue-console.py` wire limit to 1,800 bytes with a pre-send
  refusal regression; use fresh RAM paths, 768-byte chunks and full readback hash
  before performing the stage above.
- Latest host suite: **503 tests, 481 passed, 21 skipped, one error**. The sole error
  remains missing ungenerated `kernel/power/picasso-pon-reason-audit.ko`; not hidden
  by removing tests.
- Still in rescue, root unmounted, all four experimental features unauthorized.
  Host Fastboot tool is available but no Fastboot device yet. The operator must
  physically enter stock mode; reverify unique device, product, unlocked state,
  boot size and candidate digest, then temporary boot only. Current DT lacks a
  reliable software bootloader target; no guessed restart command or IMEM write.
  No permanent boot write or Fedora 45 boot/network acceptance yet.

## 受控临时启动验收 / Controlled Temporary-Boot Acceptance

### 中文

用户回复“已进入”后，主机确认唯一 Fastboot 设备位于此前物理 USB 端口，独立核验
产品为 Picasso、已解锁、boot 为 128 MiB、最大下载长度足够。重新验证完整旧 boot
备份、源码与确定性重打包结果、候选摘要和四项功能禁用记录，然后只发送**一次
临时 boot**。发送和启动均返回 OKAY；没有 flash、erase、unlock 或附加重启命令。

USB NCM/ACM 返回后，用原有严格主机密钥 USB SSH 实际登录并核验：

| 项目 | 本阶段结果 |
| --- | --- |
| 根系统与 PID 1 | 原生 Fedora 45 Server，XFS RW 根，systemd `262.1-1.fc45` PID 1 |
| 系统状态 | `running`，0 失败单元、0 等待启动任务；没有 reset-failed 或停用其他单元掩盖问题 |
| 内核身份 | `7.3.1-picasso-wifi2`，现场 config/FDT 与原基线相同 |
| 提前降温 | 服务 enabled、active/exited、success；8 个 CPU 被动 trip 40°C/2°C hysteresis，临界 110°C/1°C hysteresis 不变 |
| 同启动观察 | 60.7 秒，采样峰值 34.7°C；非压力或高温验收 |
| 资产与生命周期 | 93 个 manifest 文件均存在且摘要匹配；普通工作副本与 checkpoint 一致、dirty 不存在，原证明/checkpoint 不改 |
| 实验功能 | 四个 allow 开关仍 false；Wi-Fi/屏幕/probation/电源均 inactive、MainPID=0，无 WLAN、无 WLED 服务模块、未注册 remoteproc |
| 永久引导 | 只读复核整个 128 MiB boot 与临时试启前备份摘要一致，未写入候选 |
| 普通存储 | 私有验收 JSON 写入、fsync、重新读取一致；不是完整文件系统或耐久验收 |

新验收没有把旧 manifest/旧 Wi-Fi 证明改名当作新启动的功能证明。虽然 93 项 pin
都未变，Fedora 45 的屏幕、Wi-Fi、音量键和新无限期服务仍未测试或启用。
NTP 已启用且进程运行，但此时 Wi-Fi 关闭、USB 没有新增出口，
`NTPSynchronized=no`，墙钟回退到保存时间；不能把此前 Fedora 44 校时成功视为此刻
已联网同步。本阶段没有设时钟、改时区、建立 NAT/默认路由或写 RTC。

内核对齐、ITS、framebuffer、regulator/clock、块队列调度器、systemd unit 权限等
警告保留；0 failed 不表示这些告警、SELinux、电池/充电或完整硬件问题已解决。
首次只读验收器在完成观察后，用 PATH 中不存在的 `systemd --version` 收集版本时
停止，尚未写验收结果；不是手机启动失败。保留空结果和错误记录，改用实际
`/usr/lib/systemd/systemd` 后做新的 60 秒观察，第二份结果才是成功记录。

手机留在本次临时 Fedora 45，USB SSH 可用，永久 boot 仍为旧 44 专用版本。
**不要把此结果当作已修好下次普通重启。** 永久安装及后续屏幕/Wi-Fi 验收需要另外
明确授权；本阶段未授权、未执行。没有原始 NV、PMIC/PON、关机、充电、容器或加热试验。

### English

After “entered,” verify exactly one stock Fastboot device on the previous physical
USB port, independently checking Picasso product, unlocked state, 128 MiB boot
size and sufficient download bound. Revalidate complete original-boot backup,
source/deterministic repack, candidate digest and four-feature inhibition, then
send **one temporary boot**. Download and boot returned OKAY. No flash, erase,
unlock or additional reboot command.

After USB NCM/ACM returned, actually log in over existing strict-pinned USB SSH:

| Item | Result at this stage |
| --- | --- |
| Root and PID 1 | Native Fedora 45 Server, XFS RW root, systemd `262.1-1.fc45` PID 1 |
| System state | `running`, zero failed units and zero pending startup jobs; no reset-failed or unrelated unit disablement to hide faults |
| Kernel identity | `7.3.1-picasso-wifi2`, live config/FDT match original baseline |
| Early cooling | Enabled, active/exited, success; all eight CPU passive trips 40°C/2°C hysteresis, critical 110°C/1°C hysteresis unchanged |
| Same-boot observation | 60.7 seconds, sampled peak 34.7°C; not stress/high-temperature acceptance |
| Assets/lifecycle | All 93 manifest files exist and match; ordinary work matches checkpoint, dirty absent, old proof/checkpoint unchanged |
| Experiments | All four allow flags false; Wi-Fi/screen/probation/power inactive, MainPID=0, no WLAN, WLED service module or registered remoteproc |
| Permanent boot | Entire 128 MiB read-only digest still matches pretrial backup; candidate not installed |
| Ordinary storage | Private acceptance JSON write/fsync/readback passed; not whole-filesystem/endurance qualification |

Do not relabel old manifest/Wi-Fi proof as new-boot feature evidence. Even with
all 93 pins unchanged, Fedora 45 screen, Wi-Fi, volume key and new unlimited
service behavior remain untested/disabled. NTP is enabled and running, but Wi-Fi
is off and no new USB egress was configured: `NTPSynchronized=no`, with wall time
falling back to saved time. Earlier Fedora 44 sync success is not current online
synchronization. No clock/timezone change, NAT/default route or RTC write.

Preserve alignment, ITS, framebuffer, regulator/clock, block-scheduler and systemd
unit-permission warnings. Zero failed units does not resolve these warnings,
SELinux, battery/charging or full hardware limitations. The first read-only
verifier completed observation but stopped while collecting version using
`systemd --version`, absent from PATH, before writing acceptance evidence; not a
phone boot failure. Preserve empty output/error, use actual
`/usr/lib/systemd/systemd`, and perform a fresh 60-second observation. Only the
second result is the success record.

Leave the phone in this temporary Fedora 45 with USB SSH available and permanent
boot still 44-only. **This does not fix the next ordinary reboot.** Permanent
installation and subsequent screen/Wi-Fi acceptance need additional explicit
authorization and were not authorized/performed here. No raw NV, PMIC/PON,
poweroff, charging, container or heating trials.

## 证据 / Evidence

受保护、被忽略的仓库相对路径 / Protected, ignored repository-relative directory:
`out/fedora45-boot/`. 含私有数据，不应公开；新克隆可能没有这些文件，不能盲目重放。
/ Contains private data, not for publication; may be absent from fresh clones and
never authorizes blind replay.

- `usb-preflight.txt`: USB SSH 在救援模式拒绝的空输出，非成功登录记录 /
  Empty output from USB SSH refusal in rescue, not a successful login.
- `serial-preflight.raw`, `serial-preflight.txt`: PID 1、内核日志、未挂载磁盘根与温度 /
  PID 1, kernel logs, unmounted disk root and temperatures.
- `root-readonly.raw`, `root-readonly.txt`: 明确根分区只读查看、升级日志末尾与卸载确认 /
  Explicit-root read-only inspection, upgrade-log tail and successful unmount.
- `installed-readback.json`, `installed-boot-partition.img.gz`, `installed-boot-partition.img`,
  `installed-boot.img`, `installed-init`, `installed-config.gz`, `installed-fdt.dtb`:
  当前精确基线的只读回收，不是完整数据备份 / Read-only exact-baseline recovery,
  not a full data backup.
- `candidate/boot-f45-trial.img`, `candidate/repack.json`: 未实机验收的候选及变更边界 /
  Native-unverified candidate and byte-change boundary.
- `native-guard-check.txt`, `root-baseline.tar`: 只读真机校验函数及普通策略备份 /
  Read-only native admission tests and ordinary-policy backup.
- `stage-transfer-refusal.json`, `stage-transfer-00.raw`, `stage-refusal-inspection.txt`:
  长行失败及未执行 RW 阶段的独立复核 / Long-line failure and independent pre-RW inspection.
- `stage-trial-transfer-v1.py`, `stage-bound-policy.py`, `stage-trial-v2.log`,
  `stage-trial-policy.json`: 保留的失败助手、后续有界策略禁用及根卸载 /
  Retained failed helper, subsequent bounded policy inhibition and root unmount.
- `diskroot-tests.log`, `ramroot-tests.log`, `repack-tests.log`, `full-tests.log`,
  `full-tests-after-serial-fix.log`, `fastboot-waiting.txt`: 主机回归及尚无 Fastboot 设备 /
  Host regressions and absence of a Fastboot device at the preparation stage.
- `fastboot-preflight.json`, `temporary-boot.py`, `temporary-boot-attempt.json`,
  `temporary-boot-result.json`: 精确设备与一次临时 boot，不是永久写入 /
  Exact device and single temporary boot, not permanent installation.
- `first-native-boot.txt`, `native-verifier-failure.json`, `native-core-acceptance.json`:
  首次原生观察与版本收集失败的空结果 / First native inspection and empty result
  from version-collection failure.
- `verify-native-v1.py`, `verify-native.py`, `native-verification-input.json`,
  `native-core-acceptance-v2.json`, `native-evidence.tar`, `host-after-temporary-boot.txt`:
  保留的初版、修订验证器及成功的同启动/温控/资产/boot 未写入证明和主机清理 /
  Retained initial/revised verifier and successful same-boot/thermal/asset/unchanged-boot
  evidence plus host cleanup.
