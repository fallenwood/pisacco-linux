# Fedora 45 普通重启验收 / Fedora 45 Normal-Reboot Acceptance

> 2026-11-06 UTC 快照；不是实时健康、第二次重启或重放授权。代码及 `out/` 路径相对于仓库根目录，同级链接相对于 `notes/`；私有标识和摘要不公开。
> Dated snapshot, not live health, a second reboot grant or replay authorization. Code and `out/` paths are repository-root-relative; peer links are relative to `notes/`. Private identifiers/digests are withheld.

后续 / Later：新诊断已确认 kmscon tty1 与原生 getty 互斥。另获修复及一次新增正常重启
授权后，只调整 tty1 专用选择/屏蔽/别名，屏幕和 Wi-Fi 均自动启动通过；此前未自启动及
原因未知保留为本页阶段快照。见 [屏幕自启动修复](FEDORA-45-SCREEN-AUTOSTART.md)。
/ Later diagnosis confirmed kmscon tty1 conflicts with native getty. A separate
repair/one-additional-normal-reboot grant selected/masked/aliased tty1 only;
screen and Wi-Fi autostart passed. Earlier missing autostart/unknown cause remain
this page's snapshot; see [screen-autostart repair](FEDORA-45-SCREEN-AUTOSTART.md).

## 中文

### 授权与重启前安全检查

接续 [永久安装与功能验收](FEDORA-45-INSTALL-ACCEPTANCE.md)，用户明确回复“正常重启”，只授权一次正常重启与验收。此前仅临时启动、永久路径未验证和整体 degraded 的表述是旧阶段快照。

- 同一旧启动上的 Wi-Fi、屏幕及 RMTFS/TFTP 子进程健康；93 个资产、激活策略和新原生证明均未变，配置/FDT 与基线一致。只读直接核验完整 128 MiB boot 与已安装候选一致。
- 正常停止 Wi-Fi、屏幕并独立确认 `operator_stop` / `safe_cleanup_complete`：DSP offline，子进程停止，WLAN 消失，原 core/CPU 上限恢复，2,621,440 字节共享 RAM 清零，普通工作副本匹配已提交 checkpoint，dirty 由所属服务清理而非手工删除，WLED 模块卸载。
- 此次清理后旧启动共保留三个 RMTFS 辅助失败，包括此前两个和刚停止的旧持续会话。已归档属性及 journal，没有 `reset-failed` 或修改租约，也不把安全清理等同于无失败记录。
- 把清理凭据、一次性授权和请求 fsync 保存并回收主机副本后，只发送一次 `systemctl reboot`。该命令返回 0，随后 SSH 因关机断开，主机 SSH 返回 255；没有因此重发命令。没有 force、Fastboot、额外刷写、原始 NV 恢复、独立电源/RTC/PMIC/PON 或加热试验。

### 实际结果与屏幕限制

严格固定主机密钥的 USB SSH 在新启动 uptime 9.32 秒时看见不同启动标识，原生 PID 1 为 systemd、Fedora 45、内核 `7.3.1-picasso-wifi2`。之后一条 USB 长查询超时，helper 清理发现主机临时 IPv4 已不存在；未证明是谁移除了地址。保留超时和主机网络/USB 记录，通过非 USB LAN 查询确认仍是同一个新启动，不能把会话中断误当作第二次手机重启。

