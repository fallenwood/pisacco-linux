# Wi-Fi IPv6（7.3.1）/ Wi-Fi IPv6 (7.3.1)

## 中文

后续状态：此文保留 IPv6 部署时的受限入站策略快照。之后按新授权将当前
Wi-Fi、USB 和默认区域设为 ACCEPT，所有服务端口开放、内建检查保留；见
[防火墙开放策略](FIREWALL-OPEN.md)。下面“入站限制保持不变”不代表当前端口策略。

### 2026-11-01 状态与授权

在原生 `7.3.1-picasso-wifi2` 上启用了 Wi-Fi 双栈：IPv4 DHCP 保留，
IPv6 自动配置已取得可用链路本地地址、公网地址、RA 前缀路由和默认路由。
分别强制 IPv4、IPv6，经 `wlan0` 直接访问 `https://example.com`，
均返回 HTTP 200、证书校验成功且未使用代理；非 USB 路由的严格主机密钥
LAN SSH 也通过。这是本阶段快照，不是长期稳定性或下一次启动验收。

用户明确选择修改并部署 IPv6 配置，授权必要的正常受保护 Wi-Fi 启停与验收，
要求保留 IPv4 和入站限制。没有刷写、手机重启、Petitboot 临时启动、
默认镜像替换、原始 NV 分区访问、手动清除 dirty 标记或 NV 恢复。
此前的 Wi-Fi 恢复和首轮 Petitboot 启动授权不能在这里重用。

### 原因与兼容配置

已验收内核有 `CONFIG_IPV6=y`；此前两个 Wi-Fi worker 都强制
NetworkManager 使用 `ipv6.method=disabled`。只手动修改连接配置，
会在下一次受保护激活时因策略不符被拒绝。Petitboot 引导候选的
IPv6 配置与本次原生 Wi-Fi 无关。

原自动连接 profile 与保留的 6.18 环境共享；旧 worker 要求 IPv6 禁用。
因此没有直接改写原 profile，而是从其克隆两份隔离的双栈 profile：

| 配置 | 双栈 profile | 保留的旧 profile |
| --- | --- | --- |
| 首选网络 | `picasso-auto-${PRIMARY_SSID}-ipv6` | `picasso-auto-${PRIMARY_SSID}` |
| 2.4 GHz 回退 | `picasso-auto-${FALLBACK_SSID}-ipv6` | `picasso-auto-${FALLBACK_SSID}` |
| IPv4 / IPv6 | `ipv4.method=auto` / `ipv6.method=auto` | IPv4 DHCP / IPv6 禁用 |

这些名称是脱敏示例，不是可直接执行的配置。新 profile 保持
`ipv6.may-fail=yes`、`ipv6.never-default=no`、`connection.autoconnect=no`、
`connection.zone=drop`，以及原 WPA2/RSN/CCMP、永久 MAC、隐藏网络、
禁用 Wi-Fi 省电和不保存 PSK 的策略。没有调用读取 NetworkManager 保存密钥的 API。
没有 IPv6 RA 时仍允许 IPv4 工作；链路本地地址或 ULA 本身不能证明 IPv6 公网连通。

`tools/wifi-fallback-policy.py` 验证可选布尔字段 `ipv6_auto`：
缺省或 false 保持旧 IPv4-only 策略；true 选择 `auto` 与 `-ipv6` 后缀。
`tools/wifi-auto-service.py` 和 `tools/wifi-service.py` 在射频启动前验证策略，
激活、断开及独立清理使用同一选定后缀，并把后缀记录进生命周期状态。
非法后缀会报错并拒绝接受 NV 清理，但不妨碍停止 DSP、模块及子进程。
依赖的 worker/controller 摘要固定值同步更新，没有放宽温度、PID 租约、
watchdog 或 NV 检查。

`tools/prepare-kernel-runtime.py` 为新生成的 7.3.1 配置设置
`ipv6_auto=true`；隔离 profile 仍是设备部署前提。不要重新生成并覆盖
已验收运行时目录，也不要把旧构建 bundle 当成本次已部署的新运行时。
实际适配、摘要和精确载荷以本阶段受保护的 staged 记录为准。

### 传输故障与受保护部署

