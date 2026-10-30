# CN校验取证R2已修复并持久启用：原始INDOOR_ONLY核验通过，2.4GHz联网成功 / CN validation evidence R2 fixed and persistently enabled: raw INDOOR_ONLY verified, 2.4GHz connectivity succeeded

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本文保留R2修复阶段及原有最新持久化横幅；正文旧“当前”、enabled/active和命令均属对应历史阶段，不是实时保证。 / This preserves the R2-fix stage and its existing latest-persistence banner; the body's older “current,” enabled/active, and commands belong to their historical stages, not live guarantees.

## 中文

> 最新持久化：新`picasso-wifi-autoconnect-cn.service`已enabled/active，
> 原R2单元现disabled/failed，高温启动失败及旧源码均保留；不要并行启动旧无线所有者。
> 新包装器精确固定并继承本页R2、原startup/guard/lease/cleanup，仅在startup后调用既有
> 有界优先/回退及联网校验。${PRIMARY_SSID}20.784秒普通超时→${FALLBACK_SSID}0.678秒成功，
> 当前${PHONE_LAN_IP}/24，WLAN证书HTTPS200及后续60秒关联观察通过。
> 两SSID凭据直接由native nmcli读取，调用方不读取/导出；NM自身autoconnect设no，
> 避免与受保护启动次序争用。新boot原R2因45°C保护退出，新增硬件启动前最多300秒等待，
> 连续三次<40°C才开始，原运行45°C中止不变。旧重连预算不变，不新增掉线重连或DSP重启循环。
> 本次未重启/写boot，下次开机未实际复核；证据`out/boot-screen-wlan-20261030T152618Z/`。
> 下文R2 enabled/active及“不自动关联”描述是本次更新前的阶段记录。

用户请求：**“继续修复”**。新版本只更换取证路径，不删CN功率/DFS/NO-OUTDOOR/no-IR/HT20检查。

## 当前已实测

- 新`picasso-wifi-radio-cn-raw.service` **enabled/active，PID166423**，session `${SESSION_3}`。
- 原始同PHY、完整split nl80211 dump与iw仅用于库存的频点列表交叉一致：**41个总频点，24个启用20MHz信道**。
- 实际raw attr14确认**5180/5200/5220/5240/5260/5280/5300/5320MHz**均有INDOOR_ONLY；不是预期规则或文本补字生成的标志。
- global CN，实际EIRP/DFS/NO-OUTDOOR/no-IR子集、永久MAC和HT20均通过。
- 空闲UP先观察45秒/85次样本，然后在同一无线所有者、同一DSP lifecycle上，仅一次${FALLBACK_SSID}激活，**0.713秒nmcli返回0**。
- 新鲜WPA2-RSN CCMP握手、授权station、DHCP、实际HT20、WLAN绑定新DNS事务、证书验证HTTPS200均通过，IPv4 **${PHONE_LAN_IP}/24**。
- 之后90秒/87次样本均观察到目标关联/管理UP；进一步实时检查NM100、station authorized、UP+LOWER_UP、HTTPS`200 0 577`通过。
- 这是短期原生成功和当前快照，不是连续无丢包/长期稳定保证；历史2G BEACON_MISS失联、5GHz超时根因没有因此被证明全部修好。

## 修复方式（未绕过保护）

R2目录`/opt/picasso-wifi-cn-raw/`：

- `wifi-cn-raw-radio-service.py`只覆盖R1的**audit方法**；R1精确国家码映射/字段命名以及原startup/guard/lease/cleanup继承不动。
- `wifi-nl80211-channels.py`保留诊断阶段同一5055c3…原始GET-only采集版本，现由R2明确集成调用；历史诊断时未集成的说明不代表当前调用状态。
- `audit-wifi-regulatory-cn-raw.py`使用原CN参考/规则解析器，但直接判断原始bool和其observed attribute IDs。
- `policy.json` root0400固定原生参考和采集器/审计器hash。

每次审计从`wlan0/phy80211/{index,name}`取得实际身份，要求原始回复只含该PHY；检查协议split支持、完整dump、精确内核、41点全库存一致、原始mBm、旗标/attr ID一致。
原始属性确实缺失、DFS/功率越界、错误PHY、分片中断、库存不完整、属性冲突或dump前后监管变化仍拒绝。**不是把`indoor only`拼进文本，也不是删除室内要求。**
`iw phy info`仅继续用于HT20/无VHT及频点库存，不再用其缺失的indoor文本判断bit。
原始bit存在只证明内核的限制表示，不证明物理室内地点、RF发射认证、充电/电池安全。

## 常驻与保存

