# Wi-Fi 连接准备：SG、${PRIMARY_SSID}、设备默认 MAC（历史准备记录） / Wi-Fi Connection Preparation: SG, ${PRIMARY_SSID}, and the Device Default MAC (Historical Preparation Record)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页保留连接试验前的历史准备状态，后续结果见更新链接，不代表当前状态。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This page preserves historical preparation before the connection trial; linked updates provide later results, not a claim of current status here. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

**后续用户已录入凭据并进行了连接测试，但 802.11 认证超时，尚未关联/联网。临时凭据已删除，
不需要立即重输；先靠近 AP 诊断链路。最新结果见 [WIFI-CONNECTION-TEST.md](WIFI-CONNECTION-TEST.md)。以下为试验前准备状态。**

2026-10-27。用户指定新加坡、目标 SSID `${PRIMARY_SSID}`，不使用随机 MAC。
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
- 扫描实际发现 `${PRIMARY_SSID}`：5240 MHz / channel 48，广告支持 WPA1/WPA2，信号约 27%。
  准备的 `picasso-${PRIMARY_SSID}` 配置只接受 WPA2/RSN + CCMP，不回退 WPA1，使用永久 MAC。
  不自动连接；初始连接测试仅 IPv4，入站使用 firewalld `drop` 区域，USB SSH 规则不变。

## 本地输入密码（不发到聊天）

在主机的**本地交互终端**执行：

```sh
cd "${REPO_ROOT}"
tools/${WIFI_CREDENTIAL_SCRIPT}
```

脚本使用已有私钥和固定 known_hosts SSH 到手机，再通过隐藏输入提示两次录入。
不从 argv/管道/聊天读取密码，不使用 `--show-secrets`，不读取主机已保存的 Wi-Fi 密码。
手机把等效 WPA2 PMK 写入 root-only `/run/picasso-${PRIMARY_SSID}.passwd`（0600、O_EXCL/NOFOLLOW）。
它仍是敏感网络凭据，不可打印、上传或加入证据；只在手机 tmpfs 中，测试 finally 删除，重启也清除。
当前尚无凭据文件。输入成功后回复“已录入”，再启动限时连接测试；输入本身不启动无线。

下一步将执行 `nmcli connection up ... passwd-file /run/picasso-${PRIMARY_SSID}.passwd`，
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

## English

**The user subsequently entered credentials and a connection test ran, but 802.11 authentication timed out; association/network access had not succeeded. Temporary credentials were deleted, and did not need to be re-entered immediately; the plan was to diagnose the link closer to the AP first. See [WIFI-CONNECTION-TEST.md](WIFI-CONNECTION-TEST.md) for later results. The following is the pre-trial preparation state.**

2026-10-27. The user specified Singapore, target SSID `${PRIMARY_SSID}`, and no random MAC.
**Regulation and scanning with a non-random MAC passed; association, DHCP addressing, and internet access had not been verified.**

## Verified on the phone

- Signature-verified Fedora aarch64 libqmi/qmicli and required libraries were added only under `/opt/picasso-wifi-trial/qmi-tools`. No RPM was installed and no installation script ran; the firmware-update tool from the same package was not uploaded.
- With the WLAN driver unloaded, a read-only `DMS Get MAC Address (WLAN)` request obtained the default address reported by this device's firmware. The module still used only the three authorized NV working copies. persist/fsc, SIM, and other interfaces such as phone identifiers were not read. The returned address was a valid globally administered unicast address; no MAC was generated, derived, or fabricated.
- Standard WLFW QMI `0x0033` / TLV `0x10` supplied that address to the running firmware before loading SNOC. Both the current `wlan0` MAC and the wiphy permanent MAC matched the DMS response, and still matched after scanning. This was firmware runtime configuration, not a change to a firmware partition or calibration contents. Provisioning must be repeated after every MPSS restart; it cannot be omitted.
- `/etc/NetworkManager/conf.d/90-picasso-wifi-identity.conf` disabled scan randomization and defaulted connections to `permanent`. The default was `managed=0`, with controlled operations explicitly allowed only after identity/regulatory verification.
- The final global regulatory domain was **SG**. The wiphy's original EEPROM constraint label could still show US; the label alone did not establish actual restrictions. Frequency ranges, EIRP, and DFS flags of all 36 enabled 20 MHz channels were checked to be within the observed SG regdb rules. BDF, regdb, the original EEPROM, and regulatory protection bits were not modified. RF transmit certification and complete wide-channel certification were not claimed.
- Scanning actually found `${PRIMARY_SSID}`: 5240 MHz / channel 48, advertising WPA1/WPA2, signal approximately 27%. The prepared `picasso-${PRIMARY_SSID}` profile accepted only WPA2/RSN + CCMP, without WPA1 fallback, using the permanent MAC. It did not autoconnect; the initial connection test was IPv4-only with inbound traffic in firewalld's `drop` zone, leaving USB SSH rules unchanged.

