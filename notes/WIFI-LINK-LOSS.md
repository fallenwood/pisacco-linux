# Wi-Fi 掉线定位：固件 beacon miss 先触发，-110 是随后删钥超时 / Wi-Fi link-loss diagnosis: firmware beacon miss triggers first; -110 is the subsequent key-removal timeout

> 文档范围 / Scope: 本文保留掉线诊断阶段证据和未证实根因；后续状态横幅是历史更新，不是实时硬件结论。 / This preserves link-loss-stage evidence and the unproven root cause; later status banners are historical updates, not live hardware conclusions.

## 中文

> 后续独立受保护自动连接服务已按用户请求启用，45秒完整原生验收后转常驻，当前2.4GHz联网，见[WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md)。**本页触发链和根因未证实结论不变；新连接窗口不能改写旧失败或宣称beacon已修复。** 以下“disabled/关闭”是该诊断阶段快照。

2026-10-28，已安装wifi2 #10，原生Fedora44/XFS，USB固定位置。
**已确认实际触发链，不再把键操作-110当作最初装钥失败。尚未证明空口/固件内部为何漏beacon，尚未修复或启用默认联网。**

前序：[WIFI-AUTOCONNECT.md](WIFI-AUTOCONNECT.md)。凭据已获明确同意保存，本阶段只由native nmcli passwd-file使用，
控制器不读取密钥内容、不重新录入/派生，不扩大原NV/persist/fsc/SIM访问范围。

## 两次仅观测真机复现

新core仅在独立 `/opt/picasso-wifi-trial/modules/` 路径使用，default-off/read-only `picasso_link_observe=1`，限定Picasso+SNOC。
保持HT20、管理TX观察关闭、QMI-only日志，增加扫描/roam/目标AP beacon/SET_KEY或DISABLE_KEY完成元数据。
**没有打印MAC、key bytes或帧载荷，没有伪造ACK、改变返回状态、放宽监管域或延长/关闭beacon/probe/loss检测。**

| 相对CONNECTED时间 | 观察1 | 观察2 |
|---|---:|---:|
| 初始SET_KEY完成 | 连接前两次均成功 | 连接前两次均成功 |
| 固件WMI roam reason=2（BEACON_MISS） | +44.300s | +18.210s |
| ath10k beacon_miss / supplicant BEACON-LOSS | +44.302s | +18.214s |
| DISABLE_KEY开始 | +47.653s | +18.810s |
| ath10k独立延迟loss_work | +47.555s | +21.462s |
| DISABLE_KEY等待完成失败 | +50.887s | +21.979s |
| 本地断开 reason=4 | +51.046s | +22.126s |

两次均真实完成WPA2/CCMP、DHCP、SG交集、DNS及wlan0绑定/无代理/证书验证HTTPS200。
两次的关联期间 **没有任何WMI扫描事件**，beacon miss时host scan_state=0（IDLE）；
不能再把这两次归为关联期间后台离信道扫描导致。

观察1到最后仍有授权和来自目标peer的接收统计增长，signal约-56至-67dBm；
beacon loss前后的接口RX计数也增长。这不支持“所有无线接收完全停止”，但统计本身不等于每个包经端到端完整性验证。
PHY/实际信道/EIRP/DFS/永久MAC检查保持，未移动手机或提高发射功率。

### 观察2的RX边界证据

在原有CRC/decrypt/key-cache/CAC过滤**之前**，对匹配已关联AP的beacon只累计元数据：

- pre-filter目标beacon=2，原正常beacon处理路径计数=2；已观察的匹配帧errors=0、status=0、channel=8。
- 固件报BEACON_MISS时，最后一个正常目标beacon距今约 **6,184毫秒**。
- 这一批目标beacon没有在Linux原有CRC/解密过滤处丢掉；缺口已在更早的接收/交付边界。

这**不是空口抓包**，不能证明AP每个beacon都发出了、RF没有丢帧或固件所有入口没有CRC错误；
BSSID已损坏/未交付的帧也不在“匹配目标AP”计数内。不能仅凭signal或计数宣布“路由器坏了”或“固件一定误报”。

## 源码解释：两种清理先后顺序都合法

