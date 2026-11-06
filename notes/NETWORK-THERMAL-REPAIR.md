# 局域网恢复与 CPU 提前降温 / LAN Recovery and Early CPU Cooling

> 路径 / Paths: 代码、测试及 `out/` 证据路径相对于仓库根目录；同级笔记链接相对于
> `notes/`。私有地址、网络名、账号、启动/会话标识和私有摘要不公开。
> Code, test and `out/` evidence paths are repository-root-relative; peer-note
> links are relative to `notes/`. Private addresses, network names, accounts,
> boot/session identifiers and private digests are withheld.

后续 / Later: 用户随后明确把 Wi-Fi/屏幕的运行中止与启动门槛都提高到 65°C，
已部署并取得新原生证明；40°C 提前降频保持不变，见
[65°C 软件门槛](THERMAL-LIMIT-65.md)。下文的 45°C/40°C 软件门槛是本阶段历史快照，
不是后续当前策略。 / The operator later explicitly raised Wi-Fi/screen runtime and
startup software limits to 65°C, deployed with a fresh native proof; passive
cooling remains 40°C. See [65°C software limits](THERMAL-LIMIT-65.md). The software
45°C/40°C values below are this stage's historical snapshot, not the later policy.

## 中文

### 2026-11-06 授权与诊断

用户先要求通过 USB 查询局域网 ping 不通的原因，随后要求修复此问题以及
“手机过热自动关机”。日期采用主机 UTC；手机墙钟不一致，原生持续时间采用
同一启动的单调时钟。本页是本次操作快照，不是实时健康报告或再次操作授权。
此前状态保留在[固定 CN](WIFI-FIXED-CN.md)和
[Wi-Fi 切换恢复](WIFI-SWITCH-RECOVERY.md)。

严格主机密钥 USB SSH 确认内核为 `7.3.1-picasso-wifi2`。主机 USB 网卡最初没有
IPv4；仅临时添加直连地址用于查询，未改变主机 Wi-Fi、默认路由、DNS、NAT 或
持久 profile。手机没有 `wlan0`、LAN 地址或 Wi-Fi 默认路由，开机启用的
`picasso-wifi-autoconnect-cn-7.3.1.service` 在约启动 12 秒时失败：

```text
RuntimeError: Unclean NV lifecycle; operator review required
```

`/var/lib/picasso-wifi/dirty.json` 属于旧启动。对应会话有 `radio-ready.json`，
没有最终 `result.json` 或 `cleanup.json`；一个普通工作文件偏离干净 checkpoint。
本次失败的清理记录是 `dsp=not_started`，不能据此接受上次未收尾的工作状态。
这解释了 LAN 不可达，而不是 ICMP 过滤：`icmp_echo_ignore_all=0`，
`drop` 区域实际 target 为 `ACCEPT`，没有 echo-request 阻止规则。
未修改[防火墙开放策略](FIREWALL-OPEN.md)。

没有找到能证明本次症状由整机临界温度关机引起的记录，pstore 为空。
旧无线会话为何未收尾仍不能确定为强制复位、掉电、内核或固件故障。
项目 Wi-Fi/屏幕在 45°C 保护退出不是整机 poweroff 的证据；黑屏或失去 LAN
也不能单独证明关机。本轮未读取 PON/PMIC 寄存器来推断原因。

### 普通工作副本恢复

先核验已有普通只读备份的来源 manifest、摘要及 root/0400/单链接/8 MiB 元数据，
以及工作文件的 root/0600/单链接属性。保留三个现有工作文件、checkpoint 和精确
旧 dirty。在同一已核对启动、低于 40°C、所有 RF 所有者停止、DSP/WLAN 不存在、
相关模块未加载且无工作/共享 RAM 打开描述符时，才恢复普通工作文件。

仅从已有普通备份原子替换三个工作文件，保留扩展属性，逐一读回核验；提交新
checkpoint 后，才把精确旧 dirty 移入受保护归档。没有把变化副本直接登记为干净，
没有访问原始 NV 分区、改变只读备份、读取或导出凭据、关闭生命周期保护，
也没有加入自动恢复 dirty 的逻辑。归档是证据，不是可盲目重放的恢复授权。