## Enter the password locally, not in chat

Run in the host's **local interactive terminal**:

```sh
cd "${REPO_ROOT}"
tools/${WIFI_CREDENTIAL_SCRIPT}
```

The script used the existing private key and fixed known_hosts to SSH into the phone, then prompted twice with hidden input.
It did not accept a password from argv/pipes/chat, use `--show-secrets`, or read saved host Wi-Fi passwords.
The phone wrote the equivalent WPA2 PMK to root-only `/run/picasso-${PRIMARY_SSID}.passwd` (0600, O_EXCL/NOFOLLOW).
This remained a sensitive network credential: do not print, upload, or include it as evidence. It existed only in phone tmpfs, was deleted by the test's finally cleanup, and would also disappear on reboot.
At this stage no credential file existed. After successful entry, reply “entered” before starting the timed connection test; entry alone did not start wireless.

The next step was `nmcli connection up ... passwd-file /run/picasso-${PRIMARY_SSID}.passwd`, without putting a password in process arguments.
After checking association/encryption, MAC, IPv4 DHCP, DNS/routes/network access, the experiment would be shut down and credentials deleted.
The profile used `psk-flags=not-saved`, so no password was persisted in the connection configuration; continuous operation would require separate discussion.

## Ordering and failure records

- Sending the SG user hint before registering a wiphy whose EEPROM default was US once produced global `98` intersection while the effective channels still followed US. **A successful iw command or global label was not enough**; before scanning, the audit rejected settings beyond SG, including actual 30 dBm on 2.4 GHz.
- Clearing experimental Wi-Fi module state with no active PHY, allowing the default driver hint to complete first, and then applying the SG user restriction made it take effect correctly. Original hardware constraints were retained. ATH certification/testing and dynamic regulatory-bypass switches were not enabled, nor was the calibration country code hard-modified.
- Module reload changed the nl80211 generic-netlink family. A stale cached supplicant handle fell back to unsupported WEXT once, producing an empty scan. Restarting the phone's wpa_supplicant while disconnected refreshed the handle and restored scanning. WEXT was not enabled and failed state was not cleared to hide the error.
- Scanning was asynchronous: an empty cache after five seconds was not completion. Bounded polling eventually found the target when the cache reached 40 entries. Only the user-designated SSID record was retained, without outputting other SSIDs/BSSIDs.
- Five intermediate failures and source versions were retained. The final trial result was `sg-mac-probe6-result.json`; no new modem crash occurred.

## Safe exit and evidence

The phone still ran temporary wifi2 #10. After the experiment, wlan0 was unloaded, DSP offline, proxy/TFTP/short-lived MAC client stopped, and 2.5 MiB of RMTFS shared memory zeroed.
USB SSH remained available; boot was not flashed, and normal reboot would still return to #8.

Full O_DIRECT readback of the three original NV partitions and checks of 0400 originals again showed no change.
The original 15,285 static files, boot, seven preserved partitions, and six LUN GPTs all matched.
NV updates occurred only in working copies. Battery/charging/long-term stability still had no acceptance.

Evidence was in private directory `out/wifi-sg-mac-20261027/`; the raw default-MAC record existed only in the phone's root-only private NV directory.
Stage tests: 168 total, 167 passed, one optional QEMU test skipped.
The original [WIFI-SCAN.md](WIFI-SCAN.md) / RMTFS results remained historical stage records; scanning was not treated as a connected link or internet acceptance.
