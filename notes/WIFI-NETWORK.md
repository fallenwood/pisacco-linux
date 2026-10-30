# Wi-Fi 限时联网验收通过：${FALLBACK_SSID} / SG / 设备永久 MAC / Timed Wi-Fi Network Acceptance Passed: ${FALLBACK_SSID} / SG / Device Permanent MAC

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页是刷入前限时联网试验及清理后的历史记录，不代表当前仍在线或后续启动验收。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This is a historical record of the timed networking trial before flashing and its cleaned-up end state, not current connectivity or acceptance of a later boot. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

**后续已按用户新授权把同一份wifi2 #10写入boot，并通过正常重启，见 [WIFI-INSTALL.md](WIFI-INSTALL.md)。
以下保留刷入前的网络试验及结束时状态；不代表当前仍是临时启动，也不宣称重启后已重新联网。**

2026-10-28，Redmi K30 5G Picasso，临时 **6.18.58-picasso-lts-wifi2 #10**，原生 Fedora 44 / XFS。
**本轮已真实通过 WPA2、DHCP、DNS 和经 wlan0 的 HTTPS。当前已按试验约定断开并清理，不是仍保持在线或持久启用。**

## 同一轮实际证据

用户在本地执行一次性入口，助手仅接收完成通知后检查现有结果，**没有重复启动已运行的 exclusive 控制器**。
原始状态为 `passed_wpa2_ccmp_permanent_mac_sg_dhcp_dns_https_over_wlan0`，PID-1 单元退出成功。

| 项目 | 实际结果 |
|---|---|
| 目标 | 精确 SSID **${FALLBACK_SSID}**；定向主动发现，2447 MHz / 信道8，约 **-56 dBm** |
| 链路宽度 | PHY HT20 保守能力，关联后的实际接口 **20 MHz** |
| 地址 | 同设备 DMS 默认 WLAN MAC，经 WLFW runtime provision；当前/永久 MAC 一致，联网测试结束前再次一致；不随机、生成或借用地址 |
| 加密/关联 | 活跃精确 SSID、station authorized=yes、NetworkManager activated；本轮原生 supplicant 日志确认 **RSN/WPA2-only + CCMP PTK/GTK** |
| IPv4 | DHCP server/租约选项、wlan0 IPv4 地址、经 wlan0 的默认路由均验证 |
| 防火墙 | wlan0 实际 firewalld zone 为 **drop**；USB SSH 配置不变 |
| DNS | 直接绑定 wlan0 向 DHCP DNS 服务器发新 A 查询，`example.com` 响应 **rcode=0，2 条 answer**；不是只使用本地缓存 |
| 系统解析 | 原生 `getent ahostsv4 example.com` 成功，解析结果路由明确为 wlan0 |
| HTTPS | `curl -4 --interface wlan0 --noproxy '*' ... https://example.com/`；**HTTP 200，ssl_verify_result=0，下载577字节，约0.92秒** |
| 温度 | 本轮最高采样 **37.1°C**；低于40°C启动、45°C中止线保持不变 |

HTTPS 正常验证系统 CA/服务器证书，无 `-k`、代理、主机 NAT 或主机默认路由修改。
这验证了手机自身无线数据路径，而不是用 USB/主机联网代替 Wi-Fi。未运行 DNF、测速或长时间负载测试。

## SG：不是把 AP 国家码当作用户地区

AP Country IE 为 CN，会覆盖初始化时的 SG。连接后通过正常 `iw reg set SG` 用户请求，让内核生成
**98-intersection**（SG 与 AP 国家码的交集，不是手工伪造/设置98）。

同一轮对实际 PHY **24 个启用的20 MHz信道**逐一验证频率/EIRP/DFS 均为观察到的 SG 规则子集。
不是仅看命令成功或全局标签；没有修改 regdb、BDF、校准、regulatory 保护标志或启用测试绕过。
此验收仅覆盖实际20 MHz，不扩展为宽信道、RF/SAR/充电认证。

## 本轮仍使用的试验依赖

