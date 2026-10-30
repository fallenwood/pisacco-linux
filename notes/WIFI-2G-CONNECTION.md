# 2.4 GHz：WPA2 与 DHCP 已通过；监管域收尾验证后待重测联网（历史过程） / 2.4 GHz: WPA2 and DHCP Passed; Network Retest Awaited After Post-Association Regulatory Verification (Historical Process)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页保留分轮连接失败、修正及当时准备状态，后续完整联网见更新链接，不代表当前在线状态。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This page preserves successive connection failures, corrections, and preparation at the time; linked updates cover complete networking later, not a claim of current connectivity. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

**后续 connect4 已同轮通过 WPA2/DHCP、实际SG限制、实时DNS及显式wlan0 HTTPS，HTTP200且证书验证通过。
本轮已完成并按约定断开/删除临时凭据/恢复模块及频率，不需再次录入或重复已用的一次性命令。
最新见 [WIFI-NETWORK.md](WIFI-NETWORK.md)。以下保留早期失败、修复和当时准备状态。**

本轮用户完成本地凭据录入并要求继续。固定 USB 位置、SG、本机永久 MAC、HT20 和 WPA2/CCMP 要求不变。
**已通过真实 WPA2 握手与 DHCP，但 DNS/互联网仍未验证，当前无线已停止。**

## 第一次完整激活：不是密码错误

- 只检查 `/run/picasso-${FALLBACK_SSID}.passwd` 的普通文件/root/0600/单链接/大小元数据，不读取或显示其内容。
  native nmcli 通过 passwd-file 使用临时 PMK；无密码 argv、聊天或日志。
- 当前/永久 MAC 与本机 DMS 一致；初始 SG 实际信道限制审计通过；真实接口宽度 20 MHz。
- nmcli 激活成功、设备状态 100；supplicant 原始生命周期日志明确记录：
  **Key negotiation completed，PTK=CCMP、GTK=CCMP，CTRL-EVENT-CONNECTED**。
- NetworkManager 日志明确记录 DHCP 获得新租约，并完成 activated。这是实际 WPA2/DHCP 成功，不是仅扫描或 Open System auth。
- 紧接着的关联后监管复核失败：AP 的 Country IE 为 **CN**，内核实际全局域从 SG 变为 CN。
  检查拒绝接受外国全局域，没有把当前 2.4 GHz 信道可用等同于全 PHY 满足 SG。
- 因此在 DNS/HTTPS 测试之前主动中止、断开并删除临时凭据。失败单元和原始 CN 结果保留；不改用 CN、不修改 AP、regdb 或 regulatory 保护标志。

证据：`out/wifi-${FALLBACK_SSID}-connect-20261028/connect-result.json`、`network-lifecycle.log`。
旧 `out/wifi-${FALLBACK_SSID}-20261028/` 准备结果/校验集保持不变，新激活原始输出另有副本。

## SG 正常请求的无密码验证

不为了继续试验而提取缓存 PSK 或尝试假密码。新诊断先做 Open System auth，再用标准 RSN IE 宣告 WPA2/CCMP/PSK 能力并请求关联；
**不提供密钥、不回应四次握手、不安装 key、不授权数据端口**。这仅触发该真实 AP 的 Country IE，station 状态实际验证 authorized=no。

- 第一轮在无线初始化等待时采样到 **45.1°C**，立即按原 45°C 线中止并清理。该失败保留，未提高阈值或忽略传感器。
- cpu7-thermal 为主要热点。仅绑定控制器到 CPU0–3 不足以约束内核其他工作。
- 后续试验在确认 qcom-cpufreq-hw、CPU6/7 身份、硬件频率表、原 min/max 后，临时将两核 **scaling_max_freq 降为 1,094,400 kHz**。
  不修改 governor、最小频率、电压、热管理策略或射频功率；仍检查全部传感器。
- 第一次限频试验的即时读回断言失败，恢复检查也报错；旧结果 `cleanup_requires_attention` 不改。
  后续原生读回确认原上限，代码改为有限等待 QoS 读回稳定后验证，不把 sysfs write 成功当作限制已生效。
