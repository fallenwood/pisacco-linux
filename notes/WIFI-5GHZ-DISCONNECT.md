# 5 GHz 断开与监管域保护 / 5 GHz Disconnect and Regulatory Guard

中文：下文为修复前的只读历史快照。后续已获授权并部署审阅的路由器 US 策略，
但三次受控试验未通过：5 GHz 首次连接超时，2.4 GHz 宣告 CN，与 US 策略冲突。
用户选择统一路由器为 US 后暂缓调整；RF 安全关闭，没有新的成功证明。
完整范围、失败和后续边界见[路由器国家码策略](WIFI-ROUTER-COUNTRY.md)。
再后新授权已改为[固定 CN](WIFI-FIXED-CN.md)，2.4 GHz 持续运行和双栈恢复；
5 GHz 首次连接仍超时，不能把国家策略验收当作 5 GHz 掉线根因修复。

English: The following is the pre-repair read-only historical snapshot.
A later grant deployed reviewed router-US policy, but three bounded trials
failed: initial 5 GHz connection timed out and 2.4 GHz advertised CN, conflicting
with US policy. The user chose consistent router US configuration, then deferred
it. RF is safely off with no new accepted proof. See
[router country policy](WIFI-ROUTER-COUNTRY.md) for scope, failures and boundaries.
A later grant switched to [fixed CN](WIFI-FIXED-CN.md), restoring continuous
2.4 GHz and dual stack. Initial 5 GHz connection still times out; country-policy
acceptance is not a fix for the underlying 5 GHz disconnection cause.

## 中文

### 2026-11-01 只读诊断

用户报告首选网络连接后断开，而 2.4 GHz 回退没有同样问题。旧 LAN IPv4/IPv6
SSH 均不可达，但 USB 设备存在；经新授权，仅为主机已核对的 USB 网卡添加临时
直连地址，严格主机密钥 USB SSH 确认原生 `7.3.1-picasso-wifi2` 和一个新的启动。
没有改主机默认路由、DNS、NAT、转发或持久 profile，没有切换网络、启动射频、
修改路由器、软件、凭据或监管策略。

本次读取的是已有日志，不是新建无线试验。手机日历时钟与用户报告时间不一致，
以下顺序按同一启动的 journal 单调时间计算，不能直接对应用户报错的墙钟时间。

| 顺序 | 原生证据 |
| --- | --- |
| 首次连接 | 首选 5 GHz 在 5240 MHz（信道 48）完成 WPA2/CCMP、DHCP 与 worker 的网络校验；初始 CN 原始审计通过 |
| 初次 Country IE | AP 宣告 `US`，随后有用户监管请求产生交集，服务成功进入就绪 |
| 首次断开 | 连接约 901 秒后收到 deauthentication，reason 3；没有证据证明这次由 BEACON_MISS 发起 |
| 自动重新关联 | 约 5 秒后 wpa_supplicant 重新连接同一 AP；再次收到 `COUNTRY_IE ... alpha2=US` |
| 安全停机 | 重连约 3 秒后 worker 拒绝全局 `country US`，错误为 `Neither CN nor verified intersection candidate`，随后清理 RF |

**已确认的是重连后的监管域冲突及主动安全停机；第一次 AP 断开的底层原因仍未知。**
项目批准的策略是 CN，审计只接受 CN 或经实际逐频点核对的 `98` 交集，
不接受直接切成 US。5 GHz 本轮并非一直无法认证，也不是密码或 IPv6/firewalld
端口过滤导致的无线断开。删钥 `-110` 出现在断开后的清理阶段，不能当作初始装钥失败。

`tools/wifi-radio-service.py` 的持续监测只在观察到 SSID 改变时重新请求监管域；
快速断开并重新连接同一 SSID，可能在两次轮询之间发生，或保持相同 SSID，
因而不能依靠该条件再次建立批准的监管交集。记录证实重连后停在 US，
但本阶段没有修改该逻辑，也没有通过新试验证明修复。
这与[旧 2.4 GHz BEACON_MISS](WIFI-LINK-LOSS.md)是不同证据链，不能混为一谈。

### 当前快照、后续方向与边界

读取时服务 failed、无运行 PID，WLAN 已不存在，dirty 标记不存在。
清理记录报告 DSP offline、子进程停止、共享 RAM 清零、CPU/core 恢复及 checkpoint
提交成功；未重新读取普通 NV 文件核验摘要，因此不将清理报告扩大为新的独立 NV 验收。
本次峰值采样 36.1°C，错误不是温度超限。更早曾验收的 2.4 GHz 持续会话，
留存结果另有 `45C thermal abort`，不能把那次失联归于本次 5 GHz 原因。

下一步应核对路由器实际所在地的合法国家设置及 5 GHz Country IE，
使 AP 配置与项目批准的监管政策一致，而不是随意修改国家、提高功率或删除保护。
若实际所在地与批准政策不同，需要重新审查政策和完整性绑定。
软件方面应独立评估同 SSID 重关联时的监管请求/交集处理，并保留全部 CN
功率、DFS、室内、no-IR 和温度检查；本次没有取得修改或射频复验授权。
2.4 GHz 当前更适合作为已观察的稳定回退，但不代表无条件的长期稳定性保证。

