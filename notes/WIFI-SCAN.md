# Picasso Wi-Fi：临时内核已注册 wlan0，并通过 2.4/5 GHz 扫描 / Picasso Wi-Fi: Temporary Kernel Registered wlan0 and Passed 2.4/5 GHz Scanning

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页是首次扫描阶段的历史记录，不代表后续连接或当前安装状态。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This is a historical first-scan record, not a statement of later connection or current installation status. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

**后续进展：SG 监管域、设备 DMS 默认 MAC、${PRIMARY_SSID} 扫描均已验证；关闭 MAC 随机化，等待本地密码。
见 [WIFI-CONNECTION.md](WIFI-CONNECTION.md)。以下为首次扫描阶段历史，随机 MAC 等描述不再代表最新试验。**

2026-10-27。**已完成无线网卡注册及扫描；尚未验证关联、DHCP、DNS、ping 或互联网。**
本次扫描得到 49 条 AP 广播记录：2.4 GHz 43 条、5 GHz 6 条，nmcli 扫描/列表命令退出码 0。
采集命令仅包含频率、信号、加密类型，没有输出附近 SSID/BSSID 或密码。

测试已清理：DSP offline、代理/TFTP 停止、ath10k_snoc 卸载、wlan0 移除，2.5 MiB 共享缓冲清零。
**暂留临时 `6.18.58-picasso-lts-wifi2 #10`，USB SSH 可用，便于继续受控连接测试。**
没有刷写分区；持久默认仍是 #8，正常重启会回到 #8。Wi-Fi 未配置开机自动启动。

## 实际通过的路径

- 独立 wifi2 临时启动，运行 config/FDT 与准备产物摘要一致，XFS 原生 systemd/USB SSH 正常。
- RMTFS 动态区域 `0xffd7e000..0xffffffff`，两端各 4 KiB guard；可用区
  `0xffd7f000 / 0x280000`，字符设备 236:1、client-id 1。
  在单一 Linux RAM bank 内、不与固定保留区重叠；2.5 MiB 有限读写回环、清零和 EOF 边界通过。
- PID 1 向 DynamicUser 传递唯一内存字符 FD 和三份普通 NV 工作文件 FD；零 capabilities、
  私有根、无真实 proc/SSH/裸 UFS 设备。DevicePolicy=closed，仅精确授权该内存字符设备。
- 真实 RMTFS 请求成功读取私有 fs1/fs2；缓冲区是 client-1 全局共享，而非每文件独立。
  modem 更新仅写工作副本。没有向服务提供原分区或只读原始备份。
- MPSS 认证/启动、原厂 wlanmdsp.mbn 的 TFTP 加载、WLFW 69、MSA-ready、能力查询通过。
  实测 chip_id `0x320`、chip_family `0x4001`、board_id `0xff`、soc_id `0x400b0000`。
- 使用本机原始 modem 固件 FAT 内的默认 `image/bdwlan.bin`，26328 字节保持不变，
  封装为单一精确条目：`bus=snoc,qmi-board-id=ff,qmi-chip-id=320,variant=Xiaomi-Picasso`。
  仅安装在该设备自定义固件子目录，不使用 Fedora 通用 board-2.bin。
- 从签名校验通过的 Fedora `atheros-firmware-20261019-1.fc44.noarch` 提取标准 60 字节
  firmware-5.bin 元数据：WMI TLV/HTT 版本及 non-BMI 等标志，没有 firmware/OTP 代码 IE。
  没有替换原厂 DSP 可执行固件，也没有修改校准内容。相关许可证已保留。
- BDF 下载、固件 ready、HTT/WMI 初始化、wlan0 注册和真实扫描通过。

## 固定 MSA：依据和精确限制

原厂 DTB 9 + DTBO 19 指定 `qcom,wlan-msa-fixed-region` 为 `0x8ba00000 / 2 MiB`。
MiCode `picasso-q-oss` 固定提交 `236f9eb092623c2bc69fa2e88eb647ad30562049` 的 ICNSS 路径：
MSA info 后直接 MSA-ready / capability，不做 hypervisor/SCM 所有权重分配。
实际源码 blob 与该 git tree 的对象摘要匹配；不宣称它就是 crDroid Driftwood 的完整构建源码。

