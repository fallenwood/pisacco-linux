# 项目地图 / Project Map

## 中文

### 职责与目录

本项目把设备专用内核适配、Android 启动链兼容、Fedora 用户空间和受保护的硬件试验分开维护。
构建与打包是离线操作，不自动刷机；设备验收只绑定实际测试的镜像字节与阶段范围。

| 路径 | 职责 |
| --- | --- |
| `device.json` | 设备、ROM 与启动基线、验收阶段及详细文档的机器可读索引 |
| `sources.json` | 下载输入与上游版本、SHA256 固定 |
| `kernel/patches/` | 针对干净 LTS 源码的本地补丁；`series` 定义常规补丁顺序 |
| `kernel/*.config` | 基础、Fedora Server 与可选硬件配置片段 |
| `kernel/display/`、`kernel/power/` | 受限 WLED 驱动及只读电源原因审计模块 |
| `kernel/diagnostics/` | 不在常规补丁序列中的可选 ath10k 诊断补丁 |
| `dts/` | Picasso 专用 server、Wi-Fi、RMTFS、屏幕交接与电源试验设备树 |
| `initramfs/init` | BusyBox 救援、USB NCM/ACM 与受验证的 Fedora 根交接 |
| `shim/copydown.S` | 在保留原厂 boot DTB blob 的前提下交接到内嵌主线 Image/DTB |
| `tools/` | 获取、审计、构建、打包、安装准备和原生硬件服务/试验工具 |
| `tests/` | Python unittest 离线回归；不代替真机硬件验收 |
| `notes/` | 双语实现说明、过程、证据与失败记录，入口为 [INDEX.md](INDEX.md) |
| `downloads/`、`src/`、`out/` | 被忽略的下载、准备后内核源码及构建/本地证据产物 |

### 构建与数据流

1. `tools/fetch-sources.py` 读取 `sources.json`，校验下载 SHA256，仅从 APK 提取静态
   AArch64 BusyBox；`tools/prepare-kernel.py` 准备源码并应用本地补丁。
2. `tools/build-kernel.sh` 从 arm64 defconfig 合并配置片段，检查必需内建驱动与
   禁用的 ZRAM writeback，构建 Image/modules，并通过 `tools/build-dtb.sh` 选择 DTS。
   Wi-Fi profile 使用独立的内核 release，避免与已安装模块混用。
3. `tools/inspect-rom.py` 根据 `device.json` 审计匹配 ROM 的 boot/DTBO，离线合并
   选定设备树并检查固定保留内存；Wi-Fi 打包还需相应 `tools/audit-wifi.py` 审计。
4. `tools/mkboot.sh` 拒绝不匹配输入或过期审计，构建并校验 copydown shim，
   通过 `tools/bootimg.py` 输出 v2 boot 镜像、清单与 SHA256。不执行刷写。

构建命令与输入限制见 [PROJECT-LOG.md](PROJECT-LOG.md)，来源见 [SOURCES.md](SOURCES.md)。
不要把成功构建、离线审计或旧镜像验收当作新镜像的真机通过记录。

### 启动与运行集成

原厂 ABL 使用保留的 DTB blob/DTBO，shim 再交接到内嵌主线内核和 DTB。
内建 initramfs 默认救援，不自动发现或写入 userdata。
磁盘根必须显式提供 PARTUUID 和 ext4/XFS 类型，先禁止日志回放地只读挂载，
再验证安装标记、Fedora Server 44、原生初始化和 systemd 后才切换到读写根。
RAM-root 交接另有 tmpfs 与原生初始化保护；进入 Fedora 前终止无密码救援 shell。

原生 systemd 单元调用 `tools/` 中的屏幕、电源和 Wi-Fi 控制器。
屏幕服务管理 tty1、空闲关灯、音量上亮屏与内核背光租约；Wi-Fi 服务结合私有 RMTFS
代理、设备 MAC、实际监管域核验与独立清理；电源试验区分输入识别、PID1 正常关机请求
和实际保持断电。控制器的保护退出与失败证据不能被清除来伪装验收成功。
最新开机冷却与 CN 自动连接的阶段边界见 [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md)、
[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)；电源已知自行启动见
[POWER-AUTOSTART.md](POWER-AUTOSTART.md)。

### 检查入口

离线回归命令为 `python3 -m unittest discover -s tests -v`。
构建、安装与硬件操作必须使用各阶段笔记的输入、保护和授权边界；
完整历史检查与未验证项见 [VALIDATION.md](VALIDATION.md)。

