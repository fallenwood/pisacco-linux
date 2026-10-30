# Wi-Fi掉线自动重连已持久安装：实测3次恢复，当前次数耗尽离线 / Persistent Wi-Fi reconnection installed: 3 measured recoveries, offline after budget exhaustion at this stage

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本文保留有界重连阶段的预算、失败和验收记录；“当前”与旧单元命令属历史，不代表最新无线所有者。 / This preserves the bounded-reconnection stage's budgets, failures, and acceptance records; “current” and old-unit commands are historical, not the latest wireless owner.

## 中文

> 后续用户要求不要关闭wlan，默认已切换为[常驻真实网卡UP模式](WIFI-RADIO-UP.md)。本页重连服务现disabled/failed，预算/失败保持；新radio服务enabled/active，只保持UP且无自动关联，不能再按本页旧服务判断是否运行。以下是重连阶段历史，特别是“WLAN absent/dirty absent”不是新radio活跃状态。

> 后续USB插拔未发生手机重启。用户另请求一次试连，独立手动session `${SESSION_5}`短暂恢复2.4G/DHCP/DNS/HTTPS后又失联，已安全清理。自动预算文件SHA不变，没有删除/刷新预算或重跑旧failed unit；这是一次新的明确人工授权，不是自动第五轮。证据`out/wifi-attended-20261030T012324Z/`。

用户请求：**“开启掉线自动重连, 并且写入手机”**。
仅写入普通XFS程序/状态文件和systemd配置；没有刷boot、重启/关机、休眠、改变SELinux、NV原分区/masters、凭据或主机网络。

## 已安装及原生结果

- 新默认服务：`picasso-wifi-reconnect.service`，已enabled；本轮实际运行后次数耗尽，当前failed/exit-code，已安全退出。
- 程序：`/opt/picasso-wifi-reconnect/wifi-reconnect-service.py`，root0400。
- 沿用**未改字节**的已验收worker `wifi-auto-service.py`，SHA256=`428495f9e7007d9728b0df9887b630c62013622b9137af39d4afcf532191b725`；
  其config/probation gate、四FD后端、固件/BDF、模块、监管域和MAC逻辑均不修改。
- 原`picasso-wifi-auto.service`改为disabled，但原failed/exit-code保留；更早原`picasso-wifi.service`仍disabled/failed/watchdog。
  没有reset-failed，也没有重跑已消耗的旧诊断。
- 新控制器沙箱先完成**仅文件/安全清理状态/manager bus**原生检查，不开启RF、不消费重试预算。

随后真机自然失联触发了全部三次自动重试，**没有人为断网或注入失败**：

| 本boot轮次 | worker session | 本轮结果 |
|---|---|---|
| 初连 | `${SESSION_10}` | ${PRIMARY_SSID}超时→2.4G成功，之后真实fallback link loss；完整安全清理 |
| 自动重试1 | `${SESSION_11}` | 同顺序恢复联网，之后再次真实失联；完整安全清理 |
| 自动重试2 | `${SESSION_12}` | 同顺序恢复联网，之后再次真实失联；完整安全清理 |
| 自动重试3 | `${SESSION_13}` | 同顺序恢复联网，曾connected_guarded/${FALLBACK_SSID}/${PHONE_LAN_IP}，随后也fallback link loss；完整安全清理 |

配置退避10/30/60秒；原生持久事件中的backoff→下轮启动intent实际为**11.292/31.291/61.281秒**，包括额外清理确认与冷启动检查，不少于规定间隔。
每次均验证DHCP、新wlan0绑定DNS和证书HTTPS200、永久MAC/实际20MHz/SG信道EIRP/DFS/drop区域。
**当前本boot初连＋3次名额已经全部用完，最后一轮也再次掉线，监管器已按预算规则停止**，错误`Initial plus3 retries exhausted for this boot`。
当前WLAN absent、DSP offline、CPU/core恢复、checkpoint提交、dirty absent，最终独立owned-child清理通过；没有第五轮，也未删除或重置预算。
之前第四轮在线快照仍是当时的实测记录，不是当前在线状态。

所有历史worker failed unit和原生result/cleanup仍保留，不把失败改名为成功。
三次断线后的安全清理都通过：DSP offline、WLAN absent、proxy/TFTP停止、2,621,440字节共享RAM清零、原core/CPU上限恢复、工作副本checkpoint提交。
最后一轮活跃时dirty标记曾属于正在工作的session，**当时不能拿上一轮cleanup.json宣称当前已清理，也不能删除live dirty**。
最终第四轮已退出，当前cleanup.json才属于该轮，native安全清理正常提交checkpoint并消耗自己的生命周期dirty标记；agent没有手工删除任何marker。

## 有界恢复规则

