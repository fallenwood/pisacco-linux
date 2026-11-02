# 路由器国家码策略 / Router Country Policy

中文：下文为 2026-11-01 已暂缓的历史 US 策略快照。
2026-11-02 新授权改为手机两个频段固定 CN，不再跟随 AP 选择国家，
已通过新的原生证明、2.4 GHz 持续运行/同 SSID 重关联和双栈 LAN 验收；
5 GHz 仍连接超时。见[固定 CN 国家码](WIFI-FIXED-CN.md)。

English: The following preserves the deferred 2026-11-01 historical US-policy
snapshot. A fresh 2026-11-02 grant changed both phone bands to fixed CN rather
than AP-selected country. New native proof, continuous 2.4 GHz operation,
same-SSID reassociation and dual-stack LAN acceptance passed; 5 GHz still
times out. See [fixed CN country policy](WIFI-FIXED-CN.md).

## 中文

### 2026-11-01：已部署，等待路由器统一配置；未验收

用户要求“按照路由器信息为准”，确认国家设置合规，并授权精确的版本化部署及
必要的受保护 RF 启停验收。此授权不包含刷写、手机重启、手动清除 dirty 标记、
恢复 NV 或更改路由器。后续选择将路由器两个频段统一为 `US`，但明确暂缓调整；
因此停止后续射频试验，**不启用持续 Wi-Fi，不宣称修复已验收**。

原生内核仍为 `7.3.1-picasso-wifi2`。最后一次失败试验已独立核对：
DSP offline、WLAN 不存在、dirty 不存在，三个普通 NV 工作文件与关闭后的
checkpoint 摘要一致，且没有打开的工作文件或共享 RAM 描述符。
USB 严格主机密钥 SSH 可用；RF 关闭，不能把此前 LAN/双栈成功当作当前在线状态。
临时主机 USB 地址保留，没有新增默认路由、DNS、NAT、转发或持久 profile 改动。

### 实现与限制

`tools/wifi-router-country.py` 与原始 nl80211 审计适配器增加显式
`reviewed_router_country_ie` 策略，而不是无条件信任任意 AP 的国家字符串：

- 先审阅一个国家码，并固定从 RF 关闭的原生内核取得的独立监管规则；
  同时绑定 `/usr/lib/firmware/regulatory.db` 及其 `.p7s` 签名文件。
  原生内核要求签名 regdb，并使用内核监管数据库密钥。
- 已连接时，从 `iw ... link` 核对批准的 SSID、精确 BSSID 和频率，再读取
  **缓存** BSS 的 Country IE；没有新增主动扫描。允许整数形式的十进制频率、
  隐藏 SSID，以及一致的 beacon/probe 重复信息；缺失、矛盾或不匹配证据仍拒绝。
- 当前仅审阅 `US`。连接前使用这个明确审阅的 bootstrap 国家；
  连接后必须由当前选中 AP 的 Country IE 证实。不同或未知国家需要新审阅，
  不会自动切换信任。即使 SSID 不变，也检查实际监管域并在不匹配时重新请求。
- 逐一核对同一实际 PHY 的完整原始信道清单、功率、DFS、室内和 no-IR 限制，
  接受明确审阅国家或逐信道证明的 `98` 交集，而不是只检查国家标签。
  `NO_20MHZ` 信道不进入本项目 20 MHz 可用集合；其剩余窄带能力仍须满足
  规则和实际原始属性，且绝不允许选中 AP 利用该排除绕过 20 MHz 限制。
- 现有原生身份、MAC/PHY、租约、温度、8 秒 watchdog、45 秒清理和 NV 生命周期
  保护保留；未更改固件、BDF、校准、regdb、模块、系统单元、NM profile、
  firewalld ACCEPT 策略或旧 6.18 救援运行时。

`tools/prepare-kernel-runtime.py` 可成对接收 `--router-policy` 和
`--router-reference`，生成完整绑定的可选策略。两者缺省仍生成旧 CN 模式，
不会从输入中的旧 router 字段意外启用新模式。它期望原始、未版本化路径的输入，
不能把已部署的版本化配置直接再次迁移；本轮首次离线验证的这种输入错误保留，
在新私有输出中改正后，旧 CN 和 router 两种实际生成流程均通过。
已有已验收 runtime-bundle 没有被覆盖。

### 三次受控试验与实际阻塞

首次精确部署更新 12 个文件，后续两次修正各更新 7 个文件。
每次均先独立确认安全关闭并备份精确运行时/原证明，
以 root0400、保留 xattr 和原子持久化方式更新，随后核对完整绑定及功能门。
未改底层 worker；旧原生证明保留但未复用。

