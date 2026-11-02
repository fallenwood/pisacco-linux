# Firewalld 开放连接策略 / Firewalld Open-Connection Policy

## 中文

后续只读诊断发现 5 GHz 重关联后的监管域冲突，RF 已保护关闭；
见 [5 GHz 断开诊断](WIFI-5GHZ-DISCONNECT.md)。本页保留开放策略验收时的
在线快照，不能据此声称手机仍通过 LAN 在线；本次诊断没有修改开放规则。

### 2026-11-01 状态与授权

用户要求更新手机 firewalld，不再拦截流量；在明确区分“放行所有连接”和
“完全取消包括无效包在内的过滤”后，选择了 `accept_all_connections`。
因此保持 firewalld 运行，把当前 Wi-Fi、USB 和默认区域的目标持久设为 `ACCEPT`，
放行所有 IPv4/IPv6 服务端口及协议，包括面向公网 IPv6 地址的连接。
**firewalld 的无效数据包、IPv6 反向路径等内建检查仍保留**，不是停用整个过滤机制。

同局域网主机分别通过 IPv4 与 IPv6 直接访问手机 8080，均返回 HTTP 200，
未使用代理。IPv6 目标是公网地址，但客户端位于同一局域网，
不是从外部互联网节点完成的验收。手机 IPv4/IPv6 直接证书 HTTPS 仍返回 200，
严格主机密钥 LAN SSH 和当前受保护的 Wi-Fi 所有者保持正常。

此前 [IPv6 部署](WIFI-IPV6.md)保留入站限制的结果仍是有效历史快照；
本次是后续的新授权策略变更，**现在不再提供此前的端口访问限制**。
公开可达的服务须自行设置监听地址、认证及访问控制；
上游路由器、运营商、应用或内核路由设置仍可能影响实际可达性。

### 故障定位与兼容修改

修改前 firewalld 正在运行，`wlan0` 属于 `drop`。
运行时与永久配置仅有受限 IPv4 LAN SSH 的允许例外，8080 没有放行规则。
实际 nftables `inet firewalld` 的输入分派包含 `iifname "wlan0" drop`。
INPUT 主链的 `policy accept` 不会覆盖先命中的 DROP；
`trusted` 虽然目标为 ACCEPT，但未绑定网卡或来源。

8080 由 `pasta` 在 IPv6 通配地址监听，`v6only:0` 表示同时接受 IPv4，
手机本机 HTTP 返回 200。诊断时 `getenforce` 返回 `Disabled`；
拦截来源是 firewalld 下发、由内核执行的 nftables 规则，不是 SELinux 拒绝。
没有修改 Podman、容器端口发布或应用配置。

Wi-Fi worker/controller 检查 NetworkManager `connection.zone=drop` 和实际区域名；
直接把 profile 改到 `trusted` 或停用 firewalld 会破坏这些检查。
因此保留区域名、profile、来源与接口绑定，只修改以下目标：

| 区域 | 用途 | 修改前 | 修改后（运行时及永久） |
| --- | --- | --- | --- |
| `drop` | `wlan0` | `DROP` | `ACCEPT` |
| `picasso-usb` | 受限 USB 来源 | `default` | `ACCEPT` |
| `FedoraServer` | 默认区域 | `default` | `ACCEPT` |

**名称仍叫 `drop`，但该区域现在不再执行默认 DROP。**
原 SSH 允许规则保留，但已不是唯一能通过的端口。
只修改现有活动区域和默认区域；没有批量改写所有未使用的预定义区域。
没有新增 NAT、开启内核路由转发或修改主机网络。
IPv6 RPF、RFC3964 和无效包检查等全局设置没有改变。

先保留精确 `/etc/firewalld` 归档（含所有者、权限、ACL、扩展属性和符号链接）
及运行时/永久规则快照，再检查基线无变化。
通过 `firewall-cmd --permanent` 修改三个区域目标，检查配置，
执行一次普通 `firewall-cmd --reload`；没有停用或禁用 firewalld。
重新核对运行时和永久目标均为 ACCEPT，Wi-Fi 输入分派和默认分派最终 ACCEPT，
旧的区域 DROP/REJECT 已不再阻止端口连接。

