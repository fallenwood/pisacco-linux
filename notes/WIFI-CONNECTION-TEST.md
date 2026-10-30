# ${PRIMARY_SSID} 连接测试：802.11 认证超时，尚未联网 / ${PRIMARY_SSID} Connection Test: 802.11 Authentication Timed Out, No Network Access

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页保留早期失败连接及当时计划，后续定点诊断见更新链接，不代表当前所有目标的结果。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This page preserves an early failed connection and its plans; linked updates cover later fixed-position diagnostics, not current results for every target. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

**后续用户确认手机固定 USB 连接、无法移动，接受弱信号。不再要求移动作为继续条件。
已完成管理帧状态、省电、20 MHz、同名 2.4 GHz 检查，仍未关联；最新见 [WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md)。
本页以下保留早期记录和当时计划；旧 unanchored BSS 分割的聚合计数不再作为准确 AP 数量。**

2026-10-27。用户已在本地终端录入临时凭据并要求继续。
**这次连接未通过，不能报告 Wi-Fi 已连接或已上网。**

## 实际经过

- 仅使用本机 DMS 默认 WLAN MAC；注册后的当前/永久 MAC 一致，扫描随机化关闭。
- SG 用户监管限制在 driver 默认域完成后施加，36 个启用的 20 MHz 信道的频率/EIRP/DFS 校验通过。
- 已有 `picasso-${PRIMARY_SSID}` 配置保持 WPA2/RSN + CCMP、永久 MAC、不自动连接、IPv4、入站 drop。
- 临时凭据为 root-owned 0600、单链接普通文件。控制程序仅检查元数据，不读取、打印、传输或记录其内容；
  只有手机上的 nmcli 通过 `passwd-file` 读取。未把密码/PMK 放入 argv 或证据。
- nmcli 开始连接后，实际找到了 5240 MHz 的 ${PRIMARY_SSID}，并发出三次 IEEE 802.11 Open System Authentication。
  没收到认证应答，随后 timeout。该阶段发生在关联和 WPA2 四次握手之前。
- 最终 nmcli 提示 “Wi-Fi network could not be found”，但内核/supplicant 记录表明它曾找到 AP 并尝试认证。
  **这不是密码错误的证据；根因尚未确定。** 没有 DHCP/DNS/互联网验证结果。
- 手机先前发现该 AP 时信号约 27%；主机只读缓存对同一目标显示约 43%。弱信号可能相关，
  但未证明是唯一原因，也没有排除无线 TX/固件兼容性或 AP MAC 准入问题。

## 安全边界和恢复

本轮主控制器由 PID 1 管理：RuntimeMaxSec=110、独立 ExecStopPost 清理、无自动重启。
命令等待期间持续检查温度、DSP 状态和整体时限。RMTFS 后端仍是四个隔离 FD，自动恢复预先禁用。
峰值 44.1°C，低于 45°C 中止线；没有提高阈值或放宽监管限制。

失败后先断开/卸载无线并停止 DSP/代理/TFTP，删除临时凭据，清零经验证的 2.5 MiB RMTFS 缓冲。
ExecStopPost 再次独立验证清理完成。保留 `picasso-wifi-connect-controller.service` 的 failed 状态，
不 reset-failed，也不把清理成功当作关联成功。

冷却到 40°C 以下后做了一个无需密码的短时诊断：NetworkManager 保持 unmanaged，只扫描合法
2.4 GHz 信道 1–11 和先前目标 5240 MHz。短扫未发现 ${PRIMARY_SSID}，因此没有发送新的认证请求。
该结果不能证明 AP 已关闭或消失。诊断限时 45 秒、有独立 ExecStopPost，结束同样清理。
没有进行无止境连接重试，没有伪造/尝试其他密码，没有改 BDF/校准/SCM/SMMU。

最终检查：临时密码文件不存在，持久连接文件没有 psk 键，DSP offline、无 wlan0、无默认 IPv4 路由；
温度已降到约 36.4°C。USB SSH 正常。仍在临时 wifi2 #10；正常重启回已安装 #8，boot 未改。

原 NV 三分区各 8 MiB 再次 O_DIRECT 只读完整比对，原始 0400 私有备份未变。
原 15,285 个静态文件、完整 boot、七个保留分区和六个 LUN GPT 全部复核一致。
没有读取 persist/fsc、写回原 NV、修改主机网络/NAT，或取得新的电源/充电安全验收。