主线动态重分配在本机返回 -22。试验补丁
`kernel/patches/0003-ath10k-picasso-fixed-msa-trial.patch` 提供默认关闭、只读的
`picasso_fixed_msa=1` 参数，仅当 Picasso compatible、实际 MSA PA 和实际资源长度均精确匹配时生效。
复用现有 `qcom,msa-fixed-perm` 流程，保留固件既定权限；未修改全局 SCM/SMMU 实现或放宽其他区域。

测试使用单独的 `ath10k_snoc-picasso-fixed-msa-v2.ko`，没有替换 /usr/lib/modules 中原文件。
模块 SHA256：`3e676492be0dc97aedd3d3c4510c18ebce3ba4dd851a25d7fa474cdc66c01139`。
它的加载导致 kernel out-of-tree taint，证据保留，不把当前内核当作无告警/稳定产品。
正式改成 DTS 属性或新持久镜像后，需要新的精确字节实机验证，不能直接继承本次结果。

单模块重建使用现有 wifi2 kbuild 配置及符号表：

```sh
make -C src/linux-6.18.58 O="$PWD/out/kbuild" ARCH=arm64 LLVM=1 LOCALVERSION= \
  M=drivers/net/wireless/ath/ath10k -j8 modules
# 此 M= 构建的输出在 src/.../ath10k/，不是 O= 下原有的 .ko；先检查参数和 vermagic。
```

这是实验性、显式手动加载的路径，不是可盲目重复的安装/刷写流程。

## 保留的失败、告警与限制

- 初始黑名单把设备名 `qcom_rmtfs_mem` 当作模块名，导致内存驱动提前加载；当时 DSP 未启动，
  尚未向其提供 NV。已核对实际区域并修正为 `rmtfs_mem`，模板见 `tools/picasso-wifi-blacklist.conf`。
- 初次 OpenFile 被 PrivateDevices 的设备策略拦截；增加唯一字符设备精确授权后通过，没有授权块设备。
- 初始错误的“每文件分配缓冲”限制导致一次 modem EFS crash；已按固定上游 ABI 修正为 client 全局缓冲，
  保留内存/文件边界检查。自动恢复预先禁用，无循环重启。
- 一次试验模块误复制到旧 O= 产物，参数检查发现后未部署；一次 guard 误查 1 MiB 分配提示而非实际
  2 MiB 预留资源，失败关闭后修正。全部记录保留，不抹除失败。
- 仍有 `invalid MAC address; choosing random`：原厂 Wi-Fi MAC 未恢复，不能冒称已读取硬件 MAC。
  下一步可使用合法的本地管理/每连接稳定 MAC，不必读取 persist；如需原厂数据，应另行确认。
- 默认 BDF 的 EEPROM regdomain 0 被驱动映射到 US，**不是设备实际所在国家的确认**。
  连接前需用户确认实际地区并设置适当监管域，不能凭语言/时区猜测或放宽国家限制。
- `chan info: invalid frequency 0 (idx 41 out of bounds)` 统计事件告警仍在，扫描结果有效但 survey 统计未验收。
  没有修改特征位或屏蔽日志来伪装无告警。
- 本次成功扫描测试峰值 35.1°C；不是长期 RF、充电、温控、挂起或稳定性验收。
  Linux 电池遥测仍缺失，fastboot 当时读到 4275 mV，不报告当前百分比或充电安全。
- DNF 无互联网失败、一次 FDS 启动失败和历史告警继续保留；没有 reset-failed。

## 数据和分区保护复核

原始 NV 三分区各 8 MiB 用 O_RDONLY/O_DIRECT 完整读回，均与授权时快照相同；0400 私有原件也未变。
没有读取 fsc/persist。原 15,285 个静态文件（543,194,505 B）、完整 boot、DTBO、recovery、五个 vbmeta
和六个 LUN GPT 全部重新验证一致。NV 工作副本和受限 TFTP 状态属于 Fedora userdata 内的变化。
加密备份及独立密钥位置见 [WIFI-RMTFS.md](WIFI-RMTFS.md)，仍不可公开 NV/密钥/含私钥的根镜像。

## 下一步

请用户提供**实际国家/地区和目标 SSID**，不要在聊天中发送密码；安排本地终端交互输入凭据。
之后受控验证关联、加密、DHCP、DNS、联网、清理恢复，再讨论持久启用。
当前不会自动关联陌生网络、读取主机 Wi-Fi 密码、改主机 Wi-Fi 热点或刷写现有 boot。

