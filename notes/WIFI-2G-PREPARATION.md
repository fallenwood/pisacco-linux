# 2.4 GHz：真实 802.11 认证成功，等待本地凭据做 WPA2/联网验证 / 2.4 GHz: Real 802.11 Authentication Succeeded; Local Credentials Awaited for WPA2/Network Verification

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页是新目标试验前的历史准备快照，后续激活与监管复核见更新链接。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This is a historical preparation snapshot before testing the new target; linked updates cover later activation and regulatory rechecks. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

**后续第一次激活已真实通过 WPA2/CCMP 和 DHCP；但关联后 AP 的 CN 国家码触发监管复核中止，未验证互联网。
正常 SG 再请求/98 交集和临时 CPU 限频已用无密码关联独立验证；临时凭据已删除，待本地重新录入做整合重测。
最新见 [WIFI-2G-CONNECTION.md](WIFI-2G-CONNECTION.md)。以下为试验前准备快照。**

2026-10-28。用户指定新 SSID **${FALLBACK_SSID}**，确认这是 2.4 GHz 网络、密码与此前 ${PRIMARY_SSID} 相同。
手机仍固定 USB 连接，不要求移动。当前仅临时 wifi2 #10；不是已安装 #8 的持久 Wi-Fi 功能。

## 已经实际通过的部分

- 使用原有 HT20 保守试验 core 和固定 MSA SNOC 模块，未改动其字节或新刷 boot。
  参数只读、仅本机；PHY 无 HT40/VHT；实际 chanctx width **1 / 20 MHz**，vdev **11ng-ht20**。
- DMS → WLFW 每次重新提供同设备默认 MAC；wlan0 当前/永久地址一致，无随机地址，扫描和认证后不变。
- driver 默认域完成后施加用户指定 **SG**，实际有效信道/EIRP/DFS 审计通过；不以 AP 的 Country IE 代替用户地区。
- 从合法启用的 2.4 GHz 信道被动扫描中发现精确 SSID ${FALLBACK_SSID}：
  **2447 MHz / 信道 8，约 -60 dBm**。AP RSN、pairwise/group 均支持 **CCMP + PSK**。
- 不使用密码的 IEEE 802.11 Open System Authentication：第一帧 firmware completion **status=0**；
  nl80211 明确收到 `status: 0: Successful`，内核明确记录 **authenticated**。
  这与此前 ${PRIMARY_SSID} 5 GHz 三次 status=3/认证超时不同，证明当前 2.4 GHz 目标的认证请求/应答路径已工作。
- **尚未关联、尚未进行 WPA2 四次握手，DHCP/DNS/互联网均未测试**。Open System auth 成功不能等同于 WPA2 连接成功。

试验峰值采样 44.8°C（热点为 cpu7-thermal），没有提高 45°C 中止线。
结束后独立 ExecStopPost 验证无线/DSP/代理停止、2.5 MiB RMTFS RAM 清零、试验 core 卸载、原 core 恢复且文件哈希不变。
原 NV 三分区完整 O_DIRECT 只读比对、0400 私有备份、原 15,285 个静态文件、boot、七个保留分区、六个 GPT 再次一致。
没有读取 persist/fsc、写原 NV、修改主机网络/NAT，或隐藏此前失败单元。

## 新网络的非秘密配置

已创建并读回 **picasso-${FALLBACK_SSID}**：精确 SSID、band=bg、永久 MAC、WPA2/RSN + pairwise/group CCMP、
psk-flags=not-saved、禁止自动连接、IPv4 DHCP、初测 IPv6 关闭、入站 firewalld drop。旧 ${PRIMARY_SSID}/USB 配置未改。

先前 ${PRIMARY_SSID} 临时密码文件已经按约定删除，不能恢复或读取主机保存密码。
同一 **passphrase** 的 PMK 派生以 SSID 为盐，${PRIMARY_SSID} 和 ${FALLBACK_SSID} 的 PMK 通常不同；不能复用旧 SSID 的 PMK。
更新后的本地工具仅允许这两个固定 SSID，各自使用不同 /run 文件；仍只接受本地 TTY 隐藏输入两次。
输入 64-hex 时意味着操作者显式指定 raw PSK，而不是允许工具猜测/提取别处的密码。

在你的本地交互终端运行（不要把密码发到聊天中）：

```sh
cd "${REPO_ROOT}"
tools/${WIFI_2G_CREDENTIAL_SCRIPT}
```

此命令使用固定 SSH host key/原有 SSH 私钥，选择 `--ssid ${FALLBACK_SSID}`。
密码不进 argv、聊天或日志；只在手机 root0600 的 tmpfs 文件 `/run/picasso-${FALLBACK_SSID}.passwd` 暂存等效 PMK。
文件 O_EXCL|O_NOFOLLOW、不能覆盖已有文件。它不会启动无线或发起连接。
录入后回复“已录入”。**当前结果是录入前快照：凭据尚不存在。**

