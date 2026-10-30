# 屏幕持久化：开机服务与正常重启复核通过（仅屏幕，不整机休眠） / Display persistence: startup service and normal-reboot checks passed (screen only, not whole-system suspend)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

**后续用户纠正：不应继续显示色条。当前服务已改为原生tty1/fbcon，fb0只读，不生成/写入图案，见 [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md)。
长按电源的新请求正在独立隔离输入试验准备，见 [POWER-KEY.md](POWER-KEY.md)；尚未执行关机或刷boot。
以下是此前色条后端的持久化阶段记录，不把其目视/正常重启结果移植为新控制台或电源开关机验收。**

2026-10-28。用户明确要求：**“不要进行整机休眠,现在这样就行,写入手机”**。
仅保存已选择的屏幕行为：低亮度色条，**15秒无按键关灯，短按音量上亮屏/重新计时**。
不新增电源/音量下，不进行整机suspend/hibernate，不启用Wi-Fi。

## 已写入手机

- `/opt/picasso-screen/`：精确#10 ABI的租约背光模块、守护程序、单键策略及此前通过目视的冻结重绘helper。
- `/etc/systemd/system/picasso-screen.service`：已`enable --now`；正常重启后再次确认enabled/active及租约健康，开机自动亮屏后约15秒关灯。
- `/var/lib/picasso-screen/history/`：每次启动/停止的root-only记录；运行状态在`/run/picasso-screen/`。
- **不需要改boot**；保留已安装wifi2 #10、原#8恢复镜像、既有模块树。未写GPT/DTBO/vbmeta/原NV。

这里“写入”是持久保存普通XFS根文件系统中的模块与systemd服务，不是刷分区镜像。

## 常驻不是删除试验超时

原试验模块保持原样，不能靠去掉70/90秒界限变成无限亮灯。
独立 `kernel/display/picasso-wled-service.c`：

- 默认拒绝，需显式confirm；严格Picasso/PM8150L USID5/既有资源和完整electrical配置核对。
- **加载时关灯**，只写MOD_A亮度、sync bit0和module-enable bit7，不修改供电、电流、boost、保护或面板。
- 固定3秒租约、250ms内核检查。绑定实际insmod父进程的内核PID对象，不接收任意PID参数；PID复用不能冒充。
- 只有同一个root进程能写LIVE续约。到期关灯并永久拒绝该次加载的续约/亮灯，必须人工新启动/卸载处理。
- 正常调度下约3秒后关灯，非硬实时保证；PMIC总线/硬件失效不能由软件承诺绝对关灯。

`screen-service.py`的续约只在主循环温度/进度检查后进行，无独立“盲目续约”线程。
每次on沿用已目视验证的 **unblank→完整重绘→64/4095**；启动<40°C、>=45°C失败关灯。
重复/长按重复事件不续亮；只有音量上新press亮屏/重新计时，松开后才能认作下一次press。
丢失evdev事件、配置/读回错误等失败关灯且不自动重启。

服务有PID1 8秒Watchdog、Restart=no、独立ExecStopPost卸载、内存限制与小核进程亲和性；
仅允许fb0和已审核event0字符设备，禁止mount/reboot/swap/raw-io/clock修改系统调用，隐藏系统睡眠入口。
不调整全局CPU最大/最小频率、governor、温控或RF功率。

## 真机检查已通过（重启前）

- 正确父PID续约超过3秒保持实际低亮度64；不同root PID收到EPERM。
- 停止续约后内核独立实际归零；同一owner续约/重新开灯均收到ETIMEDOUT。
- 完整加固服务实际15秒idle关灯，限时停止并卸载成功。
- 对另名guard试验单元的**进程SIGSTOP**后，内核独立关灯；进程继续运行时因租约过期失败退出。
  这只是暂停屏幕进程，不是整机休眠。预期failed单元保留，没有reset-failed。
- 261项离线测试：260通过、1可选QEMU跳过。
- 全部15,285个原静态文件、当前boot128MiB、七保留分区、六GPT重新验证未变；带独立温度守护。
- `systemctl enable --now`之后服务active并实际完成15秒idle，`sync`后发出一次正常`systemctl reboot`。