- `wmi.h`：WMI_ROAM_REASON_BEACON_MISS=2；`wmi.c:ath10k_wmi_event_roam()`对应调用beacon-miss处理。
- `mac.c:ath10k_mac_handle_beacon_miss_iter()`正常调用`ieee80211_beacon_loss()`，并保留原`ATH10K_CONNECTION_LOSS_HZ=3*HZ`延迟work。
- mac80211先进行AP存活探测，探测失败可以在延迟work之前开始拆连接；否则ath10k延迟work也可提交connection_loss。
  **所以不能强行要求loss_work必须在DISABLE_KEY之前。** 两次实测正好覆盖两种先后顺序。
- Linux `enum set_key_cmd`：SET_KEY=0、DISABLE_KEY=1；观测证明超时的是cmd=1。
- `ath10k_install_key()`复用同一WMI路径和completion等待处理安装/删除；它的上层错误字符串仍叫“failed to install key”，
  即使正在删钥，也会这样打印。3秒等待失败得到-ETIMEDOUT（-110）。

因此，**错误日志的“install”不能单独作为重新装钥/密码失败的证据**。
最初两次SET_KEY完成、真实CCMP/TLS数据路径都已通过；后续没有观测到更早的SET_KEY超时。
删钥completion缺失仍是一个需要关注的次级问题，但不是这两轮最早的掉线触发。

## 已收窄与仍未知

已收窄到 **WCN3990固件报告beacon miss → 主机正常失联处理**，上游重点是关联态beacon接收/交付/固件监测。
已排除本轮证据中的密码/初始装钥失败、ARP/DNS/HTTPS不通作为最先触发，及关联期间off-channel扫描。
不能扩展为所有未来掉线都必然相同。

原三轮约17.6–17.8秒是当时的观察值，**不是不可变的18秒定时器**：加入观测后的两次为51.0秒和22.1秒。
它们共享相同触发链；不能靠18秒重连、取消beacon检测或吞掉-110伪造修复。

仍需进一步区分：空口真实beacon缺失/干扰，与WCN3990关联态过滤、接收或固件监测行为。
下一步可对比受限同频被动发现与关联态RX，或核对匹配版本厂商beacon/offload配置与TLV ABI；
不猜校准/BDF/链路功率，不降级固件，不制造RAW_MODE等能力以强行启用不受支持的软件加密。

## 模块、构建与恢复

- 观察1core SHA256：`517c2ee9f0bf1bb52c9497951fa3430c5607e2884ebff5317df9ce7474115446`。
- 观察2core SHA256：`43179652cf36be8635974563cb98a65dbc22dc2e7fb57ae85562b81a2971fada`。
- 配置/ABI保持`6.18.58-picasso-lts-wifi2`；LLVM真实AArch64构建，未把主机重放当真机验收。
- 公共补丁`kernel/diagnostics/ath10k-picasso-link-observer.patch`在mgmt-observer/HT20诊断补丁之后应用，
  **不在正常patches/series**。从保存的正常源码重新应用三补丁与实际v2构建源码逐字节一致。
- 主机正常mac.c/wmi.c及源码树原core已还原为改动前哈希；没有替换手机/lib/modules core、depmod或刷boot。
- `tools/diagnose-wifi-link.py`只在内存中复制/覆盖诊断配置，沿用同一守卫/私有副本/永久MAC/SG/温控/清理逻辑；
  不修改默认服务配置或读取密码。每轮新PID1单元，独立ExecStopPost、root PID租约、45°C关停、无恢复循环。

两轮最高采样均38.4°C，均安全清理：WLAN卸载、DSP offline、代理/TFTP停止、经验证2.5MiB RAM清零读回，
原core及CPU6/7最大频率恢复，原静态文件/boot/七保留分区/六GPT/三原NV及0400备份再次一致。
持久凭据按授权保留，原NV从未作为可写后端；默认Wi-Fi服务仍disabled，不声称已修复或开机联网通过。

证据：`out/wifi-link-loss-20261028/`，两个独立结果/事件/样本、源码/补丁/构建及再应用证明、清理/最终完整性。
`tools/wifi-loss-evidence.py`只分析提供的原生journal行、输出无标识符的顺序证明；它是分析工具，不是当前连接。
离线222项：221通过、1可选QEMU跳过。历史失败和负向租约试验保留，没有reset-failed。
充电/RF安全、长期热/内存/UFS/休眠/掉电等验收边界不变。

