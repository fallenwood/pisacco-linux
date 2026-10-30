# 第一次armed超时：未关机；第二轮增加实时松开提示（阶段记录） / First armed trial timed out without shutdown; second round adds a real-time release prompt (stage record)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

**后续第二轮实际已运行：真实2.361172秒松开触发候选，SSH退出0，USB断开且20秒无自动返回。
当前USB已重新出现但主机静态IPv4缺失，新boot ID/FDT/持久关机记录尚未读回；不要重跑本页旧试验。
仅恢复原USB地址后继续核验，最新见 [POWER-CYCLE-REVIEW.md](POWER-CYCLE-REVIEW.md)。完整关机/硬件开机验收仍pending。**

2026-10-28阶段记录。当前仍为同一power-key RAM候选启动，boot未写入。

## 第一轮真实结果：失败记录保留

原`test-power-shutdown.sh`实际运行过，原生结果为
`observer_timed_out_no_valid_long_release`：

| 按压 | 原生持续时间 | 判定 |
|---|---:|---|
| 第一组down/release | 4.559807秒 | 超过3秒上限，拒绝 |
| 第二组down/release | 1.682461秒 | 不足2秒，拒绝 |

- 两组均无policy_action，`shutdown_requested=false`，USB没有消失；不是关机后重启。
- boot ID仍`${BOOT_ID_3}`，系统和原生tty1/15秒idle屏幕服务仍运行。
- 不把4.56秒当成合格关机长按，更不建议持键更久；没有改硬件强制复位计时器。
- `/run/picasso-power-armed/observer-consumed`、原launch与结果保留，不删除、不重跑。
- 原生失败与durable记录另复制至`/var/lib/picasso-power/failed-primary-20261028/`，root0400；host第一轮三份回执也独立归档。

先前disarmed的2.221647秒真实长按判定成功仍成立；它不能代替本轮实际关机验收。

## 独立第二轮（已准备，未运行）

主机本地交互终端：

```sh
cd "${REPO_ROOT}"
tools/test-power-shutdown-guided2.sh
```

输入 **POWER OFF**，等ready后按下电源。
**按住直到主机终端提示/响铃“已满2秒：现在立即松开电源键！”，立即松开。不要超过3秒。**
提示来自实际按下事件的CLOCK_MONOTONIC时间；不模拟按键、不提前发关机请求。
如果提示已经超过3秒，就立即松开，该次无效，勿继续长按。
普通Linux调度/USB/终端延迟不是硬实时保证；提示并不改变2..3秒release-only策略。

后续由脚本检查USB消失及20秒内无自动返回，再要求人工OFF确认，之后提示手动开机。
未按键USB却自行返回则停止，不把自动重启/自动开机当正常关机通过。
如果第二轮再次超时且确认没有候选/请求，立即保存结果停止，不再无谓等待USB、更不循环重试。

## 独立资源与不变边界

- 新controller：`power-key-guided2.py`，只新增按住提示、独立日志槽及运行期无效温度拒绝，原hold-policy文件hash不变。
- 新wrapper：`power-shutdown-guided2.py`，要求同boot的真实disarmed成功，且第一轮原生与XFS均明确timeout/no request，精确hash后才等待新真实按键。
- 运行目录`/run/picasso-power-armed-guided2/`；新持久文件`<boot>-guided2.json`及`launch-guided2-<boot>.json`，不覆盖第一轮。
- 中断取消只尝试终止guided2的同boot/同PID起始时间/指定命令进程。不能撤销已提交给PID1的请求。
- 全传感器起始严格低于40°C，45°C中止，不提高阈值；无休眠、raw reset、boot/DTBO/GPT/vbmeta/NV写入。
- 唯一关机动作仍是实际2..3秒release后`systemctl poweroff --no-block`，之前先fsync真实事件和意图。
- USB消失不等于已证明PMIC各路断电；正常关机及原硬件冷启动仍需单独验收，尚未宣称通过。
- 正常手动开机将返回原默认#10 DTB，power功能还没有持久化；不重复RAM boot或刷写。

离线303项：302通过、1可选QEMU跳过。软件提示/路径分离测试不冒充物理关机。

证据：`out/power-shutdown-guided2-20261028/`；第二轮实际运行将另存`out/power-shutdown-trial-guided2-20261028/`。
历史真实观察见[POWER-KEY-OBSERVED.md](POWER-KEY-OBSERVED.md)。

