# 65°C 软件启动与运行门槛 / 65°C Software Startup and Runtime Limits

> 本页是 2026-11-06 主机 UTC 日期下的新授权快照，不是实时健康报告或再次操作授权。
> 手机墙钟不同，运行时间采用同一启动的单调时钟。代码及 `out/` 路径相对于仓库根目录，
> 同级文档链接相对于 `notes/`。私有网络、账号、启动/会话标识及摘要不公开。
> This is a newly authorized snapshot dated 2026-11-06 by host UTC, not live health
> or another operation grant. Phone wall time differs; durations use same-boot
> monotonic time. Code and `out/` paths are repository-root-relative; peer links
> are relative to `notes/`. Private networks, accounts, boot/session IDs and
> digests are withheld.

## 中文

### 授权与当前范围

在[局域网恢复与提前降温](NETWORK-THERMAL-REPAIR.md)之后，用户先明确要求
“提高阈值到65度”，再要求“启动门槛也提升到65度”。本次把当前原生
`7.3.1-picasso-wifi2` 的 Wi-Fi、屏幕运行软件中止线，以及这两个服务使用的
启动检查和三样本等待器，统一设为 **65,000 毫摄氏度**：

| 策略 | 本次结果 |
| --- | --- |
| Wi-Fi、屏幕启动 | 所有有效 CPU 传感器严格低于 65°C；65°C 即拒绝 |
| 启动等待器 | 三次连续样本严格低于 65°C；高温重置计数，300 秒仍未满足则失败 |
| Wi-Fi、屏幕运行 | 最热有效 CPU 传感器达到或超过 65°C 时保护退出 |
| 内核 CPU 被动降频 | 保持 40°C、2°C hysteresis，不因提升软件阈值而推迟 |
| 内核临界保护 | 保持 110°C、1°C hysteresis，未禁用或提高 |

65°C 是 CPU 传感器的软件策略，不是电池温度上限，也不等于充电或整机安全认证。
禁用的电源服务、6.18 救援运行时和旧独立诊断程序没有部署本次更改；它们原有的
独立温度门槛不能被理解为已统一修改。没有操作电压、RF 功率或充电参数。

### 部署、证明与清理

先严格主机密钥 USB SSH 核验本启动、精确 RF/屏幕所有者以及整个运行时 manifest。
保留旧源码、配置、manifest、激活策略、原生证明和会话记录；正常停止旧 Wi-Fi，
确认 DSP offline、WLAN 不存在、子进程停止、共享 RAM 清零、core/CPU 恢复、
工作 checkpoint 提交及 dirty 消失，再停止屏幕并确认租约模块已关闭、卸载。
没有清除活跃 dirty、重置失败记录、恢复 NV 工作文件或访问原始 NV 分区。

修改 `tools/wifi-auto-service.py`、`tools/screen-service.py` 和
`tools/wait-for-cool.py` 的显式门槛，保留无效/缺失遥测拒绝、精确 PID 租约、
watchdog、监管/MAC、普通 NV 生命周期、低亮度/15 秒 idle 与独立清理。
会话记录新增 `startup_limit_mc` 和 `runtime_abort_mc`，便于区分实际运行版本。
更新固定源码 pin 链、三个 Wi-Fi 配置、自动连接策略、manifest 和激活策略。
`tools/prepare-kernel-runtime.py` 同步适配新屏幕检查位置，未来离线生成不会
重新插入旧 40°C 启动条件。手机共原子替换并读回 13 个普通文件，保留 xattr。

先只授权新 probation，旧证明不能启动新无限期 worker。新原生 **45 秒** probation
完成关联、DHCP、DNS、证书 HTTPS 200 和 CN 原始审计，峰值 **35.7°C**；
独立清理再次核对 DSP/WLAN/RAM/core/CPU、普通工作文件与 checkpoint、dirty。
对未激活 profile 的 nmcli down 返回码 10 按原样保留，必要的独立安全条件通过。
根据本次真实结果和新 manifest 生成新证明，才重新允许持续 Wi-Fi。
屏幕已使用新源码启动，内核 PID 租约正常，15 秒 idle 后实际亮度为零。

首次主机预检因旧 USB helper 不接受新出现的链路本地 IPv6 而拒绝，尚未对手机
执行命令。新 helper 只允许保留既有链路本地 IPv6，并临时添加/移除自己的 IPv4；
未改主机 Wi-Fi、默认路由、DNS、NAT 或持久 profile。拒绝记录保留在证据中。

### 验证及限制

- 主机及实际部署模块的只读合成边界检查：40°C、45°C、60°C、64.999°C 通过，
  65°C、65.001°C 拒绝；缺失、越界或布尔遥测拒绝。模拟 60°C 的三样本等待通过，
  模拟 65°C 的等待超时。**这些不是把设备加热到该温度，也不是高温硬件验收。**
