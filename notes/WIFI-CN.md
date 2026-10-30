# 国家码由SG切换CN：配置已写入/全局CN已确认，PHY室内限制校验未通过 / Country code changed from SG to CN: configuration saved/global CN confirmed, PHY indoor-restriction validation failed

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本文保留首次CN配置和后续拒绝记录；失败、离线状态与旧服务命令均属历史阶段，不是实时状态。 / This preserves initial CN configuration and subsequent rejection records; failures, offline status, and old-service instructions belong to historical stages, not live status.

## 中文

> 最新已修复取证并原生通过，见[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)。R2实际raw attr14核验通过且2.4G联网/90秒观察成功，服务enabled/active；原SG/R1CN和重试失败都保留disabled。以下错误/离线信息为历史，不要按本页旧单元管理当前无线，更不能删除新session的活跃dirty。

> **后续只读排查已确认取证逻辑错误**：匹配手机的签名iw6.17源码根本不在info/list/channels文本输出原始INDOOR_ONLY，因此本页“未显示标志”的失败不能证明内核/驱动没落实限制。未删除保护或改手机政策；只准备原始nl80211 GET采集器，实际live PHY bit仍未测、无线仍关闭，见[WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md)。本页原拒绝/清理记录保留，不改写为联网成功。

> 后续用户明确“重试”，单独新runtime单元`picasso-wifi-cn-attended-20261030T083536.service`/session${SESSION_4}，在相同原样CN政策下只初始化一次，仍报5180MHz室内限制标志检查失败；**未激活任何SSID**，当前WLAN absent/DSP offline/dirty absent，独立cleanup/checkpoint/assets复核通过。旧SG/CN失败单元没有restart/reset，global CN、预算22不变；该次session最高35.7°C，三组开始读数<40，证据`out/wifi-cn-retry-20261030T083536Z/`。以下是首次CN配置阶段历史，不能把新请求误计为本阶段自动重试或声称已经联网。

用户请求：**“从SG切换到CN”**。CN必须与设备实际所在地一致，仅适用于中国大陆。

## 当前真实状态

- 内核`iw reg get`全局确认为`country CN: DFS-FCC`，不是只改配置字符串。
- 手机`/opt/picasso-wifi-cn/`保存CN原生规则参考、独立审计器、窄适配控制器和root0400政策；新`picasso-wifi-radio-cn.service`已持久安装/设为enabled。
- **新CN服务真机启动未通过，当前failed/MainPID0、真实wlan0不存在、MPSS offline，不能联网，也不能宣称保持UP成功。**
- Session `${SESSION_8}`，本阶段唯一一次无线初始化；`attempts=[]`，没有连接${PRIMARY_SSID}或${FALLBACK_SSID}、无SSID回退/重试。
- Exact error：`ValueError: Enabled 5180 MHz / 23 dBm exceeds observed CN20MHz rules or lacks DFS/indoor/IR restriction`。

## 为什么停止

内核签名regdb的CN规则对5150–5350MHz含`NO-OUTDOOR`，例如5150–5250/23dBm、5250–5350/20dBm+DFS。
真机抓取的global域是CN，PHY仍带板级US参考，并实际收紧了CN功率/信道：2G20dBm、5500–5720禁用、5.8G实际30dBm等。
**但5180/5200/5220/5240的PHY行未显示对应`indoor only`标志**；CN审计器要求确认该限制，不能仅因当前连接可能用2G就忽略其余启用信道。
因此在管理UP/SSID激活前安全退出，保留原始global+PHY规则和全部频点行。

这表示**无法完成现有检查要求**，不能据此宣布实际违法发射、硬件损坏、终端实际在室外，或假定具体驱动/iw映射根因。
没有为了通过删除NO-OUTDOOR/DFS/实际功率校验，没有伪造能力或修改BDF、校准、RF功率参数。
后续只能先只读核对内核/驱动/nl80211/iw对室内限制的表示与执行路径，再明确安排新的RF验收；本阶段无第二次RF初始化。

## 继承与持久化方式

