# 7.3.1 PON 单次只读采样已通过并卸载 / 7.3.1 one-shot read-only PON capture passed and unloaded

> 范围 / Scope：2026-11-06 阶段记录，非实时状态或重放许可。代码与 `out/` 路径相对于仓库根目录；私有启动/调用标识、令牌、摘要和原始日志只保留在受保护本地产物。 / Dated 2026-11-06 stage record, not live state or replay permission. Code and `out/` paths are repository-root-relative; private boot/invocation identifiers, tokens, digests and raw logs stay in protected local artifacts.

## 中文

### 授权与结果

接续 [7.3.1 适配与旁路存放](PON-AUDIT-7.3.1.md)。用户在明确提出“低于40°C开始、45°C中止、超时与独立清理、单次只读并卸载、不重启/关机/PMIC写入”之后回复“继续”。本轮只执行该范围，**已消耗本轮许可，不再加载或 start**。先前 6.18 采样许可及 marker 保持已消耗，不重用。

当前 Fedora 45 / `7.3.1-picasso-wifi2` 在同一次启动完成一次模块加载和捕获，返回成功；模块已卸载，缓存 snapshot 节点消失，独立 ExecStopPost 再次确认清理完成。没有重启、关机、刷写、按键注入、PMIC 寄存器写入或 NV 操作，也没有修改 boot、内核配置、FDT 或现有 Wi-Fi/屏幕资产。

### 原生测量，不是模拟 fixture

固定 primary PM8150 身份通过：type `0x51`、subtype `0x1e`、PON Gen2 primary subtype `0x04`。访问标识为 `existing-primary-regmap`，使用现有已绑定 PMIC 设备的 regmap，没有新设备注册或 probe。

| 字段 | 原生值 | 固定参考下的解释 |
| --- | ---: | --- |
| PON_REASON1 / `08c0` | `0x41` | **HARD_RESET 与 CBL_POWER 同时置位**，不只取首位。 |
| WARM_RESET_REASON1 / `08c2` | `0x00` | 保留为 raw；不能据此排除所有复位。 |
| OFF_REASON / `08c7` | `0x80` | 仅选择 POFF，无多个序列或未知低位。 |
| POFF_REASON1 / `08c5` | `0x02` | PS_HOLD，SoC 控制的关机来源线索。 |
| FAULT / `08c8`、`08c9`；S3 / `08ca` | null | 未选择，**未读取，不填零**。 |

本模块本轮只读 3 个身份字节、3 个公共原因字节及 1 个 POFF 字节，共 **7 字节**。模块 init 捕获一次，用户态读取 root0400 缓存并先保存 raw JSON 再解码；未重新访问总线或读取其他 PMIC 地址。FAULT/S3 的条件代码已用模拟输入测试，但这些银行本轮没有实机读取。

**HARD_RESET 是锁存原因位，不是本轮发生硬重启的证据。** 采样前后 boot 身份相同，原服务 owner 未变，本轮没有发出重启。多个 PON 位可以保留历史状态；捕获时间新鲜不等于状态本身来自已唯一关联的事件。

历史 [6.18 单次采样](POWER-PON-REASON.md)记录 PON=`0x40` CBL_POWER、POFF=`0x02` PS_HOLD、warm=0；本次多出 HARD_RESET 位，但跨阶段差异不能唯一归因于某次复位、固件或外部供电。仍不宣称自行启动根因、所有复位排除、充电模式或完整电源循环验收通过。

### 本轮实际执行的保护

新增 `tools/collect-pon731.py` 和静态单次 `tools/picasso-pon-audit731-read1.service`，不改旧采集器。专用代码/许可目录 `/opt/picasso-pon-audit-7.3.1-read1/` 为 root0500、文件 root0400；专用状态目录 `/var/lib/picasso-power/pon-audit731-read1/` 为 root0700、记录 root0600。

- 明确单次固定只读 scope，绑定本次 boot、精确 release、config/FDT、模块/解码器/采集器/unit 摘要及独占 run token。许可预启动窗口最多300秒；许可文件不公开。
- 只允许指定 PID1 unit 内调用，绑定 PID、`/proc` 启动时间及 InvocationID；采集器租约15秒，模块加载8秒时限。退出清理不因运行租约已过期而被阻止，但必须匹配 boot/run/module/invocation 的所有权。
- 独占并 fsync `consumed`、`load-intent.json`、加载子进程/返回、raw、解码、卸载和结果；已消耗或同名文件不覆盖。主机及手机各有一次启动请求意图，实际只发送一次 `systemctl start`，不自动重载或重读。
- 开始前3次普通温度读数均低于40°C；采集器自身检查起始以及紧邻加载前严格低于40°C，运行中达到45°C中止。原生采集器起始最高36.8°C，窗口峰值 **37.4°C**，结束最高36.8°C，持续约 **0.137秒**。没有故意加热。
- PID1 `RuntimeMaxSec=20`、`TimeoutStopSec=6`、`Restart=no`、control-group 清理、小核0–3、128MiB/12任务上限、仅 `CAP_SYS_MODULE`、只读系统及受限设备/系统调用；`Requisite` 要求既有提前降温服务已运行。无 `[Install]` 或开机加载。
- 主采集器卸载成功、写入所有权结束记录；独立 ExecStopPost 确认模块和 snapshot 已消失。已有模块、错误 owner、错误 boot/invocation 或所有权已结束时，拒绝误卸载其他模块。

