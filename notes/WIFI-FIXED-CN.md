# 固定 CN 国家码 / Fixed CN Country Policy

## 中文

### 2026-11-02：固定 CN 已部署，2.4 GHz 持续运行

用户要求“都使用CN国家码策略”，随后明确选择 `fixed_cn` 和
`deploy_and_verify`，确认 CN 设置合规，并授权精确部署及必要的受保护 Wi-Fi
启停验收。此选择替代此前等待路由器统一 US 的方向：
**手机两个批准频段都固定请求 CN，不再以 AP 宣告的 US 选择策略。**
没有路由器管理操作，也不要求 AP 必须宣告 CN 才能使用；
但实际信道仍必须完整满足 CN 限制，否则保护停机。

原生内核仍为 `7.3.1-picasso-wifi2`。当前 2.4 GHz 回退持续在线，实际监管域为 CN；
IPv4/IPv6 直连、证书校验 HTTPS 和严格主机密钥的非 USB 局域网 SSH 均通过。
USB SSH 亦用于本轮部署与独立验收。5 GHz 本轮首次连接仍超时，
**没有宣称 5 GHz 或长期掉线问题已修复**。

### 实现、部署与边界

`tools/wifi-cn-raw-radio-service.py` 的固定 `RawCN.audit()` 每次读取实际监管域，
即使 SSID 未改变，遇到 CN/`98` 以外的域也重新请求 CN，再执行完整原始审计。
正常 CN 或 `98` 不额外重复写入；显式关联前复核仍按要求重新请求。
`98` 仅作为待核对的交集候选，绝不因标签而直接信任。

本轮不是简单改国家字符串，也没有禁用 Country IE 的内核处理。
关闭的是项目的可选“跟随 AP 选择国家”模式：原始策略移除
`router_country_policy`，三个工作配置移除 `router_country`。
历史 router helper/reference 保留为未启用的绑定资产，未无关清理文件。
固定 CN 继续使用原本独立且固定摘要的 CN reference；RF 关闭时，
实际签名内核 regdb 的 CN 输出与该 reference **逐字节一致**。
签名 regdb、签名文件及内核验证要求没有改变。

同 PHY 的完整原始信道清单、功率、DFS、室内、no-IR、20 MHz 能力及属性来源
仍须通过。固定 CN 下 enabled 信道的 `NO_20MHZ` 拒绝规则不放宽；
上轮可选 router 模式的窄带排除不应用于此次 CN 策略。
保留原生身份、MAC/PHY、租约、40°C 以下启动、45°C 中止、
8 秒 watchdog、45 秒清理和普通 NV 生命周期保护。

先独立确认 RF/DSP/WLAN 关闭、dirty 不存在、普通 NV 文件与关闭 checkpoint
一致且无工作/共享 RAM 打开描述符，再精确备份当前运行时和旧证明。
原子、保留 xattr 的 root0400 部署更新 9 个绑定文件；
底层 worker、模块、系统单元、NM profiles、固件、BDF、校准、regdb、
防火墙 ACCEPT 策略和 6.18 救援运行时均未修改。
部署后先仅开启 probation；只有实际新证明通过后才启用持续 Wi-Fi。

### 本轮实际验收与保留失败

| 项目 | 结果与范围 |
| --- | --- |
| 主机回归 | 175 项 Wi-Fi 与 13 项运行时检查通过；包含同 SSID 外来域刷新及 CN/`98` 原始拒绝路径 |
| 离线生成 | 在新的私有输出中实际生成默认固定 CN bundle 并编译部署脚本；未覆盖既有已验收 bundle |
| 新原生 probation | 首选 5 GHz 超时，2.4 GHz 回退完成 WPA2/CCMP、DHCP、DNS、HTTPS、完整 CN 原始审计及 45 秒受保护运行 |
| 独立清理 | 单元 success；DSP offline、WLAN/dirty 不存在，关闭 checkpoint 与普通工作文件一致，无工作/共享 RAM 打开描述符 |
| 证明与持续运行 | 根据新原生历史结果及新 manifest 生成证明，未重用旧证明；持续运行至少 45 秒、零重启 |
| 验收工具失败 | 持续运行已通过后，读取运行时 `--get-target` 被 firewalld 拒绝，因为该选项只支持 `--permanent`；这是只读验收命令错误，不是 RF 故障 |
| 修正工具复核 | 未重启 RF、未重建证明；改读运行时和永久 `--list-all`，确认 `drop` target 均为 ACCEPT |
| 同 SSID 重关联 | 经 USB 对当前 2.4 GHz profile 正常 down/up 一次，使用已有 passwd-file 而不读取或导出凭据；相同所有者 PID/会话保留，重连后再观察 45 秒，CN 原始审计通过 |
| 网络与访问 | 重连前后 IPv4/IPv6 直连证书校验 HTTPS 200；随后非 USB IPv4/IPv6 LAN SSH 均通过，严格主机密钥核验保留 |