每boot最多4个worker会话，包括初次连接；剩余名额不是无限重启。
退避后先重新核验：

1. 前轮unit必须是exit-code1，且原生精确错误仅限：
   - `Fallback link lost; no restart loop`
   - `Both authorized SSIDs failed bounded activation`
   - `Runtime fallback failed`
2. 没有unsafe NV stop；前轮记录温度峰值<45°C，cleanup全部必要字段成功。
3. 当前dirty不存在、DSP离线、WLAN卸载、旧proxy/TFTP不活跃、CPU6/7最大值恢复、原core匹配。
4. 三份**普通工作副本**owner/mode/nlink/大小/不别名且摘要与最新checkpoint吻合；只在手机内核验，不读取或恢复原NV/masters。
5. 所有可读传感器有效；连续三次<40°C，ready前再查<40°C；最多等待120秒降温。

watchdog、timeout、OOM、信号、DSP crash、热限、监管/MAC/内存/副本校验错误或其他未知错误均不重试，即使部分清理成功。
运行温度仍45°C中止，不提高任何阈值。普通失联只是恢复逻辑的入口，不会绕过内核/工作副本边界。

本轮supervisor全阶段记录峰值**43.4°C**，首个外部观察器采样峰值39.1°C，各worker的连接/监控记录峰值另存。
这些采样时点不同，不用低的覆盖高的；43.4°C低于45°C中止线，不代表RF启动时43.4°C。
当前代码每次启动均执行上述<40°C门槛，但各次具体起始温度未独立持久化，**不从阶段峰值或后测值反推起始读数**。

## 所有权、独立退出与预算

- 每次创建全新`picasso-wifi-session-<boot8>-<uuid12>.service`，不重启先前failed unit；不使用Restart=always或--collect。
- worker仍notify/watchdog8/TimeoutStart180/Stop45/Memory256MiB/CPU0–3、独立ExecStopPost，backend仍精确worker PID对象/3秒SCM_CREDENTIALS租约。
- worker通过BindsTo＋After绑定supervisor。supervisor自己的watchdog8、Restart=no、独立ExecStopPost、Stop75、Memory128MiB、空capability、AF_UNIX、禁止reboot/module/raw-io等调用保持。
- supervisor的READY只说明**监管器就绪**，不代表WLAN已连；在线必须看budget phase、当前worker与真实关联。
- 启动intent在任何worker创建/启动之前持久化。保存独占生成的unit名、文件dev/inode/内容及worker session；清理只停止已证明归属的本boot子unit。
  未创建或文件身份不符的计划名不能拿来停止未知服务。
- `/var/lib/picasso-wifi-reconnect/boots/<boot-id>.json`保存预算；`events/`保存每阶段不可覆盖证据和unit定义。
  不因稳定一段时间、服务停止/启动而清零。普通operator clean stop可在剩余预算内续用；安全错误、耗尽或不完整所有权需人工检查，不自动重放。
- `/run/picasso-wifi-reconnect/session.json`是监管状态；真实联网/清理记录仍在`/run/picasso-wifi/`和`/var/lib/picasso-wifi/history/`。

## 日常操作（手机内）

```sh
sudo systemctl status picasso-wifi-reconnect.service
sudo systemctl stop picasso-wifi-reconnect.service
# 关闭开机自动连接/重连：
sudo systemctl disable picasso-wifi-reconnect.service
```

不要同时启动旧auto/wifi服务；不要手工删预算/dirty/旧marker，不用重启或原NV复位来绕过本boot次数和安全错误。
若要改变次数或退避，需另行明确策略并保留旧证据，不给未经审核的无限重连。

## 不变边界与未完成项

底层beacon-miss/接收稳定性**没有修复**，本次三次自然失联正好再次说明这一点。实现并实测的是受保护恢复，不是稳定链路。
LAN${LAN_SUBNET} TCP22和新公钥配置保留；另一台机器使用该私钥的SSH登录仍未实测。
SELINUX配置仍disabled但实际内核仍Permissive；当前boot仍原#10/FDT62ac，已写入power镜像待下次启动，**本次没有重启验收**。
两个精确FDT及config/Image/ABI的既有白名单不变。屏幕tty1/15秒idle/音量上/内核租约保持，不增加整机休眠。
不声明充电、RF安全、长期热/内存/UFS/掉电或保持关机验收。

证据：`out/wifi-reconnect-20261030T003551Z/`。
离线359项，358通过、1可选QEMU跳过；另有真实三次自然失联→安全清理→退避→新PID1 worker恢复联网的证据，不把模拟测试当原生实测。
本阶段只验证新普通文件/服务安装与原生运行，没有重新读取原NV或重新摘要保护分区；最近全盘/授权公钥例外检查仍见[LAN-SSH.md](LAN-SSH.md)。