## 后续无需密码的定点链路诊断

用户继续后，另建 45 秒上限的 PID-1 管理单元，保持 NetworkManager unmanaged。
通过真实 SG 限制和设备当前/永久 MAC 校验后，在 5240 MHz 被动扫描：
一次扫到 12 条 BSS（不保存其他网络标识），找到 ${PRIMARY_SSID}，实测 **-84 dBm**。
该 AP 的 RSN、pairwise 和 group cipher 均支持 **CCMP + PSK**，与 WPA2-only 配置一致。

随后只调用 `iw ... auth ... open`，即 WPA2 之前的 Open System Authentication，
不读取/请求密码，不发起关联或密码握手。内核接受命令，但三次认证发送后仍超时；
nl80211 也明确返回 `auth: timed out`。扫描到认证观察仅约 2.49 秒。
这独立复现了先前失败，不能通过重新输入密码来解释或解决，也还不能据此锁定弱信号、AP 准入或 FW/TX 路径中的哪一项。

采样最高 44.1°C，仍未提高 45°C 中止线；结束后独立 ExecStopPost 验证 DSP offline、无线卸载、
临时凭据不存在、共享 RMTFS RAM 清零。原 NV/备份、15,285 个原静态文件、boot、七个保留分区、六个 GPT 再次全部一致。
完整独立结果见 `out/wifi-link-diag2-20261027/summary-result.json`；前面失败结果保持不变。

## 当时的下一步（已由固定位置诊断方案替代）

请先把手机靠近路由器（例如 1–2 米），保持 USB 连接；检查 ${PRIMARY_SSID} 是否有 MAC 白名单/黑名单。
若有准入限制，应针对设备报告的默认 MAC，而不是以前 Android 每网络随机 MAC。
**暂时不需要重新输入密码**：先在较强信号下验证无需密码的 802.11 认证应答，再决定下一轮密码测试。
若强信号下仍失败，进一步诊断管理帧 TX completion/ACK 和原厂固件适配，不猜校准文件或扩大受保护分区读取。

证据：`out/wifi-connect-20261027/summary-result.json`、`result.json`（保留的失败连接原始结果）、
`auth-result.json`、独立清理结果及日志。前序 SG/MAC 准备结果保持不变，见 [WIFI-CONNECTION.md](WIFI-CONNECTION.md)。

## English

**The user subsequently confirmed that the phone was fixed in place with USB connected, could not be moved, and that weak signal was acceptable. Moving it was no longer required to continue.
Management-frame status, power saving, 20 MHz, and a same-name 2.4 GHz network were checked, still without association; see [WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md) for later findings.
The following preserves early records and the plan at that time; aggregate counts from the old unanchored BSS splitting are no longer treated as accurate AP counts.**

2026-10-27. The user had entered temporary credentials in a local terminal and asked to continue.
**This connection attempt failed; Wi-Fi could not be reported as connected or online.**

## What actually happened

- Only this device's DMS default WLAN MAC was used. Current/permanent MACs matched after registration; scan randomization was off.
- The SG user restriction was applied after the driver's default domain completed. Frequency/EIRP/DFS validation passed for 36 enabled 20 MHz channels.
- The existing `picasso-${PRIMARY_SSID}` profile retained WPA2/RSN + CCMP, permanent MAC, no autoconnect, IPv4, and inbound drop.
- Temporary credentials were a root-owned 0600 single-link regular file. The controller checked only metadata; it did not read, print, transmit, or log contents. Only nmcli on the phone read the file through `passwd-file`. Password/PMK were not put into argv or evidence.
- After nmcli began connecting, it actually found ${PRIMARY_SSID} at 5240 MHz and sent three IEEE 802.11 Open System Authentication requests. No authentication response arrived, followed by a timeout. This occurred before association and the WPA2 four-way handshake.
- nmcli finally reported “Wi-Fi network could not be found”, but kernel/supplicant records showed that it had found the AP and attempted authentication. **This was not evidence of a wrong password; the root cause remained undetermined.** There were no DHCP/DNS/internet verification results.
- The phone previously saw this AP at approximately 27% signal; the host's read-only cache showed approximately 43% for the same target. Weak signal might have contributed, but was not proven to be the sole cause. Wireless TX/firmware compatibility and AP MAC admission issues were not excluded.