- 最终限频诊断实际收到 auth/assoc completion status 0；观察到 AP 真实 CN 域，然后发送正常 **`iw reg set SG`**。
  Linux 根据 `reg.c` 的 COUNTRY_IE → user-request 路径生成交集域 **98**，不是用户伪造/手工设置 98。
- 实际 PHY 的 **24 个启用的 20 MHz 信道**逐一通过 SG 频率/EIRP/DFS 子集审计，且数据端口保持未授权。
  这验证了关联后“再请求 SG 并检查真实交集”的收尾方法，不是只看标签或忽略 AP 信息。
- 该最终诊断最高采样 **37.4°C**。这是一次短时结果，不是长期热稳定/充电安全认证。
- 独立 ExecStopPost 验证 DSP/无线停止、2.5 MiB RMTFS RAM 清零、原 core 恢复、CPU6 原 **2,208,000 kHz** 和 CPU7 原 **2,400,000 kHz** 上限恢复。

原始独立诊断目录均保留：

- `out/wifi-sg-postassoc-20261028/`（45.1°C 中止）
- `out/wifi-sg-postassoc-capped-20261028/`（即时读回/恢复断言失败）
- `out/wifi-sg-postassoc-capped2-20261028/`（有限等待、真实 CN→SG/98 子集验证成功）

## 首次中止后的状态与当时重测计划（后续见下节）

- DSP offline、无 WLAN 接口/默认 IPv4 路由；sshd/firewalld active。临时凭据不存在，持久连接无 psk 键。
- 原 `/lib/modules` core 完整哈希不变，诊断参数消失；CPU6/7 原上限再次原生读回一致。
- 三个原 NV 分区 O_DIRECT 只读完整比对、0400 私有备份、原 15,285 个静态文件、boot、七个保留分区、六个 GPT 全部一致。
  没有读取 persist/fsc、写原 NV、修改主机 Wi-Fi/NAT/默认路由、启用 IPA/蜂窝数据，或 reset-failed。
- 离线测试 **181 项：180 通过，1 项可选 QEMU 跳过**。增加 AP CN 不能充当 SG、98 标签仍必须接受真实信道/功率/DFS 检查的回归。

下一轮脚本已准备但未执行：
`out/wifi-${FALLBACK_SSID}-connect2-20261028/{connect-trial.py,cleanup-connect.py,run-connect.py,connect-controller.service}`。
它整合临时 CPU 上限及有界读回/恢复、WPA2 后的正常 SG 再请求/交集审计、实际 20 MHz、永久 MAC、DHCP/DNS/显式 wlan0 HTTPS。
仍保留 75 秒控制器预算/90 秒 PID-1 上限、45°C 中止、独立清理和临时凭据删除。整合路径尚待真实联网测试，不能用独立诊断替代。

最新 NV 工作副本 checkpoint 必须用：
`out/wifi-sg-postassoc-capped2-20261028/result.json:private_copy_final_hashes`，不是第一次激活或准备阶段的旧值。

密码已证实可用，但第一轮按承诺清理了文件，需要用户在本地终端**再录入一次同一密码**：

```sh
cd "${REPO_ROOT}"
tools/${WIFI_2G_CREDENTIAL_SCRIPT}
```

不要把密码发到聊天中；录入后回复“已录入”。此工具不启动无线。
正常重启仍回未改的已安装 #8；当前仍是临时 wifi2 #10，不是持久启用/生产稳定验收。

## 第二轮整合测试：SG、WPA2、DHCP、限频通过，检查工具中止

用户重新录入后执行了 connect2。实际 CPU 频率上限及恢复均通过，最高采样 **37.1°C**。
关联后正常重发 SG 并对内核 `98` 交集的 **24 个启用的 20 MHz 信道**审计通过；永久 MAC 和实际 20 MHz 保持。
同一轮 supplicant 日志再次有 PTK/GTK=CCMP、CONNECTED；NM 生命周期明确有 DHCP 新租约、activated。
**这次不是无线连接或 SG 失败**，但检查工具错误地假定存在每接口 wpa_cli 控制套接字：
`Failed to connect to non-global ctrl_ifname: wlan0`，故在 DNS/HTTPS 前提前中止。
NetworkManager 实际使用 supplicant D-Bus，此套接字不是必需配置。没有为了探测而开启 key dump 或读取 Network.Properties/PSK。