- 临时 wifi2、独立模块目录、原厂固件/BDF、标准 metadata-only firmware-5.bin。
- 原授权三份 NV 的只读原始备份和普通可写工作副本；RMTFS 后端仍是受限 DynamicUser、无 capabilities、精确字符设备权限、四个预开 FD。
  没有把原 NV 分区交给代理，没有读取 persist/fsc、写原 NV 或扩大受保护读取范围。
- MPSS 手动启动、自动恢复关闭；受限 Picasso 固定 MSA opt-in；没有全局 SCM/SMMU 放宽。
- 只读 opt-in 的 HT20/管理帧观测 core，普通 installed core 文件从未替换；每次新 MPSS 启动仍需先 DMS→WLFW MAC 提供。
- 控制器 CPU0–3；CPU6/7 最大频率在硬件可用表内临时限制为 **1,094,400 kHz**，有界读回验证。
  不修改 governor/min/电压/热策略/发射功率，检查全部传感器。此次低温不证明长期稳定。
- 明确精确SSID主动探测、profile band bg/hidden=yes（客户端探测策略，不是宣称或改动 AP 隐藏设置）、RSN/CCMP、永久 MAC、无自动连接、IPv4、入站drop。

## 凭据与结束后的真实状态

密码只在本地 TTY 隐藏输入，SSID-specific PMK 临时存手机 root0600 tmpfs；只有 native nmcli 通过 passwd-file 使用。
没有密码 argv、聊天、日志、秘密属性读取或旧缓存密钥恢复；未把 PMK 文件收集为证据。

正常 finally 及独立 PID-1 ExecStopPost 已实际验证：

- 连接断开，wlan0 unmanaged 后卸载，**DSP offline，无 WLAN 接口、无默认 IPv4 路由**。
- 代理/TFTP 停止，经验证的共享 RMTFS RAM **2,621,440字节**清零并读回。
- `/run/picasso-${FALLBACK_SSID}.passwd` 已删除，持久连接文件没有 psk 键，禁止自动连接保持。
- 原 installed core 的完整哈希保持 `ed2f66c7646c43c4b3106bed4c8a33e811d81a7aa1207775f4fabeb350900862`，诊断参数消失。
- CPU6 原最大 **2,208,000 kHz**、CPU7 原最大 **2,400,000 kHz** 已恢复并读回。
- USB sshd/firewalld active。临时 wifi2 #10 仍在运行；正常重启回已安装 #8。

三份原 NV 各8MiB再次完整 O_DIRECT 只读比对及0400私有备份一致；
**原15,285个静态文件、完整boot、七个保留分区、六个LUN GPT 再次一致**。
canonical #8 boot image SHA256 保持 `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c`。
没有刷写命令、原 NV 写回、GPT/DTBO/vbmeta 变更或主机网络改动。

## 验收边界及后续

这轮**已经完成，无需再录入密码或重复该一次性命令来验证同一结果**。
`tools/${WIFI_2G_TEST_SCRIPT}` 对应的 exclusive connect4 目录已用，重复执行会在录入前拒绝，这是预期保护。
后续助手应读现有结果，不盲目再启动。

仍不是“开机自动联网”或长期服务器验收：没有持久启用/保存Wi-Fi密码，已安装#8不继承临时#10实验支持。
再次正常使用需另行设计受控启动、私有副本生命周期、永久MAC/SG保持、热约束与凭据策略，并单独实际验证。
不能根据一次577字节HTTPS成功宣称吞吐、持续连接、漫游、休眠、断电恢复、充电/电池或RF安全通过。
Linux power-supply 遥测、长期温控/RAM/UFS/外设/watchdog等限制仍在；没有开启IPA/蜂窝数据，专有共享 modem 固件的RF行为不能保证静默。

## 不隐藏历史失败

5GHz ${PRIMARY_SSID} status3、关联后的 CN 域中止、45.1°C 热中止、即时QoS读回/恢复断言失败、wpa_cli套接字检查不兼容、单次被动漏检等原始结果均保留。
没有 reset-failed、删日志或把旧失败改成成功；当前成功不自动证明历史 DNF 任务恢复或长期状态健康。