| 阶段 | 结果及限制 |
| --- | --- |
| 首次试验 | US 实际清单中 5845 MHz 不是 disabled，但有 `NO_20MHZ`；旧的“所有 enabled 信道都能用 20 MHz”断言拒绝，未开始关联 |
| 信道修正 | 原始证据回放通过；保留 `NO_20MHZ` 并排除该信道，仍检查其功率和限制，且禁止作为选中 AP 的 20 MHz 信道 |
| 第二次试验 | 首选 5 GHz 连接预算耗尽；2.4 GHz 关联成功，但在 AP 证据校验阶段失败，原 worker 汇总为 `Actual SG intersection rejected`；旧错误文字不表示采用 SG |
| 格式修正 | 增加十进制频率、一致重复 IE 的严格解析及解析失败证据记录；不把第二次汇总错误冒充为已证实的单一格式根因 |
| 第三次试验 | 5 GHz 再次超时，2.4 GHz 关联后明确拒绝 `Selected router country changed; policy review required` |
| 新发现 | journal 记录 5 GHz 的 Country IE 为 `US`，两次 2.4 GHz 回退实际收到 `CN`；单一 US 策略正确拒绝不一致的回退 |
| 当前选择 | 用户选择两个频段统一为合规 `US`，随后选择暂缓配置；没有再次试验 |

最后主机回归为 173 项 Wi-Fi 与 13 项运行时检查通过；这不等于新的原生
45 秒验收。三次试验均失败并安全清理，最后已独立确认普通 NV/DSP/FD 关闭。
`allow_wifi=false`、`allow_wifi_probation=true`；旧持续服务虽保留 enabled，
功能门不允许使用旧证明启动新运行时。没有新的成功证明或持续 RF 所有者。

**5 GHz 首次连接超时、历史约 15 分钟后的 AP reason-3 断开，以及监管冲突后的
安全停机是不同问题。** 本轮没有证明前两者已修复，也没有同 SSID 重连、
持续 45 秒、双栈或冷启动的新验收。前一只读诊断见
[5 GHz 断开诊断](WIFI-5GHZ-DISCONNECT.md)。

### 后续边界与证据

需先在路由器管理端将两个频段设置为已核对合规的同一 `US` 配置并应用。
本轮未取得路由器管理连接，也未代为修改。用户明确确认配置完成并同意继续后，
才能重新检查实际 Country IE、精确运行时、关闭 checkpoint 和温度，再进行受控
45 秒试验、独立清理及新的证明生成。5 GHz 超时若仍出现，必须单独诊断；
不得通过信任 CN 回退、降低限制、手动清标记或重用旧证明伪造成功。
本笔记不是新授权，也不是可直接重放的设备操作指令。

受保护证据相对于仓库根目录，位于 `out/router-country-20261101/`：
`authorization.json`、`router-reference.json`、`router-policy.json`、
`preflight.json`、`preflight-v2.json`、`preflight-v3.json`、
`runtime-before.tar.gz` 及两个版本化备份、
`staged/`、`staged-v2/`、`staged-v3/`、
三个 `deploy*`/`probation*` 阶段、三个 `probation-failure*` 目录、
`native-cache-observation-v3/`、`band-country-conflict/`、
`host-tests-v3.log`、`final-clean/accepted.json` 和 `result.json`。
首次离线生成失败与各次原生失败保留，旧证明始终存于备份。
这些产物含私有网络/设备标识，仅保存在被忽略的本地目录，新克隆不保证存在。
未操作 Podman；Petitboot 菜单、USB 日志及内核交接的验收状态未变。

## English

### 2026-11-01: deployed, awaiting consistent router configuration; unaccepted

The user requested following router information, confirmed the country setting
was legitimate, and authorized exact versioned deployment and necessary guarded
RF start/stop acceptance. This excluded flashing, phone reboot, manual dirty-marker
removal, NV restoration and router changes. The later choice was to align both
router bands to `US`, followed by an explicit deferral of that adjustment.
Further RF trials therefore stopped: **continuous Wi-Fi is not enabled and the
repair is not claimed accepted**.

The native kernel remains `7.3.1-picasso-wifi2`. After the last failed trial,
independent checks confirmed offline DSP, absent WLAN/dirty marker, all three
ordinary NV work-file digests matching the closed checkpoint, and no open work
or shared-RAM descriptors. Strict-pinned USB SSH is available. RF is off, so
historical LAN/dual-stack successes are not current connectivity claims.
The temporary host USB address remains; no additional default-route, DNS, NAT,
forwarding or persistent-profile changes occurred.

### Implementation and limitations

`tools/wifi-router-country.py` and the raw nl80211 adapter add an explicit
`reviewed_router_country_ie` policy, not unconditional trust in arbitrary AP
country strings:

- Review one country first and pin isolated rules obtained from the native kernel
  with RF off, together with `/usr/lib/firmware/regulatory.db` and its `.p7s`
  signature. The native kernel requires signed regdb and uses kernel regdb keys.
- When connected, verify authorized SSID, exact BSSID and frequency from
  `iw ... link`, then read the selected **cached** BSS Country IE; no additional
  active scan is introduced. Integral decimal frequencies, hidden SSID and
  consistent repeated beacon/probe information are supported. Missing,
  conflicting or mismatched evidence is still rejected.
- Only `US` is currently reviewed. Before association, use this explicitly
  reviewed bootstrap country; afterward, require confirmation from the selected
  AP's Country IE. Different/unknown countries need another review, not automatic
  trust. Actual regulatory state is checked and refreshed when mismatched even
  if the SSID remains unchanged.
