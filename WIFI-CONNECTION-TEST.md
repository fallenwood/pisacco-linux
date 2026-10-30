# Chaldea 连接测试：802.11 认证超时，尚未联网

**后续用户确认手机固定 USB 连接、无法移动，接受弱信号。不再要求移动作为继续条件。
已完成管理帧状态、省电、20 MHz、同名 2.4 GHz 检查，仍未关联；最新见 [WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md)。
本页以下保留早期记录和当时计划；旧 unanchored BSS 分割的聚合计数不再作为准确 AP 数量。**

2026-10-27。用户已在本地终端录入临时凭据并要求继续。
**这次连接未通过，不能报告 Wi-Fi 已连接或已上网。**

## 实际经过

- 仅使用本机 DMS 默认 WLAN MAC；注册后的当前/永久 MAC 一致，扫描随机化关闭。
- SG 用户监管限制在 driver 默认域完成后施加，36 个启用的 20 MHz 信道的频率/EIRP/DFS 校验通过。
- 已有 `picasso-Chaldea` 配置保持 WPA2/RSN + CCMP、永久 MAC、不自动连接、IPv4、入站 drop。
- 临时凭据为 root-owned 0600、单链接普通文件。控制程序仅检查元数据，不读取、打印、传输或记录其内容；
  只有手机上的 nmcli 通过 `passwd-file` 读取。未把密码/PMK 放入 argv 或证据。
- nmcli 开始连接后，实际找到了 5240 MHz 的 Chaldea，并发出三次 IEEE 802.11 Open System Authentication。
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
2.4 GHz 信道 1–11 和先前目标 5240 MHz。短扫未发现 Chaldea，因此没有发送新的认证请求。
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
一次扫到 12 条 BSS（不保存其他网络标识），找到 Chaldea，实测 **-84 dBm**。
该 AP 的 RSN、pairwise 和 group cipher 均支持 **CCMP + PSK**，与 WPA2-only 配置一致。

随后只调用 `iw ... auth ... open`，即 WPA2 之前的 Open System Authentication，
不读取/请求密码，不发起关联或密码握手。内核接受命令，但三次认证发送后仍超时；
nl80211 也明确返回 `auth: timed out`。扫描到认证观察仅约 2.49 秒。
这独立复现了先前失败，不能通过重新输入密码来解释或解决，也还不能据此锁定弱信号、AP 准入或 FW/TX 路径中的哪一项。

采样最高 44.1°C，仍未提高 45°C 中止线；结束后独立 ExecStopPost 验证 DSP offline、无线卸载、
临时凭据不存在、共享 RMTFS RAM 清零。原 NV/备份、15,285 个原静态文件、boot、七个保留分区、六个 GPT 再次全部一致。
完整独立结果见 `out/wifi-link-diag2-20261027/summary-result.json`；前面失败结果保持不变。

## 当时的下一步（已由固定位置诊断方案替代）

请先把手机靠近路由器（例如 1–2 米），保持 USB 连接；检查 Chaldea 是否有 MAC 白名单/黑名单。
若有准入限制，应针对设备报告的默认 MAC，而不是以前 Android 每网络随机 MAC。
**暂时不需要重新输入密码**：先在较强信号下验证无需密码的 802.11 认证应答，再决定下一轮密码测试。
若强信号下仍失败，进一步诊断管理帧 TX completion/ACK 和原厂固件适配，不猜校准文件或扩大受保护分区读取。

证据：`out/wifi-connect-20261027/summary-result.json`、`result.json`（保留的失败连接原始结果）、
`auth-result.json`、独立清理结果及日志。前序 SG/MAC 准备结果保持不变，见 [WIFI-CONNECTION.md](WIFI-CONNECTION.md)。