证据：`out/wifi-network-acceptance-20261028/result.json`、原始 `connect-result.json`、独立清理、最终状态和完整性报告。
用户实际执行的源记录为 `out/wifi-${FALLBACK_SSID}-connect4-20261028/`；原准备校验集保持，新运行文件另存 RUN4-SHA256SUMS。
离线测试 **190项：189通过，1项可选QEMU跳过**；不把这些主机测试冒充真机网络结果。
前序记录：[WIFI-2G-CONNECTION.md](WIFI-2G-CONNECTION.md)。

## English

**The same wifi2 #10 was subsequently written to boot under new user authorization and passed a normal reboot; see [WIFI-INSTALL.md](WIFI-INSTALL.md).
The following preserves the networking trial before flashing and its end state. It does not mean the phone is still temporarily booted, nor claim networking was retested after reboot.**

2026-10-28, Redmi K30 5G Picasso, temporary **6.18.58-picasso-lts-wifi2 #10**, native Fedora 44 / XFS.
**This run really passed WPA2, DHCP, DNS, and HTTPS over wlan0. It was then disconnected and cleaned up as agreed, rather than left online or persistently enabled.**

## Actual evidence from the same run

The user ran the one-off entry point locally. The assistant inspected existing results only after receiving completion notification, **without restarting the already-run exclusive controller**.
The raw status was `passed_wpa2_ccmp_permanent_mac_sg_dhcp_dns_https_over_wlan0`; the PID-1 unit exited successfully.

| Item | Actual result |
|---|---|
| Target | Exact SSID **${FALLBACK_SSID}**; directed active discovery, 2447 MHz / channel 8, approximately **-56 dBm** |
| Link width | Conservative PHY HT20 capabilities; actual post-association interface width **20 MHz** |
| Address | Same-device DMS default WLAN MAC provisioned through WLFW at runtime; current/permanent MACs matched and were rechecked before the networking test ended; no random, generated, or borrowed address |
| Encryption/association | Active exact SSID, station authorized=yes, NetworkManager activated; this run's native supplicant logs confirmed **RSN/WPA2-only + CCMP PTK/GTK** |
| IPv4 | DHCP server/lease options, wlan0 IPv4 address, and default route over wlan0 verified |
| Firewall | Actual wlan0 firewalld zone **drop**; USB SSH configuration unchanged |
| DNS | A new A query sent directly to the DHCP DNS server, bound to wlan0; `example.com` response **rcode=0, 2 answers**, not merely local cache |
| System resolution | Native `getent ahostsv4 example.com` succeeded; resolved-address routing explicitly used wlan0 |
| HTTPS | `curl -4 --interface wlan0 --noproxy '*' ... https://example.com/`; **HTTP 200, ssl_verify_result=0, 577 bytes downloaded, approximately 0.92 seconds** |
| Temperature | Highest sample **37.1°C**; below-40°C start and 45°C abort thresholds unchanged |

HTTPS normally verified the system CA/server certificate, with no `-k`, proxy, host NAT, or host default-route changes.
This verified the phone's own wireless data path, not USB/host networking substituted for Wi-Fi.
No DNF, speed test, or long-duration load test ran.

## SG: the AP country code was not treated as the user's location

The AP Country IE was CN, which would overwrite the initial SG.
After connection, a normal `iw reg set SG` user request caused the kernel to generate **98-intersection**, the intersection of SG and the AP country code, not fabricated/manually set 98.

In the same run, frequency/EIRP/DFS of all **24 enabled 20 MHz channels** on the actual PHY were individually verified as subsets of the observed SG rules.
This was not merely command success or a global-label check. regdb, BDF, calibration, and regulatory protection flags were unchanged, and no testing bypass was enabled.
Acceptance covered only actual 20 MHz, not wide channels, RF/SAR, or charging certification.

## Trial dependencies still in use

- Temporary wifi2, separate module directory, factory firmware/BDF, and standard metadata-only firmware-5.bin.
- Read-only original backups and regular writable working copies of the three authorized NV partitions. The RMTFS backend still used restricted DynamicUser, no capabilities, exact character-device permissions, and four preopened FDs. Original NV partitions were not given to the proxy; persist/fsc were not read, original NV was not written, and protected-read scope was not expanded.
- Manual MPSS startup, automatic recovery disabled, restricted Picasso fixed-MSA opt-in; no global SCM/SMMU relaxation.
- Read-only opt-in HT20/management-frame observation core; the ordinary installed core file was never replaced. Each new MPSS startup still required DMS→WLFW MAC provisioning first.
- Controller on CPU0–3. CPU6/7 maximum frequencies were temporarily capped to **1,094,400 kHz** from the hardware-supported table, with bounded readback validation. Governor/minimum/voltage/thermal policy/transmit power were unchanged, and all sensors were checked. This low-temperature run did not prove long-term stability.
- Explicit exact-SSID active probing, profile band bg/hidden=yes (client probing policy, not an assertion of or change to AP hidden settings), RSN/CCMP, permanent MAC, no autoconnect, IPv4, and inbound drop.

