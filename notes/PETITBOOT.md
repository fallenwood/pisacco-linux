# Petitboot 多内核菜单 / Petitboot Multi-kernel Menu

中文：独立 Android boot v2 菜单候选
`out/petitboot-1.15/loader-v3/boot-petitboot-menu.img` 已通过离线检查。
**一次授权的临时启动请求返回成功，但只见亮背光黑屏，未显示菜单；内核/PID1
执行位置尚无法确认，kexec 仍禁用，不能宣称支持原生多内核切换。**
已正常返回原默认 `7.3.1-picasso-wifi2` 并核对自动屏幕/Wi-Fi 和固定密钥 LAN SSH。
默认启动镜像和 6.18 救援材料未更换。下方早期“没有镜像”或“尚未上机”的文字
均保留为阶段快照；最新结果见“首轮临时启动”。

English: The isolated Android boot v2 menu candidate at
`out/petitboot-1.15/loader-v3/boot-petitboot-menu.img` passed offline checks.
**One authorized temporary-boot request returned success, but only a lit black
screen was observed, with no menu. Kernel/PID1 execution progress is unconfirmed;
kexec remains disabled. Native multi-kernel switching is not accepted.**
Normal return to the original `7.3.1-picasso-wifi2` default, automatic screen/Wi-Fi
and pinned LAN SSH was verified. The default boot image and 6.18 rescue material
were not replaced. Earlier “no image” or “not yet tried on phone” statements below
remain historical stage snapshots; see “First temporary boot” for the latest result.

## 首次原生预检阻断快照 / First native preflight blockage snapshot

中文：后续取得一次受控临时菜单试验授权：先只读预检，再仅正常停止当前
RF 所有者；只有清理验收通过才可进入 Fastboot 临时启动，随后返回原默认内核。
不允许刷写、kexec、手工清除脏标记、恢复 NV 或访问原始 NV 分区。
严格固定主机密钥的 USB SSH 核对通过：原生 `7.3.1-picasso-wifi2`、
配置和 FDT 与已验收产物一致，当前 RF 所有者与本次启动的脏标记匹配，
最高温度为 37.4°C；屏幕服务活动，电源服务未活动。未打开输入事件流。

English: A subsequent bounded temporary-menu trial was authorized: read-only
preflight, then only a normal stop of the current RF owner; Fastboot temporary
boot and return to the existing default were conditional on successful cleanup
acceptance. Flashing, kexec, manual dirty-marker clearing, NV restoration and raw
NV partition access were excluded. Strictly host-key-pinned USB SSH confirmed
native `7.3.1-picasso-wifi2`, configuration/FDT matching accepted artifacts, and a
live RF owner matching this boot's dirty marker. The maximum temperature was
37.4°C; the screen service was active and the power service inactive. No input
event stream was opened.

中文：仅执行 `systemctl stop picasso-wifi-autoconnect-cn-7.3.1.service`。
命令返回零，但服务在停止期间触发 8 秒 watchdog，最终
`ActiveState=failed`、`Result=watchdog`，主进程以 SIGABRT 退出。
`ExecStopPost` 成功，回执为 `safe_cleanup_complete`；后续独立只读检查确认普通
NV 工作副本与 checkpoint 一致、脏标记不存在、DSP 离线、WLAN 消失、工作副本及
共享 RAM 没有打开的文件描述符。标记仅由已有所有者的清理流程处理，没有手工删除
或恢复 NV。**这些一致性结果不抵消服务异常，也不放宽进入引导试验的门禁。**

English: The only state-changing command was
`systemctl stop picasso-wifi-autoconnect-cn-7.3.1.service`. It returned zero, but
the service hit its eight-second watchdog during stopping, ending with
`ActiveState=failed`, `Result=watchdog` and main-process SIGABRT.
`ExecStopPost` succeeded with `safe_cleanup_complete`. Subsequent independent
read-only checks confirmed ordinary NV work copies matching the checkpoint,
no dirty marker, offline DSP, absent WLAN and no open work-copy/shared-RAM file
descriptors. Only the existing owner's cleanup handled its marker; there was no
manual deletion or NV restoration. **These consistency results do not override
the abnormal service result or relax the boot-trial gate.**

中文：此次阶段停在原默认内核，USB SSH 仍可用，Wi-Fi 已停止。没有重启、
`fastboot boot`、刷写或原生 kexec；候选仍未在手机启动，不能宣称菜单、实键或
背光实机验收。停止异常的原因尚未确定；继续修复、重新启动 RF 或继续上机步骤
需要新的明确范围，不能把此前授权或本记录当作重复操作许可。
独立私有证据位于仓库根目录相对路径
`out/petitboot-1.15/device-menu-trial-1/`，包括 `preflight-1/` 的路径检查失败、
校正版本化运行目录后的 `preflight-2/`、`normal-rf-stop/`、
`post-stop-diagnostic/` 和 `post-stop-consistency/receipt.json`。
这些是阶段快照，不是未来状态或自动恢复承诺；原离线证据未改写。

English: This stage stopped on the original default kernel with USB SSH available
and Wi-Fi stopped. No reboot, `fastboot boot`, flash or native kexec occurred.
The candidate has still never booted on the phone; physical menu/key/backlight
acceptance cannot be claimed. The abnormal stop's cause is not yet established.
Repair, RF restart or further hardware steps require a fresh explicit scope;
neither earlier authorization nor this record permits replay.
Separate private evidence is at repository-root-relative
`out/petitboot-1.15/device-menu-trial-1/`, including the path-check failure in
`preflight-1/`, `preflight-2/` after correcting the versioned runtime directory,
`normal-rf-stop/`, `post-stop-diagnostic/` and
`post-stop-consistency/receipt.json`. These are stage snapshots, not future-state
or automatic-recovery promises. Original offline evidence is unchanged.

## 停止守卫修复验收快照 / Stop-guard repair acceptance snapshot

中文：随后取得 `repair_stop_then_menu` 明确授权，允许修复停止 watchdog、
必要的受守卫 RF 启停验收，以及验收通过后的一次临时菜单试验；仍禁止刷写、
替换默认镜像、kexec、NV 恢复、手工清除标记和访问原始 NV 分区。
同版本主机 systemd 的真实隔离用户服务复现了机制：`STOPPING=1` 后到达的最后一个
守卫心跳可重新挂起 watchdog。仅自发退出或没有迟到心跳的外部停止未复现；
这些未复现记录也保留。修复在共享 `notify()` 的停止通知中附加
`WATCHDOG_USEC=0`，使迟到心跳无法重新挂起计时器；运行期仍为 8 秒，
`TimeoutStopSec=45s` 及独立 `ExecStopPost` 不变。实际主机回归确认旧版失败、
修复版正常退出，运行期失联仍触发 watchdog，超长清理仍触发停止超时。