## 下一轮已准备、尚未执行的连接试验

`out/wifi-${FALLBACK_SSID}-20261028/{connect-trial.py,cleanup-connect.py,run-connect.py,connect-controller.service}`
通过语法检查，但还没有因缺少本地凭据而执行。每个改动路径仍需真机实际验证，不能拿此处准备状态代替结果。

- 使用本轮最新 `result.json:private_copy_final_hashes`，不使用原 NV master 或老扫描 checkpoint。
- 先只检查凭据存在/类型/所有者/模式/大小，不读取其内容；由 native nmcli `passwd-file` 读取。
- 开始温度 <40°C、连续等待采样、45°C 中止；PID-1 RuntimeMaxSec=90，控制器预算75秒、独立 ExecStopPost、无自动重试/恢复。
- 下一轮控制器及子进程计划绑定 CPU0–3（原生 policy0 为 CPU0–5、1.8048 GHz cluster），减少诊断工具压到 2.4 GHz CPU7 的额外热量；
  不修改 governor/电压/温度阈值，也不忽略 CPU7 或其他传感器。实际 affinity 和效果须在下一轮验证。
- 仍重新验证 HT20、DMS 当前/永久地址和实际 SG。关联后再次审计 SG 和实际 20 MHz，防止仅靠初始化标签推断。
- 验证 WPA2/CCMP、DHCP、wlan0 路由、drop 防火墙、新 DNS 事务及显式绑定 wlan0 的 HTTPS（验证证书，不用代理/主机 NAT）。
- 有密码的阶段关闭 MAC/WMI/key dump 类调试，仅保留非秘密的 QMI 状态和受限 auth/assoc completion 观测。
- 无论成功/失败，断开新配置、恢复 unmanaged、删除临时凭据、卸载无线/诊断 core、停止 DSP/代理/TFTP、清共享 RAM，并复核完整性。
  成功也仅是限时联网测试，不自动持久化或留无线无人值守运行。

离线测试 **179 项：178 通过，1 项可选 QEMU 跳过**；新测试覆盖同密码按新 SSID 重新派生、目标白名单和新固定 SSH/TTY wrapper。

证据：`out/wifi-${FALLBACK_SSID}-20261028/summary-result.json`、`result.json`、独立清理/原始完整性结果和 `secret-entry-ready.json`。
先前失败保留在 [WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md)。电源/充电、宽信道、长期稳定性等仍未验收。

## English

**The first subsequent activation really passed WPA2/CCMP and DHCP, but the AP's CN country code triggered a regulatory recheck abort after association; internet access was not verified.
A normal SG re-request/98 intersection and temporary CPU frequency caps were independently verified using password-free association. Temporary credentials were deleted, pending local re-entry for an integrated retest.
See [WIFI-2G-CONNECTION.md](WIFI-2G-CONNECTION.md) for later progress. The following is the pre-trial preparation snapshot.**

2026-10-28. The user specified a new SSID, **${FALLBACK_SSID}**, confirmed it was a 2.4 GHz network, and said its password matched the earlier ${PRIMARY_SSID} password.
The phone remained fixed with USB connected; moving it was not required.
It still ran only temporary wifi2 #10; this was not persistent Wi-Fi functionality in installed #8.

## What had actually passed

- The existing conservative HT20 trial core and fixed-MSA SNOC module were used without changing their bytes or flashing a new boot. Parameters were read-only and device-scoped; the PHY had no HT40/VHT. Actual chanctx width was **1 / 20 MHz**, vdev **11ng-ht20**.
- DMS → WLFW re-provisioned the same device default MAC every time. Current/permanent wlan0 addresses matched, with no random address, and stayed unchanged after scanning and authentication.
- The user-specified **SG** was applied after the driver's default domain completed. Actual enabled-channel/EIRP/DFS audit passed; the AP's Country IE was not substituted for the user's location.
- Passive scanning of legally enabled 2.4 GHz channels found the exact SSID ${FALLBACK_SSID} at **2447 MHz / channel 8, approximately -60 dBm**. AP RSN and pairwise/group ciphers supported **CCMP + PSK**.
- Password-free IEEE 802.11 Open System Authentication: the first frame's firmware completion had **status=0**. nl80211 explicitly received `status: 0: Successful`, and the kernel explicitly recorded **authenticated**. Unlike earlier ${PRIMARY_SSID} 5 GHz's three status-3 completions/authentication timeouts, this proved the current 2.4 GHz target's authentication request/response path worked.
- **Association and the WPA2 four-way handshake had not occurred; DHCP/DNS/internet had not been tested.** Open System authentication success was not WPA2 connection success.