## Safety boundaries and recovery

PID 1 managed the main controller: RuntimeMaxSec=110, independent ExecStopPost cleanup, and no automatic restart.
Temperature, DSP state, and overall deadline were continuously checked while commands waited.
The RMTFS backend still used four isolated FDs; automatic recovery was disabled in advance.
Peak temperature was 44.1°C, below the 45°C abort threshold. Thresholds were not raised and regulatory restrictions were not relaxed.

After failure, wireless was disconnected/unloaded, DSP/proxy/TFTP stopped, temporary credentials deleted, and the verified 2.5 MiB RMTFS buffer zeroed.
ExecStopPost independently reverified cleanup. The failed state of `picasso-wifi-connect-controller.service` was retained; no reset-failed, and successful cleanup was not treated as successful association.

After cooling below 40°C, a short password-free diagnostic kept NetworkManager unmanaged and scanned only legal 2.4 GHz channels 1–11 and the previous target frequency, 5240 MHz.
The short scan did not find ${PRIMARY_SSID}, so no new authentication request was sent. That did not prove that the AP was shut down or gone.
The diagnostic had a 45-second limit and independent ExecStopPost, with the same cleanup on exit.
There were no endless connection retries, fabricated/alternative passwords, or BDF/calibration/SCM/SMMU changes.

Final checks: the temporary password file was absent, the persistent connection file had no psk key, the DSP was offline, wlan0 was absent, and there was no default IPv4 route.
Temperature had fallen to approximately 36.4°C. USB SSH worked. The phone still ran temporary wifi2 #10; normal reboot would return to installed #8, with boot unchanged.

All three original NV partitions, 8 MiB each, were again fully compared read-only using O_DIRECT, and the original 0400 private backups were unchanged.
All original 15,285 static files, complete boot, seven preserved partitions, and six LUN GPTs were rechecked unchanged.
There was no persist/fsc read, original-NV writeback, host network/NAT change, or new power/charging-safety acceptance.

## Later password-free, targeted link diagnostic

After the user asked to continue, a separate PID-1-managed unit with a 45-second limit was created, keeping NetworkManager unmanaged.
After actual SG restrictions and current/permanent device MACs passed validation, a passive scan at 5240 MHz yielded 12 BSS records (without saving other network identifiers), finding ${PRIMARY_SSID} at **-84 dBm**.
Its RSN and pairwise/group ciphers supported **CCMP + PSK**, matching the WPA2-only profile.

The diagnostic then called only `iw ... auth ... open`: Open System Authentication before WPA2, without reading/requesting a password, initiating association, or performing a password handshake.
The kernel accepted the command, but after three authentication transmissions it still timed out; nl80211 explicitly returned `auth: timed out`.
Only approximately 2.49 seconds elapsed between scanning and authentication observation.
This independently reproduced the previous failure. Re-entering the password could not explain or solve it, nor did it identify which of weak signal, AP admission, or the FW/TX path was responsible.

Highest sampled temperature was 44.1°C; the 45°C abort line was not raised.
Independent ExecStopPost verified DSP offline, wireless unloaded, temporary credentials absent, and shared RMTFS RAM zeroed.
Original NV/backups, all 15,285 original static files, boot, seven preserved partitions, and six GPTs again matched.
The full independent result is `out/wifi-link-diag2-20261027/summary-result.json`; previous failure results were unchanged.

## Next step at the time, superseded by the fixed-position diagnostic plan

First move the phone closer to the router, for example 1–2 metres away, keeping USB connected; check whether ${PRIMARY_SSID} has a MAC allowlist/blocklist.
Any admission rule should apply to the default MAC reported by the device, not the former Android per-network randomized MAC.
**There was no immediate need to re-enter the password**: first verify a password-free 802.11 authentication response at stronger signal, then decide on another password test.
If stronger signal still failed, diagnose management-frame TX completion/ACK and factory firmware compatibility further, without guessing calibration files or expanding protected-partition reads.

Evidence: `out/wifi-connect-20261027/summary-result.json`, `result.json` (retained raw failed-connection result), `auth-result.json`, independent cleanup results and logs.
Earlier SG/MAC preparation results were unchanged; see [WIFI-CONNECTION.md](WIFI-CONNECTION.md).
