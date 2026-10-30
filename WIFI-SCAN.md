# Picasso Wi-Fi：临时内核已注册 wlan0，并通过 2.4/5 GHz 扫描

**后续进展：SG 监管域、设备 DMS 默认 MAC、Chaldea 扫描均已验证；关闭 MAC 随机化，等待本地密码。
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