- R2先文件与政策无RF检查、一次原生启动且45秒UP/raw验证通过，再设为默认开机enabled；本轮没有重启验证下次开机。
- 旧SG/R1CN和前次attended失败单元、错误、源码均保留。R1CN现disabled/failed，未reset-failed、重启旧failed或删marker。
- **新默认仍仅保持网卡UP，不自动关联SSID/回退/循环重连**。本次联网是用户修复范围内单独的一次2G连接，凭据仍在原root私有目录，没有读取/哈希/导出PMK。
- 普通未关联/掉线保留接口和受保护所有者；温控45°C、DSP/backend/精确3秒Root PID lease/监管/身份/CPU等真正安全故障仍完整关闭，Restart=no。
- 原自动预算SHA `${PRIVATE_BUDGET_SHA256}`原样，不因成功联网或新服务重置。
- 活跃dirty属于session${SESSION_3}，是正常DSP工作生命周期。**不能删除，不能用上轮cleanup或旧checkpoint宣称当前已清理。**
- Watchdog8/Stop45/Memory256MiB/CPU0–3、CPU6/7运行期1094400kHz及退出恢复、私有四FD/RAM/MPSS手动启动与恢复禁用保持。
- 本轮R2仍运行，未为了测试cleanup再停止/重启一次；cleanup继承路径及离线测试保留，不声称本轮进行了R2完整stop验收。

查看当前状态（手机内）：

```sh
sudo systemctl status picasso-wifi-radio-cn-raw.service
ip link show wlan0
sudo iw dev wlan0 link
```

明确需要关闭时仅stop新R2所有者；不要启动旧SG/R1服务或另一个完整worker去争用同一DSP/RUN目录。
LAN${LAN_SUBNET} TCP22/drop、公钥均保持；可用LAN地址需以实时DHCP为准，新公钥从另一机器登录仍未单独验收。
SELinux实际仍Permissive、屏幕原生tty1/音量UP/15秒idle、待激活power DTB/自动开机限制未改变。本次无boot写/重启/PMIC/原始NV或凭据/SSH私钥读取导出。

## 证据

`out/wifi-cn-raw-fix-20261030T090245Z/`包括R2源码/政策/unit/readback、三组<40°C开始读数、原始实际bit、45秒UP、一次联网验证、90秒关联观察和实时复核。
当前session采样峰值37.4°C，45°C abort不变；不同阶段读数不混作开始温度。
离线412项：411通过、1可选QEMU跳过。新16项证明“raw bit存在、iw没有文本也应通过”，并继续拒绝真正缺bit/坏证据/错误PHY/库存缺失/越功率/缺DFS等。

## English

> Latest persistence: new `picasso-wifi-autoconnect-cn.service` is enabled/active;
> the original R2 unit is now disabled/failed, with its high-temperature startup failure and old source retained; do not start old wireless owners in parallel.
> The new wrapper exactly pins and inherits this page's R2 and original startup/guard/lease/cleanup, calling only the existing
> bounded priority/fallback and connectivity validation after startup. ${PRIMARY_SSID} had an ordinary timeout at 20.784 seconds → ${FALLBACK_SSID} succeeded in 0.678 seconds,
> with ${PHONE_LAN_IP}/24 at this update; WLAN certificate-verified HTTPS200 and subsequent 60-second association observation passed.
> Both SSID credentials are read directly by native nmcli, not read/exported by the caller; NM's own autoconnect is set to no
> to avoid contention with the guarded startup order. The original R2 exited under 45°C protection in the new boot; a new wait of at most 300 seconds before hardware startup was added,
> requiring three consecutive readings <40°C before starting; the original 45°C runtime abort is unchanged. The old reconnection budget is unchanged, with no new link-loss reconnection or DSP-restart loop.
> This operation did not reboot/write boot; the next boot has not been actually rechecked. Evidence: `out/boot-screen-wlan-20261030T152618Z/`.
> R2 enabled/active and “no automatic association” descriptions below are stage records predating this update.

User request: **“Continue fixing.”** The new version changes only the evidence path, without deleting CN power/DFS/NO-OUTDOOR/no-IR/HT20 checks.

### Measurements at this stage

- New `picasso-wifi-radio-cn-raw.service` **enabled/active, PID166423**, session `${SESSION_3}`.
- Complete split nl80211 dump from the actual same PHY cross-matched the iw frequency list used only for inventory: **41 total frequencies, 24 enabled 20MHz channels**.
- Actual raw attr14 confirmed INDOOR_ONLY at **5180/5200/5220/5240/5260/5280/5300/5320MHz**; flags were not generated from expected rules or added text.
- Global CN, actual EIRP/DFS/NO-OUTDOOR/no-IR subset, permanent MAC, and HT20 all passed.
- Idle UP was first observed for 45 seconds/85 samples, then exactly one ${FALLBACK_SSID} activation used the same wireless owner and DSP lifecycle; **nmcli returned 0 in 0.713 seconds**.
- Fresh WPA2-RSN CCMP handshake, authorized station, DHCP, actual HT20, fresh WLAN-bound DNS transaction, and certificate-verified HTTPS200 all passed; IPv4 **${PHONE_LAN_IP}/24**.
- All 87 samples over the next 90 seconds observed target association/administrative UP; further live checks passed NM100, station authorized, UP+LOWER_UP, and HTTPS`200 0 577`.
- This is short-term native success and a snapshot at the time, not a guarantee of uninterrupted loss-free/long-term stability; historical 2G BEACON_MISS and 5GHz timeout root causes are not thereby proven completely fixed.