## English

> The user later requested that wlan not be shut down, and the default switched to [persistent real-interface UP mode](WIFI-RADIO-UP.md). This page's reconnection service is now disabled/failed, with budget/failures retained; the new radio service is enabled/active and only keeps UP without automatic association. Do not use this page's old service to determine what is running. The following is reconnection-stage history; in particular, “WLAN absent/dirty absent” is not the new radio's active state.

> Later USB unplug/replug did not reboot the phone. The user separately requested one connection attempt: independent manual session `${SESSION_5}` briefly restored 2.4G/DHCP/DNS/HTTPS, then lost the link again and cleaned up safely. The automatic-budget file SHA remained unchanged; the budget was not deleted/refreshed and the old failed unit was not rerun. This was new explicit manual authorization, not an automatic fifth round. Evidence: `out/wifi-attended-20261030T012324Z/`.

User request: **“Enable automatic reconnection after disconnection, and write it to the phone.”**
Only ordinary XFS program/state files and systemd configuration were written; no boot flashing, reboot/shutdown, suspend, SELinux changes, original NV partitions/masters, credentials, or host network changes occurred.

### Installation and native results

- New default service: `picasso-wifi-reconnect.service`, enabled; after actual operation in this round its allowance was exhausted, leaving failed/exit-code with safe exit.
- Program: `/opt/picasso-wifi-reconnect/wifi-reconnect-service.py`, root0400.
- Reused the accepted worker `wifi-auto-service.py` **without changing any bytes**, SHA256=`428495f9e7007d9728b0df9887b630c62013622b9137af39d4afcf532191b725`.
  Its config/probation gate, four-FD backend, firmware/BDF, modules, regulatory domain, and MAC logic were unchanged.
- Original `picasso-wifi-auto.service` became disabled, retaining its failed/exit-code; the earlier original `picasso-wifi.service` remained disabled/failed/watchdog.
  There was no reset-failed or replay of consumed old diagnostics.
- The new controller sandbox first completed native checks of **files/safe-cleanup state/manager bus only**, without enabling RF or consuming retry budget.

Natural link loss on real hardware then triggered all three automatic retries, **without deliberate network disconnection or injected failures**:

| Round in this boot | Worker session | Result |
|---|---|---|
| Initial connection | `${SESSION_10}` | ${PRIMARY_SSID} timeout → 2.4G success, then actual fallback link loss; complete safe cleanup |
| Automatic retry 1 | `${SESSION_11}` | Connectivity restored in the same order, then actual link loss again; complete safe cleanup |
| Automatic retry 2 | `${SESSION_12}` | Connectivity restored in the same order, then actual link loss again; complete safe cleanup |
| Automatic retry 3 | `${SESSION_13}` | Connectivity restored in the same order; observed connected_guarded/${FALLBACK_SSID}/${PHONE_LAN_IP}, then fallback link loss too; complete safe cleanup |

Configured backoffs were 10/30/60 seconds; in native persistent events, backoff → next startup intent actually took **11.292/31.291/61.281 seconds**, including additional cleanup confirmation and cold-start checks, never less than the required interval.
Every round verified DHCP, fresh wlan0-bound DNS and certificate-verified HTTPS200, permanent MAC/actual 20MHz/SG channel EIRP/DFS/drop zone.
**The initial connection plus all 3 slots for this boot are now used up; the final round also disconnected, and the supervisor stopped according to budget rules**, with error `Initial plus3 retries exhausted for this boot`.
At this stage WLAN was absent, DSP offline, CPU/core restored, checkpoint submitted, dirty absent, and final independent owned-child cleanup passed; no fifth round occurred and the budget was not deleted or reset.
The earlier fourth-round online snapshot remains a measurement at that time, not current online status.

All historical worker failed units and native result/cleanup records remain; failures are not renamed successes.
Safe cleanup after all three disconnections passed: DSP offline, WLAN absent, proxy/TFTP stopped, 2,621,440 bytes of shared RAM zeroed, original core/CPU limits restored, working-copy checkpoint submitted.
While the final round was active, its dirty marker belonged to the working session; **the previous round's cleanup.json could not then establish current cleanup, and live dirty could not be deleted**.
After the fourth round finally exited, cleanup.json belonged to that round; native safe cleanup normally submitted the checkpoint and consumed its own lifecycle dirty marker. The agent manually deleted no markers.

### Bounded recovery rules

At most 4 worker sessions per boot, including the initial connection; remaining slots are not unlimited restarts.
After backoff, revalidate:

1. The previous unit must have exit-code1 and a native exact error limited to:
   - `Fallback link lost; no restart loop`
   - `Both authorized SSIDs failed bounded activation`
   - `Runtime fallback failed`