### 提前降温和频率兼容修复

实际八个 CPU 温区的内核 `step_wise` 已启用并映射到三个 cpufreq cooling device，
但被动 trip 为 90°C，远高于项目的 45°C 退出线。新
`tools/thermal-policy.py` 和 `tools/picasso-thermal-policy.service` 在原生 7.3.1
上校验全部温区、类型、governor、阈值及 cooling 映射，再把被动 trip 降至
**40°C，保持 2°C hysteresis**。临界 trip **110°C、1°C hysteresis** 不变。
没有禁用温控、提高保护线，或修改电压、RF 功率和充电设置。

此服务为有界 oneshot、开机启用，先于当前 Wi-Fi、probation 和屏幕服务；
后者均要求它成功。内核执行后续被动调频，不依赖持续运行的 Python 温控循环。
部分写入失败时保留已降低的阈值并失败，拒绝依赖服务启动，不能自动回升到
90°C 隐藏错误。运行时 trip 修改是易失的，持久 systemd 服务负责下次重新设置；
本轮没有重启验证这一启动顺序。

`tools/wifi-auto-service.py` 和 `tools/wifi-radio-service.py` 以前要求有效上限精确
等于 1,094,400 kHz，会把内核进一步降频误判成故障。现在仍拒绝超过此上限，
但允许硬件频率表内、不低于有效最小值的更低上限。启动核验硬件最大频率，
退出恢复原用户上限时同样接受更严格的内核 thermal QoS。45°C 中止、40°C 以下
启动、租约/watchdog、独立清理、监管域和 NV 守卫都保留。

更新了精确源码 pin 链、三个工作配置、自动连接策略、运行时 manifest 和激活策略。
`tools/prepare-kernel-runtime.py` 为以后离线生成的 7.3.1 bundle 加入同样的温控
资产与依赖；不是重建或替换内核。旧运行时和旧原生证明均已保留。
仅启用 probation，真实新证明通过后才允许持续 Wi-Fi；未重签或复用旧会话证明。
6.18 救援运行时、固件、BDF、regdb、NM profiles 和 firewall 规则没有替换。

### 验收与未验证边界

- 新原生 **45 秒 probation** 通过关联、DHCP、DNS、证书 HTTPS 200 和完整 CN
  审计；峰值 **34.1°C**。独立清理确认 DSP offline、WLAN 不存在、子进程停止、
  2,621,440 字节共享 RAM 清零、core/CPU 恢复、checkpoint 与工作文件一致且 dirty
  不存在。清理中对未激活 profile 的 nmcli down 返回码 10 保留在记录中，不被改写
  为全部子命令成功；独立检查确认必要的安全收尾条件均通过。
- 根据该真实结果和新 manifest 生成新证明，启用持续服务，保留开机启用和
  `Restart=no`。新的有效 live dirty 属于当前 RF 所有者，**不能删除**。
- 在低于 38°C 的门槛下，一次有界冷却接口试验只降低 CPU6/7 的有效上限，
  观察到 **652,800 / 806,400 kHz**，同一个 Wi-Fi PID/会话保持 active、零重启；
  随后移除本次临时冷却请求，恢复 Wi-Fi 的 1,094,400 kHz 上限。没有加热压力、
  提高温度阈值或制造临界关机；这验证了更严格频率上限的兼容，不是过热压力验收。
- 非 USB LAN 的 IPv4/IPv6 ping 与严格主机密钥 IPv4/IPv6 LAN SSH 均通过。
  首选 5 GHz 此次已关联并联网，观察到 5200 MHz；不能据此宣布历史首次连接超时、
  AP reason-3 断开、长期掉线或所有 5 GHz 问题已解决。
- 同一启动、同一 RF PID/会话持续观察 **1,206.32 秒、238 个样本**，零重启，
  观察和 worker 峰值均为 **36.4°C**。五组 IPv4/IPv6 直连、绑定 wlan0、无代理且
  验证证书的 HTTPS 探测全部返回 200，结束后独立复核仍通过。自然温度没有达到
  40°C；这不是实际温度越线或整机过热关机验收。