- 新持续 Wi-Fi 与屏幕同所有者观察 **93.26 秒**，零自动重启；父采样峰值
  **36.8°C**，Wi-Fi worker 峰值 **37.8°C**，屏幕会话峰值 **37.4°C**。
  严格 manifest 校验通过，40°C 被动 trip 与 110°C 临界 trip 均未变。
- 原生 IPv4/IPv6 无代理、绑定 wlan0、验证证书的 HTTPS 均返回 200；局域网访问
  在后续主机核验中复核。新的有效 live dirty 对应当前 RF 所有者，必须保留。
- 主机完整检查 **487 项：465 通过、21 跳过、1 错误**。唯一错误仍是未生成的
  `kernel/power/picasso-pon-reason-audit.ko` 文件缺失；没有通过跳过测试隐藏它。
- 未重启、关机、刷写、kexec、休眠，未读 PON/PMIC、导出凭据、改 Podman 或
  进行高温压力/充电测试；不声称修复了整机自动关机根因或完成长期稳定性验收。

### 正常重启是否自动联网

收尾已恢复 `activation.allow_wifi=true`，新证明与当前 worker/manifest 匹配。
`picasso-wifi-autoconnect-cn-7.3.1.service` 为 active/enabled，已核验
`multi-user.target.wants` 链接。启动时先要求提前降温服务成功，等待
NetworkManager、firewalld 和 udev，然后以既有凭据按授权的首选/回退顺序尝试联网。
不需要手动输入密码，但这不是“不论任何状态都保证联网”。

只有下次启动的内核/资产匹配、有效温度低于 65°C、普通 NV 生命周期干净且网络
可用时，才能完成自动连接。强制断电或复位遗留 dirty 时仍安全拒启；
`Restart=no` 不会对安全故障无限重试。正常重启前建议从 USB 正常停止当前 Wi-Fi
所有者并核验完整清理和 dirty 消失，失败则先诊断，不能删标记强行继续。
用户询问重启行为不是重启授权；本次没有执行新的真实重启/冷启动验收。

## English

### Authorization and current scope

After [LAN recovery and early cooling](NETWORK-THERMAL-REPAIR.md), the operator
explicitly requested “raise the threshold to 65 degrees,” then “raise the startup
threshold to 65 degrees too.” This changes current native
`7.3.1-picasso-wifi2` Wi-Fi/screen runtime aborts, startup checks and their shared
three-sample waiter to **65,000 millidegrees Celsius**:

| Policy | Result |
| --- | --- |
| Wi-Fi/screen startup | All valid CPU sensors strictly below 65°C; exactly 65°C refuses |
| Startup waiter | Three consecutive samples strictly below 65°C; hot samples reset the count, failure after 300 seconds |
| Wi-Fi/screen runtime | Protective service exit when the hottest valid CPU sensor reaches or exceeds 65°C |
| Kernel passive CPU cooling | Unchanged 40°C with 2°C hysteresis; not delayed by the software increase |
| Kernel critical protection | Unchanged 110°C with 1°C hysteresis; neither disabled nor raised |

65°C is a CPU-sensor software policy, not a battery-temperature limit or charging/
whole-device safety certification. The disabled power service, 6.18 rescue
runtime and old isolated diagnostic programs did not receive this deployment;
their independent limits are not claimed globally changed. No voltage, RF-power
or charging parameters were touched.

### Deployment, proof and cleanup

Strict-pinned USB SSH first verified the boot, exact RF/screen owners and entire
runtime manifest. Preserve old sources, configurations, manifest, activation,
native proof and session records. Stop old Wi-Fi normally, verify DSP offline,
absent WLAN, stopped children, cleared shared RAM, restored core/CPU, committed
work checkpoint and absent dirty; then stop the screen and verify the leased
module off/unloaded. No live-dirty deletion, failed-state reset, work-copy recovery
or raw NV access occurred.

Update explicit limits in `tools/wifi-auto-service.py`, `tools/screen-service.py`
and `tools/wait-for-cool.py`. Preserve invalid/missing-telemetry refusal, exact
PID leases, watchdog, regulatory/MAC, ordinary-NV lifecycle, low brightness,
15-second idle and independent cleanup. Session records gain `startup_limit_mc`
and `runtime_abort_mc` to identify the actual running policy. Update source pins,
three Wi-Fi configurations, autoconnect policy, manifest and activation.
`tools/prepare-kernel-runtime.py` follows the new screen-check placement so future
offline generation cannot reinsert the old 40°C startup condition. Atomically
replace/read back 13 ordinary phone files with xattrs preserved.

