# Wi-Fi自动连接已启用：独立受保护服务，当前2.4GHz联网 / Wi-Fi autoconnection enabled: independent guarded service, connected on 2.4GHz at this stage

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本文保留自动连接阶段原始记录；“当前”及操作命令均属当时快照，不代表最新所有者或实时联网状态。 / This preserves the original autoconnection-stage record; “current” and operational commands are historical snapshots, not the latest owner or live connectivity.

## 中文

> 最新默认模式是[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)：真实wlan0常驻UP但不自动关联；旧auto/reconnect服务disabled且失败保留。当前要管理无线所有者应使用`picasso-wifi-radio.service`，不要启动本页旧单元；本页联网事实保留为历史。

> 当前已由新持久重连监管器接管，旧`picasso-wifi-auto.service`已disabled且failed保留，不要再按本页旧命令启动它。每boot初连＋3次退避重试，真机3次自然掉线后的自动恢复已通过；本boot最终预算用尽离线，见[WIFI-RECONNECT.md](WIFI-RECONNECT.md)。以下在线和disabled更新均是各阶段历史。

> **后续状态更新：** session `${SESSION_1}`在本页90/303秒及最终732秒在线检查之后，因`Fallback link lost; no restart loop`退出；当前enabled/failed、DSP offline/WLAN absent，清理/checkpoint/CPU恢复完成，无dirty标记。此次LAN SSH配置期间未重启Wi-Fi；见[LAN-SSH.md](LAN-SSH.md)。以下在线结果是当时的实测历史，不是当前在线状态或永久稳定保证。

用户请求“启用wifi自动连接”。沿用此前明确保存和启用授权的两份手机私有凭据，不重新录入，不读取/哈希/导出PMK。
本阶段没有重启、刷boot、PMIC操作、原NV读写、主机网络/NAT/DNS改变或移动手机。

## 实际完成

1. 原`picasso-wifi.service`以原45秒有界配置运行新session `${SESSION_6}`：
   ${PRIMARY_SSID}约19.975秒超时；${FALLBACK_SSID}约2.877秒激活，DHCP/DNS/HTTPS200及45秒检查通过。
   **整体unit为failed/watchdog**：停止健康线程后的清理阶段未声明STOPPING，8秒watchdog触发。
   独立ExecStopPost完成安全清理、工作副本checkpoint提交、共享RAM清零、CPU上限恢复；不把局部probation通过改写为整体成功。
2. 新独立`picasso-wifi-auto.service`与`wifi-auto-service.py`保持原看门狗8秒，在清理前发`STOPPING=1`，由原45秒TimeoutStopSec约束退出。
   正常运行时watchdog/父进程进度/3秒精确PID租约均保留，不在清理阶段继续伪造代理租约。
   新session `${SESSION_7}`再跑45秒：${PRIMARY_SSID}20.407秒普通超时→2.4G0.662秒激活，联网及完整清理通过，**unit inactive/success**。
3. 只有上述相同新代码的原生完整成功后，写入root0400
   `/var/lib/picasso-wifi/auto-enable-consent-20261029.json`，记录用户请求、session、45秒成功、cleanup、unit success及精确新代码哈希。
   新控制器在`probation_seconds=0`时强制验证此证据；缺失、非root0400、unit watchdog/cleanup失败或代码哈希不同均拒绝。
   然后将**新配置**转为常驻并enable服务，不是删除旧失败的45秒限制来伪装验收。
4. 当前常驻session `${SESSION_1}`：${PRIMARY_SSID}20.477秒普通超时→2.4G0.688秒激活，首次连接DNS/HTTPS再次通过；
   观察90.88秒后仍active/running/enabled，PID3764，`${FALLBACK_SSID}`，IPv4 `${PHONE_LAN_IP}/24`。
   最大采样34.7°C；归档实时元数据时同session已约303.3秒仍连接。它们只是当时观测窗口，不是长期稳定性或根因修复证明。

