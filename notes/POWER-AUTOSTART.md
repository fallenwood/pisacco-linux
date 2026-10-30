# 未能保持关机：用户确认自行启动，电源功能持久化阻断 / Failure to remain powered off: user confirms automatic startup; power-function persistence blocked

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

> 本页保留当时失败与阻断决定。后续只读PON采样已获独立许可完成并卸载；用户随后明确接受自动启动限制，另授权受限固化，现已写boot/启用服务但未重启。见[POWER-PERSISTENT.md](POWER-PERSISTENT.md)。**保持关机/手动冷开机仍失败，未被安装结果改写为通过。**

**后续已核对精确#10二进制，比较固定版本参考关机链，并离线构建固定只读PON采样器；未上传/加载，根因仍未证实。
保持本页失败结论，最新准备与授权边界见 [POWER-CHAIN-AUDIT.md](POWER-CHAIN-AUDIT.md)。**

用户在询问“是否再次按电源才开机”后明确回复 **“自行启动的”**。
这结束了此前人工确认pending：**不是手动冷开机通过，而是关机请求后出现非人工启动，原因未证实。**

## 已测事实与未通过项分开

保留且不改写：
- KEY_POWER116真实2.361172秒松开，策略触发正确。
- XFS持久记录证实PID1接受`systemctl poweroff --no-block`；旧journal显示屏幕干净退出、module卸载、systemd-poweroff作业完成。
- USB实际断开，首20秒没有重新枚举，原始`automatic_return_without_power_press=false`保持原样。
- 新boot ID/原默认#10、15,285基线文件、完整boot、七保护分区/六GPT校验通过。
- 第一次armed4.559807秒/1.682461秒超时与最早温控拒绝原样保留。

新增接受结论：
- 用户观察到未再次按电源而自行启动；**“保持关机直到按电源启动”目标未通过**。
- 20秒只是USB未重新枚举的观察窗口，不是持续关机/CPU未启动的证明；无法据此推断实际自动启动时刻。
- systemd作业完成并不证明随后内核最终poweroff handler成功或PMIC各路断电。
- 可能曾短暂掉电后自动启动，也可能最终复位/退出关机失败；当前不能区分，不声称从未断电。
- 默认boot仍原wifi2#10，临时power候选没有写入，没有启用永久电源键关机服务。

## 已做只读检查，未定位根因

当前boot仍`${BOOT_ID_2}`，无第二次循环。
- 标准导出的cmdline/静态FDT chosen bootargs没有所选启动/复位原因键；bootconfig不存在。没有输出整条cmdline或其他标识。
- `/sys/fs/pstore`与`/var/lib/systemd/pstore`均无记录，只列元数据，未读任何payload。
- 标准power_supply列表为空；watchdog0未导出本次查询的identity/bootstatus。不能据此排除供电或watchdog原因。
- 仅过滤旧/新kernel journal的powerdown/reset/PS_HOLD/panic等行，无匹配；不把日志缺失当“内核没执行poweroff”的证明。
- 原生屏幕内核租约健康；Wi-Fi仍沿用disabled状态。只读检查起始全部传感器低于40°C。

源码意图（不是实际寄存器结果）：
- `pm8941-pwrkey.c`的reboot notifier在SYS_POWER_OFF意图设置PS_HOLD shutdown type4。
- `msm-poweroff.c`意图拉低SoC PS_HOLD，若返回会延迟10秒；PSCI源码还包含SYSTEM_OFF旧回调。
- 哪个最终handler实际走到、SPMI写入是否成功、固件/USB供电是否触发下一次启动，现有证据都不足。
- `qcom-pon.c`主要处理reboot-mode，并不是一个能从现有sysfs证明本次上电原因的接口。

**USB供电/充电引导、PS_HOLD/PON配置或最终执行、固件/复位路径都是未证实候选，不选一个当结论。**
下一步应先设计最终关机/启动原因的证据方案，而不是放宽2..3秒长按窗口。

## 安全门

停止电源候选持久化与任何“关机开机已通过”的结论；不要重跑已消费试验、清marker、再次关机或刷写。
本阶段没有增加RAM boot/重启/flash/suspend/按键注入，没有改S1/S2/S3、reboot magic、充电设置。
没有raw PMIC/MMIO、SMEM/NV/凭据读取，也没有新模块加载；不要求拔USB或保持电源键更久。
如后续需要新的硬件试验，另行明确范围、记录与操作者确认，当前不自动启动。

证据：`out/power-autostart-20261028/`；前阶段[POWER-CYCLE-POSTBOOT.md](POWER-CYCLE-POSTBOOT.md)保持为当时的待确认快照。