- 永久引导及 Wi-Fi 自启动通过：无需手动启动 Wi-Fi，父服务和新 RMTFS/TFTP 子服务均 active/success，自动重启次数为零，已完成自动关联。当前 systemd `running`，失败单元和待处理 job 均为零。
- **屏幕自启动未通过**：在任何手动启动前，启用的版本化屏幕服务和 tty1 getty 均 inactive，没有本次屏幕 session。设备节点已存在；查询时条件时间戳为零、DBus 条件结果未评估，保留的日志没有证明具体跳过原因。因此不能断言是某个条件、设备枚举竞态或 Fedora 45 特有错误。
- 第一次诊断/恢复 helper 在解析 journal 的空 MESSAGE 时遇到 `AttributeError`，尚未启动屏幕或改变硬件；保留空输出与失败。修正版先确认仍 inactive 且无 session，安全处理非字符串 MESSAGE，再只手动启动屏幕一次。启动原生 tty1/fbcon，实际亮度 64，17 秒后观察为 0，两项 65°C 限制仍在。**这只是本次启动的手动恢复，不是修复屏幕自启动。** 本次没有再要求/声称新的实键或视觉验收；此前实键与用户确认仍是上一阶段证据。
- 恢复后同一新启动、同一组所有者观察 65.79 秒，采样最高 37.8°C。双栈证书验证 HTTPS、非 USB 双栈 LAN ping 和严格 SSH、NTP 同步均通过。
- 另一进程完整 `O_DIRECT` 读回 128 MiB，并分别匹配完整分区及镜像前缀的预期；93 个资产、manifest、activation、新原生证明均与重启前一致，没有重标旧证明或修改服务源码/pin。
- 八组热保护仍是被动 40°C、临界 110°C、滞回 2°C/1°C；屏幕/Wi-Fi 启动严格低于 65°C、运行达到 65°C 中止。持续 RF 的新所有者 live dirty 正确保留。probation 和电源服务未启用。

本轮结论是**一次经过预先干净停 RF 的普通重启，永久引导和 Wi-Fi 自启动通过，屏幕需手动恢复**，不是完整自动开机验收、断电冷启动或活动 RF 状态下未经预清理的自动关机清理验收。新启动没有旧失败单元，不代表租约退出问题已修复；旧 journal/凭据已归档，并未清失败标记伪造结果。下一步屏幕自启动修复及第二次重启需明确授权。历史掉线、异常断电、充电/电量计、关机后自启和耐久仍未解决/验收。未重跑完整主机套件，缺少 `kernel/power/picasso-pon-reason-audit.ko` 的历史错误没有被修复或隐藏。

证据位于受保护的 `out/fedora45-boot/reboot/`：`pre-reboot-cleanup.json`、`pre-reboot-native-evidence.tar`、`host-command-attempt.json`、`reboot-command-response.txt`、`host-reboot-SSH-exit-code.txt`、`first-new-boot.json`、`startup-convergence.json`（超时未产出 JSON）、`host-USB-network-state.txt`、`host-usb-events.txt`、`LAN-status-after-USB-timeout.json`、`screen-autostart-inspection.json`、`screen-dependency-inspection.json`、`screen-manual-restore.json`（首次失败）、`screen-manual-restore-v2.json`、`native-acceptance.json`、`host-LAN-validation.json`、`native-evidence.tar`。手机通用归档目录为 `/var/lib/picasso-fedora45-boot-review/normal-reboot/`，保存重启前检查、独立清理、一次请求、手动恢复和最终验收；不是重放脚本。

## English

### Authorization and pre-reboot safety checks

Following [permanent installation and features](FEDORA-45-INSTALL-ACCEPTANCE.md), “normal reboot” explicitly authorized one normal restart and acceptance only. Temporary-only runtime, unverified permanent path and global degraded describe earlier snapshots.

- Old-boot Wi-Fi/screen and RMTFS/TFTP children are healthy. All 93 assets, activation and fresh native proof remain unchanged, with matching config/FDT. Read-only direct verification confirms all 128 MiB of boot match the installed candidate.
- Stop Wi-Fi/screen normally and independently verify `operator_stop` / `safe_cleanup_complete`: offline DSP, stopped children, absent WLAN, restored core/CPU caps, 2,621,440 cleared shared-RAM bytes, ordinary work matching committed checkpoint, dirty cleared by its owner rather than manual deletion, and unloaded WLED.
- Old-boot cleanup leaves three failed RMTFS helpers: the earlier two plus the just-stopped continuous owner. Archive properties/journals; do not `reset-failed`, change leases or equate safe cleanup with zero failure records.
- Fsync/archive cleanup evidence, single-use authorization/request and host copies, then send exactly one `systemctl reboot`. It returns 0; SSH disconnects during shutdown and host SSH returns 255. Do not replay because of that transport status. No force, Fastboot, further flash, raw-NV recovery, separate power/RTC/PMIC/PON or heating experiment.