最初既有 LAN SSH 超时，随后 USB SSH 也超时。只读检查发现主机对应
USB 网卡没有 IPv4 地址；用户另外授权临时直连 USB 地址
`${HOST_USB_IP}/30`。重新核对 USB 设备后仅添加该临时地址，没有修改主机
默认路由、DNS、NAT、转发或持久 NetworkManager profile，也没有降低 SSH 主机密钥验证。
之后 USB SSH 核对了同一原生内核和启动身份。

手机原 RF 所有者仍正常运行，但 `wlan0` 未关联、无载波；已有策略不在掉线后
自动重连。精确备份旧运行时、授权和证明后，正常停止所有者，
独立确认 DSP/WLAN 关闭、普通 NV checkpoint 一致、无工作文件/共享 RAM
打开描述符，并由所有者正常关闭其 dirty 标记。

创建隔离 profile 后，精确部署 13 个版本化运行时文件并重新绑定实际原生摘要、
manifest 与授权。先只开放有界 probation，不复用或改写旧 worker 的证明。
新的原生 45 秒试验实际通过，单元正常成功退出，独立 NV/DSP/描述符清理通过；
据该真实结果生成新证明，关闭 probation 授权并启用持续 RF。
新所有者连续至少 45 秒受保护运行、零重启；本次不再执行额外的外部停止。

最终复核时 USB SSH 再次超时，主机此前的 USB 网卡已不存在。
未推断手机重启或故障，也未再修改主机网络；改用已恢复的严格 pin LAN SSH，
确认仍是同一原生启动、当前 RF 所有者及新证明。保留该传输失败记录。

### 验收、限制与证据

实际连接为 2.4 GHz 回退 profile。IPv4 DHCP、默认路由、DNS/TLS HTTPS 和 LAN SSH
保留；IPv6 链路本地地址已完成 DAD，公网地址与 RA 默认路由存在，强制 IPv6 的
直接 HTTPS 成功。新旧 profile 的非秘密审计字段、drop zone 与入站 nft 规则复核一致。
已有防火墙策略允许必要 ICMPv6 ND/RA/MLD，不需要新增入站端口或放开整个 zone。
**启用 IPv6 不等于开放 IPv6 SSH**；原受限 IPv4 LAN SSH 规则未扩大。

屏幕服务 active 且零重启，电源服务 inactive/disabled；默认内核、模块、
启动单元和救援运行时未替换。当前持续 Wi-Fi 的 dirty 属于活跃所有者，
有效且保留，**不得手动清除**。历史 5 GHz 超时、掉线和不自动重连限制仍然存在。
新配置已持久部署、原自启动单元保持 enabled，但本阶段没有进行重启或冷启动验收。
Petitboot 菜单、USB 日志硬件验收和内核交接状态没有因此改变。

本次源代码的 Wi-Fi/候选运行时主机回归共 177 项通过。受保护证据均相对于仓库根目录：

| 路径（`out/wifi-ipv6-20261101/` 下） | 内容 |
| --- | --- |
| `authorization.json`、`host-usb-authorization.json` | 手机 IPv6 与独立临时主机地址授权 |
| `native-audit.stderr`、`initial-usb-ssh.stderr`、`host-usb-address-result.json` | 初始传输失败与受限主机修改 |
| `verified-transport.json`、`usb-native-audit.stdout`、`usb-network-audit.stdout` | 部署前 USB 身份、RF 和网络快照；不是最终传输状态 |
| `runtime-before.tar.gz`、`staged/deployment-plan.json`、`staged/payload.tar.gz` | 原运行时保留及精确原生适配 |
| `host-tests.log`、`icmpv6-rule-summary.json` | 主机回归与既有必要 ICMPv6 放行 |
| `stop/accepted.json`、`deploy/accepted.json` | 正常停止/独立清理及精确部署 |
| `probation/accepted.json`、`activate/accepted.json` | 新有界证明、持续所有者和真实 IPv6 HTTPS |
| `final-audit/usb.stderr.txt`、`final-audit-lan/accepted.json` | 最后 USB 超时、最终 LAN 双栈及入站限制复核 |
| `result.json` | 本阶段最终状态与当前证据入口 |