清理仍照常执行：凭据删除、无线/DSP 停止、原 core 和原 CPU 最大频率恢复，原 NV/master/静态文件/boot/保留分区/GPT 再次一致。
原始失败保留为 `out/wifi-${FALLBACK_SSID}-connect2-20261028/connect-result.json`；不改成一次完整联网成功。
DNS/互联网至此仍未验证，也没有一直保留连接。

新 `tools/wifi-auth-evidence.py` 不要求控制套接字：仅检查本轮单调时钟截断后的原生 supplicant 日志、匹配同一 AP 的 CCMP PTK/GTK 和 CONNECTED。
调用者另行检查强制 RSN-only 配置、真实 SSID、活跃设备和 station authorized=yes；不读取秘密属性。
后来断开、旧日志、不同 peer/接口、TKIP 或混合 WPA 配置均拒绝。主机单元测试和原生隔离回放已通过：
只在旧试验清理前的真实时间片验证成功，清理后的断开快照明确拒绝；回放不算当前连接验收。

下一轮准备于 `out/wifi-${FALLBACK_SSID}-connect3-20261028/`，采用此证据方式，仍保留全部 SG/限频/温度/永久 MAC/清理要求，整合网络路径尚未执行。
最新 NV checkpoint 改用 `out/wifi-${FALLBACK_SSID}-connect2-20261028/connect-result.json:private_copy_final_hashes`。
离线测试 **186 项：185 通过，1 项可选 QEMU 跳过**。

为减少“录入后再等一轮聊天”的往返，新增明确命名的一次性试验入口：

```sh
cd "${REPO_ROOT}"
tools/${WIFI_2G_TEST_SCRIPT}
```

**此命令与仅录入工具不同：本地隐藏录入后会立即启动最多 90 秒的联网试验**，不是持久启用。
密码仍只进入手机的 root0600 tmpfs 文件，不进参数、聊天或日志。启动前会用固定 SSH host key 检查本轮目录未用、没有待用凭据，拒绝覆盖/重复试验。
PID-1 独立收尾在成功/失败时删除临时凭据、停止无线/DSP、恢复频率和模块；未启动试验前若手动中断，待用凭据仍可能留在 /run，需告知助手核对，勿反复覆盖。
原 `${WIFI_2G_CREDENTIAL_SCRIPT}` 仍只录入、不启动无线，行为未改。

请等待整个命令结束后再回复“已完成”；助手应先查看保存结果和服务状态，不盲目再执行同一 exclusive 控制器。
一次性入口已通过 shell 语法/守卫测试；当时用户交互执行及新的 DNS/HTTPS 网络结果尚待验证，后续见下节。

## 第三轮一次性测试：旧信道单次被动扫描未见目标

用户执行了一次性入口，控制器确实运行，助手没有重复启动。
该轮在 WPA2 激活之前因 `scan freq 2447 passive` 一次未见目标而中止，未调用 nmcli up；
临时凭据按约定删除，最高采样 36.8°C，独立清理恢复频率/core、停止 DSP/无线并清共享 RAM。
这不能判为密码错误、网络不存在、换信道或新的握手故障；前两轮已证明的 WPA2/DHCP/SG 成功不改。
原始结果保留在 `out/wifi-${FALLBACK_SSID}-connect3-20261028/connect-result.json`。

随后不使用密码做限时发现：

- 所有合法启用 2.4 GHz 信道的三次被动扫描仍未发现精确 SSID，其他 BSS 数只作聚合，不保留邻居标识。
- 只向授权的 **${FALLBACK_SSID}** 定向主动探测、只用实际启用且可发起辐射的 2.4 GHz 信道：
  第二次发现目标，约 **-57 dBm，仍是 2447 MHz / 信道8**，Open System auth 第一帧 status0、应答成功。
- 这未证明 AP 隐藏 SSID 或某种特定驱动缺陷，也未观察到换信道。它证明不能依赖旧信道的一次被动扫描来否决连接。
- SG、HT20、设备当前/永久 MAC 校验通过；定向主动发现/认证最高采样37.1°C，结束后恢复原频率/core并停止 DSP/无线。
  没有启用 no-IR/disabled 信道、随机 MAC、调高功率或修改 AP。