## English

> A later independent guarded autoconnection service was enabled at the user's request and made persistent after complete 45-second native acceptance, with 2.4GHz connectivity at that stage; see [WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md). **This page's trigger chain and unproven-root-cause conclusion remain unchanged; a new connection window cannot rewrite old failures or claim the beacon problem is fixed.** “Disabled/off” below is a snapshot of this diagnostic stage.

2026-10-28, wifi2 #10 installed, native Fedora44/XFS, fixed USB position.
**The actual trigger chain is confirmed: key-operation -110 is no longer treated as an initial key-installation failure. Why beacons were missed over the air/inside firmware remains unproven; no fix or default connectivity was enabled.**

Preceding record: [WIFI-AUTOCONNECT.md](WIFI-AUTOCONNECT.md). Explicit consent to save credentials had been obtained; in this stage they were used only by native nmcli passwd-file.
The controller did not read key contents, re-enter/derive them, or expand access to original NV/persist/fsc/SIM.

### Two observation-only hardware reproductions

The new core was used only under the separate `/opt/picasso-wifi-trial/modules/` path, with default-off/read-only `picasso_link_observe=1`, restricted to Picasso+SNOC.
HT20, management-TX observation off, and QMI-only logging remained; scan/roam/target-AP beacon/SET_KEY or DISABLE_KEY completion metadata was added.
**No MAC, key bytes, or frame payloads were printed; no ACK was fabricated, return status changed, regulatory domain relaxed, or beacon/probe/loss detection extended/disabled.**

| Time relative to CONNECTED | Observation 1 | Observation 2 |
|---|---:|---:|
| Initial SET_KEY completion | Both succeeded before connection | Both succeeded before connection |
| Firmware WMI roam reason=2 (BEACON_MISS) | +44.300s | +18.210s |
| ath10k beacon_miss / supplicant BEACON-LOSS | +44.302s | +18.214s |
| DISABLE_KEY started | +47.653s | +18.810s |
| ath10k independent delayed loss_work | +47.555s | +21.462s |
| DISABLE_KEY completion wait failed | +50.887s | +21.979s |
| Local disconnect reason=4 | +51.046s | +22.126s |

Both genuinely completed WPA2/CCMP, DHCP, SG intersection, DNS, and wlan0-bound/no-proxy/certificate-verified HTTPS200.
Neither association period had **any WMI scan events**; host scan_state=0 (IDLE) at beacon miss.
These two runs can no longer be attributed to background off-channel scanning during association.

Observation 1 still showed authorization and growing receive statistics from the target peer to the end, with signal about -56 to -67dBm.
Interface RX counters also grew before and after beacon loss. This does not support “all wireless reception stopped completely,” but statistics alone do not mean every packet underwent end-to-end integrity validation.
PHY/actual channel/EIRP/DFS/permanent-MAC checks remained; the phone was not moved and transmit power was not raised.

#### Observation 2 RX-boundary evidence

**Before** the existing CRC/decrypt/key-cache/CAC filters, only metadata was accumulated for beacons matching the associated AP:

- Pre-filter target beacons=2, original normal beacon-processing path count=2; observed matching frames had errors=0, status=0, channel=8.
- When firmware reported BEACON_MISS, the last normal target beacon was about **6,184 milliseconds** old.
- This batch of target beacons was not dropped by Linux's original CRC/decryption filters; the gap was already at an earlier reception/delivery boundary.

This **is not an over-the-air capture**. It cannot prove the AP transmitted every beacon, RF lost no frames, or all firmware ingress paths had no CRC errors.
Frames with corrupted BSSID/not delivered are also outside the “matching target AP” count. Signal or counts alone cannot justify “the router is broken” or “firmware definitely falsely reported it.”

### Source explanation: both cleanup orders are valid

- `wmi.h`: WMI_ROAM_REASON_BEACON_MISS=2; `wmi.c:ath10k_wmi_event_roam()` calls beacon-miss handling accordingly.
- `mac.c:ath10k_mac_handle_beacon_miss_iter()` normally calls `ieee80211_beacon_loss()` and retains the original `ATH10K_CONNECTION_LOSS_HZ=3*HZ` delayed work.
- mac80211 first probes AP liveness. Failed probing can begin tearing down the connection before delayed work; otherwise ath10k delayed work can also submit connection_loss.
  **Therefore loss_work need not precede DISABLE_KEY.** The two measurements cover both orders.