## Credentials and actual end state

The password was entered hidden only on a local TTY. An SSID-specific PMK was temporarily held in phone root0600 tmpfs, used only by native nmcli through passwd-file.
No password argv/chat/logs, secret-property reads, or recovery of old cached keys; the PMK file was not collected as evidence.

Normal finally cleanup and independent PID-1 ExecStopPost actually verified:

- Connection disconnected, wlan0 set unmanaged then unloaded; **DSP offline, no WLAN interface, no default IPv4 route**.
- Proxy/TFTP stopped; the verified **2,621,440-byte** shared RMTFS RAM zeroed and read back.
- `/run/picasso-${FALLBACK_SSID}.passwd` deleted; no psk key in the persistent connection file, autoconnect prohibition retained.
- Original installed core's full hash remained `ed2f66c7646c43c4b3106bed4c8a33e811d81a7aa1207775f4fabeb350900862`; diagnostic parameters were gone.
- Original CPU6 maximum **2,208,000 kHz** and CPU7 maximum **2,400,000 kHz** restored and read back.
- USB sshd/firewalld active. Temporary wifi2 #10 was still running; a normal reboot would return to installed #8.

The three original NV partitions, 8 MiB each, were again fully compared read-only with O_DIRECT and matched the 0400 private backups.
**The original 15,285 static files, complete boot, seven preserved partitions, and six LUN GPTs matched again.**
Canonical #8 boot image SHA256 remained `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c`.
There were no flashing commands, original-NV writebacks, GPT/DTBO/vbmeta changes, or host network changes.

## Acceptance boundaries and next steps

This run **was complete; no password re-entry or repetition of the one-off command was needed to verify the same result**.
The exclusive connect4 directory targeted by `tools/${WIFI_2G_TEST_SCRIPT}` was already used; another invocation would reject before credential entry, an intentional safeguard.
Future assistants should read the existing results, not blindly restart it.

This still was not “automatic networking at boot” or long-term server acceptance.
Wi-Fi credentials had not been persistently enabled/saved, and installed #8 did not inherit temporary #10 experimental support.
Further normal use required a separately designed and actually verified controlled startup, private-copy lifecycle, permanent-MAC/SG maintenance, thermal constraints, and credential policy.
A single successful 577-byte HTTPS transfer could not establish throughput, sustained connectivity, roaming, sleep, power-loss recovery, charging/battery, or RF safety.
Linux power-supply telemetry and long-term thermal/RAM/UFS/peripheral/watchdog limitations remained.
IPA/cellular data were not enabled; RF silence of the proprietary shared modem firmware could not be guaranteed.

## Historical failures were not hidden

Raw results were retained for ${PRIMARY_SSID} 5 GHz status3, post-association CN-domain abort, 45.1°C thermal abort, immediate QoS readback/restoration assertion failure, incompatible wpa_cli-socket checks, and missed detection by a single passive scan.
There was no reset-failed, log deletion, or conversion of old failures into success.
Current success did not automatically prove historical DNF jobs had recovered or that long-term system health was acceptable.

Evidence: `out/wifi-network-acceptance-20261028/result.json`, raw `connect-result.json`, independent cleanup, final state, and integrity reports.
The source record actually run by the user was `out/wifi-${FALLBACK_SSID}-connect4-20261028/`; the original preparation verification set remained, and newly run files were separately recorded in RUN4-SHA256SUMS.
Offline tests: **190 total, 189 passed, one optional QEMU test skipped**; host tests were not presented as on-device networking results.
Earlier record: [WIFI-2G-CONNECTION.md](WIFI-2G-CONNECTION.md).