发现证据分别在 `out/wifi-${FALLBACK_SSID}-discovery-20261028/` 和
`out/wifi-${FALLBACK_SSID}-active-discovery-20261028/`，各自失败/成功不覆盖。

新的 `tools/wifi-bss.py:active_2g_frequencies()` 从已经 SG 审计的真实 PHY 选择合法 2.4 GHz 可主动探测信道，
不绑定单一历史 AP 信道；disabled/no-IR/非2.4GHz/非标准频率均排除，无可用信道则拒绝。
单元测试和实际 PHY 原生离线回放通过。

新整合控制器为 `out/wifi-${FALLBACK_SSID}-connect4-20261028/`，仍未执行有密码的完整网络路径：

- 最多两次覆盖合法2.4GHz的精确SSID主动探测；即使预扫描未见，也允许 NetworkManager 在25秒内仅尝试用户明确授权的同一 RSN-only/bg 配置。
  不把一次扫描空结果当作网络绝对不存在，也不会退到其他 SSID 或 WPA1。
- 该配置只新增客户端 `802-11-wireless.hidden=yes`，使已知SSID使用定向探测；这不是改AP设置或宣称AP确实隐藏。
  band bg、RSN/CCMP、永久MAC、不保存秘密、不自动连接、drop、IPv4等不变。
- 依旧使用真实握手日志/实时授权验证、不依赖wpa_cli套接字；保留关联后的正常SG再请求、实际交集审计、临时CPU上限、45°C中止及独立清理。
- 一次性入口 `tools/${WIFI_2G_TEST_SCRIPT}` 已指向此新 exclusive 试验，且在询问密码前先验证原生临时内核、DSP offline、温度低于40°C。
  仍须用户本地隐藏录入；**该命令录入后会立即启动限时试验**，请等整个命令结束再回复。

最新 NV 工作副本 checkpoint：
`out/wifi-${FALLBACK_SSID}-active-discovery-20261028/result.json:private_copy_final_hashes`。
原 NV/master、15,285个静态文件、boot、七个保留分区、六个GPT再次一致，凭据不存在、原CPU频率/core恢复、当前无无线/默认路由。
离线测试 **190项：189通过，1项可选QEMU跳过**。DNS/互联网仍未验证，不能报告已经完成联网验收。

## English

**Subsequent connect4 passed WPA2/DHCP, actual SG restrictions, live DNS, and explicitly wlan0-bound HTTPS in the same run: HTTP 200 with certificate verification passed.
That run completed and, as agreed, disconnected, deleted temporary credentials, and restored modules/frequencies. No further entry or repetition of the already-used one-off command was needed.
See [WIFI-NETWORK.md](WIFI-NETWORK.md) for later results. The following preserves earlier failures, corrections, and preparation at the time.**

The user completed local credential entry and asked to continue.
Fixed USB position, SG, this device's permanent MAC, HT20, and WPA2/CCMP requirements remained unchanged.
**The real WPA2 handshake and DHCP passed, but DNS/internet had not been verified, and wireless was stopped at this stage.**

## First complete activation: not a password error

- Only regular-file/root/0600/single-link/size metadata of `/run/picasso-${FALLBACK_SSID}.passwd` was checked; contents were not read or displayed. Native nmcli used the temporary PMK through passwd-file, without password argv, chat, or logs.
- Current/permanent MACs matched this device's DMS. Initial audit of actual SG channel restrictions passed; actual interface width was 20 MHz.
- nmcli activation succeeded, device state 100. Raw supplicant lifecycle logs explicitly recorded **Key negotiation completed, PTK=CCMP, GTK=CCMP, CTRL-EVENT-CONNECTED**.
- NetworkManager logs explicitly recorded a new DHCP lease and completed activated state. This was actual WPA2/DHCP success, not merely scanning or Open System auth.
- The immediate post-association regulatory recheck failed: the AP Country IE was **CN**, and the kernel's actual global domain changed from SG to CN. The check rejected a foreign global domain; availability of the current 2.4 GHz channel was not treated as proof that the whole PHY met SG.
- The trial therefore deliberately aborted before DNS/HTTPS, disconnected, and deleted temporary credentials. The failed unit and original CN result were retained. It did not switch to CN, change the AP/regdb, or modify regulatory protection flags.

