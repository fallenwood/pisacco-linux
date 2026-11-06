# Fedora 45 功能与永久引导验收 / Fedora 45 Features and Permanent Boot Installation

> 2026-11-06 UTC 分阶段快照，不是实时健康报告或重放授权。代码及 `out/` 路径相对于仓库根目录；同级链接相对于 `notes/`。私有标识与摘要不公开。
> Dated, staged snapshot, not live health or replay authorization. Code and `out/` paths are repository-root-relative; peer links are relative to `notes/`. Private identifiers and digests are withheld.

最新后续 / Latest follow-up：后来已确认 kmscon/getty 冲突，按新授权修复 tty1 选择与
专用别名，再一次正常重启后屏幕/Wi-Fi 均自启动通过；监管稳定性问题仍未解决。
见 [屏幕自启动修复](FEDORA-45-SCREEN-AUTOSTART.md)。此前未重启/手动恢复/失败状态
都保留为各阶段快照。
/ Later kmscon/getty conflict diagnosis and newly authorized tty1 selection/alias
repair passed another normal reboot with screen/Wi-Fi autostart. Regulatory
stability remains unresolved. See [screen-autostart repair](FEDORA-45-SCREEN-AUTOSTART.md);
unverified reboot/manual restoration/failure states below are staged history.

此前后续 / Earlier follow-up：另获“正常重启”授权后，一次普通重启已通过永久引导和 Wi-Fi 自启动，
新启动 running、零 failed；屏幕未自启动，已手动恢复而未修复自启动。见
[普通重启验收](FEDORA-45-NORMAL-REBOOT.md)。下文“尚未普通重启、degraded”保留为本页阶段快照。
/ A later explicit normal-reboot grant verified permanent boot/Wi-Fi autostart;
the new boot is running with zero failed units. Screen did not autostart and was
manually restored, not fixed. See [normal-reboot acceptance](FEDORA-45-NORMAL-REBOOT.md).
Unverified reboot/degraded below remain this page's earlier-stage snapshot.

## 中文

### 授权与功能验收

本记录接续 [45 引导拒绝与临时启动](FEDORA-45-BOOT-GUARD.md)。旧页的“永久 boot 未改、四项功能关闭、NTP 未同步”是此前快照，不再是本阶段留置状态。用户在“恢复并验收屏幕/Wi-Fi，验收通过后再永久写 boot”的明确提案后回复“继续”，并在真实音量上亮屏后回复“是”，确认看见终端。没有授权或执行额外普通重启、关机、原始 NV 恢复、独立电源/RTC/PMIC/PON 或加热试验。

- 在同一 Fedora 45 / `7.3.1-picasso-wifi2` 临时启动上重验 93 个运行时资产。把 manifest 和激活策略绑定到实际临时验证过的候选镜像，而非旧镜像；不改控制器、模块、监管/MAC/NV 守卫或安装标记，不伪装发行版。
- 最初只允许屏幕与有界 Wi-Fi probation，禁止持续 Wi-Fi 和电源服务。屏幕原生 tty1/fbcon 启动，实际亮度 64，15 秒空闲后为 0。记录到真实音量上事件，实际亮度再次为 64，15.105 秒后归零；用户确认终端文字可见，没有注入按键或合成像素。
- 新原生 45 秒 probation 的父 unit 成功，最终状态 `passed_bounded_probation`。独立清理为 `safe_cleanup_complete`：DSP offline、子进程停止、WLAN 消失、原 core 和 CPU 上限恢复、2,621,440 字节共享 RAM 清零、普通工作副本匹配已提交 checkpoint、dirty 不存在。控制器记录的 probation 最高温 35.7°C。
- 从这次实际结果生成新证明，保留旧证明备份，不把 Fedora 44 证明重新标为 Fedora 45。随后仅启用持续 Wi-Fi 与屏幕，关闭 probation 和电源授权。两服务保持启用；保留 65°C 启动严格低于门槛及运行达到门槛即中止、40°C 被动降频、110°C 临界保护及 2°C/1°C 滞回。
- 写入前 95.58 秒观察中，父服务与会话所有者不变、无自动重启，采样最高 36.1°C；双栈证书验证 HTTPS、非 USB 双栈 LAN ping 和严格主机密钥 SSH 通过。NTP 自动同步恢复。持续 RF 的有效 live dirty 按设计保留，不手工删除。

### 仅写 boot、读回与恢复

