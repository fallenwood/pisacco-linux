# Fedora 45 屏幕自启动修复 / Fedora 45 Screen-Autostart Repair

> 2026-11-06 UTC 分阶段快照，不是实时健康或重放授权。代码及 `out/` 路径相对于仓库根目录，同级链接相对于 `notes/`；私有标识和摘要不公开。
> Dated, staged snapshot, not live health or replay authorization. Code and `out/` paths are repository-root-relative; peer links are relative to `notes/`. Private identifiers/digests are withheld.

> 后续 / Follow-up：本页的 510 项测试及旧 `.ko` 缺失错误保留为当时事实；后续已按原 pin 取回该普通文件，并完成独立 7.3.1 PON 适配和未加载的旁路存放，最新主机测试无错误，未新增 PON 采样或重启。见 [PON-AUDIT-7.3.1.md](PON-AUDIT-7.3.1.md)。
> This page's 510-test missing-legacy-`.ko` error remains historical fact. A later stage recovered that ordinary file against its original pin and prepared/staged a separate unloaded 7.3.1 PON port. The latest host suite has no errors, without new PON sampling or reboot; see the linked note.

## 中文

### 新授权与实际原因

接续 [首次普通重启](FEDORA-45-NORMAL-REBOOT.md)。用户在“修复屏幕自启动，再做一次正常重启验收”的明确提案后回复“继续”，授权本轮修复及一次新增正常重启，不是无限重试、额外刷写、原始 NV 恢复、独立电源/RTC/PMIC/PON 或加热试验。旧页“原因未证明、屏幕需手动恢复”保留为当时快照。

后续读取 vendor unit、启用链接和同一次旧启动的 journal，确认 `kmsconvt@tty1.service` 已启用，声明 `Conflicts=getty@%i.service`，与屏幕服务的 `Requires=getty@tty1.service` 冲突。kmscon 在启动约 7.98 秒运行；前一阶段手动拉起屏幕时，约 562.9 秒才启动 getty 并停止 kmscon。这解释了为何屏幕未进入自己的启动条件/会话，而手动启动能够恢复。不是取消原屏幕条件、伪造终端或加等待来掩盖问题。

本轮首次 LAN 诊断超时，USB 查询确认仍是旧启动，屏幕仍运行，但 Wi-Fi 已因 `RuntimeError: Regulatory state changed during raw dump` 进入 `failed_safety_shutdown`。独立检查为 `safe_cleanup_complete`：DSP offline、子进程停止、WLAN 消失、core/CPU 上限恢复、2,621,440 字节共享 RAM 清零、普通 work/checkpoint 一致、dirty 不存在。保留该新发生的监管稳定性失败，没有重启旧无线服务、重试错误采样、恢复 NV 或放宽监管守卫。它不是屏幕冲突的原因，也没有被本次修复根治。

### 最小 tty1 选择与回归

新增 `tools/select-native-tty1.py`，只有显式 `--apply`、原生 root/已安装内核/磁盘标记和候选屏幕授权校验通过才修改配置。先把原链接独占备份到新目录并 fsync，再只选择 tty1：

1. 保留 `/etc/systemd/system/getty.target.wants/getty@tty1.service` 指向原生 getty 模板。
2. 移除 `/etc/systemd/system/getty.target.wants/kmsconvt@tty1.service`。
3. 把 `/etc/systemd/system/kmsconvt@tty1.service` 屏蔽到 `/dev/null`。
4. 把 `/etc/systemd/system/autovt@tty1.service` 指向 `/usr/lib/systemd/system/getty@.service`，固定该实例别名。

全局 `/etc/systemd/system/autovt@.service` 仍指向 kmscon 模板，其他 tty 和串口配置不动。没有卸载 kmscon、改 vendor 文件、getty/屏幕 unit 正文、模块或内核。

最初只处理 kmscon 的 want/mask，尚未重启便进行原生别名查询，发现 `autovt@tty1.service` 仍可通过全局模板别名加载 kmscon，绕过名称屏蔽。保留首版 helper、结果和独立备份后，补上上面的 tty1 专用别名；没有以重启试错。原生解析随后确认 `autovt@tty1` 与 `getty@tty1` 是同一个 getty unit，kmscon 实例 masked/inactive。保留两阶段备份，而非覆盖第一次原始链接。

7 项新回归测试覆盖 tty1 专用选择、全局别名/其他 tty 保持、备份不可覆盖、异常文件/链接/目录拒绝和重复选择检查；14 项候选运行时与 11 项屏幕测试也通过。`systemd-analyze verify multi-user.target` 原生静态事务检查通过。

### 新增一次正常重启与验收

