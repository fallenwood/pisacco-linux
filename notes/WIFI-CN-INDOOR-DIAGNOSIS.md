# CN室内限制拒绝：已定位校验器取证错误，实际PHY原始标志仍待验 / CN indoor-restriction rejection: validator evidence error identified, actual raw PHY flags still pending at this stage

> 文档范围 / Scope: 本文保留只读诊断阶段的取证和限制；“待验”“无线关闭”及后续横幅均为历史快照，不声称当前硬件状态。 / This preserves read-only diagnostic-stage evidence and limitations; “pending,” “wireless off,” and subsequent banners are historical snapshots, not claims about current hardware.

## 中文

> 后续明确“继续修复”已完成[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)：R2实际同PHY原始bit确认5180–5320的8点INDOOR_ONLY存在，41库存/24启用CN20MHz验证通过，常驻服务enabled/active，单次2.4G关联/网络及90秒观察通过。没有删室内检查。以下本页是只读诊断阶段快照，“未接入/未测live bit/无线关闭”不再代表最新状态；旧失败保留。

用户请求“继续排查”。本轮**只读诊断，没有启动无线、扫描、激活SSID、设置国家码或更改手机服务/校验政策**。

## 已确定的问题：取证路径错误，不是已经证明硬件缺少限制

**我新增的CN校验器在`iw phy … info`文本中查找`indoor only`，但手机的iw6.17根本不打印该属性。**
因此，前两次“5180MHz缺少室内标志”的结果不能证明内核/驱动没有落实NO-OUTDOOR；即便原始属性存在，这个文本检查也会拒绝。
失败单元、错误、cleanup仍是真实历史，不能改写为联网成功。

匹配手机的证据：

- Native：`iw-6.17-2.fc44.aarch64`，SourceRPM `iw-6.17-2.fc44.src.rpm`，`rpm -V iw`返回0、无差异。
- `/usr/bin/iw` SHA256 `2c8f212f7ce09350e300690350cd69bd8bc98aeb0b5bf9b36ea09d58b0311b4d`。
- Fedora44同版SourceRPM经OpenPGP/header/payload校验全部OK，签名指纹`36f612dcf27f7d1a48a835e4dbfcf71c6d9f90a6`；没有Fedora额外patch。
- SourceRPM SHA256 `e5e7738af71b61b22a15d1af11a946289a219158e1de3ccbedadbcd8a6023fe3`。

原版`iw-6.17/info.c:484–525`的频率打印分支仅输出disabled、no IR/passive/no ibss、radar及功率，**不读取`NL80211_FREQUENCY_ATTR_INDOOR_ONLY`**；整个info.c没有这个属性引用。
`iw list`使用同一printer，所以换成list也不解决；`phy.c`的channels printer同样没有该属性处理。

另一个已排除的猜测：`info.c:958–970`会查询协议特征，在支持时自动请求split dump；手机原生`iw features`回报`0x1/* split wiphy dump`。
所以不能把这次问题简单归咎于“iw phy info一定用了旧的非split请求”。当前确定的是**收到了也不打印**。

## 内核/驱动路径

精确Linux6.18.58源码中：

1. `net/wireless/reg.c:1568–1580`，`map_regdom_flags()`明确把`NL80211_RRF_NO_OUTDOOR`映射到`IEEE80211_CHAN_INDOOR_ONLY`。
2. `reg.c:1750–1820`，信道规则更新将orig/bw限制与映射后的规则flags合并；不能为绕过EEPROM/US板级限制更换regpair或BDF。
3. `net/wireless/nl80211.c:1330–1342`在large/split输出中导出`NL80211_FREQUENCY_ATTR_INDOOR_ONLY`。
4. ath/regd.c的相关notifier路径修改radar/no-IR等，已读到的这些路径没有显式清除INDOOR_ONLY；**这仍不是对已卸载PHY实际bit的测量**。

UAPI头文件还明确INDOOR_ONLY是使用条件，不能因为“手机插在电脑USB上”就推断物理室内或已验证供电来源；本轮没有发送`REG_INDOOR`环境提示、读取PMIC或改充电设置。

## 已准备的只读原始属性采集器（未接入现有服务）

新增`tools/wifi-nl80211-channels.py`，只允许：

- generic-netlink GET_FAMILY解析nl80211；
- GET_PROTOCOL_FEATURES，必须支持split；
- 带SPLIT_WIPHY_DUMP的GET_WIPHY，支持指定PHY index。