English: Fresh explicit `repair_stop_then_menu` approval permitted the stop
watchdog repair, necessary guarded RF start/stop acceptance, and one temporary
menu trial after acceptance. Flashing, default-image replacement, kexec, NV
restoration, manual marker clearing and raw NV partition access remained excluded.
Actual isolated user services under the same host systemd version reproduced
the mechanism: a final guard heartbeat arriving after `STOPPING=1` can rearm the
watchdog. Self-initiated shutdown and external stop without the late heartbeat
did not reproduce it; those records are also retained. The shared `notify()`
now adds `WATCHDOG_USEC=0` to stopping notifications so late heartbeats cannot
rearm the timer. The active eight-second watchdog, `TimeoutStopSec=45s` and
independent `ExecStopPost` remain unchanged. Actual host regressions demonstrated
old-version failure, fixed-version success, continued active-watchdog enforcement
and continued timeout enforcement for excessive cleanup.

中文：161 项 Wi-Fi 仓库测试通过，新增测试检查实际通知数据报和运行期通知未变。
先校验并私下备份手机上的完整版本化运行文件、activation 和原证明，再仅更新
11 个版本化脚本/配置/策略/manifest/activation 文件及其精确哈希绑定；没有更改
旧版运行文件、服务单元、模块或内核镜像。新控制器先实际完成 45 秒有界原生
probation，服务结果和独立清理均成功，之后才从该次实际结果生成新的 Root0400
证明并关闭此次 probation activation；没有把旧证明换个哈希继续使用。

English: All 161 repository Wi-Fi tests passed; new tests inspect actual notify
datagrams and unchanged runtime notifications. The complete exact versioned phone
runtime, activation and previous proof were verified and privately backed up
before updating only 11 versioned script/configuration/policy/manifest/activation
files and their exact hash bindings. Legacy runtime files, service units, modules
and kernel images were unchanged. The new controller first completed an actual
45-second bounded native probation with successful unit result and independent
cleanup. Only then was a new Root0400 proof derived from that actual result and
this probation activation closed; the old proof was not merely rebound to a new
hash.

中文：随后守卫持续 Wi-Fi 正常运行至少 45 秒，保持运行期 8 秒 watchdog、
45 秒停止上限且没有自动重启；正常外部停止耗时约 13.89 秒，最终
`Result=success`，不再在 8 秒时异常退出。再次独立确认普通 NV 工作副本与
checkpoint 一致、脏标记不存在、DSP/WLAN 关闭且相关 FD 已关闭；原始默认内核
仍通过 USB SSH 可达，Wi-Fi 当前停止。保留了原有默认启用状态，但修复后重新
开机的自动启动仍待返回默认内核时实测。菜单候选尚未启动，实键/屏幕仍未验收。
私有证据位于仓库根目录相对路径
`out/petitboot-1.15/device-menu-trial-1/`，包括
`late-guard-probe-results.json`、`watchdog-safety-bounds.json`、
`host-wifi-regression-final.log`、`runtime-baseline-backup/`、
`runtime-stop-repair-staged/deployment-plan.json`、
`runtime-stop-repair-deployment/`、
`native-repaired-bounded-probation/accepted.json` 和
`native-repaired-external-stop/accepted.json`。

English: Guarded continuous Wi-Fi then ran normally for at least 45 seconds with
the eight-second active watchdog, 45-second stop limit and no automatic restarts.
A normal external stop took approximately 13.89 seconds and ended with
`Result=success`, rather than aborting at eight seconds. Independent checks again
confirmed ordinary NV work copies matching the checkpoint, no dirty marker,
DSP/WLAN off and related FDs closed. The original default kernel remains reachable
over USB SSH with Wi-Fi currently stopped. Existing default enablement is
preserved, but post-repair startup on a new boot still awaits the return-to-default
test. The menu candidate has not booted; physical keys/display remain unaccepted.
Private evidence is under repository-root-relative
`out/petitboot-1.15/device-menu-trial-1/`, including
`late-guard-probe-results.json`, `watchdog-safety-bounds.json`,
`host-wifi-regression-final.log`, `runtime-baseline-backup/`,
`runtime-stop-repair-staged/deployment-plan.json`,
`runtime-stop-repair-deployment/`,
`native-repaired-bounded-probation/accepted.json` and
`native-repaired-external-stop/accepted.json`.

## 首轮临时启动 / First temporary boot

中文：RF 正常停止、独立 NV/DSP 清理与文件系统同步通过后，现场手动进入原厂
Fastboot 并松开所有按键。主机独立核对与原验收设备相同的 USB/设备身份、
`product=picasso`、解锁状态、128 MiB `boot` 分区大小、当时电压与下载容量。
再次核对候选文件、用户空间回执、输入源及两个保留目标的精确尺寸/哈希后，
**仅执行一次 `fastboot boot`，没有 `fastboot flash` 或 kexec**。
命令返回成功只证明引导请求被接受，不证明候选 Linux、PID1 或菜单已运行。

English: After normal RF stop, independent NV/DSP cleanup and filesystem sync
passed, the onsite operator manually entered stock Fastboot and released all keys.
The host independently matched the previously accepted USB/device identity,
`product=picasso`, unlocked state, 128 MiB `boot` partition, contemporaneous voltage
and download capacity. Candidate files, userspace receipt, source inputs and both
retained targets were checked again against exact sizes/hashes.
**Exactly one `fastboot boot` was issued; no `fastboot flash` or kexec occurred.**
Successful command return proves acceptance of the boot request, not execution
of the candidate Linux, PID1 or menu.

中文：用户报告屏幕有背光但一直黑屏，没有菜单，未测试按键。约七分钟后的只读
检查未发现 Fastboot 或可达的固定密钥 USB/LAN SSH。该候选原本没有 USB/IP 诊断，
因此不能用网络不可达判定内核失败，也不能从背光亮判断租约、温度闸门或
framebuffer 已验收。本次没有获得菜单、按键、限时关灯或目标内核交接的验收。
随后再次由现场进入原厂 Fastboot，主机重新核对精确目标后仅正常
`fastboot reboot`，返回原默认镜像；没有重试候选。

English: The operator reported a lit backlight but a continuously black screen,
no menu and no key testing. Read-only checks approximately seven minutes later
found neither Fastboot nor reachable pinned USB/LAN SSH. This candidate deliberately
had no USB/IP diagnostic transport, so missing network access does not establish
kernel failure, and lit backlight does not establish accepted lease, thermal gates
or framebuffer operation. Menu, keys, timed display-off and target-kernel handoff
were not accepted. The operator then re-entered stock Fastboot. After independently
matching the exact target again, the host issued only normal `fastboot reboot`
to the existing default image; the candidate was not retried.

中文：返回后实际观察到新的原生 `7.3.1-picasso-wifi2` 启动，配置/FDT 与原验收
产物一致，屏幕和 Wi-Fi 自动活动；Wi-Fi 同一 PID 至少 45 秒稳定、无自动重启，
运行期 watchdog 仍为 8 秒、停止上限仍为 45 秒，电源服务仍未活动。
固定密钥 LAN SSH 可用；没有修改主机网卡、路由、DNS 或 NAT。当前新的
`dirty.json` 正常属于新启动的活动 RF 所有者，已保留，不能删除。
没有可用 pstore 文件，故无法从回收日志确定此次候选停在哪个启动阶段，
也不能声称没有发生内核错误。