一次性安装脚本首次在触碰 boot 前拒绝：误把普通控制器的 `connected_guarded` 当成当前 CN 射频控制器状态。独立复核发现两个服务和原 PID 正常，实际状态为 `radio_up_association_observed_not_internet_validated`，写入字节为零、没有写入 attempt。保留失败及原脚本；修正版检查实际 CN 所有者、已完成自动关联，并重新执行双栈证书验证 HTTPS。未修改设备安全守卫。

通过视觉确认和上述复核后，正常停止 Wi-Fi、屏幕，再独立确认 DSP/RAM/普通 NV 生命周期清理完成。唯一名称、既有 GPT 标识、128 MiB 长度、设备号、无 holders、非根文件系统与完整旧分区摘要都匹配后，排他打开明确的 boot 块设备。用关机/休眠 inhibitor 保护这次操作，仅写候选与零填充到原分区全长，fsync 后以对齐 `O_DIRECT` 完整读回并匹配预期。旧完整备份与压缩备份保留；没有写其他原始分区、原始 NV 或升级/重装根文件系统。

随后恢复两服务，产生明确的新所有者，不声称跨人工停止仍保持同 PID。写后另一进程再次独立 `O_DIRECT` 读回全部 128 MiB 并匹配；新所有者观察 37.38 秒，采样最高 36.8°C，屏幕空闲归零，双栈 HTTPS、非 USB 双栈 LAN ping/严格 SSH、NTP 同步通过。新 RMTFS/TFTP 子服务健康，运行期有效 dirty 保留。没有新普通重启：目前仍是原临时启动，永久路径的实际重启验收尚未完成。

### 保留的失败与局限

- 首次写后 verifier 要求 systemd `running`，因此在保存验收文件前拒绝。复核发现全局为 `degraded`，不是写入/读回错误：有两个已结束的旧 RMTFS 子 unit 为 failed，分别属于 probation 和写前持续会话；journal 显示 `TimeoutError: Root controller lease expired`。父 unit 成功及普通 NV 安全清理不等于全局没有 failed unit。
- 旧辅助进程的超时与退出清理阶段相符，守卫 fail-closed；没有做独立强制超时试验、定位为 Fedora 45 特有问题或修改退出次序。当前新辅助进程 active/success，旧失败不属于它们；仍保留两个 failed 状态和 journal，未 `reset-failed`、放宽租约或伪称全绿。
- 最新结果是“永久 boot 全读回和当前服务通过、保留历史辅助失败”，不是完整 systemd 健康或冷启动通过。普通重启仍需新的明确授权，并应先正常停止 RF、确认独立清理和普通 checkpoint；不要强制重启或删除 dirty。
- 历史 5 GHz/link-loss、整机异常断电、充电/电量计、关机后自行启动及长期稳定性均未解决或未验收。此前主机完整套件仍有缺少 `kernel/power/picasso-pon-reason-audit.ko` 的已知错误；本阶段没有重跑全套或宣称修复该错误。

受保护证据：`out/fedora45-boot/features/`，包括 `probation.json`、`native-feature-acceptance.json`（视觉确认前的原快照）、`host-LAN.txt`、`permanent-write-native.json`（拒绝）、`install-refusal-inspection.json`、`permanent-write-native-v2.json`（成功）、`post-install-native.json`（首次 verifier 未产出 JSON）、`post-install-refusal-inspection.json`、`post-install-native-v2.json`、`post-install-host-LAN.json` 与 `installed-evidence.tar`。手机通用归档目录为 `/var/lib/picasso-fedora45-boot-review/features/`，另存视觉确认、原策略/证明、独立清理、attempt 与最终读回结果。这些不是可直接重放的指令。

## English

### Authorization and feature acceptance

This follows [45 guard refusal and temporary boot](FEDORA-45-BOOT-GUARD.md). Its unchanged permanent boot, four inhibited features and unsynchronized NTP describe an earlier snapshot, not this phase's final state. The operator answered “continue” to the explicit proposal to restore/accept screen and Wi-Fi, then permanently install boot only after acceptance, and answered “yes” after physical volume-UP wake to confirm visible terminal text. No additional normal reboot, poweroff, raw-NV recovery, separate power/RTC/PMIC/PON or heating experiment was authorized or performed.