重启前本阶段最高已采样36.4°C；无屏幕阶段NV/凭据读取。

## 正常重启后的复核已通过

操作者恢复主机USB后，使用原有严格pin的SSH主机公钥回连；boot ID确实变化，没有再次重启或fastboot/flash。

- 仍是原wifi2 #10；内核config/FDT、守护程序、单键策略、冻结renderer、模块及unit哈希全部匹配。
- 开机约10.03秒服务自行显示图案，约25.17秒记录idle关灯，间隔约15.14秒；unit enabled/active，Restart=no。
- 同一MainPID持续运行至复核时约900秒uptime，3秒租约未过期，不是70/90秒演示单元。
- 新boot内实际收到一次真实音量上事件，记录actual_brightness=64，约15秒后再次actual=0；没有合成按键。
- **新boot的目视结果尚未收到单独反馈**，不把事件/寄存器读回冒充目视验收；先前visual2目视通过的事实保持原范围。
- 新boot最高已采样39.4°C，复核时约31–33°C；完整性复核的独立温度守护最高35.1°C。
- 全部15,285个原静态文件、当前boot128MiB、七保留分区、六GPT再次校验未变；无NV/凭据读取。
- SSH/firewalld active；Wi-Fi仍disabled，没有为屏幕启动DSP/WLAN。
- 离线回归再次261项：260通过、1可选QEMU跳过。旧guard预期失败、主机sudo限制、pending结果和原checksum快照均保留。

## 曾遇到的主机USB阻塞（已恢复，历史记录）

USB已重新枚举为相同MAC/CDC-NCM/1d6b:0104，但主机NetworkManager尝试DHCP，丢失${HOST_USB_IP}/24。
agent宿主工具环境设置NoNewPrivs，`sudo`被拒绝，无法执行原本窄范围USB恢复。
未使用特权容器、提权绕过或扩大主机网络改动；没有重复重启或刷写手机。

当时尚不能确认新boot ID/开机服务/租约/完整性。操作者随后回复“已恢复”，本阶段已完成上述正常重启复核。
下面保留当时使用的恢复步骤；**当前不用再运行**。今后USB重新枚举且丢失地址时，可在正常主机本地交互终端使用：

```sh
cd "${REPO_ROOT}"
tools/restore-screen-usb.sh
```

helper先唯一核对USB MAC `${USB_HOST_MAC}`、cdc_ncm及gadget VID/PID，然后只对此接口设置unmanaged/up/${HOST_USB_IP}/24，
不改主机Wi-Fi、默认路由、DNS、NAT。若sudo要求认证，只在本地终端输入，不在聊天/argv/日志中提供。
随后使用既有私钥路径、严格pin的主机公钥SSH打印手机boot ID与屏幕服务状态。
本次恢复及复核已完成；不重复执行visual1/visual2试验，也不为此再次重启。

## 边界

用户取消整机休眠及新增按键，本阶段不再以三键/60秒为持久化前置。
当前是15秒、音量上、低亮度色条，不是原生DSI/GPU/触摸或桌面；不承诺阻止硬件长按复位。
电池/充电、面板重新初始化、长期稳定或物理RF静默均未认证。
若温控/配置异常导致服务失败，保持停止，不自动重试；仍可通过恢复后的USB SSH排查。

## 日常控制（手机内执行）

- 临时停止并关灯：`sudo systemctl stop picasso-screen.service`（下次开机仍启动）。
- 取消开机启动并关灯：`sudo systemctl disable --now picasso-screen.service`。
- 手动恢复：温度<40°C时`sudo systemctl start picasso-screen.service`；若失败先检查日志，不使用reset-failed掩盖问题。

证据：`out/display-persistent-20261028/result.json`及同目录新`FINAL-SHA256SUMS`。
此前pending-result、原SHA256SUMS和主机恢复失败保留；此前单键目视验收见[DISPLAY-VISUAL2.md](DISPLAY-VISUAL2.md)。

## English

