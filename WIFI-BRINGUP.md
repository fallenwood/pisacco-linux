# Picasso Wi-Fi 第一阶段记录：DSP 启动与 RMTFS 依赖定位（历史）

**后续 wlan0 已注册并通过扫描，最新进展见 [WIFI-SCAN.md](WIFI-SCAN.md)。**

2026-10-27。**没有无线网卡接口，尚未通过扫描、关联、DHCP 或联网测试。**
本页记录第一阶段；用户随后已批准 NV 只读私有副本，第二阶段准备进度见 [WIFI-RMTFS.md](WIFI-RMTFS.md)。
本次仅 `fastboot boot` 临时启动独立测试镜像；没有刷写分区。测试后正常重启回已安装的
`6.18.58-picasso-lts #8` / Fedora 44 / XFS，USB SSH 可用。

## 已完成

- 独立 `dts/sm7250-xiaomi-picasso-wifi.dts`、`kernel/picasso-wifi.config` 和
  `DTS_PROFILE=wifi` 构建入口。模块版本为 `6.18.58-picasso-lts-wifi1`，不覆盖 #8 模块。
- `kernel/patches/0002-sm7250-wifi-mpss-pas.patch`：SM7250 MPSS PAS 4 支持及 PD mapper
  modem root/WLAN domain。`auto_boot=false`，不自动启动 DSP；没有启用 IPA/蜂窝数据栈。
  补丁重新应用到原版 6.18.58 的三个文件后，与实际编译源码逐字节一致。
- 本机原厂 DTB 9 + DTBO 19 离线核对：MMIO、12 路 CE IRQ 顺序、SMMU stream 0xc0/1、
  SMP2P、CX/MSS、真实 AOSS QMP 和 Wi-Fi 五路供电。21 个固定保留区仍受保护。
- WLAN MSA 是 `0x8ba00000 / 2 MiB`；MPSS 区是 `0x8c000000 / 248 MiB`，原厂 modem ELF
  装载范围恰好落在该区内。**没有把约 8 MiB 的 WLAN DSP ELF 塞进 2 MiB MSA。**
  这不等于验证了原始 ABL RAM map 或全部 RAM。
- 固件来自此前只读保存的本机 `modem` 固件镜像。36 个所需文件被校验后复制到 Fedora
  `/usr/lib/firmware/qcom/sm7250/picasso/`，没有修改原厂固件分区。
- 原生临时启动 #9 成功，systemd、XFS、USB SSH 正常；运行 config 和 FDT 与测试产物一致。
- MPSS 固件认证/启动成功，QRTR 出现 subsystem control 43、service notification 66；
  PD locator 64 和受限 TFTP 4096 正常注册。ath10k SNoC 探测到正确的 MSA 地址。
- 98 项离线测试：97 通过，1 个可选 QEMU 测试跳过。实际构建/手机测试未使用 QEMU。

## 实机发现的阻塞

第一次约 20 秒测试：DSP running，但无 WLFW QMI service 69、无 WLAN TFTP 请求、`iw dev` 为空。
停止时出现 `timeout waiting for shutdown ack`，随后 PAS shutdown 成功、状态回到 offline。
这条告警没有被删除或当作正常验收。

第二次在约 30 秒观察后，短暂注册**只拒绝、不访问存储**的 service 14：

```text
QMI message 1: /boot/modem_fs1
response: FAILURE / NOT_SUPPORTED
modem fatal: EFS: rmts_get_buffer api failed
```

这确认原厂 modem 固件启动路径依赖 RMTFS/NV。拒绝操作引发一次 modem crash；已预先禁用
remoteproc 自动恢复，未发生重启循环；测试结束 PAS shutdown 成功，DSP 回到 offline。
**不是 Wi-Fi 已成功，也不能仅凭 ELF 认证成功声称 modem 完整初始化。**
实际 chip_id/board_id 尚未读到，没有猜测或套用其他机型 BDF/校准文件。

测试峰值分别为 37.1°C、37.8°C，不是长期温控/充电安全验收。一次后续预检因温度阈值拒绝
开始 DSP 测试，失败证据保留；哈希操作后的重试只增加等待降温，未提高 40°C 开始阈值。
Linux 电池遥测仍缺失；fastboot 此次仅读到 4278 mV，不能据此报告电量百分比或充电安全。