English: Recovery actually observed a new native `7.3.1-picasso-wifi2` boot with
configuration/FDT matching accepted artifacts and automatic active screen/Wi-Fi.
Wi-Fi kept the same PID for at least 45 seconds with no automatic restarts;
the active watchdog remained eight seconds and stop timeout 45 seconds.
The power service remained inactive. Pinned LAN SSH works; no host interface,
route, DNS or NAT configuration was changed. The new live `dirty.json` legitimately
belongs to this boot's active RF owner and is retained; do not delete it.
No pstore files were available, so recovered logs cannot establish the candidate's
last execution stage or prove absence of a kernel error.

中文：私有证据位于仓库根目录相对路径
`out/petitboot-1.15/device-menu-trial-1/`：
`pre-fastboot-clean-seal/`、`stock-fastboot-preflight/`、
`temporary-menu-boot/`、`black-screen-observation/` 和 `return-default/`。
`return-default/acceptance/` 保留第一次只读监控客户端的占位符替换
`SyntaxError`，不是手机服务故障，也没有执行该监控；
修正后的 `return-default/acceptance-v2/accepted.json` 才是最终恢复验收。
这次一次性启动额度已用完。下一轮需先评估独立于菜单的早期启动日志，
优先考虑不联网、不启射频、无 shell 的 USB 诊断；它尚未实现或验证，
任何第二次上机启动均需新明确范围，不能以本记录重放操作。

English: Private evidence is under repository-root-relative
`out/petitboot-1.15/device-menu-trial-1/`:
`pre-fastboot-clean-seal/`, `stock-fastboot-preflight/`,
`temporary-menu-boot/`, `black-screen-observation/` and `return-default/`.
`return-default/acceptance/` retains the first read-only monitoring client's
placeholder-substitution `SyntaxError`; it was not a phone-service failure and
that monitor did not execute. Corrected
`return-default/acceptance-v2/accepted.json` is the final recovery acceptance.
The one-boot allowance is consumed. A subsequent trial first needs early-boot
logging independent of the menu, preferably USB diagnostics without networking,
radio or a shell. That is not yet implemented or validated. Any second hardware
boot requires a fresh explicit scope; this record is not replay permission.

## 后续离线 USB 日志候选 / Subsequent offline USB log candidate

中文：用户在黑屏试验及默认恢复之后，仅选择离线诊断构建。此轮没有再次查询或
操作手机、停止活动 RF、配置主机网络、进入 Fastboot 或启动候选。新产物隔离在
`out/petitboot-1.15/loader-v5/`，不覆盖 `loader-v3`、默认或救援产物。
`loader-v4` 的主机构建在打包前主动停止，以补上最早期 stderr 和失败时 UI 日志；
不把这个保留的未完成目录视为验收产物。
本修订内核标识为 `7.3.1-picasso-petitboot2`；`loader-v3` 的旧标识和回执保持不变。
**USB 诊断仍未上机验证，不能视为已解决黑屏或已获得再次启动许可。**

English: After the black-screen trial and default recovery, the user selected
offline diagnostic construction only. This stage made no further phone queries
or operations, active-RF stops, host-network changes, Fastboot entry or candidate
boots. New output is isolated under `out/petitboot-1.15/loader-v5/`; `loader-v3`,
default and rescue artifacts are not overwritten. The host `loader-v4` build was
deliberately stopped before packing to add earliest stderr and failure-time UI
logs; its retained incomplete directory is not an accepted artifact. This revision identifies as
`7.3.1-picasso-petitboot2`; the old `loader-v3` identity and receipts remain intact.
**USB diagnostics are not hardware-validated. This neither resolves the black
screen nor grants another boot attempt.**

中文：保留原 DT 的 USB peripheral 模式与严格 input-only 差异检查；内置原控制器、
PHY、`g_serial` CDC ACM 和 `ttyGS0` 控制台，不依赖模块自动加载或 configfs。
不启用 USB 网卡、IP、RF、块设备或目标根文件系统，禁用 SysRq。USB 使用固定的
通用诊断标签，不复制手机的真实序列号。早于 PID1 的日志只能在 gadget 成功注册后
经内核控制台输出；发生更早故障时仍可能没有任何 USB 输出。

English: The existing DT's USB peripheral mode and strict input-only difference
check are retained. The existing controller/PHY, `g_serial` CDC ACM and `ttyGS0`
console are built in without module autoload or configfs. USB networking, IP,
radio, block devices and target-root mounting remain absent; SysRq is disabled.
USB uses a fixed generic diagnostic label, not the phone's real serial number.
Pre-PID1 messages can reach the kernel USB console only after the gadget registers;
an earlier failure can still produce no USB output.

中文：内置早期 `/dev/kmsg` 节点，PID1 入口即写标记并把 stderr 定向到内核日志；
启动期 console 日志级别为 7，转发器启动后降回 3，避免持续干扰菜单。
`/init` 挂载 RAM 文件系统后，即启动独立日志转发器，再进入 console、
温度、按键与 WLED 检查。阶段标记覆盖 PID1、隔离闸门、降温、console、输入、
WLED、亮度和 discovery；失败信息写入 RAM 内核日志。转发器只读 `/dev/kmsg`、
只写 `/dev/ttyGS0`，使用非阻塞、无 controlling tty、raw/no-echo/no-signal 的串口；
`/init` 标准输入为 `/dev/null`。没有 USB 命令解析器、getty 或交互 shell。
CDC ACM 在硬件上仍是双向端点，这不是物理单向链路的声明。

English: A built-in early `/dev/kmsg` node lets PID1 mark entry and redirect
stderr to the kernel log immediately. Console log level starts at seven and
returns to three after relay startup to avoid continued menu interference.
Immediately after mounting RAM filesystems, `/init` starts a separate
log relay before console, thermal, input and WLED checks. Stage markers cover
PID1, isolation gates, cooling, console, input, WLED, brightness and discovery;
failures enter the RAM kernel log. The relay reads only `/dev/kmsg` and writes
only `/dev/ttyGS0`, using nonblocking, no-controlling-terminal, raw/no-echo/no-signal
serial access. `/init` receives standard input from `/dev/null`. There is no USB
command parser, getty or interactive shell. CDC ACM still has bidirectional
hardware endpoints; this is not a physically one-way-link claim.

中文：失败关灯、停止 UI/discovery 后，额外转发各自 RAM 日志的最后 80 行，
单条内核日志最多 768 字符，避免超大用户空间写入被 `/dev/kmsg` 拒绝。
内核日志缓冲区至少 1 MiB，转发器保留未完成的部分写入，断连后重开端点；
它不在菜单失败/120 秒显示窗口结束时退出，因此可在正常失败关灯后继续取证。
它不阻塞 PID1 等待 USB 主机，但会在转发进程退出时阻止菜单继续。
日志并非持久或无损：内核 USB console 队列有限、环形日志可覆盖、断线时已排队
输出可丢失。转发器明确报告覆盖与断连；若 PID1 从未运行或 UDC 未绑定，
RAM 回放仍不可用。温度阈值、PID 对象租约、电气限制与双层 kexec 禁令没有放宽。
原始 USB 日志可能含私有设备信息，只能存入受保护的忽略产物，不直接发布到 notes。