最后保留匹配当前 RF 所有者的有效 live dirty 标记，不能手动删除。
`allow_wifi=true`、`allow_wifi_probation=false`；屏幕保持运行，电源服务仍禁用。
旧证明、此前 US 模式失败和本次只读探针错误均保留，不把失败改写成成功。

本轮同 SSID 重关联在 **2.4 GHz、实际 CN** 下完成，没有人为把射频切成 US 来
制造错误；外来域刷新由聚焦主机测试覆盖，不能声称已完成 5 GHz US hint 的实机
重连验收。5 GHz 首次连接超时、历史约 15 分钟后的 reason-3 AP 断开和监管域
安全停机仍是不同问题；前两者未解决。短时通过不是长期稳定、充电或整机温控证明。
没有新增手机重启/冷启动验收，没有刷写、kexec、NV 恢复、手动清标记、
主机网络改动或 Podman 操作；Petitboot 硬件状态不变。

### 证据

以下路径相对于仓库根目录，均在被忽略的受保护本地产物
`out/fixed-cn-20261102/` 中：`authorization.json`、`preflight.json`、
`runtime-before.tar.gz`、`cn-reference.json`、`host-tests.log`、
`staged/deployment-plan.json`、`staged/validated.json`、`generator-check-fixed-cn/`、
`deploy/accepted.json`、`probation/accepted.json`、
`activate/stdout.jsonl`、`activate/stderr.txt`、`activate/status.json`、
`continuous-and-reconnect/accepted.json`、`lan-probe-v4/accepted.json`、
`lan-probe-v6/accepted.json` 和 `result.json`。
`activate` 的错误状态保留，由后续独立复核证实真实运行状态；
不能重新执行已消费的证明启用阶段。产物包含私有标识，新克隆不保证存在。
前阶段完整记录见[路由器国家码策略](WIFI-ROUTER-COUNTRY.md)和
[5 GHz 断开诊断](WIFI-5GHZ-DISCONNECT.md)。本笔记不构成后续设备操作授权。

## English

### 2026-11-02: fixed CN deployed; continuous 2.4 GHz operation

The user requested CN policy everywhere, then explicitly selected `fixed_cn` and
`deploy_and_verify`, confirmed CN compliance, and authorized exact deployment
and necessary guarded Wi-Fi start/stop acceptance. This supersedes waiting for
consistent router US configuration: **the phone requests fixed CN for both
authorized bands, rather than selecting policy from an AP's US advertisement.**
No router management occurred, and an AP need not advertise CN to be used.
Actual channels must nevertheless satisfy all CN limits or trigger safety shutdown.

The native kernel remains `7.3.1-picasso-wifi2`. The 2.4 GHz fallback is running
continuously with actual CN domain. Direct certificate-verified IPv4/IPv6 HTTPS
and strict-pinned non-USB LAN SSH over both families passed. USB SSH was also
used for deployment and independent acceptance. Initial 5 GHz connection still
timed out: **5 GHz and long-term disconnection issues are not claimed fixed**.

### Implementation, deployment and boundaries

Fixed `RawCN.audit()` in `tools/wifi-cn-raw-radio-service.py` reads actual
regulatory state on every call. Even with unchanged SSID, a domain other than
CN/`98` triggers a new CN request before full raw auditing. CN/`98` avoids
unnecessary repeated writes; explicit pre-association refresh still requests
the domain. `98` is only a candidate intersection to verify, never trusted by label.

This is not string relabeling or disabling kernel Country IE handling. The
project's optional AP-selected-country mode is disabled: remove
`router_country_policy` from raw policy and `router_country` from all three worker
configurations. Historical router helper/reference files remain as inactive
bound assets, without unrelated cleanup. Fixed CN retains its original isolated,
hash-pinned reference. With RF off, current signed native regdb CN output matched
that reference **byte for byte**. Signed regdb, its signature and kernel validation
requirements are unchanged.