**Follow-up user correction: color bars should not remain. The service was converted to native tty1/fbcon, with fb0 read-only and no pattern generation/writes; see [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md).
The new long-press power request was being prepared as a separate isolated input trial; see [POWER-KEY.md](POWER-KEY.md). No shutdown or boot flashing had occurred at that point.
The record below is the earlier color-bar backend persistence stage. Its visual/normal-reboot results must not be transferred to acceptance of the new console or power-off/on.**

2026-10-28. The user explicitly requested: **“不要进行整机休眠,现在这样就行,写入手机”** (“Do not suspend the whole system; this is fine as it is; write it to the phone.”).
Persist only the selected screen behavior: low-brightness color bars, **light-off after15 seconds without key activity, short volume-up press for screen-on/timer reset**.
Do not add power/volume-down, perform whole-system suspend/hibernate, or enable Wi-Fi.

### Written to the phone

- `/opt/picasso-screen/`: leased backlight module for exact #10 ABI, daemon, single-key policy, and frozen redraw helper that had passed visual confirmation.
- `/etc/systemd/system/picasso-screen.service`: `enable --now` completed. After normal reboot, enabled/active and healthy lease were reconfirmed; automatic startup screen-on followed by light-off after about15 seconds.
- `/var/lib/picasso-screen/history/`: root-only records of every start/stop; runtime state in `/run/picasso-screen/`.
- **No boot change needed**; installed wifi2 #10, original #8 recovery image, and existing module tree retained. No GPT/DTBO/vbmeta/original NV writes.

“Write” here means persist ordinary modules and a systemd service on the XFS root filesystem, not flash partition images.

### Persistence is not removal of trial deadlines

The original trial module stays unchanged; deleting its70/90-second limits is not a way to make illumination unlimited.
Separate `kernel/display/picasso-wled-service.c`:

- Refuses by default and requires explicit confirm; strictly checks Picasso/PM8150L USID5/existing resources and complete electrical configuration.
- **Turns light off when loaded**; writes only MOD_A brightness, sync bit0, and module-enable bit7, not power/current/boost/protection/panel settings.
- Fixed3-second lease,250ms kernel checks. Binds to the actual insmod parent process's kernel PID object; no arbitrary PID parameter, and PID reuse cannot impersonate the owner.
- Only the same root process can write LIVE to renew. Expiry turns the light off and permanently rejects renewal/illumination for that load; manual new startup/unload is required.
- Under normal scheduling, light-off occurs after about3 seconds, not a hard-real-time guarantee. Software cannot promise absolute shutoff if the PMIC bus/hardware fails.

`screen-service.py` renews only after temperature/progress checks in the main loop, without a separate “blind renewal” thread.
Every on follows the visually verified **unblank→complete redraw→64/4095** sequence; start <40°C, fail off at >=45°C.
Repeat/held-key repeat events do not extend illumination; only a new volume-up press turns on/restarts the timer, and release must occur before the next press counts.
Lost evdev events, configuration/read-back errors, and similar failures turn the light off without automatic restart.

The service has PID18-second Watchdog, Restart=no, independent ExecStopPost unload, memory limit, and small-core process affinity.
Only fb0 and audited event0 character devices are allowed; mount/reboot/swap/raw-io/clock-changing syscalls are forbidden and system sleep entry points hidden.
Global CPU max/min frequencies, governor, thermal management, and RF power are not adjusted.

### Real-device checks passed before reboot

- The correct parent PID renewed beyond3 seconds and maintained actual low brightness64; a different root PID received EPERM.
- After renewal stopped, the kernel independently brought actual brightness to zero; the same owner received ETIMEDOUT for both renewal/reillumination.
- The complete hardened service actually turned the light off after15-second idle, then stopped within the limit and unloaded successfully.
- After **process SIGSTOP** of a separately named guard trial unit, the kernel independently turned the light off; when the process resumed, lease expiry made it fail and exit.
  This pauses only the screen process, not the whole system. The expected failed unit remains; no reset-failed.
- 261 offline tests:260 passed,1 optional QEMU skipped.
- All original15,285 static files, current boot128MiB, seven reserved partitions, and six GPTs reverified unchanged, with an independent thermal guard.
- After `systemctl enable --now`, the service was active and actually completed15-second idle; after `sync`, one normal `systemctl reboot` was issued.