Evidence: `out/wifi-${FALLBACK_SSID}-connect-20261028/connect-result.json`, `network-lifecycle.log`.
Old preparation results/verification sets in `out/wifi-${FALLBACK_SSID}-20261028/` were unchanged; raw output from the new activation was separately copied.

## Password-free verification of a normal SG request

No cached PSK was extracted and no fake password tried to continue testing.
The new diagnostic performed Open System auth, then advertised WPA2/CCMP/PSK capabilities with a standard RSN IE and requested association.
**It supplied no keys, did not respond to the four-way handshake, installed no key, and did not authorize the data port.**
This only triggered the real AP's Country IE; station state was actually verified as authorized=no.

- The first run sampled **45.1°C** while waiting for wireless initialization, immediately aborted at the existing 45°C line, and cleaned up. The failure was retained; thresholds were not raised and sensors were not ignored.
- cpu7-thermal was the principal hotspot. Binding only the controller to CPU0–3 did not constrain other kernel work sufficiently.
- Later trials confirmed qcom-cpufreq-hw, CPU6/7 identities, hardware frequency tables, and original min/max values, then temporarily lowered both cores' **scaling_max_freq to 1,094,400 kHz**. Governor, minimum frequency, voltage, thermal policy, and RF power were unchanged; all sensors were still checked.
- The first capped trial's immediate readback assertion failed, and the restoration check also reported an error. The old `cleanup_requires_attention` result was not changed. Later native readback confirmed the original limits. Code changed to wait a bounded interval for QoS readback to settle before verifying, rather than treating a successful sysfs write as an effective cap.
- The final capped diagnostic actually received auth/assoc completion status 0, observed the AP's real CN domain, and then sent normal **`iw reg set SG`**. Linux generated intersection domain **98** through the COUNTRY_IE → user-request path in `reg.c`; 98 was not fabricated or manually set by the user.
- All **24 enabled 20 MHz channels** of the actual PHY individually passed the SG frequency/EIRP/DFS subset audit, with the data port remaining unauthorized. This verified the post-association method of “request SG again and check the real intersection”, not just reading labels or ignoring AP information.
- Highest sampled temperature in the final diagnostic was **37.4°C**. This was one short result, not certification of long-term thermal stability or charging safety.
- Independent ExecStopPost verified DSP/wireless stopped, 2.5 MiB RMTFS RAM zeroed, original core restored, and original CPU6 **2,208,000 kHz** / CPU7 **2,400,000 kHz** limits restored.

All original independent diagnostic directories were retained:

- `out/wifi-sg-postassoc-20261028/` (45.1°C abort)
- `out/wifi-sg-postassoc-capped-20261028/` (immediate readback/restoration assertion failure)
- `out/wifi-sg-postassoc-capped2-20261028/` (bounded wait and successful real CN→SG/98 subset verification)

## State after the first abort and the retest plan at that time (later progress below)

- DSP offline, no WLAN interface/default IPv4 route; sshd/firewalld active. Temporary credentials absent, persistent connection had no psk key.
- Complete original `/lib/modules` core hash unchanged, diagnostic parameters gone; CPU6/7 original limits read back natively and matched again.
- Full O_DIRECT read-only comparison of the three original NV partitions, 0400 private backups, original 15,285 static files, boot, seven preserved partitions, and six GPTs all matched. No persist/fsc reads, original-NV writes, host Wi-Fi/NAT/default-route changes, IPA/cellular-data enablement, or reset-failed.
- Offline tests: **181 total, 180 passed, one optional QEMU test skipped**. Added regressions established that AP CN could not stand in for SG and that a 98 label still required checks of real channels/power/DFS.

The next scripts were prepared but had not run:
`out/wifi-${FALLBACK_SSID}-connect2-20261028/{connect-trial.py,cleanup-connect.py,run-connect.py,connect-controller.service}`.
They integrated temporary CPU limits with bounded readback/restoration, a normal SG re-request/intersection audit after WPA2, actual 20 MHz, permanent MAC, DHCP/DNS, and explicit wlan0 HTTPS.
They retained the 75-second controller budget/90-second PID-1 cap, 45°C abort, independent cleanup, and temporary-credential deletion.
The integrated path still awaited actual network testing; independent diagnostics could not replace it.