证据：`out/wifi-rmtfs-20261027/result.json`，准备阶段 `preparation-status.json` 和其校验清单保持不变。

## English

**Later progress: SG regulation, the device's DMS default MAC, and ${PRIMARY_SSID} scanning were verified; MAC randomization was disabled, pending local password entry.
See [WIFI-CONNECTION.md](WIFI-CONNECTION.md). The following is the historical first-scan stage; statements about a random MAC no longer describe the latest trial.**

2026-10-27. **Wireless interface registration and scanning were completed; association, DHCP, DNS, ping, and internet access had not been verified.**
This scan yielded 49 AP broadcast records: 43 at 2.4 GHz and six at 5 GHz. The nmcli scan/list commands exited with code 0.
Collection commands included only frequency, signal, and encryption type; nearby SSIDs/BSSIDs and passwords were not output.

The trial was cleaned up: DSP offline, proxy/TFTP stopped, ath10k_snoc unloaded, wlan0 removed, and 2.5 MiB of shared buffer zeroed.
**The temporary `6.18.58-picasso-lts-wifi2 #10` was left running, with USB SSH available, to allow further controlled connection testing.**
No partition was flashed; the persistent default remained #8, to which normal reboot would return. Wi-Fi was not configured to start automatically at boot.

## Paths actually verified

- Separate temporary wifi2 boot; runtime config/FDT hashes matched the prepared artifacts. Native systemd/USB SSH on XFS worked.
- Dynamic RMTFS region `0xffd7e000..0xffffffff`, with 4 KiB guards at both ends; usable area `0xffd7f000 / 0x280000`, character device 236:1, client-id 1. It lay in a single Linux RAM bank without overlapping fixed reservations. Bounded 2.5 MiB read/write loopback, zeroing, and EOF-boundary checks passed.
- PID 1 passed the unique memory character FD and three regular NV working-file FDs to DynamicUser. Zero capabilities, a private root, and no real proc/SSH/raw UFS devices applied. DevicePolicy=closed granted access only to that exact memory character device.
- Real RMTFS requests successfully read private fs1/fs2. The buffer was global to client-1, not separate for each file. Modem updates wrote only to working copies; original partitions and read-only original backups were not given to the service.
- MPSS authentication/startup, TFTP loading of factory wlanmdsp.mbn, WLFW 69, MSA-ready, and capability queries passed. Measured chip_id `0x320`, chip_family `0x4001`, board_id `0xff`, soc_id `0x400b0000`.
- The default `image/bdwlan.bin` from this phone's original modem firmware FAT was used, with all 26328 bytes unchanged, packaged as one exact entry: `bus=snoc,qmi-board-id=ff,qmi-chip-id=320,variant=Xiaomi-Picasso`. It was installed only in this device's custom firmware subdirectory, not using Fedora's generic board-2.bin.
- Standard 60-byte firmware-5.bin metadata was extracted from signature-verified Fedora `atheros-firmware-20261019-1.fc44.noarch`: WMI TLV/HTT versions and flags such as non-BMI, with no firmware/OTP code IEs. Factory DSP executable firmware was not replaced and calibration contents were not modified. Relevant licenses were retained.
- BDF download, firmware ready, HTT/WMI initialization, wlan0 registration, and actual scanning passed.

## Fixed MSA: basis and precise limitations

Factory DTB 9 + DTBO 19 specified `qcom,wlan-msa-fixed-region` as `0x8ba00000 / 2 MiB`.
The ICNSS path at pinned MiCode `picasso-q-oss` commit `236f9eb092623c2bc69fa2e88eb647ad30562049` proceeds directly from MSA info to MSA-ready/capability, without hypervisor/SCM ownership reassignment.
The actual source blobs matched the object hashes in that git tree; this was not a claim that they constituted the complete sources used to build crDroid Driftwood.

Mainline dynamic reassignment returned -22 on this phone. Trial patch `kernel/patches/0003-ath10k-picasso-fixed-msa-trial.patch` provided a default-off, read-only `picasso_fixed_msa=1` parameter, effective only when Picasso compatible, actual MSA PA, and actual resource length all matched exactly.
It reused the existing `qcom,msa-fixed-perm` path and preserved firmware-established permissions, without changing global SCM/SMMU implementations or relaxing other regions.