- Linux `enum set_key_cmd`: SET_KEY=0, DISABLE_KEY=1; observation proves the timed-out command was cmd=1.
- `ath10k_install_key()` reuses the same WMI path and completion wait for installation/removal; its upper-level error string still says “failed to install key,”
  including during key removal. Failure of the 3-second wait yields -ETIMEDOUT (-110).

Therefore **“install” in the error log alone is not evidence of reinstallation/password failure**.
The initial two SET_KEY completions and real CCMP/TLS data path passed; no earlier SET_KEY timeout was observed afterward.
Missing key-removal completion remains a secondary concern, but was not the earliest link-loss trigger in these two rounds.

### Narrowed findings and remaining unknowns

The chain is narrowed to **WCN3990 firmware reports beacon miss → normal host link-loss handling**; upstream focus is associated-state beacon reception/delivery/firmware monitoring.
The evidence in these rounds excludes password/initial key-install failure, ARP/DNS/HTTPS failure as the first trigger, and off-channel scanning during association.
This cannot be generalized to every future disconnection.

The original three rounds' about 17.6–17.8 seconds were observations at the time, **not an immutable 18-second timer**: the two runs with added observation lasted 51.0 and 22.1 seconds.
They share the same trigger chain; reconnecting every 18 seconds, canceling beacon detection, or swallowing -110 cannot fake a fix.

Further distinction is needed between genuine over-the-air beacon absence/interference and WCN3990 associated-state filtering, reception, or firmware monitoring behavior.
Next steps may compare restricted same-frequency passive discovery with associated RX, or check matching vendor beacon/offload configuration and TLV ABI.
Do not guess calibration/BDF/link power, downgrade firmware, or fabricate capabilities such as RAW_MODE to force unsupported software encryption.

### Modules, build, and restoration

- Observation 1 core SHA256: `517c2ee9f0bf1bb52c9497951fa3430c5607e2884ebff5317df9ce7474115446`.
- Observation 2 core SHA256: `43179652cf36be8635974563cb98a65dbc22dc2e7fb57ae85562b81a2971fada`.
- Configuration/ABI remained `6.18.58-picasso-lts-wifi2`; actual LLVM AArch64 builds were used, not host replay presented as hardware acceptance.
- Public patch `kernel/diagnostics/ath10k-picasso-link-observer.patch` is applied after the mgmt-observer/HT20 diagnostic patches,
  **not in normal patches/series**. Reapplying the three patches to saved normal source matched the actual v2 build source byte-for-byte.
- Normal host mac.c/wmi.c and the source tree's original core were restored to pre-change hashes; the phone's /lib/modules core was not replaced, depmod was not run, and boot was not flashed.
- `tools/diagnose-wifi-link.py` copies/overrides diagnostic configuration only in memory, reusing the same guards/private copies/permanent MAC/SG/thermal/cleanup logic.
  It does not change default service configuration or read passwords. Each round uses a new PID1 unit, independent ExecStopPost, root PID lease, 45°C shutdown, and no recovery loop.

Both rounds peaked at sampled 38.4°C and cleaned up safely: WLAN unloaded, DSP offline, proxy/TFTP stopped, verified 2.5MiB RAM zeroed and read back,
original core and CPU6/7 maximum frequencies restored; original static files/boot/seven protected partitions/six GPTs/three original NVs and 0400 backups matched again.
Persistent credentials were retained as authorized; original NV was never a writable backend. The default Wi-Fi service remained disabled; no claim of a fix or accepted boot-time connectivity is made.

Evidence: `out/wifi-link-loss-20261028/`, with two independent results/events/samples, source/patch/build and reapplication proof, cleanup/final integrity.
`tools/wifi-loss-evidence.py` only analyzes supplied native journal lines and outputs identifier-free ordering proof; it is an analysis tool, not a current connection.
Offline: 222 cases, 221 passed, 1 optional QEMU skipped. Historical failures and negative lease trials are retained, without reset-failed.
Charging/RF safety and long-term thermal/memory/UFS/suspend/power-loss acceptance boundaries remain unchanged.