- 原SG worker `wifi-auto-service.py` SHA428495…、旧radio控制器SHAa1d1…、原config-auto字节均未改，既有45s旧worker证明不是新的CN运行验收。
- CN适配器只覆盖三个方法：精确`iw reg set SG`请求映射为CN、CN严格审计、审计字段改为CN命名。startup/guard/独立cleanup继承原代码。
- 原生参考在**无WLAN/MPSS未启动**时从当前内核获取，SHA `0bb35936c13e1e16977c29d2f8c42e672075fd523c5faa9a6361fc74ed1160f7`。
- 当前内核`CONFIG_CFG80211_REQUIRE_SIGNED_REGDB=y`、`CONFIG_CFG80211_USE_KERNEL_REGDB_KEYS=y`；未替换regdb或签名。
- 旧SG `picasso-wifi-radio.service` **disabled/failed**，失败session `${SESSION_9}`原样保留。新CN服务虽enabled，但failed不等于已通过启动验收；不要直接重启旧SG服务、删除失败或反复启动新CN服务。
- Native ready样本0，没有声称CN45sUP或关联成功。下次开机实际激活也未验收；本次没有重启。

3组真实开始温度均<40°C、45°C abort、精确3秒Root PID lease/四FD backend、8秒watchdog/45秒cleanup、CPU0–3/256MiB/CPU6/7运行期1094400kHz及退出恢复保持。
正常cleanup提交working checkpoint、清空共享RAM、恢复原core/CPU、dirty absent，独立postcleanup assets/checkpoint审计通过；当前没有活动dirty，不可拿旧active快照宣称本轮仍运行。
原自动预算SHA `${PRIVATE_BUDGET_SHA256}`不变，未reset-failed、重放旧专用试验或刷新预算。

## 证据/下一步

`out/wifi-cn-20261030T075148Z/`保存原生CN参考、部署/签名策略、全局+PHY完整失败观察和最终独立审计。
离线384项：383通过、1可选QEMU跳过。首轮测试仅因Python增加类元数据字段而断言失败，原失败日志保留，修正为只比较可调用方法；不是RF失败重放。
最初参考采集器字符串转义SyntaxError发生在执行前，保留错误；之后独立源码采集器只写一次CN请求，无RF初始化。

当前只可经USB SSH管理。SSID/PMK保存位置、公钥/来源限定LAN22规则、SELinux实际Permissive、屏幕tty1/音量UP/15秒idle和待激活power DTB均未改。
没有boot写/重启/PMIC/原始NV或凭据/SSH私钥读取导出。CN配置已落盘不等于无线已可用、已联网或长期RF/充电安全通过。

## English

> The later evidence-collection fix passed natively; see [WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md). Actual R2 raw attr14 validation passed, 2.4G connectivity/90-second observation succeeded, and the service was enabled/active; original SG/R1CN and retry failures were all retained disabled. The errors/offline information below is historical. Do not manage current wireless through this page's old unit, and never delete a new session's active dirty marker.

> **Later read-only investigation confirmed an evidence-collection logic error**: the signed iw6.17 source matching the phone never prints raw INDOOR_ONLY in info/list/channels text output. Therefore this page's “flag not displayed” failure cannot prove the kernel/driver failed to enforce the restriction. No protection was removed or phone policy changed; only a raw nl80211 GET collector was prepared, while actual live PHY bits remained unmeasured and wireless off. See [WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md). The original rejection/cleanup records remain, not rewritten as connectivity success.

> The user later explicitly requested “retry.” A separate new runtime unit `picasso-wifi-cn-attended-20261030T083536.service`/session${SESSION_4} initialized once under the identical unchanged CN policy and again failed the 5180MHz indoor-restriction flag check. **No SSID was activated**; WLAN was absent/DSP offline/dirty absent, and independent cleanup/checkpoint/assets rechecks passed. Old SG/CN failed units were not restarted/reset; global CN and budget22 stayed unchanged. That session peaked at 35.7°C, with three starting groups <40; evidence: `out/wifi-cn-retry-20261030T083536Z/`. Below is the initial CN-configuration-stage history; this new request must not be counted as an automatic retry in that stage or claimed as connectivity.

User request: **“Switch from SG to CN.”** CN must match the device's actual location and applies only to mainland China.

### Actual state at this stage

- Kernel `iw reg get` globally confirmed `country CN: DFS-FCC`, not merely a configuration-string change.
- Phone `/opt/picasso-wifi-cn/` stored native CN rule reference, independent auditor, narrow adapter controller, and root0400 policy; new `picasso-wifi-radio-cn.service` was persistently installed/set enabled.
- **The new CN service did not pass hardware startup; it was failed/MainPID0, real wlan0 absent, MPSS offline. It could not connect, and successful persistent UP cannot be claimed.**
- Session `${SESSION_8}`, this stage's only wireless initialization; `attempts=[]`, with no ${PRIMARY_SSID} or ${FALLBACK_SSID} connection, SSID fallback, or retry.
- Exact error: `ValueError: Enabled 5180 MHz / 23 dBm exceeds observed CN20MHz rules or lacks DFS/indoor/IR restriction`.