## English

> This page preserves the failure and blocking decision at that time. Follow-up read-only PON sampling received separate permission, completed, and unloaded. The user later explicitly accepted the automatic-startup limitation and separately authorized restricted persistence; boot was written/services enabled without reboot. See [POWER-PERSISTENT.md](POWER-PERSISTENT.md). **Remaining powered off/manual cold-start still failed; installation results do not rewrite them as passed.**

**Follow-up checked the exact #10 binary, compared the pinned reference shutdown chain, and built a fixed read-only PON sampler offline; it had not been uploaded/loaded at that point, and the root cause remained unproven.
The failure conclusion on this page remains. Latest preparation/authorization boundaries: [POWER-CHAIN-AUDIT.md](POWER-CHAIN-AUDIT.md).**

When asked whether another power-key press had been required to start, the user explicitly replied **“自行启动的”** (“It started by itself”).
This ended the earlier pending human confirmation: **manual cold-start did not pass; non-manual startup followed the shutdown request, with the cause unproven.**

### Measured facts separated from failed acceptance

Preserved without rewriting:
- Real KEY_POWER116 release after2.361172 seconds; policy trigger correct.
- XFS durable record proves PID1 accepted `systemctl poweroff --no-block`; old journal shows clean screen exit, module unload, and completed systemd-poweroff job.
- USB actually disconnected, with no re-enumeration for the first20 seconds; original `automatic_return_without_power_press=false` remains unchanged.
- New boot ID/original default #10,15,285 baseline files, full boot, seven protected partitions/six GPTs passed verification.
- First armed4.559807-second/1.682461-second timeout and earliest thermal refusal retained unchanged.

New acceptance conclusions:
- The user observed automatic startup without pressing power again; **“remain off until power is pressed” failed**.
- The20 seconds are a USB non-re-enumeration observation window, not proof of sustained power-off/no CPU startup. Actual automatic-startup time cannot be inferred from it.
- A completed systemd job does not prove the subsequent final kernel poweroff handler succeeded or all PMIC rails powered down.
- There may have been brief power loss followed by automatic startup, or a final reset/failure to complete shutdown. Existing evidence cannot distinguish these; no claim is made that power never dropped.
- Default boot remained original wifi2#10; the temporary power candidate had not been written and no permanent power-key shutdown service enabled.

### Read-only checks completed without locating the root cause

Current boot still `${BOOT_ID_2}`; no second cycle.
- Standard exported cmdline/static FDT chosen bootargs contain no selected boot/reset-reason keys; bootconfig absent. Full cmdline and other identifiers were not output.
- `/sys/fs/pstore` and `/var/lib/systemd/pstore` contain no records; only metadata listed, no payload read.
- Standard power_supply list empty; watchdog0 did not export the queried identity/bootstatus. This does not rule out power or watchdog causes.
- Only powerdown/reset/PS_HOLD/panic and similar lines were filtered from old/new kernel journals; no matches. Missing logs do not prove “kernel never executed poweroff.”
- Native screen kernel lease healthy; Wi-Fi remained disabled. All sensors were below40°C at the start of read-only checks.

Source intent, not actual register results:
- `pm8941-pwrkey.c` reboot notifier intends to set PS_HOLD shutdown type4 for SYS_POWER_OFF.
- `msm-poweroff.c` intends to lower SoC PS_HOLD and delay10 seconds if it returns; PSCI source also includes a legacy SYSTEM_OFF callback.
- Evidence is insufficient to establish which final handler ran, whether SPMI writes succeeded, or whether firmware/USB power triggered the next startup.
- `qcom-pon.c` mainly handles reboot-mode; it is not an interface that proves this startup reason through existing sysfs.

**USB power/charging boot, PS_HOLD/PON configuration or final execution, and firmware/reset paths are all unproven candidates. None is selected as the conclusion.**
The next step should design evidence for final shutdown/startup causes, rather than relax the2..3-second hold window.

### Safety gate

At this stage power-candidate persistence and any “shutdown/startup passed” conclusion were stopped. Do not rerun consumed trials, clear markers, shut down again, or flash.
This stage added no RAM boot/reboot/flash/suspend/key injection and changed no S1/S2/S3, reboot magic, or charging setting.
No raw PMIC/MMIO, SMEM/NV/credential reads, or new module loads. No request to unplug USB or hold power longer.
Any subsequent hardware trial requires a separately explicit scope, records, and operator confirmation; it is not started automatically.

Evidence: `out/power-autostart-20261028/`; preceding [POWER-CYCLE-POSTBOOT.md](POWER-CYCLE-POSTBOOT.md) remains the pending-confirmation snapshot from that time.