重启前正常停止屏幕、确认 WLED 卸载；重新核验先前已经安全停机的 RF、普通 work/checkpoint 和 dirty 缺席，归档监管失败。完整 boot 只读 `O_DIRECT` 摘要与此前安装一致。93 个已固定运行时资产、manifest、activation 和持久原生 Wi-Fi 证明均未变；改变的是上述系统级 tty1 选择链接，不是把旧证明改标为新证明。

独占保存并 fsync 本轮一次请求，仅发送一次 `systemctl reboot`，返回 0；本轮没有第二次重启、force、Fastboot 或 boot 写入。

- 新启动标识与旧启动不同；USB SSH 在 uptime 9.39 秒已经观察到屏幕 session 为 starting。随后两服务均自动达到 active/success，**重启后没有手动启动屏幕、getty 或 Wi-Fi**。
- 原生 getty 与 tty1 专用 autovt 是同一 unit，kmscon tty1 masked/inactive。屏幕为原生 tty1/KD_TEXT/fbcon，实际 startup 亮度 64，15 秒 idle 事件实际为 0；热策略先于屏幕和 Wi-Fi 主程序启动。
- 同一新启动、同一组所有者观察 95.31 秒，采样最高 36.1°C；父服务与 RMTFS/TFTP 子服务均健康、无自动重启。systemd `running`，零失败单元、零待处理 job。
- 双栈证书验证 HTTPS、非 USB 双栈 LAN ping 和严格主机密钥 SSH、NTP 同步通过。完整 128 MiB boot 与镜像前缀再次独立直接读回一致。
- 八组热保护仍是被动 40°C、临界 110°C、滞回 2°C/1°C；屏幕/Wi-Fi 仍严格低于 65°C 才启动、达到 65°C 即中止。有效 live dirty 属于新 RF 所有者并正确保留，probation/电源服务未启用。
- 验收快照中本次实键计数为 0，没有新的用户视觉确认，不把此前实键/视觉结果冒充本次；本次直接通过的是自启动、原生控制台元数据和 startup/idle 实际亮度。此前实键行为的代码及守卫没有改变。

完整主机套件 **510 项：488 通过、21 跳过、1 错误**；唯一错误仍是缺少 `kernel/power/picasso-pon-reason-audit.ko`，没有删除或伪称通过。当前屏幕自启动已在一次新增正常重启上通过；监管采样变化/历史掉线、旧辅助退出租约问题、异常断电、充电/电量计、关机后自启和耐久仍未解决或未验收。该测试先验清理 RF，不是活动 RF 未预清理的自动关机清理或断电冷启动验收。

证据位于受保护的 `out/fedora45-boot/screen-autostart/`：`diagnostic.json`（首次 LAN 超时未产出 JSON）、`USB-status.json`、`diagnostic-v2.json`、`kmscon-inspection.json`、`selection.json`、`autovt-alias-check.txt`、`select-native-tty1-v1.py`、`selection-v2.json`、`preflight.json`、`pre-reboot-verified.json`、`pre-reboot-verified-v2.json`、`pre-reboot-native-evidence.tar`、`host-command-attempt.json`、`reboot-response.txt`、`first-new-boot.json`、`autostart-converged.json`、`post-reboot-acceptance.json`、`host-LAN-validation.json`、`native-evidence.tar`、各测试日志及 `full-host-tests.log`。手机通用归档目录 `/var/lib/picasso-fedora45-boot-review/screen-autostart/` 另保留两个 selection-backup、静态事务、旧监管失败、一次请求和最终验收；不是重放授权。

## English

### New authorization and actual cause

Following [the first normal reboot](FEDORA-45-NORMAL-REBOOT.md), “continue” answered the explicit proposal to fix screen autostart and perform one more normal reboot. It does not authorize unlimited retries, further flashing, raw-NV recovery, separate power/RTC/PMIC/PON or heating experiments. Earlier unknown-cause/manually-restored statements remain dated snapshots.

Read vendor units, enabled links and that same old boot's journal: enabled `kmsconvt@tty1.service` declares `Conflicts=getty@%i.service`, conflicting with the screen service's `Requires=getty@tty1.service`. Kmscon runs around boot 7.98 seconds; only the preceding manual screen start around 562.9 seconds starts getty and stops kmscon. This explains the missing screen condition/session and successful manual recovery. Do not remove screen conditions, fake terminal content or hide the conflict with delays.

Initial LAN diagnosis times out. USB confirms the same old boot, screen still running, but Wi-Fi has entered `failed_safety_shutdown` with `RuntimeError: Regulatory state changed during raw dump`. Independent `safe_cleanup_complete` checks offline DSP, stopped children, absent WLAN, restored core/CPU caps, 2,621,440 cleared shared-RAM bytes, matching ordinary work/checkpoint and absent dirty. Preserve this newly observed regulatory-stability failure; no restart of the old radio, retry of rejected sampling, NV recovery or regulatory relaxation. It neither caused the screen conflict nor is fixed by this repair.

### Minimal tty1 selection and regression