## English

### Responsibilities and directories

The project separates device-specific kernel adaptations, Android boot-chain
compatibility, Fedora userspace and guarded hardware experiments. Builds and
packaging are offline and do not automatically flash. Hardware acceptance applies
only to the exact tested image bytes and the recorded stage scope.

| Path | Responsibility |
| --- | --- |
| `device.json` | Machine-readable device/ROM/boot baselines, validation stages and detailed-document references |
| `sources.json` | Download inputs, upstream versions and SHA256 pins |
| `kernel/patches/` | Local patches against clean LTS sources; `series` defines the normal patch order |
| `kernel/*.config` | Base, Fedora Server and optional hardware configuration fragments |
| `kernel/display/`, `kernel/power/` | Bounded WLED drivers and read-only power-reason audit modules |
| `kernel/diagnostics/` | Optional ath10k diagnostics outside the normal patch series |
| `dts/` | Picasso-specific server, Wi-Fi, RMTFS, screen-handoff and power-trial device trees |
| `initramfs/init` | BusyBox rescue, USB NCM/ACM and validated Fedora root handoff |
| `shim/copydown.S` | Embedded mainline Image/DTB handoff while preserving the stock boot DTB blob |
| `tools/` | Fetching, auditing, building, packaging, install preparation and native hardware services/trials |
| `tests/` | Offline Python unittest regressions, not a substitute for hardware acceptance |
| `notes/` | Bilingual implementation, procedure, evidence and failure records; entry point [INDEX.md](INDEX.md) |
| `downloads/`, `src/`, `out/` | Ignored downloads, prepared kernel sources and build/local-evidence artifacts |

### Build and data flow

1. `tools/fetch-sources.py` reads `sources.json`, verifies download SHA256 and
   extracts only static AArch64 BusyBox from the APK. `tools/prepare-kernel.py`
   prepares sources and applies local patches.
2. `tools/build-kernel.sh` merges configuration fragments into arm64 defconfig,
   checks required built-in drivers and disabled ZRAM writeback, builds Image/modules
   and selects DTS through `tools/build-dtb.sh`. Wi-Fi profiles use distinct kernel
   releases to avoid mixing with installed modules.
3. `tools/inspect-rom.py` uses `device.json` to audit matching ROM boot/DTBO,
   merge the selected device trees offline and check fixed reserved memory.
   Wi-Fi packaging also requires the appropriate `tools/audit-wifi.py` audit.
4. `tools/mkboot.sh` rejects mismatched inputs/stale audits, builds and checks the
   copydown shim, then uses `tools/bootimg.py` to produce a v2 boot image, manifest
   and SHA256. It does not flash.

Build commands/input constraints: [PROJECT-LOG.md](PROJECT-LOG.md).
Provenance: [SOURCES.md](SOURCES.md). A successful build, offline audit or old-image
acceptance is not hardware acceptance of a new image.

### Boot and runtime integration

Stock ABL uses the preserved DTB blob/DTBO before the shim hands off to the embedded
mainline kernel and DTB. Built-in initramfs defaults to rescue and never implicitly
discovers or writes userdata. Disk root requires explicit PARTUUID and ext4/XFS
type, starts with read-only/no-journal-replay mounting, and validates installation,
Fedora Server 44, native-init and systemd markers before switching to read-write root.
RAM-root handoff has separate tmpfs/native-init guards. Unauthenticated rescue
shells terminate before entering Fedora.

Native systemd units call screen, power and Wi-Fi controllers in `tools/`.
The screen service manages tty1, idle backlight-off, volume-up wake and the kernel
backlight lease. Wi-Fi integrates a private RMTFS proxy, device MAC, actual
regulatory-domain checks and independent cleanup. Power experiments distinguish
input recognition, normal PID1 shutdown requests and actually remaining powered
off. Protective exits and failure evidence must not be cleared to fabricate success.
Latest startup-cooldown/CN-association stage boundaries:
[DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md), [WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md).
Known self-start failure: [POWER-AUTOSTART.md](POWER-AUTOSTART.md).

### Check entry point

Offline regression command: `python3 -m unittest discover -s tests -v`.
Build, install and hardware operations must respect the inputs, safeguards and
authorization boundaries in their stage notes. Complete historical checks and
unverified behavior: [VALIDATION.md](VALIDATION.md).