主机临时 USB 地址保留供诊断使用，手机端只读。没有刷写、重启手机、重启 RF、
手动清除标记、恢复 NV 或操作 Podman。firewalld 的开放策略未改，
此前 LAN/双栈验收与活跃 RF 状态是历史快照，不是当前在线状态。
Petitboot 菜单、USB 日志和内核交接的硬件验收状态未变。

受保护证据均相对于仓库根目录，位于 `out/wifi-band-diagnostic-20261101/`：
`authorization.json`、`usb-candidate.json`、`host-address-result.json`、
`verified-transport.json`、`native-audit.stdout.json`、`native-audit.stderr.txt`、
`native-audit.status.json` 和 `result.json`。
它们含私有设备/网络/启动标识，仅保存在被忽略的本地产物中；
新克隆不保证存在，不能将历史辅助程序或授权盲目重放。

## English

### 2026-11-01 read-only diagnosis

The user reported preferred-network disconnections while the 2.4 GHz fallback
did not have the same problem. Old LAN IPv4/IPv6 SSH was unreachable, but USB
was present. With a fresh grant, only a temporary direct address was added to
the verified host USB interface. Strict-pinned USB SSH confirmed native
`7.3.1-picasso-wifi2` on a new boot. No host default-route, DNS, NAT, forwarding
or persistent-profile changes, network switch, RF start, router/software/
credential modification or regulatory-policy change occurred.

Existing logs were read; no wireless experiment was initiated. The phone's
calendar clock disagrees with the user-reported time. Ordering below uses
same-boot journal monotonic timestamps, not a direct wall-clock correlation.

| Order | Native evidence |
| --- | --- |
| Initial connection | Preferred 5 GHz at 5240 MHz (channel 48) completed WPA2/CCMP, DHCP and worker network validation; initial raw CN audit passed |
| Initial Country IE | AP advertised `US`; a subsequent user regulatory request produced an intersection and the service reached ready |
| First disconnect | Deauthentication reason 3 arrived about 901 seconds after connection; BEACON_MISS initiation was not established |
| Automatic reassociation | wpa_supplicant reconnected to the same AP about 5 seconds later and received `COUNTRY_IE ... alpha2=US` again |
| Safety shutdown | About 3 seconds after reconnect, the worker rejected global `country US` with `Neither CN nor verified intersection candidate`, then cleaned up RF |

**The confirmed cause of the post-reconnect safety shutdown is regulatory-domain
conflict; the underlying first AP disconnection remains unexplained.**
Approved project policy is CN. Auditing accepts CN or a `98` intersection
verified against actual channels, not a direct switch to US. This 5 GHz run did
authenticate; password failure and IPv6/firewalld port filtering do not explain
its wireless disconnection. Key-removal `-110` followed the disconnect during
teardown and is not evidence of initial key-install failure.

Continuous monitoring in `tools/wifi-radio-service.py` requests the regulatory
domain again only when it observes an SSID change. Rapid reconnect to the same
SSID can occur between polls or retain the same SSID, so this condition cannot
be relied on to reestablish the approved intersection. Recorded post-reconnect
state was US; this stage changed no logic and proved no fix through a new trial.
This is a different evidence chain from
[historical 2.4 GHz BEACON_MISS](WIFI-LINK-LOSS.md).

### Current snapshot, next direction and boundaries

At inspection the service was failed with no running PID, WLAN was absent and
no dirty marker existed. Cleanup reported offline DSP, stopped children, cleared
shared RAM, restored CPU/core and committed checkpoint. Ordinary NV files were
not reread for digest verification, so this is not new independent NV acceptance.
Peak sampled temperature was 36.1°C; this failure was not thermal. A previously
accepted 2.4 GHz continuous session separately ended with `45C thermal abort`;
that earlier outage must not be attributed to this 5 GHz cause.

Next investigate the router's legally correct country setting for its actual
location and 5 GHz Country IE, aligning AP configuration with approved project
regulatory policy rather than guessing a country, increasing power or removing
guards. A different actual location requires policy/integrity review. Software
handling of regulatory requests/intersections after same-SSID reassociation
should be evaluated separately while retaining all CN power, DFS, indoor, no-IR
and thermal checks. No modification/RF-revalidation grant was obtained here.
2.4 GHz remains the better observed fallback, not an unconditional endurance
guarantee.

The temporary host USB address remains available for diagnosis; phone operations
were read-only. No flashing, phone/RF reboot, manual marker removal, NV
restoration or Podman operation occurred. Firewalld's open policy was unchanged.
Earlier LAN/dual-stack acceptance and live-RF state are historical, not current
online status. Petitboot menu, USB logging and kernel-handoff hardware acceptance
are unchanged.

Protected evidence is repository-root-relative under
`out/wifi-band-diagnostic-20261101/`: `authorization.json`, `usb-candidate.json`,
`host-address-result.json`, `verified-transport.json`, `native-audit.stdout.json`,
`native-audit.stderr.txt`, `native-audit.status.json` and `result.json`.
Private device/network/boot identifiers remain only in ignored local artifacts.
These may be absent in a fresh clone; historical helpers/grants must not be
blindly replayed.