## English

**Follow-up second round actually ran: a real2.361172-second release triggered the candidate, SSH exited0, USB disconnected with no automatic return for20 seconds.
USB reappeared but host static IPv4 was missing; new boot ID/FDT/durable shutdown records had not yet been read back at that point. Do not rerun this page's old trial.
Only restore original USB address and continue checks; latest: [POWER-CYCLE-REVIEW.md](POWER-CYCLE-REVIEW.md). Complete shutdown/hardware-startup acceptance remained pending.**

2026-10-28 stage record. At this stage it was still the same power-key RAM-candidate boot, with boot not written.

### First round real results: failure records retained

Original `test-power-shutdown.sh` actually ran; native result:
`observer_timed_out_no_valid_long_release`.

| Press | Native duration | Classification |
|---|---:|---|
| First down/release pair | 4.559807 seconds | Exceeded3-second upper bound, rejected |
| Second down/release pair | 1.682461 seconds | Shorter than2 seconds, rejected |

- Neither pair produced policy_action; `shutdown_requested=false`, USB did not disappear. This was not reboot after shutdown.
- Boot ID still `${BOOT_ID_3}`; system and native tty1/15-second idle screen service still running.
- 4.56 seconds is not an acceptable shutdown long-press, and holding longer is not recommended. Hardware forced-reset timers unchanged.
- `/run/picasso-power-armed/observer-consumed`, original launch, and results retained without deletion/rerun.
- Native failure/durable records additionally copied to `/var/lib/picasso-power/failed-primary-20261028/`, root0400; three host first-round receipts also independently archived.

Earlier disarmed real2.221647-second long-press classification success remains valid, but cannot replace actual shutdown acceptance in this round.

### Separate second round (prepared, not run at that stage)

Local interactive host terminal:

```sh
cd "${REPO_ROOT}"
tools/test-power-shutdown-guided2.sh
```

Enter **POWER OFF**, wait for ready, then press power.
**Hold until the host terminal prompts/rings “已满2秒：现在立即松开电源键！” (“2 seconds reached: release the power key immediately!”), then release immediately. Do not exceed3 seconds.**
The prompt comes from the actual press event's CLOCK_MONOTONIC time; no simulated key or premature shutdown request.
If the prompt is already beyond3 seconds, release immediately; that attempt is invalid, so do not keep holding.
Ordinary Linux scheduling/USB/terminal delays are not hard-real-time guarantees; the prompt does not change the2..3-second release-only policy.

The script then checks USB disappearance/no automatic return within20 seconds, requires human OFF confirmation, and prompts manual startup.
If USB returns on its own without a key press, stop; automatic reboot/startup is not a normal-shutdown pass.
If the second round times out again and no candidate/request is confirmed, save results immediately and stop; do not pointlessly wait for USB or retry in a loop.

### Separate resources and unchanged boundaries

- New controller `power-key-guided2.py`: adds only hold prompt, separate log slot, and runtime invalid-temperature rejection; original hold-policy file hash unchanged.
- New wrapper `power-shutdown-guided2.py`: requires real disarmed success in the same boot and explicit first-round timeout/no request in both native and XFS records; only waits for a new real key after exact hash checks.
- Runtime directory `/run/picasso-power-armed-guided2/`; new durable files `<boot>-guided2.json` and `launch-guided2-<boot>.json`, without overwriting first round.
- Interruption cancellation only attempts to terminate the guided2 process with same boot/same PID start time/specified command. Requests submitted to PID1 cannot be revoked.
- All sensors strictly below40°C at start; abort45°C without raising thresholds. No suspend, raw reset, boot/DTBO/GPT/vbmeta/NV writes.
- Sole shutdown action remains `systemctl poweroff --no-block` after actual2..3-second release, preceded by fsync of real event/intent.
- USB disappearance does not prove all PMIC rails powered down; normal shutdown/original hardware cold-start require separate acceptance and were not claimed passed.
- Normal manual startup returns original default #10 DTB; power function had not been persisted. No repeated RAM boot or flash.

303 offline tests:302 passed,1 optional QEMU skipped. Software prompt/path-separation tests are not physical shutdown acceptance.

Evidence: `out/power-shutdown-guided2-20261028/`; second-round actual execution would be saved separately in `out/power-shutdown-trial-guided2-20261028/`.
Historical real observation: [POWER-KEY-OBSERVED.md](POWER-KEY-OBSERVED.md).