Wi-Fi PID、启动与生命周期身份、有效 live dirty 标记，以及 runtime manifest、
activation 和真实原生 probation 证明的摘要均保持不变。
**没有重启射频、更新 worker 源码、重签或复用另一 worker 的证明、清除 dirty、
恢复 NV、刷写或重启手机。** 共享防火墙区域策略会影响同一系统的旧环境，
但救援内核/运行时文件未替换，没有新增 6.18 或冷启动验收。

### 只读查看与证据

下面是手机上的只读查看命令，不需要重载或重新启停服务：

```sh
sudo firewall-cmd --state
sudo firewall-cmd --get-zone-of-interface=wlan0
sudo firewall-cmd --zone=drop --list-all
sudo firewall-cmd --permanent --zone=drop --list-all
sudo nft list chain inet firewalld filter_INPUT_POLICIES
```

脱敏的连接示例为 `http://${PHONE_LAN_IP}:8080/` 和
`http://[${PHONE_IPV6}]:8080/`；占位符含义见 [INDEX.md](INDEX.md)，
不是可原样执行的地址。SSH 必须继续使用可信的主机密钥 pin。

受保护证据均相对于仓库根目录，位于 `out/firewall-open-20261101/`：

| 路径 | 内容 |
| --- | --- |
| `authorization.json` | 明确选择 ACCEPT 所有连接、保留内建检查的授权 |
| `preflight/firewall-before.tar.gz`、`preflight/accepted.json` | 精确旧配置、原始规则及所有者/证明基线 |
| `apply/accepted.json` | 三个区域的永久设置、重载及同所有者核对 |
| `verify/accepted.json` | 实际 ACCEPT 分派、双栈 HTTPS、同一有效 RF 所有者与证明 |
| `host-probes/result.json` | 同局域网 IPv4/IPv6 8080 HTTP 200 与主机路由 |
| `result.json` | 最终阶段状态与当前证据入口 |

`out/` 是被忽略的私有产物，不公开真实地址、SSID、账号、启动/会话标识、
私有摘要或外部本地路径。旧备份和一次性辅助程序仅用于保留证据，
不是自动恢复或重放授权。新规则已持久加载，但本阶段没有进行手机重启验收。

## English

Subsequent read-only diagnosis found a regulatory-domain conflict after 5 GHz
reassociation and RF safety shutdown; see
[5 GHz disconnect diagnosis](WIFI-5GHZ-DISCONNECT.md). This page retains the
open-policy acceptance's online snapshot, not current LAN availability.
That diagnosis did not change the open rules.

### 2026-11-01 state and authorization

The user requested that phone firewalld stop blocking traffic. After explicitly
distinguishing “allow all connections” from “remove all filtering, including
invalid-packet checks”, the user selected `accept_all_connections`.
Firewalld therefore remains running, with the current Wi-Fi, USB and default
zone targets persistently set to `ACCEPT`, allowing all IPv4/IPv6 service ports
and protocols, including connections to public IPv6 addresses.
**Built-in invalid-packet, IPv6 reverse-path and related checks remain**;
the filtering mechanism was not entirely disabled.

A host on the same LAN directly reached phone port 8080 over both IPv4 and IPv6,
receiving HTTP 200 without a proxy. The IPv6 destination was public, but the
client was on the same LAN; this is not acceptance from an external Internet
node. Phone direct certificate-verified IPv4/IPv6 HTTPS still returned 200;
strict-pinned LAN SSH and the current guarded Wi-Fi owner remained healthy.

The retained-inbound-restriction outcome in [IPv6 deployment](WIFI-IPV6.md)
remains a valid historical snapshot. This later, separately authorized policy
change **no longer provides those port-access restrictions**. Publicly reachable
services need their own bind-address, authentication and access controls.
Upstream routers, providers, applications and kernel routing settings may still
affect reachability.

### Diagnosis and compatible change