- 主机 Wi-Fi 回归 178 项（176 通过、2 项跳过）、温控 6 项及运行时 14 项通过。
  全套 484 项：462 通过、21 跳过、1 错误；错误由未生成的
  `kernel/power/picasso-pon-reason-audit.ko` 导致文件缺失。没有为掩盖此错误而
  跳过测试或读取 PMIC。完整统计见测试日志。

首次启动观察器时，主机命令在 35 秒超时：`systemd-run` 未使用 `--no-block`，
会等待 oneshot 的整段观察完成。后续只读 LAN SSH 确认原生观察器仍在运行、RF
所有者未改变，不是无线故障。被外部超时中断的 shell 遗留的主机临时 USB 地址已
明确移除，没有重复启动观察器或 RF。该工具失败与证据保留。

本轮没有刷写、重启/关机、kexec、休眠、PMIC/PON 操作或 Podman 修改。
没有新增冷启动、充电/电池遥测、整机散热安全或长期稳定性验收，也没有证明用户
所述整机自动关机的底层原因已修复。需要正常重启时先通过 USB 正常停止当前 Wi-Fi
所有者，核验 checkpoint 提交、DSP/WLAN 退出且 dirty 消失；清理失败就先诊断，
不能强删标记继续。异常掉电后仍可能需要独立审阅恢复。

### 只读复核

以下仅查询当前配置，不启动 RF、重载策略或修改 trip：

```sh
sudo systemctl show picasso-thermal-policy.service -p ActiveState -p Result
sudo systemctl show picasso-wifi-autoconnect-cn-7.3.1.service -p ActiveState -p Result -p NRestarts
sudo python3 -I /opt/picasso-kernel-7.3.1/picasso-thermal/thermal-policy.py
```

## English

### 2026-11-06 authorization and diagnosis

The operator first requested USB investigation of failed LAN ping, then requested
repair of both connectivity and “phone overheating and automatically shutting
down.” The date uses host UTC; phone wall time disagrees, so native durations use
same-boot monotonic time. This is an operation snapshot, not live health or another
operation grant. Earlier records remain in [fixed CN](WIFI-FIXED-CN.md) and
[Wi-Fi switch recovery](WIFI-SWITCH-RECOVERY.md).

Strict-pinned USB SSH confirmed `7.3.1-picasso-wifi2`. The host USB interface
initially lacked IPv4; only a temporary direct address was added for queries,
without host Wi-Fi, default-route, DNS, NAT or persistent-profile changes. The
phone had no `wlan0`, LAN address or Wi-Fi default route. Boot-enabled
`picasso-wifi-autoconnect-cn-7.3.1.service` failed around 12 seconds after boot:

```text
RuntimeError: Unclean NV lifecycle; operator review required
```

`/var/lib/picasso-wifi/dirty.json` belonged to an earlier boot. That session had
`radio-ready.json` but no final `result.json` or `cleanup.json`; one ordinary work
file differed from the clean checkpoint. The failed current startup's cleanup
record said `dsp=not_started`, not acceptance of the preceding unclean state.
This explains LAN failure, not ICMP filtering: `icmp_echo_ignore_all=0`, actual
`drop` target `ACCEPT`, and no echo-request block. The
[open firewall policy](FIREWALL-OPEN.md) was not changed.

No record established critical-temperature whole-phone shutdown as the cause;
pstore was empty. Why the old session lacked cleanup remains unproven: forced
reset, power loss, kernel and firmware faults are not distinguished. A project
Wi-Fi/screen exit at 45°C is not system poweroff evidence; black screen or lost
LAN alone does not establish shutdown. No PON/PMIC registers were read to infer it.

### Ordinary work-copy recovery

Verify existing ordinary read-only backup provenance manifest, digests and
root/0400/single-link/8 MiB metadata, plus root/0600/single-link work files. Preserve
all three current work files, checkpoint and exact old dirty marker. Restore only
on the verified same boot, below 40°C, with all RF owners stopped, absent DSP/WLAN,
related modules unloaded and no work/shared-RAM file descriptors open.

Atomically replace only the ordinary work files from existing ordinary backups,
preserving xattrs and verifying each readback. Commit a new checkpoint before
moving the exact old dirty marker into a protected archive. Changed work was not
simply declared clean. No raw NV partitions, read-only backup changes, credential
retrieval/export, disabled lifecycle guard or automatic dirty-recovery logic.
Archives preserve evidence, not blind replay authorization.