New `tools/select-native-tty1.py` requires explicit `--apply`, native root/installed kernel/disk marker and candidate screen consent. Exclusively back up and fsync original links before selecting tty1 only:

1. Preserve `/etc/systemd/system/getty.target.wants/getty@tty1.service` targeting the native getty template.
2. Remove `/etc/systemd/system/getty.target.wants/kmsconvt@tty1.service`.
3. Mask `/etc/systemd/system/kmsconvt@tty1.service` to `/dev/null`.
4. Point `/etc/systemd/system/autovt@tty1.service` at `/usr/lib/systemd/system/getty@.service`, fixing that instance alias.

Global `/etc/systemd/system/autovt@.service` still targets the kmscon template; other VTs/serial consoles remain unchanged. No kmscon removal, vendor-file, getty/screen unit-body, module or kernel change.

The initial want/mask-only selection is checked natively before any reboot: `autovt@tty1.service` still loads kmscon through the global template alias, bypassing the name mask. Retain the first helper/result/exclusive backup, then add the tty1-specific alias above; no reboot trial-and-error. Native resolution now makes autovt/getty tty1 the same getty unit, with kmscon tty1 masked/inactive. Keep both backups rather than overwriting the original link record.

Seven new regressions cover tty1 selection, unchanged global alias/other VTs, non-overwritable backups, unexpected files/links/directories and already-selected validation. Fourteen candidate-runtime and eleven screen tests pass too. Native `systemd-analyze verify multi-user.target` static transaction verification passes.

### One additional normal reboot and acceptance

Normally stop screen/unload WLED. Independently recheck already safety-stopped RF, ordinary work/checkpoint and absent dirty; archive regulatory failure. Read-only full-boot `O_DIRECT` digest matches installation. All 93 pinned runtime assets, manifest, activation and persisted native Wi-Fi proof remain unchanged. The system-level tty1 selection links changed, not a relabelled proof.

Exclusively save/fsync this phase's single request, send exactly one `systemctl reboot`, return 0. No second reboot in this phase, force, Fastboot or boot write.

- Different new boot identity; USB SSH already sees screen session starting at uptime 9.39 seconds. Both services then reach active/success automatically: **no manual screen, getty or Wi-Fi start after reboot**.
- Native getty and tty1-specific autovt are one unit; kmscon tty1 is masked/inactive. Screen uses native tty1/KD_TEXT/fbcon, actual startup brightness 64 and actual idle-event 0 after 15 seconds. Thermal policy precedes screen/Wi-Fi main programs.
- Same-new-boot/same-owner observation: 95.31 seconds, peak sample 36.1°C. Parents/RMTFS/TFTP children healthy with no automatic restarts. Systemd running, zero failed units and pending jobs.
- Certificate-verified dual-stack HTTPS, non-USB dual-stack LAN ping/strict host-key SSH and NTP synchronization pass. Independently directly read back all 128 MiB and the image prefix again; both match.
- Eight thermal sets retain passive 40°C, critical 110°C and 2°C/1°C hysteresis. Screen/Wi-Fi keep strict-below-65°C startup/abort-at-65°C runtime guards. Preserve valid new-RF-owner live dirty; probation/power remain inactive.
- This acceptance snapshot has zero physical presses and no new operator visual confirmation. Do not relabel preceding physical/visual evidence as current. This phase directly accepts autostart, native-console metadata and actual startup/idle brightness; existing physical-key code/guards remain unchanged.

Full host suite: **510 tests, 488 passed, 21 skipped, one error**. The sole error remains missing `kernel/power/picasso-pon-reason-audit.ko`, not removed or falsely accepted. Screen autostart passes one additional normal reboot. Regulatory sampling changes/historical link loss, old helper exit leases, abnormal power loss, charging/fuel gauge, self-restart after shutdown and endurance remain unresolved/unqualified. Deliberate RF pre-cleanup does not qualify unattended active-RF shutdown cleanup or power-loss cold start.

Protected evidence under `out/fedora45-boot/screen-autostart/`: `diagnostic.json` (initial LAN timeout/no JSON), `USB-status.json`, `diagnostic-v2.json`, `kmscon-inspection.json`, `selection.json`, `autovt-alias-check.txt`, `select-native-tty1-v1.py`, `selection-v2.json`, `preflight.json`, `pre-reboot-verified.json`, `pre-reboot-verified-v2.json`, `pre-reboot-native-evidence.tar`, `host-command-attempt.json`, `reboot-response.txt`, `first-new-boot.json`, `autostart-converged.json`, `post-reboot-acceptance.json`, `host-LAN-validation.json`, `native-evidence.tar`, targeted test logs and `full-host-tests.log`. Generic phone archive `/var/lib/picasso-fedora45-boot-review/screen-autostart/` also retains both selection-backup directories, static transactions, old regulatory failure, single request and final acceptance; none grants replay.