Require complete same-PHY raw channel inventory, power, DFS, indoor, no-IR,
20 MHz capability and attribute provenance. Fixed CN's rejection of enabled
`NO_20MHZ` channels is not relaxed; the previous optional router mode's
narrow-channel exclusion is not used here. Preserve native identity, MAC/PHY,
lease, below-40°C startup, 45°C abort, 8-second watchdog, 45-second cleanup and
ordinary NV lifecycle guards.

First independently verify RF/DSP/WLAN off, absent dirty marker, ordinary NV
files matching the closed checkpoint, and no open work/shared-RAM descriptors.
Back up exact runtime and old proof. Atomic xattr-preserving root0400 deployment
updated 9 bound files. The underlying worker, modules, system units, NM profiles,
firmware, BDF, calibration, regdb, firewall ACCEPT policy and 6.18 rescue runtime
were unchanged. Enable only probation initially; continuous Wi-Fi requires a
genuine new native proof.

### Actual acceptance and retained failures

| Item | Result and scope |
| --- | --- |
| Host regressions | 175 Wi-Fi and 13 runtime checks passed, including unchanged-SSID foreign-domain refresh and raw CN/`98` rejection paths |
| Offline generation | Actually generated default fixed-CN bundle in fresh private output and compiled deployment scripts; no accepted bundle overwritten |
| New native probation | Preferred 5 GHz timed out; 2.4 GHz fallback completed WPA2/CCMP, DHCP, DNS, HTTPS, full raw CN audit and 45-second guarded operation |
| Independent cleanup | Unit success; DSP offline, WLAN/dirty absent, ordinary work files matched closed checkpoint and no open work/shared-RAM descriptors |
| Proof and continuous operation | Derived new proof from actual new native history/result and manifest, without reusing old proof; at least 45 seconds continuous operation with zero restarts |
| Verification-tool failure | After successful continuous observation, firewalld rejected runtime `--get-target`, which requires `--permanent`; this was a read-only probe error, not an RF fault |
| Corrected independent probe | No RF restart or proof regeneration; runtime and permanent `--list-all` both confirmed ACCEPT target for `drop` |
| Same-SSID reassociation | Over USB, ordinarily down/up the current 2.4 GHz profile once using its existing passwd-file without reading/exporting credentials; same owner PID/session retained, another 45-second post-reconnect observation and raw CN audit passed |
| Network/access | Direct certificate-verified IPv4/IPv6 HTTPS 200 before and after reconnect; subsequent non-USB LAN SSH passed for both families with strict host-key verification |

Retain the valid live dirty marker matching the current RF owner; do not remove
it manually. `allow_wifi=true`, `allow_wifi_probation=false`. Screen remains
active and the power service disabled. Old proof, earlier US-mode failures and
the read-only probe error remain preserved, not rewritten as successes.

Native same-SSID reassociation used **2.4 GHz with actual CN**; RF was not
artificially switched to US to manufacture a fault. Focused host tests cover
foreign-domain refresh, not hardware acceptance of a 5 GHz US-hint reconnect.
Initial 5 GHz timeout, historical reason-3 AP deauthentication after about
15 minutes, and subsequent regulatory safety shutdown remain distinct problems;
the first two are unresolved. Short observation is not endurance, charging or
whole-device thermal qualification. No new phone reboot/cold-start acceptance,
flashing, kexec, NV restoration, manual marker removal, host-network changes or
Podman operations occurred. Petitboot hardware status is unchanged.

### Evidence

Repository-root-relative paths below are protected ignored local artifacts under
`out/fixed-cn-20261102/`: `authorization.json`, `preflight.json`,
`runtime-before.tar.gz`, `cn-reference.json`, `host-tests.log`,
`staged/deployment-plan.json`, `staged/validated.json`, `generator-check-fixed-cn/`,
`deploy/accepted.json`, `probation/accepted.json`, `activate/stdout.jsonl`,
`activate/stderr.txt`, `activate/status.json`,
`continuous-and-reconnect/accepted.json`, `lan-probe-v4/accepted.json`,
`lan-probe-v6/accepted.json` and `result.json`. The failed `activate` probe status
remains; subsequent independent verification establishes actual running state.
Do not replay its consumed proof/activation phase. Artifacts contain private
identifiers and may be absent from a fresh clone. See historical
[router country policy](WIFI-ROUTER-COUNTRY.md) and
[5 GHz disconnect diagnosis](WIFI-5GHZ-DISCONNECT.md) for preceding evidence.
This note grants no further device operations.