### Why it stopped

The kernel's signed regdb CN rules include `NO-OUTDOOR` for 5150–5350MHz, for example 5150–5250/23dBm and 5250–5350/20dBm+DFS.
Native capture showed global CN while the PHY retained the board-level US reference and actually tightened CN power/channels: 2G20dBm, 5500–5720 disabled, actual 5.8G30dBm, etc.
**However, PHY lines for 5180/5200/5220/5240 did not display the corresponding `indoor only` flag**. The CN auditor requires confirmation of this restriction; other enabled channels cannot be ignored merely because the current connection might use 2G.
It therefore safely exited before administrative UP/SSID activation, retaining original global+PHY rules and every frequency line.

This means **the existing check requirements could not be completed**, not that unlawful transmission, hardware damage, or actual outdoor location was established, nor that a specific driver/iw mapping root cause can be assumed.
NO-OUTDOOR/DFS/actual-power validation was not removed for a pass; capabilities were not fabricated and BDF/calibration/RF-power parameters were unchanged.
Further work must first read-only check kernel/driver/nl80211/iw indoor-restriction representation and enforcement paths, then explicitly arrange new RF acceptance; no second RF initialization occurred in this stage.

### Inheritance and persistence

- Original SG worker `wifi-auto-service.py` SHA428495…, old radio controller SHAa1d1…, and original config-auto bytes were unchanged; existing 45s old-worker proof is not new CN runtime acceptance.
- The CN adapter overrides only three methods: mapping the exact `iw reg set SG` request to CN, strict CN audit, and renaming audit fields to CN. Startup/guard/independent cleanup inherit the original code.
- Native reference was obtained from the current kernel **with no WLAN/MPSS not started**, SHA `0bb35936c13e1e16977c29d2f8c42e672075fd523c5faa9a6361fc74ed1160f7`.
- Current kernel has `CONFIG_CFG80211_REQUIRE_SIGNED_REGDB=y` and `CONFIG_CFG80211_USE_KERNEL_REGDB_KEYS=y`; regdb/signatures were not replaced.
- Old SG `picasso-wifi-radio.service` was **disabled/failed**, with failed session `${SESSION_9}` retained unchanged. Although the new CN service was enabled, failed does not mean startup acceptance passed; do not directly restart old SG, delete failures, or repeatedly start new CN.
- Native ready samples=0; neither CN45sUP nor association success was claimed. Actual activation at next boot remained unaccepted; no reboot occurred.

Three real starting-temperature groups were all <40°C; 45°C abort, exact 3-second Root PID lease/four-FD backend, 8-second watchdog/45-second cleanup, CPU0–3/256MiB/CPU6/7 runtime1094400kHz and exit restoration remained.
Normal cleanup submitted the working checkpoint, cleared shared RAM, restored original core/CPU, and left dirty absent; independent postcleanup assets/checkpoint audit passed. No active dirty existed at this stage; an old active snapshot cannot establish that this round still ran.
Original automatic-budget SHA `${PRIVATE_BUDGET_SHA256}` remained unchanged, without reset-failed, old dedicated-experiment replay, or budget refresh.

### Evidence/next steps

`out/wifi-cn-20261030T075148Z/` stores native CN reference, deployment/signature policy, complete failed global+PHY observation, and final independent audit.
Offline: 384 cases, 383 passed, 1 optional QEMU skipped. The first test run failed an assertion only because Python added class-metadata fields; the original failure log was retained and comparison corrected to callable methods only. It was not RF-failure replay.
The first reference collector's string-escaping SyntaxError occurred before execution and was retained; the later independent source collector wrote a CN request only once, without RF initialization.

Management was available only through USB SSH at this stage. SSID/PMK storage, public key/source-restricted LAN22 rule, actual SELinux Permissive, screen tty1/volume-UP/15-second idle, and pending power DTB were unchanged.
No boot write/reboot/PMIC/original NV or credential/SSH-private-key reading/export occurred. CN configuration on disk does not mean wireless availability, connectivity, or long-term RF/charging safety acceptance.