三次均是新session，不是重放已消耗的旧诊断。常驻服务已按用户请求保持运行；后续状态以实时unit/session为准。

## 改动范围与不变保护

- 新代码：`tools/wifi-auto-service.py`；新unit：`tools/picasso-wifi-auto.service`。
- 手机新配置：`/opt/picasso-wifi/config-auto.json`；原`config.json`、原代码及原unit未改。
- 原`picasso-wifi.service` **disabled/failed/watchdog**保留，不reset-failed，不把原失败重跑成成功。
  原控制器/config/unit及覆盖前runtime已另存root0400：
  `/var/lib/picasso-wifi/deployments/auto-enable-20261029T152332Z/`。
- 只接受两份精确已审计FDT：原#10 `62ac…`和已写入的power DTB `ecbf…`，配置基准必须仍是原#10。
  既有离线audit证明全部旧节点/属性和保留区逐字节不变，只新增三个PON/pwrkey节点；不接受任意其他FDT。
  动态RMTFS内存范围和设备身份仍每次新发现并验证。**新power DTB上的开机联网尚未原生重启验收**。
- 新控制器补齐所有可读传感器数值有效范围检查，仍启动严格<40°C/运行45°C中止，不提高任何热限。
- 原顺序${PRIMARY_SSID} band a/20秒→普通失败后${FALLBACK_SSID} band bg/25秒；安全异常立即失败，不回退掩盖。
  主SSID后续失联最多一次回退，回退再次失联则退出；`Restart=no`，不循环DSP/重连。
- SG实际24信道20MHz/EIRP/DFS子集、永久MAC、WPA2/RSN CCMP、drop区域、实际授权、DNS/HTTPS、CPU6/7运行期1094400kHz及退出恢复保持。
- 原私有四FD/RAM RMTFS/手动MPSS/auto_boot=false/recovery disabled/独立清理/原NV0400备份不可写边界不变。
  此次未读取或重新摘要原NV分区/masters，没有其他NV或凭据范围扩展。
- 活跃时`dirty.json`属于当前运行session，DSP正在运行、工作副本可能合理变化；**不删除该marker，也不能把它直接叫作脏退出**。
  只有安全关停才提交新checkpoint并按原控制器规则消耗自己创建的生命周期dirty标记。
- 屏幕仍原生tty1/15秒idle/音量上亮屏/内核租约；power服务保持enabled但本boot未激活；未休眠。

## 日常操作（手机内执行；本阶段未执行关停）

```sh
sudo systemctl status picasso-wifi-auto.service
sudo systemctl stop picasso-wifi-auto.service
# 如需关闭开机自动连接：
sudo systemctl disable picasso-wifi-auto.service
```

不要启动旧failed服务、删除dirty/marker、手工恢复原NV工作副本、启用NM无限自动重连或增加systemd Restart循环。
若新服务因失联/安全检查退出，先保存session/cleanup/history并检查温度/副本状态，不能直接循环重启。

## 未解决项和证据

此前BEACON_MISS→正常失联处理→后续DISABLE_KEY超时的事实不变。**没有修复或证明beacon接收根因**，也未改变固件/校准/BDF/功率/监管/失联检测来掩盖问题。
本次超过此前17–51秒的90秒窗口不能替代长期RF/热/充电/内存/UFS/休眠/掉电稳定性验收。
本次未重启；“开机自动连接”指已持久enable，不能称为已经实际冷启动验证。

主机证据：`out/wifi-enable-20261029T152332Z/`。旧watchdog失败、新有界完整成功、常驻观察和全部source/config证明分开保存。
一次精确替换因匹配两处被工具拒绝，未产生部分编辑；以更精确上下文改正，未更改旧控制器。
离线回归：342项，341通过，1项可选QEMU跳过；不替代原生网络/开机/长期安全证明。

## English