Authorize only new probation first; the old proof cannot start the new unlimited
worker. New native **45-second** probation passed association, DHCP, DNS,
certificate-verified HTTPS 200 and raw CN audit, peaking at **35.7°C**. Independent
cleanup rechecked DSP/WLAN/RAM/core/CPU, work/checkpoint and dirty. nmcli down
return code 10 for inactive profiles remains unchanged; necessary independent
safety conditions passed. Only then derive a new proof from the actual result
and new manifest and permit continuous Wi-Fi. The screen runs new source with
healthy kernel PID lease and actual brightness zero after 15-second idle.

The first host preflight refused before any phone command: the old USB helper
did not accept a newly present link-local IPv6 address. A new helper preserves
existing link-local IPv6 and temporarily adds/removes only its own IPv4 address;
no host Wi-Fi, default-route, DNS, NAT or persistent-profile changes. The refusal
record is retained.

### Verification and limitations

- Host and deployed-module read-only synthetic boundaries accept 40°C, 45°C,
  60°C and 64.999°C, reject 65°C and 65.001°C, and reject missing, out-of-range or
  Boolean telemetry. Simulated 60°C passes the three-sample waiter; simulated
  65°C times out. **These do not heat the device or qualify high-temperature hardware.**
- New continuous Wi-Fi and screen retained the same owners for **93.26 seconds**,
  with zero automatic restarts. Parent samples peaked at **36.8°C**, Wi-Fi worker
  at **37.8°C**, screen session at **37.4°C**. Strict manifest checks passed;
  passive 40°C and critical 110°C trips remained unchanged.
- Native direct IPv4/IPv6 HTTPS, bound to wlan0 with no proxy and verified
  certificates, returned 200; later host checks rechecked LAN access. The new
  valid live dirty belongs to the current RF owner and must remain.
- Full host suite: **487 tests, 465 passed, 21 skipped, one error**. The sole error
  remains missing ungenerated `kernel/power/picasso-pon-reason-audit.ko`; tests
  were not skipped to hide it.
- No reboot, poweroff, flash, kexec, suspend, PON/PMIC read, credential export,
  Podman changes, heating stress or charging test. Whole-phone shutdown root
  cause and endurance qualification are not declared resolved.

### Automatic Wi-Fi after a normal reboot

Finalization restored `activation.allow_wifi=true`; the new proof matches the
current worker/manifest. `picasso-wifi-autoconnect-cn-7.3.1.service` is
active/enabled with verified `multi-user.target.wants` linkage. At boot it
requires successful early cooling, waits for NetworkManager/firewalld/udev, then
uses existing credentials in the authorized preferred/fallback order. No manual
password entry is needed, but connectivity is not guaranteed regardless of state.

The next boot still requires matching kernel/assets, valid temperatures below
65°C, a clean ordinary-NV lifecycle and an available network. Dirty state from
forced power loss/reset still refuses safely; `Restart=no` does not endlessly
retry safety faults. Before a normal reboot, preferably stop the current Wi-Fi
owner over USB and verify complete cleanup/absent dirty. Diagnose failures instead
of removing markers. Asking about reboot behavior was not a reboot grant: no new
actual reboot/cold-start acceptance was performed.

## 证据 / Evidence

受保护、被忽略的仓库相对入口 / Protected, ignored repository-relative entry:
`out/thermal-limit-65/`. 产物含未公开的私有元数据；不保证存在于新克隆，不能盲目
重放辅助程序。 / Artifacts contain withheld private metadata, may be absent from
fresh clones, and do not authorize helper replay.

| 路径 / Path | 内容 / Contents |
| --- | --- |
| `initial-preflight-refusal.json`, `preflight.json` | 主机预检拒绝及精确原生基线 / Host refusal and exact native baseline |
| `runtime-before.tar`, `snapshot/` | 原运行时、策略和旧证明 / Original runtime, policies and old proof |
| `stage.py`, `deploy-plan.json`, `deployment.json`, `staged/` | 精确部署计划和绑定 / Exact deployment plans and bindings |
| `stop-and-backup.py`, `stopped.json` | 精确旧所有者停止、清理及手机私有归档入口 / Exact-owner stop, cleanup and phone-private archive entry |
| `deploy.py`, `deployed.txt` | 部署、实际模块合成边界和屏幕启动 / Deployment, deployed-module synthetic boundaries and screen start |
| `probation.json`, `continuous-start.json` | 新 45 秒原生证明、独立清理和开机依赖复核 / New native 45-second proof, independent cleanup and boot-dependency checks |
| `observation.json`, `native-evidence.tar`, `host-network.txt` | 同所有者观察、原生记录和非 USB LAN/主机清理复核 / Same-owner observation, native records and non-USB LAN/host cleanup checks |
| `tests.log` | 全套主机检查及保留的文件缺失错误 / Full host suite and retained missing-file error |
