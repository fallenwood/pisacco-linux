# Wi-Fi 连接准备：SG、Chaldea、设备默认 MAC（历史准备记录）

**后续用户已录入凭据并进行了连接测试，但 802.11 认证超时，尚未关联/联网。临时凭据已删除，
不需要立即重输；先靠近 AP 诊断链路。最新结果见 [WIFI-CONNECTION-TEST.md](WIFI-CONNECTION-TEST.md)。以下为试验前准备状态。**

2026-10-27。用户指定新加坡、目标 SSID `Chaldea`，不使用随机 MAC。
**监管域与非随机 MAC 扫描已通过；尚未关联、获取 DHCP 地址或验证上网。**

## 已通过实机验证

- 签名校验的 Fedora aarch64 libqmi/qmicli 及必要库仅加在 `/opt/picasso-wifi-trial/qmi-tools`。
  没有安装 RPM/运行安装脚本；没有上传同包的 firmware-update 工具。
- 在 WLAN 驱动未加载时，用只读 `DMS Get MAC Address (WLAN)` 获取本机固件报告的默认地址。
  模块所用 NV 仍仅为已授权三份工作副本；未读取 persist/fsc、SIM 或手机标识等其他接口。
  返回值是有效全球管理单播地址；没有生成、推导或伪造 MAC。
- 用标准 WLFW QMI `0x0033` / TLV `0x10` 向运行中固件提供该地址，再加载 SNOC。
  `wlan0` 当前 MAC 和 wiphy 永久 MAC 均与 DMS 返回值一致；扫描后仍一致。
  这是固件运行配置，不是固件分区/校准内容修改。每次 MPSS 重启须重新 provision，不能省略。
- `/etc/NetworkManager/conf.d/90-picasso-wifi-identity.conf` 关闭扫描随机化，
  连接默认 `permanent`；默认 `managed=0`，仅验证身份/监管域后显式允许受控操作。
- 最终全局监管域为 **SG**。wiphy 原 EEPROM 约束标签仍可显示 US，不能据此断言实际限制。
  核对 36 个启用的 20 MHz 信道的频率范围、EIRP、DFS 标志均不超出已观察到的 SG regdb 规则。
  不修改 BDF、regdb、原 EEPROM 或监管保护位；不宣称取得 RF 发射认证或宽信道完整认证。
- 扫描实际发现 `Chaldea`：5240 MHz / channel 48，广告支持 WPA1/WPA2，信号约 27%。
  准备的 `picasso-Chaldea` 配置只接受 WPA2/RSN + CCMP，不回退 WPA1，使用永久 MAC。
  不自动连接；初始连接测试仅 IPv4，入站使用 firewalld `drop` 区域，USB SSH 规则不变。

## 本地输入密码（不发到聊天）

在主机的**本地交互终端**执行：

```sh
cd /home/vbox/droid
./picasso/tools/enter-chaldea-password.sh
```

脚本使用已有私钥和固定 known_hosts SSH 到手机，再通过隐藏输入提示两次录入。
不从 argv/管道/聊天读取密码，不使用 `--show-secrets`，不读取主机已保存的 Wi-Fi 密码。
手机把等效 WPA2 PMK 写入 root-only `/run/picasso-chaldea.passwd`（0600、O_EXCL/NOFOLLOW）。
它仍是敏感网络凭据，不可打印、上传或加入证据；只在手机 tmpfs 中，测试 finally 删除，重启也清除。
当前尚无凭据文件。输入成功后回复“已录入”，再启动限时连接测试；输入本身不启动无线。

下一步将执行 `nmcli connection up ... passwd-file /run/picasso-chaldea.passwd`，
不把密码放在进程参数中；检查关联/加密、MAC、IPv4 DHCP、DNS/路由/联网后关闭实验并删除凭据。
配置的 `psk-flags=not-saved`，不把密码持久保存进连接配置；如需常驻另行讨论。

## 顺序与失败记录

- 先发 SG user hint、后注册 EEPROM 默认 US 的 wiphy，曾产生 global `98` 交集和实际信道仍为 US 的状态。
  **仅看 iw 命令成功或 global 标签不够**；审计在扫描前拒绝实际 30 dBm 的 2.4 GHz 等超 SG 情况。
- 清空无活动 PHY 的实验 Wi-Fi 模块状态，先让默认 driver hint 完成，再施加 SG 用户限制后正确生效。
  保留硬件原约束，不打开 ATH certification/testing、动态监管绕过开关，也不硬改校准国家码。
- 模块重载改变 nl80211 generic-netlink family；旧 supplicant 缓存句柄曾退回不支持的 WEXT，导致空扫描。
  在无连接时重启手机 wpa_supplicant 更新句柄后恢复；没有为了隐藏错误打开 WEXT 或清除 failed 状态。
- 扫描是异步的，不能把 5 秒空缓存当作完成。最终采用限时轮询，缓存到 40 条时目标被发现；
  仅保留用户指定 SSID 记录，不输出其他 SSID/BSSID。
- 五轮中间失败及源码版本均保留。最终试验结果为 `sg-mac-probe6-result.json`；无新增 modem crash。

## 安全退出和证据

当前仍为临时 wifi2 #10；实验后 wlan0 卸载、DSP offline、代理/TFTP/短期 MAC 客户端停止，
2.5 MiB RMTFS 共享内存清零。保持 USB SSH；没有刷 boot，正常重启仍回 #8。

再次验证原 NV 三分区 O_DIRECT 完整读回和 0400 原件未变；原 15,285 个静态文件、boot、七个保留分区、
六个 LUN GPT 全部一致。NV 更新仅发生在工作副本。仍无电池/充电/长期稳定性验收。

证据位于私有目录 `out/wifi-sg-mac-20261027/`；默认 MAC 原始记录仅在手机 root-only NV 私有目录。
本阶段测试：168 项，167 通过，1 项可选 QEMU 跳过。
原 [WIFI-SCAN.md](WIFI-SCAN.md) / RMTFS 结果继续作为历史阶段保留，不把扫描当成已连接或互联网验收。