> The latest default mode is [WIFI-RADIO-UP.md](WIFI-RADIO-UP.md): real wlan0 stays administratively UP without automatic association; the old auto/reconnect services are disabled and their failures retained. Use `picasso-wifi-radio.service` to manage the wireless owner at that stage, and do not start the old unit on this page; this page's connectivity facts are historical.

> A new persistent reconnection supervisor has since taken over. The old `picasso-wifi-auto.service` is disabled with its failed state retained; do not start it using this page's old commands. An initial connection plus 3 backed-off retries per boot was implemented, and automatic recovery after 3 natural disconnections passed on hardware; the final budget for this boot was exhausted and the device went offline. See [WIFI-RECONNECT.md](WIFI-RECONNECT.md). The online and disabled updates below are histories of their respective stages.

> **Later status update:** After this page's 90/303-second and final 732-second online checks, session `${SESSION_1}` exited with `Fallback link lost; no restart loop`. At that update the service was enabled/failed, DSP offline/WLAN absent; cleanup/checkpoint/CPU restoration completed with no dirty marker. Wi-Fi was not restarted during this LAN SSH configuration; see [LAN-SSH.md](LAN-SSH.md). The online results below are historical measurements, not the current online state or a permanent stability guarantee.

The user requested “enable Wi-Fi autoconnection.” The two phone-private credentials previously explicitly authorized for saving and use were reused without re-entry; no PMK was read, hashed, or exported.
This stage involved no reboot, boot flashing, PMIC operations, original NV reads/writes, host network/NAT/DNS changes, or moving the phone.

### Work actually completed

1. The original `picasso-wifi.service` ran new session `${SESSION_6}` with its original bounded 45-second configuration:
   ${PRIMARY_SSID} timed out after about 19.975 seconds; ${FALLBACK_SSID} activated in about 2.877 seconds, and DHCP/DNS/HTTPS200 and the 45-second check passed.
   **The overall unit was failed/watchdog**: cleanup after stopping the health thread did not announce STOPPING, triggering the 8-second watchdog.
   Independent ExecStopPost completed safe cleanup, working-copy checkpoint submission, shared-RAM zeroing, and CPU-limit restoration; a partial probation pass is not rewritten as overall success.
2. New independent `picasso-wifi-auto.service` and `wifi-auto-service.py` kept the original 8-second watchdog and sent `STOPPING=1` before cleanup, with exit bounded by the original 45-second TimeoutStopSec.
   The watchdog, parent-process progress checks, and 3-second exact-PID lease remain during normal operation; proxy leases are not fabricated during cleanup.
   New session `${SESSION_7}` ran another 45 seconds: ${PRIMARY_SSID} had an ordinary timeout at 20.407 seconds → 2.4G activated in 0.662 seconds; connectivity and complete cleanup passed, and **the unit was inactive/success**.
3. Only after native complete success with that same new code, a root0400 file was written:
   `/var/lib/picasso-wifi/auto-enable-consent-20261029.json`, recording the user request, session, 45-second success, cleanup, unit success, and exact new-code hashes.
   The new controller mandatorily validates this evidence when `probation_seconds=0`; missing evidence, a mode/owner other than root0400, unit watchdog/cleanup failure, or different code hashes all cause rejection.
   **The new configuration** was then made persistent and the service enabled; the old failed 45-second limit was not removed to fake acceptance.
4. Persistent session `${SESSION_1}` at this stage: ${PRIMARY_SSID} ordinary timeout at 20.477 seconds → 2.4G activation in 0.688 seconds; first-connection DNS/HTTPS passed again.
   After 90.88 seconds of observation it remained active/running/enabled, PID3764, on `${FALLBACK_SSID}`, IPv4 `${PHONE_LAN_IP}/24`.
   Maximum sampled temperature was 34.7°C; at archival of live metadata the same session remained connected at about 303.3 seconds. These were observation windows at the time, not proof of long-term stability or a root-cause fix.

All three were new sessions, not replays of consumed diagnostics. The persistent service was left running as requested; later status must be determined from the live unit/session.

### Change scope and unchanged protections