直接解析freq、原始mBm功率、disabled/no-IR/radar/INDOOR_ONLY/no20MHz等，按PHY和频点合并分片；拒绝中断/截断/重复冲突/错误序号/非内核回复，8秒/4MiB/2048消息硬限。
没有SET、scan、模块加载、设备创建、固件或NV操作，也不输出其他接口MAC/SSID/密钥。
数值常量由当前项目精确UAPI头通过小型C程序生成核对：INDOOR_ONLY=14、SPLIT_WIPHY_DUMP=174等；不是猜值。

手机上仅用临时`python -c`执行了只读GET：协议支持、完整dump、`phys=[]`，同时WLAN不存在/DSP offline。
**空PHY仅验证传输/解析路径，不证明本机运行时INDOOR_ONLY=true。** 未将采集器安装为服务或替换手机旧审计器。

## 离线复现

`out/wifi-cn-indoor-diagnosis-20261030T084546Z/reproduce-display-omission.py`：

- 合成一条明确带attr14的5180MHz/2300mBm频点（明确是合成，不是手机测量）；
- 原始TLV解析保留`indoor_only=true`；
- iw6.17当前文本格式丢弃该属性；
- **原样旧CN审计器仍报同一错误**，复现即使内核bit存在也被文本检查错误阻断。

396项离线测试：395通过、1可选QEMU跳过。新12项覆盖原始attr14、缺失标志、坏flag/TLV、disabled功率、分片一致性、GET-only限制、中断dump、空PHY不算验收等。

## 正确修复方向和当前状态

下一步应保留原CN规则/功率/DFS/NO-OUTDOOR检查，只把取证源替换成**相同PHY的完整原始nl80211属性**；真实属性缺失或dump不完整仍拒绝。
不能用全局CN字样、期望规则、no-IR或人工拼`indoor only`字符串代替真实bit，也不能删检查后称修好。
接入控制器、更新政策pin及有界原生启动/关联需下一步明确安排；本轮旧CN源SHA53aa…、auditorSHAaf60…、政策/服务与失败状态均未改。

当前仍global CN、wlan0不存在、MPSS offline、dirty absent，自动预算SHA`${PRIVATE_BUDGET_SHA256}`不变；boot不变，USB SSH可用。
此前5GHz激活超时与2.4GHz自然BEACON_MISS失联仍是独立未解决问题，显示/审计错误的定位不等于无线已稳定、已联网或RF/充电安全通过。

## English

> A later explicit “continue fixing” request completed [WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md): R2 actual same-PHY raw bits confirmed INDOOR_ONLY at all 8 frequencies from 5180–5320, 41-inventory/24-enabled CN20MHz validation passed, the persistent service was enabled/active, and a single 2.4G association/network check plus 90-second observation passed. The indoor check was not removed. This page below is a read-only diagnostic-stage snapshot: “not integrated/live bits unmeasured/wireless off” no longer represents the latest state at that update; old failures remain.

The user requested “continue investigating.” This round was **read-only diagnosis: no wireless startup, scan, SSID activation, country-code setting, or phone service/validation-policy change**.

### Confirmed issue: wrong evidence path, not proven missing hardware restriction

**The CN validator I added looked for `indoor only` in `iw phy … info` text, but the phone's iw6.17 does not print this attribute at all.**
Thus the earlier two “5180MHz missing indoor flag” results cannot prove the kernel/driver failed to enforce NO-OUTDOOR; this text check rejects even when the raw attribute exists.
Failed units, errors, and cleanup remain true history and cannot be rewritten as connectivity success.

Evidence matching the phone:

- Native: `iw-6.17-2.fc44.aarch64`, SourceRPM `iw-6.17-2.fc44.src.rpm`; `rpm -V iw` returned 0 with no differences.
- `/usr/bin/iw` SHA256 `2c8f212f7ce09350e300690350cd69bd8bc98aeb0b5bf9b36ea09d58b0311b4d`.
- Matching Fedora44 SourceRPM passed all OpenPGP/header/payload checks, signing fingerprint `36f612dcf27f7d1a48a835e4dbfcf71c6d9f90a6`; no extra Fedora patches.
- SourceRPM SHA256 `e5e7738af71b61b22a15d1af11a946289a219158e1de3ccbedadbcd8a6023fe3`.

The upstream `iw-6.17/info.c:484–525` frequency-printing branch outputs only disabled, no IR/passive/no ibss, radar, and power; **it does not read `NL80211_FREQUENCY_ATTR_INDOOR_ONLY`**. The entire info.c has no reference to that attribute.
`iw list` uses the same printer, so switching to list does not solve it; the channels printer in `phy.c` likewise lacks handling for that attribute.