The latest NV working-copy checkpoint had to be:
`out/wifi-sg-postassoc-capped2-20261028/result.json:private_copy_final_hashes`, not old values from the first activation or preparation.

The password was proven usable, but the first trial had deleted the file as promised, so the user needed to **enter the same password once more** locally:

```sh
cd "${REPO_ROOT}"
tools/${WIFI_2G_CREDENTIAL_SCRIPT}
```

Do not send the password in chat; reply “entered” after entry. This tool did not start wireless.
Normal reboot still returned to unchanged installed #8. The current kernel was still temporary wifi2 #10, not persistent enablement or production-stability acceptance.

## Second integrated test: SG, WPA2, DHCP, and frequency caps passed; verification tool aborted

connect2 ran after the user re-entered credentials. Actual CPU frequency limits and restoration passed; highest sample was **37.1°C**.
A normal SG re-request after association and audit of all **24 enabled 20 MHz channels** in the kernel's `98` intersection passed; permanent MAC and actual 20 MHz remained.
The same run's supplicant logs again showed PTK/GTK=CCMP and CONNECTED; the NM lifecycle explicitly showed a new DHCP lease and activated.
**This was not a wireless connection or SG failure**, but the checker incorrectly assumed a per-interface wpa_cli control socket existed:
`Failed to connect to non-global ctrl_ifname: wlan0`.
It therefore aborted before DNS/HTTPS.
NetworkManager actually used supplicant D-Bus; that socket was not required configuration.
Key dumps were not enabled and Network.Properties/PSK were not read for probing.

Cleanup proceeded normally: credentials deleted, wireless/DSP stopped, original core and CPU maximum frequencies restored; original NV/master/static files/boot/preserved partitions/GPT again matched.
The original failure remained `out/wifi-${FALLBACK_SSID}-connect2-20261028/connect-result.json`, not rewritten as a full networking success.
DNS/internet remained unverified up to this point, and the connection was not left running.

New `tools/wifi-auth-evidence.py` did not require a control socket. It checked only native supplicant logs after this run's monotonic-time cutoff, matching CCMP PTK/GTK and CONNECTED for the same AP.
The caller separately checked enforced RSN-only configuration, real SSID, active device, and station authorized=yes, without reading secret properties.
Later disconnection, old logs, another peer/interface, TKIP, or mixed WPA configuration were rejected.
Host unit tests and native isolated replay passed: validation succeeded only within the real time window before old-trial cleanup, while the disconnected snapshot after cleanup was explicitly rejected. Replay was not current-connection acceptance.

The next trial was prepared in `out/wifi-${FALLBACK_SSID}-connect3-20261028/`, using this evidence method and retaining all SG/frequency-cap/temperature/permanent-MAC/cleanup requirements; the integrated network path had not run.
The latest NV checkpoint became `out/wifi-${FALLBACK_SSID}-connect2-20261028/connect-result.json:private_copy_final_hashes`.
Offline tests: **186 total, 185 passed, one optional QEMU test skipped**.

To reduce the round trip of “enter credentials, then wait for another chat turn”, an explicitly named one-off trial entry point was added:

```sh
cd "${REPO_ROOT}"
tools/${WIFI_2G_TEST_SCRIPT}
```

**Unlike the entry-only tool, this command immediately starts a networking trial of at most 90 seconds after local hidden entry**; it is not persistent enablement.
The password still goes only into the phone's root0600 tmpfs file, not arguments/chat/logs.
Before starting, the fixed SSH host key is used to check that this run's directory is unused and no pending credentials exist; overwrite/repeated trials are rejected.
PID-1 independent finalization deletes temporary credentials, stops wireless/DSP, and restores frequencies/modules on success or failure.
If manually interrupted before the trial starts, pending credentials may remain in /run; inform the assistant to check rather than repeatedly overwriting.
The original `${WIFI_2G_CREDENTIAL_SCRIPT}` remained entry-only and did not start wireless; its behavior was unchanged.