Before modification, firewalld was running and `wlan0` belonged to `drop`.
Runtime/permanent configuration allowed only restricted IPv4 LAN SSH, with no
8080 exception. Actual `inet firewalld` input dispatch included
`iifname "wlan0" drop`. The INPUT base-chain `policy accept` does not override an
earlier DROP; `trusted` had an ACCEPT target but no assigned interfaces/sources.

`pasta` listened on IPv6 wildcard port 8080 with `v6only:0`, accepting IPv4 too;
phone-local HTTP returned 200. Diagnostic `getenforce` returned `Disabled`.
The blocker was kernel-executed nftables rules installed by firewalld, not an
SELinux denial. Podman, container port publication and application configuration
were not changed.

Wi-Fi workers/controllers check NetworkManager `connection.zone=drop` and the
actual zone name. Switching profiles to `trusted` or stopping firewalld would
break those checks. Zone names, profiles, sources and interface assignments
were therefore retained; only these targets changed:

| Zone | Purpose | Before | After (runtime and permanent) |
| --- | --- | --- | --- |
| `drop` | `wlan0` | `DROP` | `ACCEPT` |
| `picasso-usb` | Restricted USB source | `default` | `ACCEPT` |
| `FedoraServer` | Default zone | `default` | `ACCEPT` |

**The zone is still named `drop`, but no longer applies a default DROP.**
The old SSH allow rule remains but is no longer the only permitted port.
Only existing active/default zones changed, not every unused predefined zone.
No NAT, kernel routing/forwarding enablement or host-network change was added.
Global IPv6 RPF, RFC3964, invalid-packet and related settings were unchanged.

An exact `/etc/firewalld` archive, including ownership, modes, ACLs, extended
attributes and symlinks, and runtime/permanent rule snapshots were retained
before checking for baseline drift. The three targets were changed using
`firewall-cmd --permanent`, configuration checked, and one ordinary
`firewall-cmd --reload` performed. Firewalld was neither stopped nor disabled.
Runtime/permanent targets were rechecked as ACCEPT; Wi-Fi and default input
dispatch terminate in ACCEPT, so the old zone DROP/REJECT no longer blocks ports.

Wi-Fi PID, boot/lifecycle identity, valid live dirty marker, and hashes of the
runtime manifest, activation and actual native probation proof were unchanged.
**No RF restart, worker-source update, proof rebinding/reuse from another worker,
dirty-marker removal, NV restoration, flashing or phone reboot occurred.**
Shared firewall-zone policy also affects older environments on this installation,
but rescue kernel/runtime files were not replaced; no new 6.18 or cold-start
acceptance was performed.

### Read-only inspection and evidence

These phone commands are read-only and do not reload or restart services:

```sh
sudo firewall-cmd --state
sudo firewall-cmd --get-zone-of-interface=wlan0
sudo firewall-cmd --zone=drop --list-all
sudo firewall-cmd --permanent --zone=drop --list-all
sudo nft list chain inet firewalld filter_INPUT_POLICIES
```

Sanitized connection examples are `http://${PHONE_LAN_IP}:8080/` and
`http://[${PHONE_IPV6}]:8080/`. See [INDEX.md](INDEX.md) for placeholders;
these are not replayable addresses. Continue using trusted SSH host-key pins.

Protected evidence is repository-root-relative, under `out/firewall-open-20261101/`:

| Path | Contents |
| --- | --- |
| `authorization.json` | Explicit all-connection ACCEPT with retained built-in checks |
| `preflight/firewall-before.tar.gz`, `preflight/accepted.json` | Exact previous configuration/rules and owner/proof baseline |
| `apply/accepted.json` | Three permanent zone targets, reload and same-owner checks |
| `verify/accepted.json` | Actual ACCEPT dispatch, dual-stack HTTPS and same valid RF owner/proof |
| `host-probes/result.json` | Same-LAN IPv4/IPv6 port 8080 HTTP 200 and host routes |
| `result.json` | Final stage state and current evidence entry point |

`out/` contains ignored private artifacts. Actual addresses, SSIDs, accounts,
boot/session identifiers, private digests and outside-repository local paths
are not published. Old backups and one-shot helpers preserve evidence, not
automatic rollback/replay authorization. New rules are persistently loaded,
but this stage performed no phone reboot acceptance.