2. No unsafe NV stop; previous recorded peak temperature <45°C; all required cleanup fields successful.
3. Currently no dirty marker, DSP offline, WLAN unloaded, old proxy/TFTP inactive, CPU6/7 maxima restored, original core matching.
4. Three **ordinary working copies** must have valid owner/mode/nlink/size/non-aliasing and digests matching the latest checkpoint; verification is phone-local only, without reading or restoring original NV/masters.
5. All readable sensors valid; three consecutive readings <40°C and another <40°C check before ready; at most 120 seconds waiting to cool down.

Watchdog, timeout, OOM, signals, DSP crash, thermal limit, regulatory/MAC/memory/copy validation errors, and any unknown error are not retried, even if some cleanup succeeded.
Runtime still aborts at 45°C; no threshold is raised. Ordinary link loss only enters recovery logic and does not bypass kernel/working-copy boundaries.

The supervisor's all-stage recorded peak this round was **43.4°C**; the first external observer sampled a peak of 39.1°C, with individual workers' connection/monitoring peaks stored separately.
These readings have different sampling times; a lower reading does not overwrite a higher one. 43.4°C is below the 45°C abort threshold, not evidence of RF startup at 43.4°C.
The current code executes the <40°C gate on every startup, but each specific starting temperature was not independently persisted; **starting readings are not inferred from stage peaks or later measurements**.

### Ownership, independent exit, and budget

- A fresh `picasso-wifi-session-<boot8>-<uuid12>.service` is created each time; previous failed units are not restarted, and neither Restart=always nor --collect is used.
- The worker retains notify/watchdog8/TimeoutStart180/Stop45/Memory256MiB/CPU0–3, independent ExecStopPost, and a backend tied to the exact worker PID object/3-second SCM_CREDENTIALS lease.
- The worker binds to the supervisor via BindsTo＋After. The supervisor retains its own watchdog8, Restart=no, independent ExecStopPost, Stop75, Memory128MiB, empty capability set, AF_UNIX, and bans on reboot/module/raw-io and similar calls.
- Supervisor READY means **the supervisor is ready**, not that WLAN is connected; online status requires budget phase, current worker, and real association.
- Startup intent is persisted before any worker creation/start. It records the exclusively generated unit name, file dev/inode/content, and worker session; cleanup stops only proven-owned child units from this boot.
  A planned name that was not created or whose file identity mismatches cannot be used to stop an unknown service.
- `/var/lib/picasso-wifi-reconnect/boots/<boot-id>.json` stores the budget; `events/` stores non-overwritable evidence for each stage and unit definitions.
  The budget does not reset after a stable period or service stop/start. An ordinary operator clean stop may resume within remaining budget; safety errors, exhaustion, or incomplete ownership require manual inspection, not automatic replay.
- `/run/picasso-wifi-reconnect/session.json` is supervisor state; real connectivity/cleanup records remain in `/run/picasso-wifi/` and `/var/lib/picasso-wifi/history/`.

### Routine operations (on the phone)

```sh
sudo systemctl status picasso-wifi-reconnect.service
sudo systemctl stop picasso-wifi-reconnect.service
# Disable boot-time autoconnection/reconnection:
sudo systemctl disable picasso-wifi-reconnect.service
```

Do not simultaneously start old auto/wifi services; do not manually delete budget/dirty/old markers or use reboot/original NV reset to bypass this boot's allowance and safety errors.
Changing retry count or backoff requires a separately explicit policy and preservation of old evidence, not unaudited unlimited reconnection.

### Unchanged boundaries and unfinished work

The underlying beacon-miss/reception stability issue **was not fixed**; three natural disconnections in this run demonstrate that again. Guarded recovery was implemented and measured, not a stable link.
LAN${LAN_SUBNET} TCP22 and new public-key configuration remain; SSH login from another machine using that private key has not been measured.
SELINUX configuration remains disabled, but the actual kernel remains Permissive; this boot remains original #10/FDT62ac, with the power image written for next startup; **no reboot acceptance occurred in this run**.
The existing allowlist of two exact FDTs and config/Image/ABI is unchanged. Screen tty1/15-second idle/volume-up/kernel lease remains, without whole-system suspend.
No charging, RF safety, long-term thermal/memory/UFS/power-loss, or staying-powered-off acceptance is claimed.

Evidence: `out/wifi-reconnect-20261030T003551Z/`.
Offline: 359 cases, 358 passed, 1 optional QEMU skipped; there is separate evidence of three actual natural disconnections → safe cleanup → backoff → new PID1 worker restoring connectivity, without calling simulated tests native measurements.
This stage validated only new ordinary-file/service installation and native operation; original NV was not reread and protected partitions were not re-digested. See [LAN-SSH.md](LAN-SSH.md) for the most recent whole-disk/authorized-public-key exception checks.
