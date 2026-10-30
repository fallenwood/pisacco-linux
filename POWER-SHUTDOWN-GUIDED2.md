# 第一次armed超时：未关机；第二轮增加实时松开提示（阶段记录）

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
- boot ID仍`279ae843-fcc4-4cfe-a49b-4ff754fd91ef`，系统和原生tty1/15秒idle屏幕服务仍运行。
- 不把4.56秒当成合格关机长按，更不建议持键更久；没有改硬件强制复位计时器。
- `/run/picasso-power-armed/observer-consumed`、原launch与结果保留，不删除、不重跑。
- 原生失败与durable记录另复制至`/var/lib/picasso-power/failed-primary-20261028/`，root0400；host第一轮三份回执也独立归档。

先前disarmed的2.221647秒真实长按判定成功仍成立；它不能代替本轮实际关机验收。

## 独立第二轮（已准备，未运行）

主机本地交互终端：

```sh
cd /home/vbox/droid
./picasso/tools/test-power-shutdown-guided2.sh
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