- Audit the complete actual same-PHY raw channel inventory, power, DFS, indoor
  and no-IR limits. Accept the reviewed country or a channel-verified `98`
  intersection, not merely a country label. A `NO_20MHZ` channel is excluded from
  this project's usable 20 MHz set; its remaining narrow-channel capabilities
  still require rule/raw-attribute validation. The selected AP cannot use that
  exclusion to bypass its 20 MHz requirement.
- Preserve native identity, MAC/PHY, lease, thermal, 8-second watchdog,
  45-second cleanup and NV lifecycle guards. Firmware, BDF, calibration, regdb,
  modules, system units, NM profiles, firewalld ACCEPT policy and the retained
  6.18 rescue runtime are unchanged.

`tools/prepare-kernel-runtime.py` accepts the optional paired `--router-policy`
and `--router-reference` inputs and generates fully bound assets. Omitting both
retains legacy CN mode without accidentally inheriting router opt-in fields
from an input. It expects original unversioned paths, not an already deployed
versioned configuration to relocate again. The first offline validation made
that input mistake; the failure was retained and corrected in fresh private
outputs, where both real legacy-CN and router generation passed. The previously
accepted runtime-bundle was not overwritten.

### Three bounded trials and the actual blocker

Initial exact deployment updated 12 files; each of the two corrections updated
7. Each was preceded by independent clean-stop verification and an exact
runtime/old-proof backup, used root0400/xattr-preserving atomic durable writes,
and checked all bindings and the feature gate afterward. The underlying worker
was unchanged. The old native proof was preserved, not reused.

| Stage | Result and limitation |
| --- | --- |
| First trial | Actual US inventory included non-disabled 5845 MHz with `NO_20MHZ`; the old assertion that every enabled channel supports 20 MHz rejected it before association |
| Channel correction | Exact raw-evidence replay passed; retain `NO_20MHZ`, exclude that channel, audit its power/restrictions and forbid selecting it as a 20 MHz AP channel |
| Second trial | Preferred 5 GHz connection budget expired; 2.4 GHz associated but failed AP-evidence validation, summarized by the unchanged worker as `Actual SG intersection rejected`; that historical label does not mean SG was selected |
| Format correction | Added strict decimal-frequency/consistent-repeat parsing and retained parsing-failure evidence; the second summarized error is not presented as proof of a single format root cause |
| Third trial | 5 GHz timed out again; after 2.4 GHz association, explicitly rejected `Selected router country changed; policy review required` |
| New finding | Journal records show `US` Country IE for 5 GHz and actual `CN` hints for both 2.4 GHz fallback attempts; the single reviewed US policy correctly rejects inconsistent fallback |
| Current choice | User chose consistent legitimate `US` on both router bands, then deferred configuration; no further trial occurred |

Final host regressions passed 173 Wi-Fi and 13 runtime checks. They do not
constitute new native 45-second acceptance. All three native trials failed and
cleaned safely; final ordinary NV/DSP/FD closure was independently checked.
`allow_wifi=false`, `allow_wifi_probation=true`. Although the old continuous
unit remains enabled, its feature gate prevents starting the new runtime on the
old proof. There is no new accepted proof or continuous RF owner.

**Initial 5 GHz connection timeout, the historical AP reason-3 disconnect after
about 15 minutes, and subsequent regulatory safety shutdown are distinct
problems.** Neither of the first two is proven fixed. No new same-SSID
reassociation, continuous 45-second, dual-stack or cold-start acceptance was
obtained. See the preceding
[5 GHz disconnect diagnosis](WIFI-5GHZ-DISCONNECT.md).

### Next boundary and evidence

First apply the reviewed legitimate consistent `US` configuration to both router
bands through router management. No management connection was available here
and no router setting was changed. Only after explicit confirmation that this
is complete and continuation is approved may the actual Country IE, exact
runtime, closed checkpoint and temperature be rechecked before a guarded
45-second trial, independent cleanup and genuine new proof generation.
Persistent 5 GHz timeout requires separate diagnosis, not trusting CN fallback,
relaxing restrictions, clearing markers manually or reusing old proof.
This note is neither fresh permission nor replayable device instructions.

Protected repository-root-relative evidence is under
`out/router-country-20261101/`: `authorization.json`, `router-reference.json`,
`router-policy.json`, `preflight.json`, `preflight-v2.json`, `preflight-v3.json`,
`runtime-before.tar.gz` and two versioned backups,
`staged/`, `staged-v2/`, `staged-v3/`, three `deploy*`/`probation*` phases,
three `probation-failure*` directories, `native-cache-observation-v3/`,
`band-country-conflict/`, `host-tests-v3.log`, `final-clean/accepted.json`
and `result.json`. The initial offline-generator failure and all native failures
are retained; the old proof remains in backups. Private network/device
identifiers stay in these ignored local artifacts, which may be absent from a
fresh clone. No Podman operation occurred. Petitboot menu, USB logging and kernel
handoff acceptance are unchanged.