Peak sampled temperature was 44.8°C, with cpu7-thermal the hotspot. The 45°C abort line was not raised.
Independent ExecStopPost verified wireless/DSP/proxy stopped, 2.5 MiB RMTFS RAM zeroed, trial core unloaded, and original core restored with unchanged file hash.
Full O_DIRECT read-only comparisons of the three original NV partitions, 0400 private backups, original 15,285 static files, boot, seven preserved partitions, and six GPTs all matched again.
There was no persist/fsc read, original-NV write, host network/NAT change, or hiding of earlier failed units.

## Non-secret configuration for the new network

**picasso-${FALLBACK_SSID}** was created and read back: exact SSID, band=bg, permanent MAC, WPA2/RSN + pairwise/group CCMP, psk-flags=not-saved, autoconnect prohibited, IPv4 DHCP, IPv6 disabled for the first test, and inbound firewalld drop.
The old ${PRIMARY_SSID}/USB configurations were unchanged.

The previous temporary ${PRIMARY_SSID} password file had been deleted as agreed; it could not be recovered, nor could saved host passwords be read.
PMK derivation from the same **passphrase** uses the SSID as salt, so ${PRIMARY_SSID} and ${FALLBACK_SSID} generally have different PMKs; the old SSID's PMK cannot be reused.
The updated local tool allowed only these two fixed SSIDs, with separate /run files, and still accepted only twice-entered hidden input on a local TTY.
Entering 64 hexadecimal characters meant the operator explicitly supplied a raw PSK, not permission for the tool to guess/extract passwords elsewhere.

Run in your local interactive terminal; do not send the password in chat:

```sh
cd "${REPO_ROOT}"
tools/${WIFI_2G_CREDENTIAL_SCRIPT}
```

This command used the fixed SSH host key/existing SSH private key and selected `--ssid ${FALLBACK_SSID}`.
The password did not enter argv, chat, or logs; only the equivalent PMK was temporarily stored on the phone in root0600 tmpfs file `/run/picasso-${FALLBACK_SSID}.passwd`.
O_EXCL|O_NOFOLLOW prevented overwriting an existing file. The command did not start wireless or connect.
After entry, reply “entered”. **This record was a pre-entry snapshot: credentials did not yet exist.**

## Prepared but unexecuted next connection trial

`out/wifi-${FALLBACK_SSID}-20261028/{connect-trial.py,cleanup-connect.py,run-connect.py,connect-controller.service}` passed syntax checks but had not run because local credentials were missing.
Each changed path still required actual on-device verification; preparation here was not a substitute for results.

- Use this trial's latest `result.json:private_copy_final_hashes`, not the original NV master or an old scan checkpoint.
- Initially check only credential existence/type/owner/mode/size, without reading contents; native nmcli reads it via `passwd-file`.
- Start below 40°C, sample continuously while waiting, abort at 45°C. PID-1 RuntimeMaxSec=90, controller budget 75 seconds, independent ExecStopPost, no automatic retry/recovery.
- The next controller and children were planned to bind to CPU0–3 (native policy0 covered CPU0–5, a 1.8048 GHz cluster), reducing extra heat from diagnostic tools on 2.4 GHz CPU7. Governor/voltage/temperature thresholds would not change, nor would CPU7 or other sensors be ignored. Actual affinity and effect required verification in the next trial.
- Reverify HT20, DMS current/permanent addresses, and actual SG. Reaudit SG and actual 20 MHz after association rather than inferring compliance from initialization labels alone.
- Verify WPA2/CCMP, DHCP, wlan0 routes, drop firewall, a new DNS transaction, and HTTPS explicitly bound to wlan0 with certificate verification, without proxy/host NAT.
- Disable MAC/WMI/key-dump debugging during the credentialed stage; retain only non-secret QMI state and restricted auth/assoc completion observation.
- On success or failure, disconnect the new profile, restore unmanaged, delete temporary credentials, unload wireless/diagnostic core, stop DSP/proxy/TFTP, clear shared RAM, and recheck integrity. Even success would be only a timed networking test, without automatic persistence or unattended wireless operation.

Offline tests: **179 total, 178 passed, one optional QEMU test skipped**. New tests covered deriving again for a new SSID from the same password, the target allowlist, and the new fixed SSH/TTY wrapper.

Evidence: `out/wifi-${FALLBACK_SSID}-20261028/summary-result.json`, `result.json`, independent cleanup/raw integrity results, and `secret-entry-ready.json`.
Earlier failures remain in [WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md).
Power/charging, wide channels, long-term stability, and other such areas still had no acceptance.