Another excluded guess: `info.c:958–970` queries protocol features and automatically requests a split dump when supported; native `iw features` on the phone reported `0x1/* split wiphy dump`.
Thus this problem cannot simply be blamed on “iw phy info necessarily used an old non-split request.” The confirmed point is **it does not print the attribute even if received**.

### Kernel/driver path

In exact Linux6.18.58 source:

1. `net/wireless/reg.c:1568–1580`: `map_regdom_flags()` explicitly maps `NL80211_RRF_NO_OUTDOOR` to `IEEE80211_CHAN_INDOOR_ONLY`.
2. `reg.c:1750–1820`: channel-rule updates combine orig/bw restrictions with mapped rule flags; regpair or BDF must not be replaced to bypass EEPROM/US board-level restrictions.
3. `net/wireless/nl80211.c:1330–1342` exports `NL80211_FREQUENCY_ATTR_INDOOR_ONLY` in large/split output.
4. Relevant ath/regd.c notifier paths modify radar/no-IR and related flags; the paths read did not explicitly clear INDOOR_ONLY. **This is still not a measurement of the actual bit on the already-unloaded PHY.**

The UAPI header also explicitly identifies INDOOR_ONLY as a condition of use. “The phone is plugged into the computer's USB” cannot imply a physical indoor location or verified power source; this round sent no `REG_INDOOR` environmental hint, read no PMIC, and changed no charging settings.

### Prepared read-only raw-attribute collector (not integrated into existing service)

New `tools/wifi-nl80211-channels.py` permits only:

- Generic-netlink GET_FAMILY to resolve nl80211.
- GET_PROTOCOL_FEATURES, requiring split support.
- GET_WIPHY with SPLIT_WIPHY_DUMP, supporting a specified PHY index.

It directly parses frequency, raw mBm power, disabled/no-IR/radar/INDOOR_ONLY/no20MHz, etc., merging fragments by PHY/frequency; rejects interrupted/truncated dumps, duplicate conflicts, incorrect sequence numbers, and non-kernel replies, with hard limits of 8 seconds/4MiB/2048 messages.
There are no SET, scan, module-load, device-create, firmware, or NV operations, and no output of other interface MACs/SSIDs/keys.
Numeric constants were generated and checked by a small C program using the project's exact current UAPI header: INDOOR_ONLY=14, SPLIT_WIPHY_DUMP=174, etc.; they were not guessed.

On the phone, only a transient `python -c` executed read-only GET: protocol support, complete dump, `phys=[]`, with WLAN absent/DSP offline.
**An empty PHY set validates only transport/parsing, not INDOOR_ONLY=true on this machine at runtime.** The collector was not installed as a service and did not replace the phone's old auditor.

### Offline reproduction

`out/wifi-cn-indoor-diagnosis-20261030T084546Z/reproduce-display-omission.py`:

- Synthesizes a 5180MHz/2300mBm frequency entry explicitly containing attr14 (explicitly synthetic, not a phone measurement).
- Raw TLV parsing retains `indoor_only=true`.
- iw6.17's current text format discards the attribute.
- **The unchanged old CN auditor still reports the same error**, reproducing incorrect text-check rejection even when the kernel bit exists.

Offline: 396 tests, 395 passed, 1 optional QEMU skipped. The 12 new cases cover raw attr14, missing flags, malformed flag/TLV, disabled power, fragment consistency, GET-only restrictions, interrupted dumps, and empty PHY not counting as acceptance.

### Correct fix direction and state at this stage

The next step should retain original CN rules/power/DFS/NO-OUTDOOR checks, replacing only the evidence source with **complete raw nl80211 attributes from the same PHY**; missing real attributes or incomplete dumps must still reject.
Global CN text, expected rules, no-IR, or manually constructed `indoor only` strings cannot substitute for real bits; deleting the check cannot be called a fix.
Controller integration, policy-pin update, and bounded native startup/association require explicit next-step arrangements; this round left old CN source SHA53aa…, auditorSHAaf60…, policy/service, and failed state unchanged.

At this stage global CN remained, wlan0 absent, MPSS offline, dirty absent, automatic-budget SHA`${PRIVATE_BUDGET_SHA256}` unchanged; boot unchanged and USB SSH usable.
Prior 5GHz activation timeouts and natural 2.4GHz BEACON_MISS disconnections remain separate unresolved issues; locating a display/audit error does not mean wireless stability, connectivity, or RF/charging safety acceptance.