这些时限不是对任意内核或总线永久阻塞的绝对硬实时保证。本轮没有加载超时、内核阻塞、卸载错误或重试；若未来失败，应保留记录并复核，而非强制卸载、重复加载或电源循环。

### 复核、测试与保留记录

独立进程确认：同一启动、原屏幕/Wi-Fi/getty/降温服务 owner 与状态保持；93 个版本化及共享资产、运行时清单、config/FDT 匹配；systemd running、零 failed。两个清理记录全部通过，只有一个实际卸载请求，两个采样模块与 snapshot 均不存在，consumed/load-intent/unloaded 保留。

既有 kernel taint `4096`（out-of-tree）前后不变，不宣称内核从未 tainted。预加载 kernel journal cursor 之后无新增内核日志事件。PID1 journal 确认调用、结果及成功结束；成功静态 unit 被 GC 后部分运行字段为空，**不把空的 ExecStopPost 字段当执行证明**，而使用持久记录、journal 和独立缺席检查。

17 项新采集器模拟测试全部通过，覆盖许可/租约/所有权、恰好40°C拒启、紧邻加载温度复查、45°C中止与清理、一次加载失败不重试、consumed不可覆盖和防误卸载；既有13项模块测试通过。初次 mock 执行的3个测试失败因 fixture 未提供离线解码器文件；补齐测试 fixture 后通过，初始日志保留，没有手机硬件重试。完整主机套件 **540 项：519通过、21跳过、零失败/错误**；软件测试不等于电源或耐久验收。

证据位于 `out/pon-731/read1/`：`preflight.json`、`prepared.json`、`armed.json`、`launch-intent.json`、`completed.json`、`independent-native.json`、`native-evidence.tar.gz`，以及模拟测试、全量测试和初次失败日志。归档中的 raw/result 与独立检查一致。私有原始 JSON、cursor、令牌、boot/InvocationID、PID 和摘要不复制到笔记。

模块文件继续在独立备用目录中；采样 unit static/inactive，不常驻、不随开机加载。本轮许可和 marker 已消耗，不删除或改名来重放。任何新 PMIC/PON/RTC 读取、电源写入、重启或电源循环都须另行明确范围与授权。现有40°C被动降温、110°C critical、Wi-Fi/屏幕65°C软件门槛及监管/MAC/NV保护不变；自行启动、异常断电、充电/电量计和长期稳定性仍未解决。

## English

### Authorization and result

Following [the 7.3.1 port and separate staging](PON-AUDIT-7.3.1.md), the user replied “继续” after the explicit proposal: start below40°C, abort at45°C, timeout and independent cleanup, one read-only capture then unload, without reboot/shutdown/PMIC writes. Only that scope was executed. **This permission is consumed; do not load or start again.** The historical 6.18 permission and marker remain consumed and were not reused.

The current Fedora 45 / `7.3.1-picasso-wifi2` completed one successful module load/capture in the same boot. The module was unloaded, its cached snapshot disappeared, and independent ExecStopPost reconfirmed cleanup. No reboot, shutdown, flashing, key injection, PMIC register write or NV operation; no boot, kernel config, FDT or existing Wi-Fi/screen asset changes.

### Native measurements, not synthetic fixtures

Fixed primary PM8150 identity passed: type `0x51`, subtype `0x1e`, PON Gen2 primary subtype `0x04`. Access was `existing-primary-regmap`, using the existing bound PMIC device's map without new device registration/probe.

| Field | Native value | Interpretation under the fixed reference |
| --- | ---: | --- |
| PON_REASON1 / `08c0` | `0x41` | **Both HARD_RESET and CBL_POWER set**, not reduced to the first bit. |
| WARM_RESET_REASON1 / `08c2` | `0x00` | Retained raw; does not exclude every reset. |
| OFF_REASON / `08c7` | `0x80` | POFF only, without multiple sequences or unknown low bits. |
| POFF_REASON1 / `08c5` | `0x02` | PS_HOLD: a SoC-controlled shutdown-source clue. |
| FAULT / `08c8`, `08c9`; S3 / `08ca` | null | Unselected and **not read**, not filled with zero. |

This module read 3 identity bytes, 3 common-reason bytes and 1 POFF byte: **7 bytes** in this capture. Module init captured once; userspace read the root0400 cache and saved raw JSON before decoding. No repeated bus access or other PMIC addresses. Synthetic tests cover conditional FAULT/S3 code, but those banks were not read on hardware in this stage.

