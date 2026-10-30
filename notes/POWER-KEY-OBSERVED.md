# 电源键实测：真实按下/松开与长按判定通过，尚未关机（阶段记录） / Power-key measurement: real press/release and long-press classification passed; no shutdown yet (stage record)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

**后续第一次armed已经执行，但4.559807秒/1.682461秒都无效，超时且无关机请求。
原marker已消耗，不重跑本页旧关机命令。独立第二轮增加满2秒实时松开提示，见 [POWER-SHUTDOWN-GUIDED2.md](POWER-SHUTDOWN-GUIDED2.md)。
本页保持真实disarmed成功与准备阶段的原事实；不把后续超时改为成功。**

2026-10-28。用户报告“电源键试验完成”，已核对同一候选启动中的原生记录。

## 已实际通过

| 真实KEY_POWER事件 | 持续时间 | 结果 |
|---|---:|---|
| 第一组down/release | 1.697253秒 | 未触发，短于2秒 |
| 第二组down/release | 2.221647秒 | release时识别为orderly_poweroff候选 |

- 真实`pm8941_pwrkey/event1`，CLOCK_MONOTONIC事件；不是合成按键或离线回放。
- 原生结果`armed_orderly_poweroff=false`、`shutdown_requested=false`，本轮没有请求关机。
- 同一boot ID、候选FDT保持；原生控制台/15秒idle屏幕服务与内核租约仍active。
- 观察器marker已消耗，**不重跑只观察脚本、不删除marker**。
- 完整事件、cooldown与接受记录已复制到手机XFS root0400 `/var/lib/picasso-power/observations-20261028/`，host也独立保存。
- USB权限失败、温控拒绝和脚本错误快照全部保留；观察成功不覆盖此前失败。

这证明电源输入及2..3秒松开判定，不证明系统正常关机、PMIC彻底断电、硬件开机或持久化已通过。

## 下一步会真正关机：只有操作者明确确认才启动

在主机本地交互终端执行：

```sh
cd "${REPO_ROOT}"
tools/test-power-shutdown.sh
```

脚本要求输入 **POWER OFF** 才启动新试验；否则取消。当前未运行此脚本，没有启用任何自动关机服务。
Ctrl-C/中断会尝试终止有同boot/PID起始时间/指定命令行证明的单一等待进程，不扫描或杀其他进程；
这只是best-effort取消，**已提交给PID1的关机请求不能靠取消撤销**，异常时不要反复按电源。

1. 核对同一boot、已保存的真实观察与候选FDT，再等所有传感器低于40°C；45°C拒绝。
2. 新的独占armed实例会提示ready；**然后**按住电源约2秒后松开，不超过3秒。
3. 按键release和关机意图先fsync到XFS，再请求PID1 `systemctl poweroff --no-block`，不是reset或整机休眠。
4. SSH断开不算通过。脚本等待USB消失并静候20秒；若未按键USB却自行返回则停止并报告可能自动重启，不自动重试。
5. USB稳定消失且你确认未自行重启、已关机时，输入OFF。随后按电源约2秒松开，让原PMIC/引导程序开机。
6. 只恢复原手机USB静态地址，严格pin的SSH回连，保存新的boot ID和XFS中的关机请求记录，再由助手核对。

**USB消失也不能单独证明PMIC各电源完全断开**；需结合正常关机请求、未自行重启窗口、人工确认及手动开机的新boot。
不声明充电、无电流、射频静默或长期电源安全；保持USB连接，不改硬件强制复位计时器。

## 暂时启动与持久化边界

当前仍为RAM启动的power候选。正常开机将返回原默认#10（原DTB），因而电源键功能不会自动永久保留。
**没有写boot、DTBO、GPT、vbmeta、NV或更改OEM链。** 完成正常关机/开机验收后，再单独决定已测试镜像持久化。
冷开机后若屏幕起始温度保护拒绝，先保留失败记录并冷却，不提高阈值，不把它当作电源键硬件失败。

## 代码与证据

- `power-shutdown-current.py`：必须同boot真实观察通过、明确确认flag、精确hash；只启动等待新物理按键的armed实例，不在启动时关机。
- `power-key-service.py`：只为armed分支增加XFS持久意图记录；核心输入及hold策略不变。
- `test-power-shutdown.sh`：本地确认、单次请求、USB未自动返回窗口、人工OFF确认、手动开机、原USB恢复；无flash/reboot/reset/suspend命令。
- 刷写/关机/硬件开机尚未执行或验收；下一轮命令仅准备好。
- 离线294项：293通过、1可选QEMU跳过。持久记录/确认门/PID复用取消检查是软件测试，不冒充实际关机。

证据：`out/power-key-observed-20261028/`。冷却拒绝历史见[POWER-KEY-COOLDOWN.md](POWER-KEY-COOLDOWN.md)。