### Fix method (no protection bypass)

R2 directory `/opt/picasso-wifi-cn-raw/`:

- `wifi-cn-raw-radio-service.py` overrides only R1's **audit method**; R1 exact country-code mapping/field naming and inherited original startup/guard/lease/cleanup remain unchanged.
- `wifi-nl80211-channels.py` retains the diagnostic stage's same 5055c3… raw GET-only collector version, now explicitly integrated and called by R2; the historical diagnostic statement that it was not integrated does not represent its later invocation state.
- `audit-wifi-regulatory-cn-raw.py` uses the original CN reference/rule parser but directly evaluates raw booleans and their observed attribute IDs.
- Root0400 `policy.json` pins native reference and collector/auditor hashes.

Every audit obtains actual identity from `wlan0/phy80211/{index,name}` and requires raw replies to contain only that PHY; it checks protocol split support, complete dump, exact kernel, complete matching 41-frequency inventory, raw mBm, and consistency of flags/attribute IDs.
Genuinely missing raw attributes, DFS/power violations, wrong PHY, interrupted fragments, incomplete inventory, attribute conflicts, or regulatory changes across a dump still reject. **This does not splice `indoor only` into text or remove indoor requirements.**
`iw phy info` remains only for HT20/no-VHT and frequency inventory, no longer for bit judgment using its absent indoor text.
Raw-bit presence proves only the kernel's restriction representation, not physical indoor location, RF-transmission certification, or charging/battery safety.

### Persistence and preservation

- R2 first passed file/policy checks without RF, one native startup, and 45-second UP/raw validation, then was enabled as the default at boot; this round did not reboot to validate the next startup.
- Old SG/R1CN and previous attended failed units, errors, and source were retained. R1CN became disabled/failed; no reset-failed, restart of old failed units, or marker deletion occurred.
- **The new default at this stage still only kept the interface UP, without automatic SSID association/fallback/reconnection loops**. This connectivity was one separate 2G connection within the user's fix scope; credentials remained in the original root-private directory, without reading/hashing/exporting the PMK.
- Ordinary unassociated/link-loss states retain the interface and guarded owner; true safety failures including 45°C thermal limit, DSP/backend/exact 3-second Root PID lease/regulatory/identity/CPU still fully shut down, with Restart=no.
- Original automatic-budget SHA `${PRIVATE_BUDGET_SHA256}` remained unchanged; successful connectivity/new service did not reset it.
- Active dirty belonged to session${SESSION_3} and was a normal DSP working lifecycle. **It must not be deleted, and the previous cleanup or old checkpoint cannot establish current cleanup.**
- Watchdog8/Stop45/Memory256MiB/CPU0–3, CPU6/7 runtime1094400kHz and exit restoration, private four-FD/RAM/manual MPSS startup/recovery disabled remained.
- R2 was still running this round; it was not stopped/restarted again just to test cleanup. The inherited cleanup path and offline tests remain, without claiming a complete R2 stop acceptance in this round.

Check state at this stage (on the phone):

```sh
sudo systemctl status picasso-wifi-radio-cn-raw.service
ip link show wlan0
sudo iw dev wlan0 link
```

When explicitly needing shutdown at this stage, stop only the new R2 owner; do not start old SG/R1 services or another complete worker to compete for the same DSP/RUN directory.
LAN${LAN_SUBNET} TCP22/drop and public keys remain; usable LAN address depends on live DHCP. Login from another machine with the new public key has not been separately accepted.
Actual SELinux remains Permissive; native screen tty1/volume-UP/15-second idle, pending power DTB/automatic-start limitations were unchanged. No boot write/reboot/PMIC/original NV or credential/SSH-private-key reading/export occurred.

### Evidence

`out/wifi-cn-raw-fix-20261030T090245Z/` includes R2 source/policy/unit/readback, three starting-reading groups <40°C, actual raw bits, 45-second UP, one connectivity validation, 90-second association observation, and live recheck.
This session's sampled peak was 37.4°C, with 45°C abort unchanged; readings from different stages are not conflated with starting temperatures.
Offline: 412 cases, 411 passed, 1 optional QEMU skipped. The 16 new cases prove “raw bit exists, no iw text should still pass,” while continuing to reject genuinely missing bits/bad evidence/wrong PHY/incomplete inventory/excess power/missing DFS, etc.