### Early cooling and frequency compatibility

All eight CPU zones already had enabled kernel `step_wise` and mappings to three
cpufreq cooling devices, but passive trips were 90°C, far above the project's
45°C exit line. New `tools/thermal-policy.py` and
`tools/picasso-thermal-policy.service` validate all zones, types, governor, trips
and cooling mappings on native 7.3.1 before lowering passive trips to **40°C,
retaining 2°C hysteresis**. Critical trips remain **110°C with 1°C hysteresis**.
No thermal disabling, raised protection limits, voltage, RF-power or charging
changes occurred.

This bounded, boot-enabled oneshot precedes current Wi-Fi, probation and screen
services, which require its success. The kernel performs subsequent passive
frequency control without a persistent Python cooling loop. Partial failure
leaves already lowered trips in place and fails dependent startup rather than
silently rolling temperatures upward to 90°C. Runtime trips are volatile; the
persistent systemd service reapplies them at the next boot. That new boot order
was not reboot-tested in this operation.

`tools/wifi-auto-service.py` and `tools/wifi-radio-service.py` previously demanded
an effective maximum of exactly 1,094,400 kHz, mistaking further kernel cooling
for failure. They still reject higher limits, but permit lower hardware-table
frequencies at or above the effective minimum. Startup verifies hardware maximum
frequency; restoring the original user maximum also accepts stricter kernel
thermal QoS. The 45°C abort, below-40°C startup, leases/watchdog, independent
cleanup, regulatory and NV guards remain.

Update exact source pins, three worker configurations, autoconnect policy, runtime
manifest and activation policy. `tools/prepare-kernel-runtime.py` includes the same
cooling assets/dependencies in future offline 7.3.1 bundles; this is not a kernel
rebuild/replacement. Preserve the old runtime and native proof. Enable probation
only, and permit continuous Wi-Fi only after a genuine new native proof; no
rebinding/reuse of another session's proof. The 6.18 rescue runtime, firmware, BDF,
regdb, NM profiles and firewall rules were not replaced.

### Acceptance and unverified boundaries

- New native **45-second probation** passed association, DHCP, DNS,
  certificate-verified HTTPS 200 and full CN audit, peaking at **34.1°C**.
  Independent cleanup verified DSP offline, absent WLAN, stopped children,
  2,621,440 bytes of cleared shared RAM, restored core/CPU, matching work/checkpoint
  and absent dirty. nmcli down return code 10 for inactive profiles remains in the
  cleanup record, not rewritten as every subcommand succeeding; independent checks
  confirmed all required safe finalization conditions.
- Derive a new proof from that actual result and new manifest, then enable
  continuous operation, retaining boot enablement and `Restart=no`. Its valid live
  dirty belongs to the current RF owner and **must not be deleted**.
- A bounded cooling-interface test, gated below 38°C, only lowered CPU6/7 effective
  maxima. **652,800 / 806,400 kHz** were observed with the same active Wi-Fi
  PID/session and zero restarts. Remove this temporary cooling request afterward,
  returning to Wi-Fi's 1,094,400 kHz ceiling. No heating stress, raised thermal
  thresholds or critical shutdown was manufactured. This validates stricter-cap
  compatibility, not overheating stress qualification.
- Non-USB LAN IPv4/IPv6 ping and strict-pinned IPv4/IPv6 LAN SSH passed. Preferred 5 GHz
  associated and carried traffic this time, observed at 5200 MHz. This does not
  resolve historical initial timeouts, AP reason-3 disconnections, long-term link
  loss or every 5 GHz issue.
- Same-boot, same-RF-PID/session observation passed **1,206.32 seconds and 238
  samples**, with zero restarts. Both observation and worker peaked at **36.4°C**.
  Five sets of IPv4/IPv6 direct, wlan0-bound, no-proxy, certificate-verified HTTPS
  probes all returned 200; independent final checks passed again. Natural
  temperature did not reach 40°C: this is not an actual trip-crossing or
  whole-phone overheating-shutdown qualification.
