# Wi-Fi自动连接已启用：独立受保护服务，当前2.4GHz联网

> 最新默认模式是[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)：真实wlan0常驻UP但不自动关联；旧auto/reconnect服务disabled且失败保留。当前要管理无线所有者应使用`picasso-wifi-radio.service`，不要启动本页旧单元；本页联网事实保留为历史。

> 当前已由新持久重连监管器接管，旧`picasso-wifi-auto.service`已disabled且failed保留，不要再按本页旧命令启动它。每boot初连＋3次退避重试，真机3次自然掉线后的自动恢复已通过；本boot最终预算用尽离线，见[WIFI-RECONNECT.md](WIFI-RECONNECT.md)。以下在线和disabled更新均是各阶段历史。

> **后续状态更新：** session `c2d482b79523`在本页90/303秒及最终732秒在线检查之后，因`Fallback link lost; no restart loop`退出；当前enabled/failed、DSP offline/WLAN absent，清理/checkpoint/CPU恢复完成，无dirty标记。此次LAN SSH配置期间未重启Wi-Fi；见[LAN-SSH.md](LAN-SSH.md)。以下在线结果是当时的实测历史，不是当前在线状态或永久稳定保证。

用户请求“启用wifi自动连接”。沿用此前明确保存和启用授权的两份手机私有凭据，不重新录入，不读取/哈希/导出PMK。
本阶段没有重启、刷boot、PMIC操作、原NV读写、主机网络/NAT/DNS改变或移动手机。

## 实际完成

1. 原`picasso-wifi.service`以原45秒有界配置运行新session `54eeff51eaa2`：
   Chaldea约19.975秒超时；Chaldea-2.4G约2.877秒激活，DHCP/DNS/HTTPS200及45秒检查通过。
   **整体unit为failed/watchdog**：停止健康线程后的清理阶段未声明STOPPING，8秒watchdog触发。
   独立ExecStopPost完成安全清理、工作副本checkpoint提交、共享RAM清零、CPU上限恢复；不把局部probation通过改写为整体成功。
2. 新独立`picasso-wifi-auto.service`与`wifi-auto-service.py`保持原看门狗8秒，在清理前发`STOPPING=1`，由原45秒TimeoutStopSec约束退出。
   正常运行时watchdog/父进程进度/3秒精确PID租约均保留，不在清理阶段继续伪造代理租约。
   新session `9bd7a4ea20f8`再跑45秒：Chaldea20.407秒普通超时→2.4G0.662秒激活，联网及完整清理通过，**unit inactive/success**。
3. 只有上述相同新代码的原生完整成功后，写入root0400
   `/var/lib/picasso-wifi/auto-enable-consent-20261029.json`，记录用户请求、session、45秒成功、cleanup、unit success及精确新代码哈希。
   新控制器在`probation_seconds=0`时强制验证此证据；缺失、非root0400、unit watchdog/cleanup失败或代码哈希不同均拒绝。
   然后将**新配置**转为常驻并enable服务，不是删除旧失败的45秒限制来伪装验收。
4. 当前常驻session `c2d482b79523`：Chaldea20.477秒普通超时→2.4G0.688秒激活，首次连接DNS/HTTPS再次通过；
   观察90.88秒后仍active/running/enabled，PID3764，`Chaldea-2.4G`，IPv4 `192.168.1.64/24`。
   最大采样34.7°C；归档实时元数据时同session已约303.3秒仍连接。它们只是当时观测窗口，不是长期稳定性或根因修复证明。

三次均是新session，不是重放已消耗的旧诊断。常驻服务已按用户请求保持运行；后续状态以实时unit/session为准。

## 改动范围与不变保护

- 新代码：`tools/wifi-auto-service.py`；新unit：`tools/picasso-wifi-auto.service`。
- 手机新配置：`/opt/picasso-wifi/config-auto.json`；原`config.json`、原代码及原unit未改。
- 原`picasso-wifi.service` **disabled/failed/watchdog**保留，不reset-failed，不把原失败重跑成成功。
  原控制器/config/unit及覆盖前runtime已另存root0400：
  `/var/lib/picasso-wifi/deployments/auto-enable-20261029T152332Z/`。
- 只接受两份精确已审计FDT：原#10 `62ac…`和已写入的power DTB `ecbf…`，配置基准必须仍是原#10。
  既有离线audit证明全部旧节点/属性和保留区逐字节不变，只新增三个PON/pwrkey节点；不接受任意其他FDT。
  动态RMTFS内存范围和设备身份仍每次新发现并验证。**新power DTB上的开机联网尚未原生重启验收**。
- 新控制器补齐所有可读传感器数值有效范围检查，仍启动严格<40°C/运行45°C中止，不提高任何热限。
- 原顺序Chaldea band a/20秒→普通失败后Chaldea-2.4G band bg/25秒；安全异常立即失败，不回退掩盖。
  主SSID后续失联最多一次回退，回退再次失联则退出；`Restart=no`，不循环DSP/重连。
- SG实际24信道20MHz/EIRP/DFS子集、永久MAC、WPA2/RSN CCMP、drop区域、实际授权、DNS/HTTPS、CPU6/7运行期1094400kHz及退出恢复保持。
- 原私有四FD/RAM RMTFS/手动MPSS/auto_boot=false/recovery disabled/独立清理/原NV0400备份不可写边界不变。
  此次未读取或重新摘要原NV分区/masters，没有其他NV或凭据范围扩展。
- 活跃时`dirty.json`属于当前运行session，DSP正在运行、工作副本可能合理变化；**不删除该marker，也不能把它直接叫作脏退出**。
  只有安全关停才提交新checkpoint并按原控制器规则消耗自己创建的生命周期dirty标记。
- 屏幕仍原生tty1/15秒idle/音量上亮屏/内核租约；power服务保持enabled但本boot未激活；未休眠。

## 日常操作（手机内执行；本阶段未执行关停）

```sh
sudo systemctl status picasso-wifi-auto.service
sudo systemctl stop picasso-wifi-auto.service
# 如需关闭开机自动连接：
sudo systemctl disable picasso-wifi-auto.service
```

不要启动旧failed服务、删除dirty/marker、手工恢复原NV工作副本、启用NM无限自动重连或增加systemd Restart循环。
若新服务因失联/安全检查退出，先保存session/cleanup/history并检查温度/副本状态，不能直接循环重启。

## 未解决项和证据

此前BEACON_MISS→正常失联处理→后续DISABLE_KEY超时的事实不变。**没有修复或证明beacon接收根因**，也未改变固件/校准/BDF/功率/监管/失联检测来掩盖问题。
本次超过此前17–51秒的90秒窗口不能替代长期RF/热/充电/内存/UFS/休眠/掉电稳定性验收。
本次未重启；“开机自动连接”指已持久enable，不能称为已经实际冷启动验证。

主机证据：`out/wifi-enable-20261029T152332Z/`。旧watchdog失败、新有界完整成功、常驻观察和全部source/config证明分开保存。
一次精确替换因匹配两处被工具拒绝，未产生部分编辑；以更精确上下文改正，未更改旧控制器。
离线回归：342项，341通过，1项可选QEMU跳过；不替代原生网络/开机/长期安全证明。