Peak sampled temperature before reboot in this stage was36.4°C; no NV/credential reads during the screen stage.

### Checks after normal reboot passed

After the operator restored host USB, reconnection used the original strictly pinned SSH host public key. The boot ID really changed; no additional reboot or fastboot/flash.

- Still original wifi2 #10; kernel config/FDT, daemon, single-key policy, frozen renderer, module, and unit hashes all matched.
- At about10.03 seconds after boot, the service displayed the pattern automatically; idle light-off was recorded at about25.17 seconds, about15.14 seconds later. Unit enabled/active, Restart=no.
- The same MainPID continued to about900 seconds uptime at review, with the3-second lease unexpired; this was not a70/90-second demo unit.
- One real volume-up event occurred in the new boot, recording actual_brightness=64 and actual=0 about15 seconds later; no synthetic key.
- **No separate visual feedback for the new boot had been received**. Events/register read-back cannot impersonate visual acceptance; earlier visual2 visual acceptance retains its original scope.
- Peak sampled new-boot temperature39.4°C, about31–33°C at review; the independent integrity-check thermal guard peaked at35.1°C.
- All original15,285 static files, current boot128MiB, seven reserved partitions, and six GPTs checked unchanged again; no NV/credential reads.
- SSH/firewalld active; Wi-Fi still disabled, with no DSP/WLAN startup for the screen.
- Offline regression again261 tests:260 passed,1 optional QEMU skipped. The old expected guard failure, host sudo restriction, pending results, and original checksum snapshots remain.

### Earlier host USB blocker (restored; historical record)

USB re-enumerated with the same MAC/CDC-NCM/1d6b:0104, but host NetworkManager attempted DHCP and lost${HOST_USB_IP}/24.
The agent's host tool environment set NoNewPrivs, causing `sudo` refusal and preventing the original narrowly scoped USB recovery.
No privileged container, privilege bypass, or broader host-network changes were used; the phone was not repeatedly rebooted or flashed.

At that point the new boot ID/startup service/lease/integrity could not be confirmed. The operator later replied “已恢复” (“restored”), and this stage completed the normal-reboot checks above.
The recovery procedure used then is preserved below; **do not run it again now**. If future USB re-enumeration loses the address, use a normal local interactive host terminal:

```sh
cd "${REPO_ROOT}"
tools/restore-screen-usb.sh
```

The helper first uniquely checks USB MAC `${USB_HOST_MAC}`, cdc_ncm, and gadget VID/PID, then sets unmanaged/up/${HOST_USB_IP}/24 only on that interface.
It does not change host Wi-Fi, default route, DNS, or NAT. If sudo requires authentication, enter it only in the local terminal, not chat/argv/logs.
It then uses the existing private-key path and strictly pinned host public key for SSH to print the phone boot ID and screen-service state.
This recovery/review completed; do not repeat visual1/visual2 trials or reboot again for it.

### Boundaries

The user canceled whole-system suspend and additional keys; three-key/60-second behavior is no longer a prerequisite for this stage's persistence.
At this recorded stage the behavior was15 seconds, volume-up, and low-brightness color bars, not native DSI/GPU/touch or a desktop. Preventing hardware long-press reset is not promised.
Battery/charging, panel reinitialization, long-term stability, and physical RF silence are not certified.
If thermal/configuration anomalies fail the service, leave it stopped without automatic retry; the restored USB SSH remains available for investigation.

### Everyday control (run on the phone)

- Temporarily stop and turn light off: `sudo systemctl stop picasso-screen.service` (still starts at the next boot).
- Disable startup and turn light off: `sudo systemctl disable --now picasso-screen.service`.
- Manually restore: below40°C, `sudo systemctl start picasso-screen.service`. On failure inspect logs first; do not conceal problems with reset-failed.

Evidence: `out/display-persistent-20261028/result.json` and new `FINAL-SHA256SUMS` in the same directory.
Earlier pending-result, original SHA256SUMS, and host recovery failures remain. Earlier single-key visual acceptance: [DISPLAY-VISUAL2.md](DISPLAY-VISUAL2.md).