Wait for the entire command to finish before replying “completed”.
The assistant should inspect saved results and service state first, not blindly rerun the same exclusive controller.
The one-off entry point passed shell syntax/guard tests; at that time user-interactive execution and new DNS/HTTPS results still awaited verification, covered below.

## Third one-off test: one passive scan on the old channel missed the target

The user ran the one-off entry point; the controller actually executed, and the assistant did not start it again.
Before WPA2 activation, the run aborted because one `scan freq 2447 passive` did not see the target; nmcli up was not called.
Temporary credentials were deleted as agreed. Highest sample was 36.8°C; independent cleanup restored frequencies/core, stopped DSP/wireless, and cleared shared RAM.
This could not be classified as a wrong password, a nonexistent network, a channel change, or a new handshake fault.
Previously proven WPA2/DHCP/SG successes from the first two runs remained valid.
The raw result was retained in `out/wifi-${FALLBACK_SSID}-connect3-20261028/connect-result.json`.

Bounded password-free discovery followed:

- Three passive scans of all legally enabled 2.4 GHz channels still missed the exact SSID; other BSS counts were aggregate only, with no neighbor identifiers retained.
- Directed active probing only of authorized **${FALLBACK_SSID}**, using only actually enabled 2.4 GHz channels permitting radiation, found the target on the second attempt: approximately **-57 dBm, still 2447 MHz / channel 8**. The first Open System auth frame had status0 and received a successful response.
- This did not prove a hidden AP SSID or a specific driver defect, and no channel change was observed. It proved that a single passive scan on an old channel could not reliably veto a connection.
- SG, HT20, and current/permanent device MAC checks passed. Highest sample in directed active discovery/authentication was 37.1°C; original frequencies/core were restored and DSP/wireless stopped on exit. No no-IR/disabled channels, random MAC, increased power, or AP changes were used.

Discovery evidence was separately retained in `out/wifi-${FALLBACK_SSID}-discovery-20261028/` and `out/wifi-${FALLBACK_SSID}-active-discovery-20261028/`, without overwriting their failures/successes.

New `tools/wifi-bss.py:active_2g_frequencies()` selected legal actively probeable 2.4 GHz channels from the real PHY already audited for SG, rather than binding to one historical AP channel.
It excluded disabled/no-IR/non-2.4GHz/nonstandard frequencies and failed when none were usable.
Unit tests and native offline replay of the actual PHY passed.

The new integrated controller was `out/wifi-${FALLBACK_SSID}-connect4-20261028/`; its complete credentialed network path had not yet run:

- At most two exact-SSID active probes covering legal 2.4 GHz channels. Even if the prescan missed the target, NetworkManager could spend 25 seconds trying only the same explicitly authorized RSN-only/bg profile. One empty scan was not absolute proof that the network did not exist; there was no fallback to another SSID or WPA1.
- Only client-side `802-11-wireless.hidden=yes` was added to the profile, enabling directed probing for the known SSID. This did not change AP settings or claim the AP was actually hidden. band bg, RSN/CCMP, permanent MAC, no saved secrets, no autoconnect, drop, IPv4, and other requirements were unchanged.
- Real handshake logs/live authorization validation were still used without a wpa_cli socket. Normal post-association SG re-request, actual intersection audit, temporary CPU limits, 45°C abort, and independent cleanup remained.
- One-off entry point `tools/${WIFI_2G_TEST_SCRIPT}` now targeted this new exclusive trial and, before requesting a password, checked the native temporary kernel, DSP offline, and temperature below 40°C. Local hidden user entry was still required; **the command immediately started the timed trial after entry**. Wait for the whole command to finish before replying.

Latest NV working-copy checkpoint:
`out/wifi-${FALLBACK_SSID}-active-discovery-20261028/result.json:private_copy_final_hashes`.
Original NV/master, 15,285 static files, boot, seven preserved partitions, and six GPTs again matched; credentials were absent, original CPU frequencies/core restored, and there was no wireless/default route.
Offline tests: **190 total, 189 passed, one optional QEMU test skipped**.
DNS/internet remained unverified at this point; completed networking acceptance could not yet be claimed.