Testing used a separate `ath10k_snoc-picasso-fixed-msa-v2.ko`, without replacing the original under /usr/lib/modules.
Module SHA256: `3e676492be0dc97aedd3d3c4510c18ebce3ba4dd851a25d7fa474cdc66c01139`.
Loading it caused an out-of-tree kernel taint; that evidence was retained, and the kernel was not presented as a warning-free/stable product.
A formal DTS property or new persistent image would require new exact-byte on-device verification; it could not simply inherit this result.

The single-module rebuild used the existing wifi2 kbuild configuration and symbol table:

```sh
make -C src/linux-6.18.58 O="$PWD/out/kbuild" ARCH=arm64 LLVM=1 LOCALVERSION= \
  M=drivers/net/wireless/ath/ath10k -j8 modules
# Output from this M= build is under src/.../ath10k/, not the existing .ko under O=; check parameters and vermagic first.
```

This was an experimental, explicitly manually loaded path, not an installation/flashing procedure to repeat blindly.

## Retained failures, warnings, and limitations

- The initial blacklist mistook device name `qcom_rmtfs_mem` for a module name, causing early memory-driver loading. The DSP had not started and NV had not been supplied. The actual region was checked and the name corrected to `rmtfs_mem`; template: `tools/picasso-wifi-blacklist.conf`.
- The first OpenFile attempt was blocked by the PrivateDevices device policy. It passed after exact authorization for the unique character device, without granting block-device access.
- An initially incorrect “per-file buffer allocation” restriction caused one modem EFS crash. It was corrected to a client-global buffer according to the pinned upstream ABI, while retaining memory/file bounds checks. Automatic recovery was disabled in advance; no reboot loop occurred.
- One trial module was mistakenly copied from an old O= artifact; parameter checks caught this before deployment. One guard check misread the 1 MiB allocation message instead of the actual 2 MiB reserved resource; it failed closed and was corrected. All records were retained rather than erasing failures.
- `invalid MAC address; choosing random` remained: the factory Wi-Fi MAC had not been restored, and a hardware-MAC read could not be claimed. A valid locally administered/per-connection stable MAC could be used next without reading persist; factory data would require separate confirmation.
- The driver mapped the default BDF's EEPROM regdomain 0 to US. **That did not confirm the device's actual country.** Before connecting, the user needed to confirm the actual region and the appropriate regulatory domain had to be set. Language/time zone must not be used to guess the country or relax country restrictions.
- The statistics-event warning `chan info: invalid frequency 0 (idx 41 out of bounds)` remained. Scan results were valid, but survey statistics had not passed acceptance. Feature bits were not changed and logs were not suppressed to feign a warning-free state.
- Peak temperature for the successful scan was 35.1°C, not acceptance of long-term RF, charging, thermal control, suspend, or stability. Linux battery telemetry remained missing; fastboot then reported 4275 mV. No current percentage or charging safety was claimed.
- DNF failures without internet access, one FDS startup failure, and historical warnings were retained; no reset-failed.

## Data and partition protection recheck

The three original NV partitions, 8 MiB each, were fully read back using O_RDONLY/O_DIRECT and all matched the authorized snapshots; 0400 private originals were also unchanged.
fsc/persist were not read. The original 15,285 static files (543,194,505 B), complete boot, DTBO, recovery, five vbmeta partitions, and all six LUN GPTs were reverified unchanged.
NV working copies and restricted TFTP state were changes within Fedora userdata.
Encrypted-backup and separate-key locations are in [WIFI-RMTFS.md](WIFI-RMTFS.md); NV/keys/root images containing private keys must still not be published.

## Next step

Ask the user for the **actual country/region and target SSID**. Do not send passwords in chat; arrange credential entry interactively in a local terminal.
Then verify association, encryption, DHCP, DNS, network access, and cleanup/recovery in a controlled trial before discussing persistent enablement.
At this stage there would be no automatic association with unfamiliar networks, reading of host Wi-Fi passwords, changes to the host Wi-Fi hotspot, or flashing of the existing boot.

Evidence: `out/wifi-rmtfs-20261027/result.json`. Preparation-stage `preparation-status.json` and its verification manifest remained unchanged.