- Host Wi-Fi regression: 178 tests (176 passed, two skipped), plus six thermal and
  14 runtime tests passed. Full suite: 484 tests, 462 passed, 21 skipped and one
  missing-file error for ungenerated `kernel/power/picasso-pon-reason-audit.ko`.
  No test was skipped to hide it, and no PMIC read was performed. Full counts are
  in the logs.

The first observer launch's host command timed out after 35 seconds: without
`--no-block`, `systemd-run` waits for the entire oneshot observation. Subsequent
read-only LAN SSH confirmed the native observer still running and unchanged RF
owner; this was not wireless failure. Explicitly remove the temporary host USB
address left by the externally interrupted shell. No observer/RF launch replay
occurred. This tooling failure and evidence are retained.

No flashing, reboot/poweroff, kexec, suspend, PMIC/PON or Podman operations occurred.
There is no new cold-start, charging/battery-telemetry, whole-device thermal-safety
or endurance qualification, nor proof that the underlying reported whole-device
automatic shutdown was fixed. Before a required normal reboot, stop the current
Wi-Fi owner normally over USB and verify committed checkpoint, DSP/WLAN exit and
absent dirty. Diagnose failed cleanup rather than force-removing markers.
Unexpected power loss can still require separately reviewed recovery.

### Read-only verification

These inspect current configuration without starting RF, reloading policy or
changing trips:

```sh
sudo systemctl show picasso-thermal-policy.service -p ActiveState -p Result
sudo systemctl show picasso-wifi-autoconnect-cn-7.3.1.service -p ActiveState -p Result -p NRestarts
sudo python3 -I /opt/picasso-kernel-7.3.1/picasso-thermal/thermal-policy.py
```

## 证据 / Evidence

以下均为被忽略的受保护本地产物，包含未公开的网络/设备标识及私有摘要；新克隆不
保证存在。普通 NV 内容没有导出到主机。 / These are ignored, protected local artifacts
containing withheld network/device identifiers and private digests; fresh clones
may lack them. Ordinary NV contents were not exported to the host.

入口目录 / Entry directory: `out/network-thermal-repair/`.

| 路径 / Path | 内容 / Contents |
| --- | --- |
| `diagnosis.txt`, `preflight.json` | 原生诊断及普通文件恢复前核验 / Native diagnosis and ordinary-file recovery preflight |
| `recover-work.py`, `recovery-result.json` | 单次受审阅恢复及手机私有归档入口 / Single reviewed recovery and phone-private archive entry |
| `runtime-before.tar`, `snapshot/` | 原运行时、manifest、策略及旧证明 / Original runtime, manifest, policies and old proof |
| `stage-runtime.py`, `deploy-plan.json`, `staged/` | 精确普通文件变更和 pin 绑定 / Exact ordinary-file changes and pin bindings |
| `deploy-runtime.py`, `deploy-result.txt` | 部署、原生只读核验和提前降温生效 / Deployment, native read-only checks and early cooling activation |
| `probation-result.jsonl`, `continuous-start.json` | 新 45 秒证明、独立清理和持续运行启用 / New 45-second proof, independent cleanup and continuous activation |
| `native-lower-cap-test.json` | 无加热的原生更低频率兼容试验 / Native lower-cap compatibility test without heating |
| `observation-launch-timeout.json`, `lan-health-first.json` | 启动工具超时及原生观察仍在进行的复核 / Launch-tool timeout and confirmation the native observation continued |
| `final-native.json`, `native-evidence.tar`, `lan-ipv6-ssh.txt`, `final-host-network.txt` | 最终原生汇总、原生逐样本证据和非 USB LAN/主机清理复核 / Final native summary, native sample evidence and non-USB LAN/host cleanup checks |
| `wifi-tests.log`, `thermal-tests.log`, `runtime-tests.log`, `all-tests.log`, `all-tests-final.log` | 主机回归和保留的全套检查错误 / Host regressions and retained full-suite error |

手机原生会话历史及下载的 `native-evidence.tar` 还保存本轮 probation、持续启动、
降频试验、逐样本观察与最终结果；没有覆盖初始失败或中间快照。 / Native phone
session history and downloaded `native-evidence.tar` retain probation, continuous
start, lower-cap test, observation samples and final result, without overwriting
initial failures or intermediate snapshots.