### Actual results and screen limitation

Strict-pinned USB SSH observes a different boot identity at new-boot uptime 9.32 seconds: native systemd PID 1, Fedora 45, `7.3.1-picasso-wifi2`. A later long USB query times out; helper cleanup finds the host's temporary IPv4 already absent, without proving who removed it. Preserve timeout/network/USB evidence. Non-USB LAN confirms the same new boot; transport loss is not evidence of another phone reboot.

- Permanent boot and Wi-Fi autostart pass without manually starting Wi-Fi. Parent/new RMTFS/TFTP children are active/success with zero automatic restarts and completed association. Current systemd is `running`, with zero failed units and pending jobs.
- **Screen autostart fails**: before any manual start, enabled versioned screen service and tty1 getty are inactive with no current screen session. Device nodes exist; queried condition timestamps are zero and DBus results unevaluated. Retained logs do not establish which condition or cause skipped startup. Do not assert a particular condition, enumeration race or Fedora-45-specific defect.
- First diagnostic/restore helper hits `AttributeError` on a null journal MESSAGE before starting screen/changing hardware. Preserve empty output/failure. The corrected helper confirms inactive/no session, handles non-string messages, and manually starts screen only once. Native tty1/fbcon starts at actual 64 and is observed at 0 after 17 seconds, retaining both 65°C limits. **This restores the current boot only; it does not fix screen autostart.** No new physical-key/visual acceptance was requested or claimed; those remain preceding-stage evidence.
- Post-restoration same-new-boot/same-owner observation: 65.79 seconds, peak sample 37.8°C. Certificate-verified dual-stack HTTPS, non-USB dual-stack LAN ping/strict SSH and NTP synchronization pass.
- Another process fully `O_DIRECT`-reads 128 MiB and independently matches whole-partition and image-prefix expectations. All 93 assets, manifest, activation and fresh native proof match pre-reboot state: no relabelled proof or service source/pin changes.
- Eight thermal sets retain passive 40°C, critical 110°C and 2°C/1°C hysteresis. Screen/Wi-Fi require strict-below-65°C startup and abort at 65°C runtime. Preserve new-owner live dirty during continuous RF. Probation/power remain inactive.

This accepts **one normal reboot after deliberate clean RF stop, permanent boot/Wi-Fi autostart, and manually restored screen**, not complete autostart, power-loss cold start, or unattended shutdown cleanup with active RF and no pre-cleanup. No old failed units in the new boot does not fix the exit-lease issue: old journals/evidence are archived, not hidden by clearing failures. Screen-autostart repair and a second reboot require explicit authorization. Historical link loss, abnormal power loss, charging/fuel gauge, self-restart after shutdown and endurance remain unresolved/unqualified. No full host-suite rerun; the historical missing `kernel/power/picasso-pon-reason-audit.ko` error remains unfixed/unhidden.

Protected evidence under `out/fedora45-boot/reboot/`: `pre-reboot-cleanup.json`, `pre-reboot-native-evidence.tar`, `host-command-attempt.json`, `reboot-command-response.txt`, `host-reboot-SSH-exit-code.txt`, `first-new-boot.json`, `startup-convergence.json` (timeout/no JSON), `host-USB-network-state.txt`, `host-usb-events.txt`, `LAN-status-after-USB-timeout.json`, `screen-autostart-inspection.json`, `screen-dependency-inspection.json`, `screen-manual-restore.json` (first failure), `screen-manual-restore-v2.json`, `native-acceptance.json`, `host-LAN-validation.json` and `native-evidence.tar`. Generic phone archive `/var/lib/picasso-fedora45-boot-review/normal-reboot/` retains preflight, independent cleanup, single request, manual restoration and final acceptance; these are not replay scripts.