## English

**Follow-up first armed trial ran, but4.559807 seconds/1.682461 seconds were both invalid; it timed out without a shutdown request.
Original marker consumed; do not rerun this page's old shutdown command. The separate second round adds a real-time release prompt at2 seconds; see [POWER-SHUTDOWN-GUIDED2.md](POWER-SHUTDOWN-GUIDED2.md).
This page retains the actual disarmed success and original preparation-stage facts; later timeout is not rewritten as success.**

2026-10-28. The user reported “电源键试验完成” (“power-key trial completed”); native records in the same candidate boot were checked.

### Actually passed

| Real KEY_POWER event | Duration | Result |
|---|---:|---|
| First down/release pair | 1.697253 seconds | No trigger; shorter than2 seconds |
| Second down/release pair | 2.221647 seconds | Recognized as orderly_poweroff candidate on release |

- Actual `pm8941_pwrkey/event1`, CLOCK_MONOTONIC events, not synthetic keys/offline replay.
- Native result `armed_orderly_poweroff=false`, `shutdown_requested=false`; no shutdown requested this round.
- Same boot ID/candidate FDT retained; native console/15-second idle screen service and kernel lease still active.
- Observer marker consumed; **do not rerun observation-only script or delete marker**.
- Full events, cooldown, and acceptance records copied to phone XFS root0400 `/var/lib/picasso-power/observations-20261028/`; host also retains independent copies.
- USB-permission failures, thermal refusals, and script-error snapshots all retained. Observation success does not overwrite earlier failures.

This proves power input and2..3-second release classification, not normal system shutdown, complete PMIC power-off, hardware startup, or persistence acceptance.

### Next step planned then would really shut down: start only after explicit operator confirmation

Local interactive host terminal:

```sh
cd "${REPO_ROOT}"
tools/test-power-shutdown.sh
```

The script requires **POWER OFF** to start a new trial, otherwise it cancels. At this stage it had not run and no automatic shutdown service was enabled.
Ctrl-C/interruption attempts to terminate only one waiting process proven by same boot/PID start time/specified command line; no scanning/killing other processes.
This is best-effort cancellation only; **a shutdown request already submitted to PID1 cannot be undone by cancellation**. Do not repeatedly press power on anomalies.

1. Verify same boot, saved real observation, and candidate FDT, then wait for all sensors below40°C; refuse at45°C.
2. A new exclusive armed instance prompts ready; **then** hold power about2 seconds and release without exceeding3 seconds.
3. fsync key release and shutdown intent to XFS before requesting PID1 `systemctl poweroff --no-block`; not reset or whole-system suspend.
4. SSH disconnect is not a pass. Wait for USB disappearance and20 seconds; if USB returns by itself without a key press, stop and report possible automatic reboot, without automatic retry.
5. If USB remains stably absent and the operator confirms no automatic restart and actual power-off, enter OFF. Then hold power about2 seconds and release, letting the original PMIC/bootloader start the phone.
6. Restore only the original phone USB static address, reconnect with strictly pinned SSH, save new boot ID and XFS shutdown-request record, then have the assistant verify.

**USB disappearance alone does not prove all PMIC rails fully powered off**. Combine normal shutdown request, no-automatic-restart window, human confirmation, and the new manual-start boot.
No claims about charging, zero current, RF silence, or long-term power safety. Keep USB connected; do not change hardware forced-reset timers.

### Temporary boot and persistence boundaries

Still the RAM-booted power candidate at that time. Normal startup returns original default #10/original DTB, so power-key functionality is not automatically permanent.
**No boot, DTBO, GPT, vbmeta, NV writes or OEM-chain changes.** After normal shutdown/startup acceptance, separately decide whether to persist the tested image.
If cold-start screen protection refuses because of starting temperature, retain the failure and cool down rather than raise thresholds or call it power-key hardware failure.

### Code and evidence

- `power-shutdown-current.py`: requires real observation passed in same boot, explicit confirmation flag, and exact hashes; starts only an armed instance waiting for a new physical press, without shutting down on startup.
- `power-key-service.py`: adds XFS durable-intent records only to the armed branch; core input/hold policy unchanged.
- `test-power-shutdown.sh`: local confirmation, single request, USB no-automatic-return window, human OFF confirmation, manual startup, original USB restoration; no flash/reboot/reset/suspend commands.
- Flashing/shutdown/hardware startup had not run or been accepted at this stage; the next command was only prepared.
- 294 offline tests:293 passed,1 optional QEMU skipped. Durable-record/confirmation-gate/PID-reuse cancellation checks are software tests, not actual shutdown acceptance.

Evidence: `out/power-key-observed-20261028/`. Earlier cooling refusal: [POWER-KEY-COOLDOWN.md](POWER-KEY-COOLDOWN.md).