`out/` 是私有忽略产物；不公开其地址、网络名、启动/会话标识、私有摘要或凭据，
新克隆不保证存在这些文件。历史单次部署辅助程序不可盲目重跑；
进一步改变射频、证明或主机网络仍须遵守相应授权与生命周期检查。

## English

Subsequent state: this note preserves the restricted-inbound-policy snapshot from
IPv6 deployment. A later grant set the current Wi-Fi, USB and default zones to
ACCEPT, opening all service ports while retaining built-in checks; see
[the open firewall policy](FIREWALL-OPEN.md). “Inbound restrictions unchanged”
below does not describe the current port policy.

### 2026-11-01 state and authorization

Wi-Fi dual stack is enabled on native `7.3.1-picasso-wifi2`: IPv4 DHCP remains,
and automatic IPv6 has a ready link-local address, a public address, an RA prefix
route and a default route. Separate forced IPv4 and IPv6 requests directly through
`wlan0` to `https://example.com` returned HTTP 200 with certificate verification
and no proxy. Strict host-key-pinned LAN SSH over a non-USB route also passed.
This is a stage snapshot, not endurance or next-boot acceptance.

The user explicitly selected IPv6 configuration/deployment and necessary normal
guarded Wi-Fi starts/stops and acceptance, retaining IPv4 and inbound restrictions.
No flashing, phone reboot, temporary Petitboot boot, default-image replacement,
raw NV partition access, manual dirty-marker removal or NV restoration occurred.
Earlier Wi-Fi recovery and first Petitboot boot approvals cannot be reused here.

### Cause and compatible configuration

The accepted kernel has `CONFIG_IPV6=y`; both previous Wi-Fi workers enforced
NetworkManager `ipv6.method=disabled`. A connection-only manual change would be
refused at the next guarded activation. The Petitboot loader candidate's IPv6
configuration is unrelated to native Wi-Fi in this stage.

Original autoconnect profiles are shared with the retained 6.18 environment,
whose old worker requires IPv6 disabled. Rather than overwrite them, two isolated
dual-stack clones were created:

| Configuration | Dual-stack profile | Retained legacy profile |
| --- | --- | --- |
| Preferred network | `picasso-auto-${PRIMARY_SSID}-ipv6` | `picasso-auto-${PRIMARY_SSID}` |
| 2.4 GHz fallback | `picasso-auto-${FALLBACK_SSID}-ipv6` | `picasso-auto-${FALLBACK_SSID}` |
| IPv4 / IPv6 | `ipv4.method=auto` / `ipv6.method=auto` | IPv4 DHCP / IPv6 disabled |

These names are sanitized examples, not replayable configuration. New profiles
retain `ipv6.may-fail=yes`, `ipv6.never-default=no`, `connection.autoconnect=no`,
`connection.zone=drop`, and existing WPA2/RSN/CCMP, permanent MAC, hidden-network,
disabled Wi-Fi power-saving and non-saved-PSK policies. No NetworkManager
saved-secret retrieval API was called. IPv4 may work without IPv6 RA; a link-local
address or ULA alone does not establish public IPv6 connectivity.

`tools/wifi-fallback-policy.py` validates optional Boolean `ipv6_auto`:
absent/false retains legacy IPv4-only policy; true selects `auto` and `-ipv6`.
`tools/wifi-auto-service.py` and `tools/wifi-service.py` validate policy before RF
startup and use the same selected suffix for activation, disconnect and independent
cleanup, recording it in lifecycle state. An invalid suffix reports an error and
refuses NV-cleanup acceptance without preventing DSP/module/child shutdown.
Dependent worker/controller hash pins were updated coherently; temperature,
PID-lease, watchdog and NV checks were not relaxed.

`tools/prepare-kernel-runtime.py` sets `ipv6_auto=true` in newly generated 7.3.1
configuration; isolated profiles remain a device-deployment prerequisite. Do not
regenerate over the accepted runtime directory or mistake an old build bundle for
the newly deployed runtime. Actual adaptation, hashes and exact payload are bound
in this stage's protected staged receipts.

### Transport failures and guarded deployment