- Recheck 93 runtime assets on the same Fedora 45 / `7.3.1-picasso-wifi2` temporary boot. Bind manifest/activation to the actually tested candidate, not the old image. Do not change controllers, modules, regulatory/MAC/NV guards, install markers or release declarations.
- Initially permit only screen and bounded Wi-Fi probation, not continuous Wi-Fi or power. Native tty1/fbcon starts at actual brightness 64 and idles to 0 after 15 seconds. A real volume-UP event restores actual 64, then idles to 0 after 15.105 seconds. The operator confirms visible terminal text; no injected keys or synthetic pixels.
- Fresh native 45-second probation has a successful parent unit and `passed_bounded_probation`. Independent `safe_cleanup_complete` verifies offline DSP, stopped children, absent WLAN, restored core/CPU caps, 2,621,440 cleared shared-RAM bytes, ordinary work matching committed checkpoint and absent dirty. Controller-recorded probation peak: 35.7°C.
- Generate new proof from those actual results, retaining the old backup rather than relabelling Fedora 44 proof. Enable only continuous Wi-Fi and screen, inhibiting probation/power. Keep both services enabled, strict-below-65°C startup and abort-at-65°C runtime guards, passive 40°C cooling, critical 110°C protection and 2°C/1°C hysteresis.
- Before installation, a 95.58-second observation retains parent/session owners with no automatic restart; peak sample 36.1°C. Certificate-verified dual-stack HTTPS, non-USB dual-stack LAN ping and strict host-key SSH pass. Automatic NTP synchronization resumes. Preserve valid live dirty during continuous RF; never delete it manually.

### Boot-only write, readback and restoration

The first one-off installer refused before touching boot: it expected the ordinary controller's `connected_guarded`, not the actual CN radio status. Independent inspection confirms both services/original PIDs healthy, actual `radio_up_association_observed_not_internet_validated`, zero written bytes and no write attempt. Preserve the failure/original script. The corrected verifier checks the actual CN owner/completed autoconnect and repeats certificate-verified dual-stack HTTPS. Device safety guards remain unchanged.

After visual confirmation and those checks, stop Wi-Fi/screen normally and independently verify clean DSP/RAM/ordinary-NV lifecycle. Require unique name, established GPT identity, 128 MiB size, device number, no holders, non-root target and exact whole-old-partition digest before exclusive opening of the explicit boot block device. A shutdown/sleep inhibitor protects the operation. Write only the candidate plus zero padding through the original partition, fsync, then aligned `O_DIRECT` full readback matching expectation. Retain original full/compressed backups. No other raw partition/raw NV writes or root upgrade/reinstallation.

Restore both services with explicitly new owners, not a claim of unchanged PIDs across deliberate stops. Another process independently `O_DIRECT`-reads all 128 MiB again and matches. New-owner observation: 37.38 seconds, peak sample 36.8°C; screen idles to zero. Dual-stack HTTPS, non-USB dual-stack LAN ping/strict SSH and NTP synchronization pass. New RMTFS/TFTP children are healthy; preserve valid live dirty. No new normal reboot: still the original temporary boot, so actual restart through permanent boot is unverified.

### Preserved failures and limitations

- The first post-write verifier demanded systemd `running` and refused before saving acceptance. Inspection finds global `degraded`, not an image-write/readback failure: two ended old RMTFS units are failed, belonging to probation and the pre-write continuous session. Journals show `TimeoutError: Root controller lease expired`. Successful parent units and safe ordinary-NV cleanup do not imply globally zero failed units.
- Expiry is consistent with the old helpers' exit-cleanup phase and fail-closed guards. No separate forced-expiry experiment, attribution as Fedora-45-specific, or cleanup-order change. New helpers are active/success; the old failures do not belong to them. Retain both failed states/journals; no `reset-failed`, lease relaxation or false all-green claim.
- Latest result means full permanent-boot readback and operational current services with historical helper failures, not complete systemd health or cold-start acceptance. A normal reboot still requires fresh explicit authorization and prior orderly RF stop, independent cleanup/checkpoint checks; do not force reboot or delete dirty.
- Historical 5 GHz/link-loss, abnormal whole-phone power loss, charging/fuel gauge, self-restart after shutdown and endurance remain unresolved/unqualified. The earlier full host suite still has its known missing `kernel/power/picasso-pon-reason-audit.ko` error. This phase did not rerun the full suite or claim that error fixed.

Protected evidence is under `out/fedora45-boot/features/`: `probation.json`, `native-feature-acceptance.json` (original pre-visual-confirmation snapshot), `host-LAN.txt`, `permanent-write-native.json` (refusal), `install-refusal-inspection.json`, `permanent-write-native-v2.json` (success), `post-install-native.json` (first verifier produced no JSON), `post-install-refusal-inspection.json`, `post-install-native-v2.json`, `post-install-host-LAN.json` and `installed-evidence.tar`. Generic phone archive `/var/lib/picasso-fedora45-boot-review/features/` separately retains visual confirmation, old policies/proof, independent cleanup, attempt and final readback. None are replay instructions.