English: After failure-path display-off and UI/discovery stop, the last 80 lines
of each RAM log are also relayed. Individual kernel-log messages are capped at
768 characters to avoid oversized userspace writes rejected by `/dev/kmsg`.
The kernel log buffer is at least 1 MiB. The relay retains incomplete
partial writes and reopens after disconnect. It survives menu failure and the
120-second display-window expiry, allowing evidence collection after normal
failure-path display-off. It does not block PID1 waiting for a USB host, but an
exited relay prevents further menu operation. Logs are neither persistent nor
lossless: the kernel USB console queue is finite, the ring can overrun and
disconnect can lose already queued output. Overrun and disconnect are reported.
RAM replay remains unavailable if PID1 never runs or the UDC never binds.
Thermal thresholds, PID-object lease, electrical limits and both kexec barriers
are unchanged. Raw USB logs can contain private device information; keep them
in protected ignored artifacts, never publish them directly in notes.

中文：v5 已离线打包，镜像为 60,788,736 字节；17 项仓库检查通过，1 项明确受阻。
检查覆盖实际 Image 内的 initramfs、早期字符设备、匹配模块、目标载荷、
配置/DT 隔离，以及主机伪终端上的积压/背压、忽略输入、断连重连和失败日志保留。
DTB 与此前已做 schema 检查的 v3 完全相同，原 v3/default/rescue 回执哈希仍匹配。
ARM64 动态加载器验证通过，但完整 ARM64 串口回放没有通过本机模拟器：
QEMU 9.1.1 不转换目标 glibc 使用的 `TCGETS2`，而同一个主机伪终端支持该 ioctl。
这由 guest trace 和
[该版上游 ioctl 表](https://github.com/qemu/qemu/blob/v9.1.1/linux-user/ioctls.h)
核对；没有为绕过模拟器而修改生产 termios 逻辑，也不把跳过项记作成功。

English: v5 is packed offline at 60,788,736 bytes; 17 repository checks passed
and one is explicitly blocked. Checks cover the actual Image's initramfs, early
character device, matching module, retained payloads, configuration/DT isolation,
and host-PTY backlog/backpressure, ignored input, reconnect and failure-log
retention. Its DTB is identical to previously schema-checked v3, and retained
v3/default/rescue receipt hashes still match. ARM64 dynamic-loader verification
passed, but full ARM64 serial replay could not pass this host's emulator:
QEMU 9.1.1 does not translate the target glibc's `TCGETS2`, while the same host PTY
accepts it. Guest tracing and
[that upstream ioctl table](https://github.com/qemu/qemu/blob/v9.1.1/linux-user/ioctls.h)
confirm the limitation. Production termios logic was not changed to work around
the emulator, and the skipped check is not counted as success.

中文：私有证据为仓库根目录相对路径
`out/petitboot-1.15/loader-v5/build.json`、
`out/petitboot-1.15/loader-v5-offline-validation.json`、
`out/petitboot-1.15/loader-v5-tests.log`。首次 QEMU 失败保留在同目录的
`loader-v5-tests-initial.log` 和 `loader-v5-qemu-diagnostic.log`，不是手机启动证据。
下列命令仅用于离线构建/检查；现有输出目录不能重用，需选择新的隔离名字，
并满足前述默认/救援私有产物与回执前提。

English: Private repository-root-relative evidence is
`out/petitboot-1.15/loader-v5/build.json`,
`out/petitboot-1.15/loader-v5-offline-validation.json` and
`out/petitboot-1.15/loader-v5-tests.log`. The initial QEMU failure is retained in
`loader-v5-tests-initial.log` and `loader-v5-qemu-diagnostic.log` in the same
directory; these are not phone-boot evidence. Commands below are offline-only
build/check procedures. Existing output directories cannot be reused: choose
a fresh isolated name and satisfy the earlier private default/rescue artifact
and receipt prerequisites.

```sh
python3 tools/build-petitboot-loader.py \
  --userspace out/petitboot-1.15/aarch64-v9 \
  --sysroot out/petitboot-1.15/sysroot \
  --output out/petitboot-1.15/loader-v5 --jobs 6

PETITBOOT_NATIVE_BUILD=out/petitboot-1.15/native-v14 \
PETITBOOT_LOADER_BUILD=out/petitboot-1.15/loader-v5 \
  python3 -m unittest discover -s tests -p 'test_petitboot*.py' -v
```

## 初始用户空间阶段快照 / Initial userspace stage snapshot

中文：已按选择从 U-Boot 路线切换到 Petitboot。当前成果是隔离构建的 ARM64
用户空间适配，**不是可启动的手机镜像，也不是多内核启动验收**。
现有默认 7.3.1、已验证的 6.18 救援材料、手机分区和服务均未因本轮改变。
离线阶段未连接手机、停启射频、执行原生 kexec、重启或刷写。

English: The selected route changed from U-Boot to Petitboot. The current result
is an isolated ARM64 userspace adaptation, **not a bootable phone image or accepted
multi-kernel boot**. This stage did not change the existing 7.3.1 default, verified
6.18 rescue assets, phone partitions or services. The offline stage did not connect
to the phone, stop/start radio services, execute native kexec, reboot or flash anything.

中文：之后经明确授权，通过严格固定主机密钥的 SSH 完成只读核对：
运行内核为 `7.3.1-picasso-wifi2`，`gpio-keys` 提供音量上，
`pm8941_pwrkey` 提供电源键；没有音量下能力，也没有 RESIN 设备树节点。
未打开按键事件流，未修改设备文件、服务或启动状态。此次核对只是快照，
不代表三个实键已验收。独立证据见
`out/petitboot-1.15/device-read-only-audit.json`，阶段状态见
`out/petitboot-1.15/status.json`；不改写前面的离线证据。

English: Subsequently, explicit approval allowed a read-only SSH audit with strict
pinned host-key checking. The running kernel was `7.3.1-picasso-wifi2`;
`gpio-keys` supplied volume up and `pm8941_pwrkey` supplied power. There was no
volume-down capability or RESIN device-tree node. No key-event stream was opened,
and no device files, services or boot state were changed. This is a snapshot,
not acceptance of three physical keys. Separate evidence is
`out/petitboot-1.15/device-read-only-audit.json`; stage status is
`out/petitboot-1.15/status.json`. The earlier offline evidence is not rewritten.

中文：目标链路为 ABL → 独立 Linux/initramfs → Petitboot 菜单 → kexec →
选中的 Linux。音量上/下移动，电源键短按释放确认。多执行的是引导 Linux 阶段，
并非两次启动完整 Fedora，也不是安装 GRUB、Syslinux 或 U-Boot。

English: The intended chain is ABL → dedicated Linux/initramfs → Petitboot menu
→ kexec → selected Linux. Volume up/down navigates; a short power-button release
confirms. The additional stage is a loader Linux, not a second complete Fedora
startup, and does not install GRUB, Syslinux or U-Boot.

## 已实现的隔离适配 / Implemented isolated adaptation

中文：
- `petitboot/sources.json` 固定 Petitboot v1.15
  (`695b1d97d09c6c73bfbc8008d79415333e3a3aa1`) 和 kexec-tools v2.0.32
  (`15d78e5799eea7ec5ea9c5897ae95aaa0ce8970c`)。固定提交不等于验证上游签名。
- `petitboot/patches/0001-local-discovery-and-phone-keys.patch` 添加
  `pb-discover --local-only`：不初始化 udev/网络发现、不自动启动、重新发现时也不
  扫描 SCSI。仍通过本地事件载入配置，拒绝远程配置 URL；它不是完整沙箱，
  不应将任意配置文件或内核地址视为已授权。
- 修复本地配置设备没有 UUID 时被重复登记、重新发现时重复释放的问题。
  同时使用 ncurses 公共 API 替代不透明 `ITEM` 字段访问，保留菜单项属性和数组引用；
  四处只读字符串指针修正适配当前 GNU 头文件。
- `petitboot-nc --input-event /dev/input/eventN` 可重复指定输入设备，不自动枚举键盘。
  映射音量上/下；电源按下不确认，仅 50–1000 ms 的释放确认。
  忽略初始已按住的键、陈旧事件和重复事件；输入丢失、短读或 `SYN_DROPPED`
  会记录错误并结束菜单。指定按键模式必须具备三个键，否则拒绝运行。
  不更改 PMIC 长按复位行为。
- `tools/build-petitboot.py` 从固定提交导出新源树，在独立目录应用补丁并构建，
  拒绝覆盖已有输出，不安装到手机。构建 ARM64 时显式隔离目标 sysroot。
  产物包含程序、运行库、Linux 控制台 terminfo、许可与 `build.json`。
  它还不包含引导内核、完整 initramfs、BusyBox 或目标内核/DTB/模块。
- Petitboot 的 kexec 与 shutdown 路径都指向 `petitboot/blocked-transition`，
  以错误码 125 拒绝操作，不能通过上游强制回退绕过。
  已编译的 `kexec.unvalidated` 仅保留供后续审查，不是获准执行的引导入口。

English:
- `petitboot/sources.json` pins Petitboot v1.15
  (`695b1d97d09c6c73bfbc8008d79415333e3a3aa1`) and kexec-tools v2.0.32
  (`15d78e5799eea7ec5ea9c5897ae95aaa0ce8970c`). Revision pinning is not upstream
  signature verification.
- `petitboot/patches/0001-local-discovery-and-phone-keys.patch` adds
  `pb-discover --local-only`: no udev/network discovery initialization, autoboot
  or SCSI rescan, including after reinitialization. Local events still supply
  configuration; remote configuration URLs are rejected. This is not a complete
  sandbox or authorization for arbitrary configuration files or kernel locations.
- A local configuration device without a UUID was registered twice and freed
  twice on rescan; this is corrected. Public ncurses APIs replace opaque `ITEM`
  field access while retaining item attributes and array references. Four
  read-only string pointer corrections accommodate current GNU headers.
- Repeatable `petitboot-nc --input-event /dev/input/eventN` explicitly selects
  input devices without scanning keyboards. Volume up/down navigates. Power
  press alone does not confirm; only a release after 50–1000 ms confirms.
  Initially held keys, stale events and repeats are ignored. Input loss, short
  reads or `SYN_DROPPED` log an error and stop the menu. Explicit phone-key mode
  requires all three keys or refuses to run. PMIC long-hold reset is unchanged.
- `tools/build-petitboot.py` exports pinned commits into new source trees,
  applies patches and builds in isolated directories. It refuses existing output
  and does not install on the phone. ARM64 builds explicitly isolate the target
  sysroot. Output contains programs, runtime libraries, Linux-console terminfo,
  licenses and `build.json`. It does not yet include a loader kernel, complete
  initramfs, BusyBox or target kernels/DTBs/modules.
- Both Petitboot kexec and shutdown paths point to
  `petitboot/blocked-transition`, refusing with exit status 125, including upstream
  forced fallbacks. The compiled `kexec.unvalidated` is retained for later review,
  not an authorized boot entry point.

## 主机构建与证据 / Host builds and evidence

中文：以下路径相对于仓库根目录。需要固定版本源树
`src/petitboot-1.15`、`src/kexec-tools-2.0.32`；构建器不会自动下载或安装依赖。
本机使用 autotools、gettext、flex/bison、pkg-config、ncurses、libudev、
elfutils、device-mapper 和 libfdt 开发包。ARM64 使用 Clang/lld、
GNU aarch64 binutils 及独立 Fedora 44 aarch64 sysroot；sysroot 中须包含上述
开发包、glibc-devel、libgcc、libatomic、gcc 的目标运行库开发文件和 Linux terminfo。
目标 RPM 检查签名并禁止运行安装脚本/触发器。未执行修改性 Podman 操作。
内核用途的交叉 GCC 缺少完整用户空间头文件语义，不能仅加 `--sysroot` 就代替此工具链。

English: Paths below are repository-root-relative. Pinned source trees
`src/petitboot-1.15` and `src/kexec-tools-2.0.32` are prerequisites; the builder
does not download sources or install dependencies. Host prerequisites are
autotools, gettext, flex/bison, pkg-config and development packages for ncurses,
libudev, elfutils, device-mapper and libfdt. ARM64 uses Clang/lld, GNU aarch64
binutils and a separate Fedora 44 aarch64 sysroot containing those development
packages, glibc-devel, libgcc, libatomic, GCC target-runtime development files and
Linux terminfo. Target RPM signatures were checked and installation scripts/
triggers disabled. No modifying Podman operation was executed. Kernel-oriented
cross GCC lacks complete userspace header behavior; adding `--sysroot` alone is
not a substitute for this toolchain.

```sh
python3 tools/build-petitboot.py --arch native
python3 tools/build-petitboot.py --arch aarch64 \
  --sysroot out/petitboot-1.15/sysroot
```

中文：默认输出为 `out/petitboot-1.15/native` 和 `out/petitboot-1.15/aarch64`。
已存在时必须选择新的 `--output out/...`，不可覆盖失败或历史构建。
已通过的本轮输出是 `out/petitboot-1.15/native-v11/build.json` 和
`out/petitboot-1.15/aarch64-v6/build.json`。ARM64 用户空间目录约 9.9 MiB，
不代表完整启动镜像大小或手机内存用量。

English: Default output is `out/petitboot-1.15/native` or
`out/petitboot-1.15/aarch64`. If it exists, choose a fresh `--output out/...`;
do not overwrite failed or historical builds. Accepted outputs for this stage
are `out/petitboot-1.15/native-v11/build.json` and
`out/petitboot-1.15/aarch64-v6/build.json`. The ARM64 userspace directory is
approximately 9.9 MiB, not the size of a complete boot image or phone RAM usage.

```sh
PETITBOOT_NATIVE_BUILD=out/petitboot-1.15/native-v11 \
  python3 -m unittest discover -s tests -p test_petitboot_build.py -v
```

中文：上游及新增单元/解析测试 120 项通过；仓库准备与隔离集成测试 5 项通过。
后者在无外网、无硬件节点的 rootless user/mount/network namespace 和临时 chroot
中运行真实 daemon：收到两个本地菜单项，连续三次重新发现后重新载入，显示 ncurses
菜单，并证实选择模拟内核被拒绝。模拟文件不是可启动内核，不涉及设备启动。
ARM64 ELF、程序帮助/版本和按键测试已在 QEMU user-mode 通过，不能替代手机验收。
日志见 `out/petitboot-1.15/native-v11/petitboot-check.log`、
`out/petitboot-1.15/runtime-tests.log`。早期配置、编译、非 UTF-8 测试失败，
以及本地设备重复释放的失败/回溯分别保留在较早构建目录、
`runtime-before-device-id-fix.log` 和 `runtime-reinit-backtrace.log`
（后两者也在 `out/petitboot-1.15/`）；修复前证据不是当前成功结果。

English: All 120 upstream/new unit and parser tests passed; all five repository
preparation and isolated integration tests passed. The latter runs the real
daemon in rootless user/mount/network namespaces and a temporary chroot without
external networking or hardware nodes: two local entries arrive, three rescans
are followed by successful reload, ncurses renders the menu, and choosing a
dummy kernel is refused. Dummy files are not bootable kernels and no device boot
is involved. ARM64 ELF inspection, program help/version and key tests passed in
QEMU user-mode, not on the phone. Logs are
`out/petitboot-1.15/native-v11/petitboot-check.log` and
`out/petitboot-1.15/runtime-tests.log`. Earlier configuration, compilation and
non-UTF-8 test failures remain in earlier build directories. The local-device
double-free failure/backtrace remain in `runtime-before-device-id-fix.log` and
`runtime-reinit-backtrace.log`, also under `out/petitboot-1.15/`. Pre-fix evidence
is not the current successful result.

## 初始阶段边界快照 / Initial stage boundary snapshot

中文：当前设备树明确没有 RESIN/音量下节点；不能把输入适配编译成功当作三个实键
均可用，也不能擅自启用 RESIN 或修改 PMIC 复位配置。独立引导内核/initramfs 尚未
生成；现有 `CONFIG_CMDLINE_FORCE=y` 与内置磁盘根切换会影响引导入口，
不能假设增加 `--append` 就进入菜单。继承 framebuffer、背光 PID 租约、温控和
单一亮度所有者仍须专门适配，不能直接把完整 Fedora 屏幕服务复制进 initramfs。
`src/linux-7.3.1/drivers/input/misc/pm8941-pwrkey.c` 中，`qcom,pm8941-resin`
还会配置去抖/上拉并注册 PS_HOLD 关机通知；增加这个节点不是纯只读输入操作，
需要另行审查输入专用路径。

English: The current device tree explicitly omits RESIN/volume-down. A compiled
input adapter does not prove three usable physical keys and does not authorize
enabling RESIN or changing PMIC reset configuration. A dedicated loader kernel/
initramfs has not been generated. Existing `CONFIG_CMDLINE_FORCE=y` and built-in
disk-root handoff affect entry selection; adding `--append` cannot be assumed
to enter a menu. The inherited framebuffer, PID-leased backlight, temperature
guards and single brightness owner require dedicated integration, not simply
copying the full Fedora screen service into an initramfs.
In `src/linux-7.3.1/drivers/input/misc/pm8941-pwrkey.c`, `qcom,pm8941-resin` also
configures debounce/pull-up and registers a PS_HOLD shutdown notifier. Adding
that node is not read-only input enablement; an input-only path needs separate review.

中文：原生 kexec、DTB/保留内存/驱动关闭交接、选中 7.3.1 或 6.18 后的网络和
模块匹配、物理菜单显示均未验证。后续手机只读按键采样、临时启动和持久化应分别
明确范围；原生 kexec、重启或刷写前必须重新授权，并独立核实当前射频所有者的
正常停止与 NV 检查点清理。活跃 `dirty.json` 不是缓存，禁止为进入菜单而删除。
优先临时启动独立候选；未验收前不替换默认 `boot`，也不承诺自动回退。

English: Native kexec, DTB/reserved-memory/driver-shutdown handoff, networking and
matching modules after selecting 7.3.1 or 6.18, and physical menu display are
unverified. Later phone-side read-only key sampling, temporary boot and persistence
need separate scope. Native kexec, reboot or flashing requires renewed approval
and independent verification of the current radio owner's clean stop and NV
checkpoint cleanup. A live `dirty.json` is not a cache and must not be deleted to
enter a menu. Prefer a temporary independent candidate; do not replace default
`boot` before acceptance or promise automatic fallback.

## 后续独立菜单候选 / Subsequent dedicated menu candidate

中文：后续工作仍限主机离线构建，没有再次连接手机。新增
`tools/build-petitboot-loader.py`、`petitboot/loader.config`、
`petitboot/loader.dts`、`petitboot/init` 和 `petitboot/console-check.c`。
构建器只接受 `out/petitboot-1.15/` 下的新目录，拒绝符号链接重定向、
覆盖现有输出或把输出嵌入输入 bundle/sysroot。从校验过的 Linux 7.3.1
归档重新提取源码，应用原四个补丁及独立输入补丁，不修改已验收的源码、
内核、模块或镜像。打包前后均核对保留材料的大小和摘要；旧 6.18 回执中的
仓库目录前缀会显式解析到本仓库内，不通过仅匹配文件名来绕过校验。

English: Subsequent work remains host-only and offline, with no further phone
connection. Added files are `tools/build-petitboot-loader.py`,
`petitboot/loader.config`, `petitboot/loader.dts`, `petitboot/init` and
`petitboot/console-check.c`. The builder only accepts fresh directories below
`out/petitboot-1.15/`, rejecting symlink redirects, existing output and output
nested inside the input bundle/sysroot. It extracts the verified Linux 7.3.1
archive anew and applies the original four patches plus the separate input
patch, without changing accepted sources, kernels, modules or images. Retained
inputs are checked for size and digest before and after packing. A repository
directory prefix in the old 6.18 receipt is explicitly resolved inside this
repository, not bypassed by matching filenames alone.

中文：候选内核使用独立 release `7.3.1-picasso-petitboot1` 和强制的 RAM-only
`rdinit=/init` 命令行，不含磁盘根参数。关闭 block、IP、WLAN、蓝牙、
remoteproc、RPMSG、QRTR 和 RMTFS 路径；保留 Petitboot 必需的 UNIX socket、
SPMI、输入、原生 fbcon 与温度遥测。不打包射频固件、RMTFS、Wi-Fi 服务或目标
内核模块，不挂载磁盘，也不 `switch_root`。内核模块自动加载程序路径为空；
只手动加载为此内核单独编译的租约背光模块。未配置 USB/网络诊断或交互式救援
shell，日志仅位于 RAM 中的 `/run/petitboot/`。

English: The candidate has its own `7.3.1-picasso-petitboot1` release and a forced
RAM-only `rdinit=/init` command line without disk-root parameters. Block, IP,
WLAN, Bluetooth, remoteproc, RPMSG, QRTR and RMTFS paths are disabled. UNIX
sockets required by Petitboot, SPMI, input, native fbcon and thermal telemetry
remain. No radio firmware, RMTFS/Wi-Fi services or target-kernel modules are
packaged; no disk is mounted and no `switch_root` occurs. The module-autoload
executable path is empty. Only the leased backlight module, rebuilt for this
kernel, is loaded manually. USB/network diagnostics and an interactive rescue
shell are not provisioned; logs reside only in RAM under `/run/petitboot/`.

中文：`petitboot/kernel-patches/0001-picasso-input-only-keys.patch` 为电源及
RESIN 添加板级输入专用匹配项：不配置上拉、硬件去抖或 PS_HOLD 复位通知，
不设置唤醒源；保留旧匹配项行为。初始按住状态写入输入状态，输入专用模式不为
孤立释放合成按下事件，状态读取失败会报错。候选 DT 只更换原电源节点的匹配、
删除其去抖/上拉属性，并增加 RESIN/音量下节点。标准 SPMI IRQ 屏蔽、确认仍会
访问中断控制器；这不是“零硬件写入”。继承的 PMIC 长按复位行为未改变，
RESIN 接线及三个实键仍未通过手机验收。

English: `petitboot/kernel-patches/0001-picasso-input-only-keys.patch` adds
board-specific input-only power and RESIN matches. These do not configure
pull-up, hardware debounce, a PS_HOLD reset notifier or a wake source; legacy
matches retain their behavior. Initially held state is recorded, input-only
mode does not synthesize a press for an orphan release, and status-read failures
are reported. The candidate DT only changes the original power-node match,
removes its debounce/pull-up properties and adds RESIN/volume-down. Standard
SPMI IRQ masking and acknowledgement still access the interrupt controller;
this is not “zero hardware writes.” Inherited PMIC long-hold reset is unchanged.
RESIN wiring and all three physical keys remain unaccepted on the phone.

中文：BusyBox `/init` 保持 PID 1，单独拥有背光租约及亮度；`printf` 和 `read`
经 ARM64 BusyBox 核对为 shell 内建命令，避免用外部写入进程冒充租约所有者。
沿用三次连续低于 40°C 的启动冷却条件，最多等待约 300 秒；启动达到 55°C
或运行达到 45°C 即失败。先校验 tty1/KD_TEXT、唯一 fbcon 和已审计的
1080×2400 framebuffer，再加载初始关灯的 WLED 模块，验证 PID、固定电气配置、
最大亮度 256 和实际亮度。只使用亮度 64，约每 0.5 秒续期三秒租约并复查。
菜单试验为 240 个半秒检查周期，名义约 120 秒，另有处理/调度开销；不是精确
墙钟计时器。期限结束、输入/UI/daemon 丢失、遥测异常或租约失败会停止菜单，
对本进程已经拥有的背光执行关灯/卸载；未取得所有权时不抢占继承硬件。
脚本不自动重启、关机或回退。

English: BusyBox `/init` remains PID 1 and the sole backlight lease/brightness
owner. ARM64 BusyBox confirms `printf` and `read` are shell builtins, avoiding
an external writer impersonating the lease owner. Startup retains three
consecutive samples below 40°C with approximately 300 seconds maximum cooling;
55°C at startup or 45°C during operation aborts. It checks tty1/KD_TEXT, a single
fbcon and the audited 1080×2400 framebuffer before loading the initially-off
WLED module, then verifies PID, fixed electrical configuration, maximum 256
and actual brightness. Brightness is only 64, renewing the three-second lease
and rechecking approximately every 0.5 seconds. The menu trial has 240 half-second
check cycles, nominally about 120 seconds plus processing/scheduling overhead,
not an exact wall-clock timer. Expiry, lost input/UI/daemon, bad telemetry or
lease failure stops the menu and turns off/unloads backlight hardware already
owned by this process; it does not seize inherited hardware before ownership.
The script does not automatically reboot, power off or fall back.

中文：`petitboot-nc --menu-only` 移除 shell、重启、配置、插件等辅助入口，
不注册标准输入监听，按键处理只保留上/下/确认。kexec/shutdown helper
继续拒绝操作，且 `/init` 先设置不可逆的本次启动
`kernel.kexec_load_disabled=1`。候选不包含 `kexec.unvalidated`。
菜单指向大小/摘要核对过的 `7.3.1-picasso-wifi2` 和
`6.18.58-picasso-lts` 原始 Image/配对 DTB；后者是保留的已验收救援材料，
不能误称为另一套 `-wifi2` 产物。目标内核保留自己的强制命令行；
显示菜单或核对历史回执不等于验证 kexec、目标根文件系统服务或模块交接。

English: `petitboot-nc --menu-only` removes auxiliary shell, reboot,
configuration and plugin entries, registers no stdin waiter, and limits key
processing to up/down/confirm. The kexec/shutdown helper still refuses
transitions, and `/init` first sets the irreversible per-boot
`kernel.kexec_load_disabled=1`. The candidate excludes `kexec.unvalidated`.
Menu entries reference size/digest-checked raw Images and paired DTBs for
`7.3.1-picasso-wifi2` and `6.18.58-picasso-lts`. The latter is the retained
accepted rescue material, not another `-wifi2` artifact. Targets retain their
own forced command lines. Rendering a menu or checking historical receipts
does not validate kexec, target-root services or module handoff.

中文：原生启动与射频/NV 清理仍是独立的待授权步骤。本候选的关灯保护、温控、
实键及 framebuffer 均未在手机上验收；旧默认 7.3.1 和 6.18 材料的历史验收不能
继承给它。此前只读审查及单次 Wi-Fi 恢复授权均不允许临时启动、清除活跃
`dirty.json`、刷写或替换默认镜像。

English: Native boot and radio/NV cleanup remain separate steps requiring
approval. This candidate's fail-off, thermal checks, physical keys and
framebuffer have not been accepted on the phone. Historical acceptance of the
old 7.3.1 default and 6.18 material does not transfer to it. Earlier read-only
audit and one-start Wi-Fi recovery approvals do not authorize a temporary boot,
clearing a live `dirty.json`, flashing or replacing the default image.

### v3 构建快照 / v3 build snapshot

中文：除了前述用户空间交叉工具链，还需要固定的 Linux/BusyBox 下载文件、
已有默认和救援材料及其完整验收回执、当前 ROM 的固定 boot/DTBO 输入。
新克隆没有这些私有产物时不能把该命令当作完整环境初始化，也不能制造验收回执。
使用 Clang/LLVM、make、flex、bison、bc 和内核自带 `gen_init_cpio`，
不需要 root 来创建设备节点。先构建内核与模块，再编译匹配的 WLED 模块并重新
生成内置 initramfs/Image，避免把旧 ABI 的模块装入新内核。

English: In addition to the userspace cross toolchain above, prerequisites are
the pinned Linux/BusyBox downloads, existing default/rescue assets and complete
acceptance receipts, and pinned stock boot/DTBO inputs for the current ROM.
This command is not a complete environment bootstrap for a fresh clone lacking
private artifacts, and acceptance receipts must not be fabricated. It uses
Clang/LLVM, make, flex, bison, bc and the kernel's `gen_init_cpio`, without root
for device-node creation. The kernel/modules are built first, then the matching
WLED module and final built-in initramfs/Image, avoiding an old module ABI.

```sh
python3 tools/build-petitboot-loader.py \
  --userspace out/petitboot-1.15/aarch64-v9 \
  --sysroot out/petitboot-1.15/sysroot \
  --output out/petitboot-1.15/loader-v3 --jobs 6

PETITBOOT_NATIVE_BUILD=out/petitboot-1.15/native-v14 \
PETITBOOT_LOADER_BUILD=out/petitboot-1.15/loader-v3 \
  python3 -m unittest discover -s tests -p 'test_petitboot*.py' -v
```

中文：上述命令与输入是 v3 历史快照，不能用当前 USB 诊断源码重验旧 v3 的源码一致性。
这些是主机离线构建/检查命令，不是设备操作许可。输出目录已存在时须选择
新名字，不能重放以覆盖历史。最初隐藏辅助菜单后仍保留九项计数，造成
`native-v12` 的真实 UI 集成测试崩溃；改为一项初始占位后修复。
`loader-v1` 因 `BLOCK` 依赖可见性未真正关闭而被配置守卫拒绝，之后显式启用
EXPERT 并关闭选择 RPMSG 的传输驱动。`loader-v2` 是已打包的中间候选，
后续补上仅菜单模式的隐藏插件事件与 daemon 未连接时的退出清理，
不是新的手机验证。失败与中间产物均保留，不把它们改写为最终结果。

English: The commands and inputs above are a historical v3 snapshot; current USB
diagnostic sources cannot revalidate old v3 source identity.
These are host-only offline build/check commands, not device-operation
permission. Choose a new output name if it exists rather than overwriting
history. Initially, hiding auxiliary entries left a nine-item count and crashed
the real UI integration test in `native-v12`; a single initial placeholder fixes
this. `loader-v1` was rejected because BLOCK's dependency visibility prevented
its requested disablement; EXPERT and explicit disabling of RPMSG-selecting
transports correct this. `loader-v2` is a packed intermediate candidate.
Subsequent menu-only cleanup handles hidden plugin events and exit while the
daemon is disconnected; it is not new phone validation. Failed and intermediate
artifacts remain preserved rather than rewritten as final results.

中文：绑定校验器缺失后，两次隔离 pip 准备因网络重置/超时失败；最终通过主机
Fedora `dt-schema` 包补齐，临时 venv 已删除。孤立的绑定文件缺少 `input.yaml`
上下文，随后在完整隔离内核源树中完成 `dt-doc-validate`，并用
`dt-mk-schema`/`dt-validate` 核对两个候选输入节点，日志见
`out/petitboot-1.15/schema-validation.log`。`checkpatch` 为零错误、两项提示：
英式 `acknowledgement` 拼写及本地补丁同时包含驱动/绑定；它不是已经整理好的
上游提交系列。未执行修改性 Podman 操作。

English: With the binding validator missing, two isolated pip preparation
attempts failed on network resets/timeouts. The host Fedora `dt-schema` package
provided it; the temporary venv was removed. An isolated binding file lacked
the `input.yaml` context. Subsequent `dt-doc-validate` used the full isolated
kernel tree, and `dt-mk-schema`/`dt-validate` checked both candidate input nodes;
the log is `out/petitboot-1.15/schema-validation.log`. Checkpatch reports zero
errors and two advisories: British `acknowledgement` spelling and combining
driver/binding changes in a local patch. This is not an upstream-ready patch
series. No modifying Podman operation was executed.

### 本阶段离线结果 / Offline results for this stage

中文：最终主机用户空间为 `out/petitboot-1.15/native-v14/` 和
`out/petitboot-1.15/aarch64-v9/`；前者 120 项上游/新增测试通过。
`out/petitboot-1.15/loader-v3/` 的 boot 镜像为 57,712,640 字节，
仍只是候选，不是运行内存用量或手机兼容性证明。新内核、独立模块和最终镜像均已
实际编译；shim 布局、原 stock DTB 保留及 21 段静态固定/保留内存覆盖检查通过，
不等于新增实机 RAM 验证。

English: Final host userspace builds are `out/petitboot-1.15/native-v14/` and
`out/petitboot-1.15/aarch64-v9/`; all 120 upstream/new tests passed in the former.
The boot image in `out/petitboot-1.15/loader-v3/` is 57,712,640 bytes, still a
candidate rather than a RAM-use measurement or phone compatibility proof.
The new kernel, separate module and final image were actually compiled.
Shim layout, preservation of stock DTBs and static coverage of 21 fixed/reserved
regions passed; this is not new live RAM validation.

中文：14 项仓库测试全部通过，包括真实 daemon/UI、隐藏辅助入口、本地菜单重新
发现、拒绝内核加载、实际输入 IRQ 的孤立释放/错误路径、温度及租约失败、framebuffer
布局拒绝、输出隔离和 DT/配置越界拒绝。还从实际 Image 中找到内置压缩 initramfs，
解析其 cpio，核对 `/init`、程序、两个完整目标 Image/DTB 及匹配 release 的 ARM64
模块，而不是只检查构建目录。ARM64 实际按键测试与程序帮助在 QEMU user-mode
通过。结果见 `out/petitboot-1.15/loader-offline-validation.json`、
`loader-v3-tests.log`、`loader-v3-schema.log`、`loader-v3-qemu.log`
（后三者也在 `out/petitboot-1.15/`），构建回执为
`out/petitboot-1.15/loader-v3/build.json`。原
`out/petitboot-1.15/offline-validation.json` 未重写；
`out/petitboot-1.15/status.json` 在新阶段内嵌保留了原阶段状态。

English: All 14 repository tests passed, including the real daemon/UI, hidden
auxiliary entries, local-menu rescans, refused kernel loading, actual input IRQ
orphan-release/error paths, thermal/lease failures, rejected framebuffer layouts,
output isolation and out-of-scope DT/configuration rejection. They also locate
the compressed initramfs in the actual Image, parse its cpio and check `/init`,
programs, both complete target Images/DTBs and the ARM64 module's matching
release, rather than only inspecting a build directory. Actual ARM64 key tests
and program help passed under QEMU user-mode. Evidence is
`out/petitboot-1.15/loader-offline-validation.json`, `loader-v3-tests.log`,
`loader-v3-schema.log` and `loader-v3-qemu.log`, the latter three also under
`out/petitboot-1.15/`. The build receipt is
`out/petitboot-1.15/loader-v3/build.json`. Original
`out/petitboot-1.15/offline-validation.json` is unchanged;
`out/petitboot-1.15/status.json` embeds the preceding phase's status in the new
phase record.

## 上游 / Upstream

- [Petitboot v1.15](https://github.com/open-power/petitboot/tree/v1.15)
- [kexec-tools v2.0.32](https://github.com/horms/kexec-tools/tree/v2.0.32)