Existing LAN SSH initially timed out, followed by USB SSH. Read-only inspection
found no IPv4 address on the corresponding host USB interface. The user separately
authorized a temporary direct USB address, `${HOST_USB_IP}/30`. After rechecking
the USB device, only that temporary address was added: no host default-route,
DNS, NAT, forwarding or persistent NetworkManager profile changes, and no weaker
SSH host-key checking. USB SSH then verified the same native kernel/boot identity.

The phone's original RF owner was running normally, but `wlan0` was unassociated
with no carrier; existing policy does not automatically reconnect after loss.
After exact runtime/authorization/proof backup, the owner was normally stopped.
Independent checks confirmed DSP/WLAN off, matching ordinary NV checkpoint and
no open work/shared-RAM descriptors; the owner normally closed its own dirty marker.

Following isolated-profile creation, exactly 13 versioned runtime files were
deployed with actual native hashes, manifest and consent rebound. Initially only
bounded probation was permitted; the old worker's proof was neither reused nor
rewritten. A fresh native 45-second trial passed with normal unit success and
independent NV/DSP/descriptor cleanup. Its actual result produced a new proof,
bounded consent was consumed and continuous RF enabled. The new owner ran guarded
for at least 45 seconds with no restarts; no further external stop was performed.

During final review USB SSH timed out again, and the previous host USB interface
no longer existed. No phone reboot/failure was inferred and no further host
network modification was made. Restored strict-pinned LAN SSH confirmed the same
native boot, current RF owner and new proof. This transport failure was retained.

### Acceptance, limitations and evidence

The actual connection uses the 2.4 GHz fallback profile. IPv4 DHCP, default route,
DNS/TLS HTTPS and LAN SSH remain available. IPv6 link-local DAD completed, a public
address and RA default route exist, and forced direct IPv6 HTTPS succeeded.
Legacy non-secret profile audit fields, the drop zone and inbound nft rules matched
the prior audit. Existing firewall policy permits essential ICMPv6 ND/RA/MLD;
no inbound port or zone-wide permission was added. **Enabling IPv6 does not open
IPv6 SSH**; the restricted IPv4 LAN SSH rule was not expanded.

The screen service is active with no restarts; power remains inactive/disabled.
Default kernel, modules, startup units and rescue runtime were not replaced.
The current continuous Wi-Fi dirty marker belongs to the live owner, is valid
and retained, and **must not be manually cleared**. Historical 5 GHz timeouts,
link loss and disabled automatic reconnection remain unresolved. Configuration
was persistently deployed and the original startup unit remains enabled, but
this stage performed no reboot/cold-start acceptance. Petitboot menu, USB logging
hardware acceptance and kernel-handoff status are unchanged.

All 177 Wi-Fi/candidate-runtime host regressions passed for these source changes.
Protected evidence paths are repository-root-relative:

| Path (under `out/wifi-ipv6-20261101/`) | Contents |
| --- | --- |
| `authorization.json`, `host-usb-authorization.json` | Phone IPv6 and separate temporary-host-address grants |
| `native-audit.stderr`, `initial-usb-ssh.stderr`, `host-usb-address-result.json` | Initial transport failures and bounded host change |
| `verified-transport.json`, `usb-native-audit.stdout`, `usb-network-audit.stdout` | Predeployment USB identity/RF/network snapshot; not final transport state |
| `runtime-before.tar.gz`, `staged/deployment-plan.json`, `staged/payload.tar.gz` | Retained runtime and exact native adaptation |
| `host-tests.log`, `icmpv6-rule-summary.json` | Host regressions and existing essential ICMPv6 allowance |
| `stop/accepted.json`, `deploy/accepted.json` | Normal stop/independent cleanup and exact deployment |
| `probation/accepted.json`, `activate/accepted.json` | New bounded proof, continuous owner and actual IPv6 HTTPS |
| `final-audit/usb.stderr.txt`, `final-audit-lan/accepted.json` | Final USB timeout and final LAN dual-stack/inbound-policy review |
| `result.json` | Final stage state and current evidence entry point |

`out/` contains private ignored artifacts; their addresses, network names,
boot/session IDs, private hashes and credentials are not published. These files
may be absent in a fresh clone. Historical one-shot deployment helpers must not
be blindly rerun; further RF/proof/host-network changes remain subject to their
applicable authorization and lifecycle checks.