- New code: `tools/wifi-auto-service.py`; new unit: `tools/picasso-wifi-auto.service`.
- New phone configuration: `/opt/picasso-wifi/config-auto.json`; original `config.json`, original code, and original unit were unchanged.
- The original `picasso-wifi.service` remains **disabled/failed/watchdog**, without reset-failed or rerunning the original failure as success.
  The original controller/config/unit and pre-overwrite runtime were separately saved root0400 at:
  `/var/lib/picasso-wifi/deployments/auto-enable-20261029T152332Z/`.
- Only two exact audited FDTs are accepted: original #10 `62ac…` and the written power DTB `ecbf…`; the configuration baseline must still be original #10.
  Existing offline audit proves all old nodes/properties and reserved regions byte-for-byte unchanged, with only three PON/pwrkey nodes added; no arbitrary other FDT is accepted.
  Dynamic RMTFS memory ranges and device identity are still freshly discovered and validated each time. **Boot-time connectivity with the new power DTB has not undergone native reboot acceptance.**
- The new controller adds valid numeric-range checks for every readable sensor, still requiring strictly <40°C at startup and aborting at 45°C during operation; no thermal limit is raised.
- Original order remains ${PRIMARY_SSID} band a/20 seconds → after ordinary failure, ${FALLBACK_SSID} band bg/25 seconds; safety anomalies fail immediately and are not concealed by fallback.
  At most one fallback follows loss of the primary SSID; loss of fallback exits. `Restart=no`, with no DSP/reconnection loop.
- Actual SG 24-channel 20MHz/EIRP/DFS subset, permanent MAC, WPA2/RSN CCMP, drop zone, actual authorization, DNS/HTTPS, CPU6/7 operating limit 1094400kHz, and restoration on exit remain.
- Original private four-FD/RAM RMTFS/manual MPSS/auto_boot=false/recovery disabled/independent cleanup/original NV0400 backup non-writable boundaries remain.
  This operation neither read nor re-digested the original NV partitions/masters and did not expand access to other NV or credentials.
- During activity, `dirty.json` belongs to the current running session; the DSP is running and working copies may legitimately change. **Do not delete this marker or directly call it a dirty exit.**
  Only safe shutdown submits a new checkpoint and consumes its own lifecycle dirty marker according to the original controller rules.
- The screen retains native tty1/15-second idle/volume-up wake/kernel lease; the power service remains enabled but was not activated this boot; no suspend occurred.

### Routine operations (on the phone; shutdown was not performed in this stage)

```sh
sudo systemctl status picasso-wifi-auto.service
sudo systemctl stop picasso-wifi-auto.service
# To disable boot-time autoconnection:
sudo systemctl disable picasso-wifi-auto.service
```

Do not start old failed services, delete dirty/markers, manually restore original NV working copies, enable unlimited NM autoconnection, or add systemd Restart loops.
If the new service exits on link loss/safety checks, first preserve session/cleanup/history and check temperature/copy state; do not simply loop restarts.

### Unresolved issues and evidence

The previous BEACON_MISS → normal link-loss handling → later DISABLE_KEY timeout facts are unchanged. **The beacon-reception root cause was neither fixed nor proven**, and firmware/calibration/BDF/power/regulatory/link-loss detection was not changed to conceal it.
This 90-second window, exceeding earlier 17–51-second windows, does not replace long-term RF/thermal/charging/memory/UFS/suspend/power-loss stability acceptance.
No reboot occurred; “boot-time autoconnection” means persistent enablement, not an actually validated cold start.

Host evidence: `out/wifi-enable-20261029T152332Z/`. Old watchdog failure, new bounded complete success, persistent observation, and all source/config proofs are stored separately.
One exact replacement was refused by the tool because it matched two locations; no partial edit resulted. More precise context corrected it without changing the old controller.
Offline regression: 342 cases, 341 passed, 1 optional QEMU skipped; this does not replace native network/boot/long-term safety proof.