## 文件服务隔离和写入边界

- TFTP 使用私有 RootDirectory，只有复制的 factory firmware、程序及所需动态库。
  sysfs firmware-name 是路径发现用的静态 stub，不冒充 DSP 运行状态；不暴露真实 `/sys`、
  `/proc`、SSH 密钥或块设备。ProtectSystem=strict、PrivateDevices、零 capabilities、
  仅 AF_QIPCRTR/AF_UNIX、180 秒上限，无自动重启/开机启用。
- `tools/qmi-rejector.py` 仅解析 QMI 元数据并返回错误；不打开请求路径、不授权 DMA buffer、
  不返回文件句柄、不打印 NV/数据内容。8 项测试验证错误编码及拒绝行为。
- 实测拒绝端使用 UID 65534、PrivateDevices 和零 capabilities。systemd 对共享 nobody UID
  的警告也保留在日志中；这是一次性诊断，**不是生产服务模板**。未来代理应使用独立
  DynamicUser/UID，不能照搬该共享身份。
- HLOS 没有挂载、提取或改写 modemst1、modemst2、fsg、fsc、persist，也未请求 SIM 数据；
  没有提供假 NV、空白 NV 或编造校准。没有启用 ModemManager/rmtfs 存储代理。
- Fedora 中新增独立模块、固件、`/opt/picasso-wifi-trial/`、有限的状态/日志及
  `/etc/modprobe.d/90-picasso-wifi-trial.conf`。该黑名单阻止测试驱动在 SSH 就绪前自动探测；
  #8 没有这些无线驱动，不受影响。临时 unit/诊断程序位于 `/run`，正常重启后已消失。
- 返回 #8 后重新验证原 15,285 个静态文件（543,194,505 B）、boot 完整分区、DTBO、recovery、
  五个 vbmeta 和六个 LUN 的 GPT，全部与安装记录一致。没有更改已有安装的启动镜像。
- DNF 无互联网失败和 journal 时钟回退等历史证据继续保留；没有 reset-failed 或关闭服务掩盖问题。

## 下一阶段：需用户明确确认 NV 只读提取

1. 补全本机 RMTFS 共享缓冲区。原厂是动态 `0x280000`、client-id 1、guard memory；
   当前 Wi-Fi DTS 尚无对应区域。需按主线 binding/驱动核对，不能随意写死物理地址。
2. 经用户确认后，仅只读提取 `modemst1/modemst2/fsg` 为受限私有副本，不挂载、不写回原分区。
   其中可能包含 IMEI 等设备身份及基带校准；副本及内容不得公开。DSP 如需更新，只能写 Fedora
   内的副本；原分区不得作为可写后端。若还请求其他受保护数据，应再次停止确认。
3. 隔离的 RMTFS 代理只访问这些副本及指定共享缓冲；仍不读取 persist，不提供裸 UFS 设备。
4. 重新临时启动、加载 WLAN 固件并取得真实 chip/board ID，再准确匹配本机原厂 BDF。
5. 实测扫描、受控连接、地址/DNS/联网及清理恢复；通过后才讨论是否持久安装新内核/服务。

用户不同意 NV 读取时，应保持无线关闭，不得用假 NV 或降低存储隔离来绕过依赖。

## 产物与证据

目录 `out/wifi-bringup-20261027/`，权限 0700。`result.json` 汇总结论；历史尝试/失败不覆盖。

| 测试产物 | SHA256 |
| --- | --- |
| 临时 boot，33,820,672 B | `e3bf5f6188e63bbc860983ca7155e2b58e62dd4e99eda4b60210353b329d2289` |
| Image | `7cc71895310671f082727d0ee83cfdf6922d30435ffa8d282a6c12f04a348f5f` |
| config | `b71eb08469114bd07066d72252b1a8509bafa1acdbc634ea2617d4e514194867` |
| runtime FDT | `be68235e44f6749d2b585bf51bface873696adad82e59964b84df041cb4884ff` |

`out/boot-picasso.img` 仍是已安装 #8 的 `81f28d44…fde043c`；没有将 Wi-Fi 试验状态冒充为
已通过的持久安装或全功能无线验收。不要盲目重复单机 staging/probe 脚本。