**HARD_RESET is a latched reason bit, not evidence that a hard reboot occurred during this operation.** Boot identity and existing service owners remained unchanged; no reboot was issued. Multiple PON bits may preserve history. A fresh capture timestamp does not uniquely associate the state with an event.

The historical [6.18 sample](POWER-PON-REASON.md) recorded PON=`0x40` CBL_POWER, POFF=`0x02` PS_HOLD, warm=0. The additional HARD_RESET bit now cannot uniquely identify a reset, firmware behavior or external-power cause across stages. Automatic-startup causality, exclusion of every reset, charging mode and a complete power cycle remain unproven.

### Protections actually exercised

Added `tools/collect-pon731.py` and static one-shot `tools/picasso-pon-audit731-read1.service`, leaving the legacy collector unchanged. Dedicated code/permission directory `/opt/picasso-pon-audit-7.3.1-read1/` is root0500 with root0400 files; `/var/lib/picasso-power/pon-audit731-read1/` is root0700 with root0600 records.

- Explicit fixed read-only single-use scope binds this boot, exact release, config/FDT, module/decoder/collector/unit hashes and exclusive run token. Pre-start permission lasts at most300 seconds; the permit is private.
- Execution requires the specified PID1 unit, PID, `/proc` start time and InvocationID. Collector lease15 seconds; module-load deadline8 seconds. Cleanup is not blocked by an expired runtime lease, but requires matching boot/run/module/invocation ownership.
- Exclusive fsynced consumed, load-intent, load-child/return, raw, decode, unload and result records. No replacement of spent/same-name records. Host and phone each preserve a one-start intent; exactly one `systemctl start`, without load/read retry.
- Three ordinary temperature readings before arming were below40°C. The collector enforces strictly below40°C at startup and immediately before loading, aborting at45°C. Native start maximum36.8°C, window peak **37.4°C**, final maximum36.8°C; duration approximately **0.137 seconds**. No deliberate heating.
- PID1 `RuntimeMaxSec=20`, `TimeoutStopSec=6`, `Restart=no`, control-group cleanup, small cores0–3, 128MiB/12-task caps, only `CAP_SYS_MODULE`, read-only system and restricted devices/syscalls. `Requisite` requires the existing early-cooling service already active. No `[Install]` or boot loading.
- The collector unloaded successfully and recorded ownership ended. Independent ExecStopPost confirmed module/snapshot absence. Preexisting modules, wrong owner/boot/invocation, or ended ownership refuse to unload an unrelated module.

These deadlines cannot provide an absolute hard-real-time guarantee against an arbitrary permanently blocked kernel/bus. This run had no load timeout, kernel stall, unload error or retry. A future failure needs preserved evidence/review, not forced unloading, repeated loading or power cycling.

### Verification, tests and retained evidence

An independent process confirmed the same boot and existing screen/Wi-Fi/getty/cooling owners/states, all93 versioned/shared assets, runtime manifest, config/FDT, systemd running and zero failed units. Both cleanup records passed, with one actual unload request; neither sampler nor snapshot remained. consumed/load-intent/unloaded records are retained.

Existing kernel taint `4096` (out-of-tree) remained unchanged; this is not a claim that the kernel was never tainted. No new kernel journal event followed the preload kernel cursor. PID1 journal confirms invocation/result and successful deactivation. Some runtime fields become empty after successful static-unit GC: **empty ExecStopPost properties are not used as execution proof**; persistent records, journal and independent absence checks are.

All17 new synthetic collector tests passed: permission/lease/ownership, exact40°C refusal, immediate pre-load temperature recheck,45°C abort/cleanup, no load retry, exclusive consumed records and unrelated-module protection. All13 existing module tests passed. Three initial mock-execution failures came from a missing offline decoder file in the fixture; the completed fixture passed, with the original log retained and no native hardware retry. Full host suite: **540 tests,519 passed,21 skipped,no failures/errors**. Software tests do not establish power/endurance acceptance.

Evidence under `out/pon-731/read1/`: `preflight.json`, `prepared.json`, `armed.json`, `launch-intent.json`, `completed.json`, `independent-native.json`, `native-evidence.tar.gz`, synthetic/full-suite logs and initial failures. Archived raw/result match the independent inspection. Private raw JSON, cursor, tokens, boot/InvocationID, PIDs and hashes are not copied into notes.

The module file remains separately available. The capture unit is static/inactive, not resident or boot-loaded. Permission and marker are consumed; never delete/rename them for replay. New PMIC/PON/RTC reads, power writes, reboot or power cycling require a separately explicit scope/grant. Existing40°C passive cooling,110°C critical,65°C Wi-Fi/screen software limits and regulatory/MAC/NV protections remain unchanged. Automatic startup, abnormal power loss, charging/fuel gauge and long-term stability remain unresolved.
