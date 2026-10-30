# Picasso Wi-Fi人工值守诊断补丁（非正常补丁序列） / Attended Picasso Wi-Fi diagnostic patches (not the normal patch series)

> 文档范围 / Scope: 本文从`kernel/diagnostics/README.md`集中保留可选诊断补丁的实现、操作及历史验收边界；不是默认联网方案、修复证明或当前硬件状态，操作须遵守原有授权和保护。 / This centralizes optional diagnostic-patch implementation, procedures, and historical acceptance boundaries from `kernel/diagnostics/README.md`; it is not a default connectivity scheme, proof of a fix, or current hardware status. Operations remain subject to existing authorization and guards.

## 中文

这些可选补丁**不在**`kernel/patches/series`中，不由正常构建启用，也不是生产用途的Wi-Fi修复。参数默认false，
插入模块后只读，且仅适用于Picasso + ath10k SNOC。

- `kernel/diagnostics/ath10k-picasso-mgmt-observer.patch`：仅记录auth/assoc完成的frame-control、
  descriptor、原始固件status、原始ACK RSSI字段及长度。不记录地址、
  密钥、NV数据或数据包转储，不合成ACK，也不改变完成处理。
- `kernel/diagnostics/ath10k-picasso-ht20-only.patch`：显式启用保守的HT20/legacy能力通告；
  移除HT40/SGI40和VHT能力。不改变校准、监管
  规则/信道标志、功率、天线mask、固件或保护控制。
- `kernel/diagnostics/ath10k-picasso-link-observer.patch`：在上述两个补丁之后应用。
  只读的`picasso_link_observe=1`显式启用项记录scan/roam原因、原有RX过滤之前
  匹配自身AP的beacon计数/status、beacon年龄、延迟失联
  work，以及key命令/完成元数据。不记录地址、密钥或帧载荷；
  不改变callback、用于决策的计数器、key结果、RX
  过滤、beacon/probe定时器或任何保护。WPA2期间保持管理TX日志
  关闭（`picasso_mgmt_status=0`）。实际因果链与限制见
  [WIFI-LINK-LOSS.md](WIFI-LINK-LOSS.md)。

仅在独立或临时备份的、已准备好的6.18.58源码树中应用，使用
匹配的wifi2 config和Module.symvers。沿用现有AArch64 LLVM构建设置，
编译`M=drivers/net/wireless/ath/ath10k`。保留源码/补丁/模块hash；
随后恢复已准备源码和主机基准产物。M=输出
位于源码ath10k目录，**不是**可能已过时的O=模块目录。

将生成的core放到唯一的`/opt/picasso-wifi-trial/modules/`路径；
不得替换已安装的`/lib/modules`文件，不为它运行depmod，也不刷boot。
验证精确原生wifi2/config/FDT、没有活跃WLAN/DSP、私有副本NV
checkpoint、内存和用户态hash后，卸载离线实验Wi-Fi栈，
加载正常ath/mac80211依赖，再以
`picasso_mgmt_status=1 picasso_ht20_only=1`插入精确暂存core。保留独立受保护SNOC模块、
DMS→WLFW设备MAC配置和实际SG监管审计要求。

参数被接受不等于已验证。检查只读Y参数值、
仅HT20的PHY能力、当前/永久设备MAC、实际SG限制，以及
实际channel-context宽度0/1（20_NOHT/20）。保留固件status原值；
ath10k把非零视为未获确认，但没有匹配ABI定义时，不得赋予更具体的
厂商status含义。

使用有界PID-1服务，具有独立ExecStopPost，在等待期间持续检查温度，
启动低于40°C、45°C中止，没有自动DSP恢复。
清理断开/卸载WLAN、停止DSP/私有proxy/TFTP、清空已验证
RMTFS RAM、卸载诊断core，并重新加载未改动的已安装core。核验
其文件hash以及诊断参数不存在。重新检查原始NV/master文件、
已安装文件、boot/保护分区/GPT。Open System auth不需要密码。

实际硬件试验及失败见
[WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md)。observer在
原生wifi2上实际运行；HT20变体实际选择了20 MHz，但**没有**修复
三次status-3认证完成。两个补丁均不能证明关联、
DHCP、Internet、持久启用、充电安全或稳定性。

## English

These optional patches are **not** in `kernel/patches/series`, not enabled by
normal builds, and not a production Wi-Fi fix. The parameters default to false,
are read-only after insertion, and apply only to Picasso + ath10k SNOC.

- `kernel/diagnostics/ath10k-picasso-mgmt-observer.patch`: log only auth/assoc completion frame-control,
  descriptor, raw firmware status, raw ACK RSSI field and length. No addresses,
  keys, NV data, packet dumps, synthetic ACKs or altered completion handling.
- `kernel/diagnostics/ath10k-picasso-ht20-only.patch`: opt-in conservative HT20/legacy advertisement;
  remove HT40/SGI40 and VHT capabilities. Does not change calibration, regulatory
  rules/channel flags, power, antenna masks, firmware or protection controls.
- `kernel/diagnostics/ath10k-picasso-link-observer.patch`: apply after the two patches above. The
  read-only `picasso_link_observe=1` opt-in logs scan/roam reasons, matched own-AP
  beacon counts/status before the existing RX filter, beacon age, delayed-loss
  work and key command/completion metadata. No addresses, keys or frame payloads;
  it does not change callbacks, counters used for decisions, key results, RX
  filtering, beacon/probe timers, or any protection. Leave management TX logging
  off during WPA2 (`picasso_mgmt_status=0`). See
  [WIFI-LINK-LOSS.md](WIFI-LINK-LOSS.md) for actual causality/limitations.

Apply only in a separate/temporarily backed-up prepared 6.18.58 source tree using
matching wifi2 config and Module.symvers. Compile `M=drivers/net/wireless/ath/ath10k`
with the existing AArch64 LLVM build settings. Preserve source/patch/module hashes;
restore the prepared source and baseline host artifacts afterward. The M= output
is in the source ath10k directory, **not** a potentially stale O= module directory.

Stage the resulting core under a unique `/opt/picasso-wifi-trial/modules/` path;
never replace installed `/lib/modules` files, run depmod for it, or flash boot.
After verifying exact native wifi2/config/FDT, no active WLAN/DSP, private-copy NV
checkpoint, memory and userspace hashes, unload the offline experiment Wi-Fi stack,
load normal ath/mac80211 dependencies, then insert the exact staged core with
`picasso_mgmt_status=1 picasso_ht20_only=1`. Keep the separate guarded SNOC module,
DMS→WLFW device-MAC provisioning and actual SG regulatory audit requirements.

An accepted parameter is not verification. Check read-only Y parameter values,
HT20-only PHY capabilities, current/permanent device MAC, actual SG limits and
actual channel-context width 0/1 (20_NOHT/20). Preserve firmware status values;
nonzero is treated as unacknowledged by ath10k, but do not assign a more specific
vendor status meaning without the matching ABI definition.

Use a bounded PID-1 service with independent ExecStopPost, continuous temperature
checks during waits, start below 40°C, abort at 45°C, no automatic DSP recovery.
Cleanup disconnects/unloads WLAN, stops DSP/private proxy/TFTP, clears the validated
RMTFS RAM, unloads diagnostic core, and reloads the untouched installed core. Verify
its file hash and diagnostic-parameter absence. Recheck original NV/master files,
installed files, boot/protected/GPT. No password is needed for Open System auth.

Actual hardware tests and their failures are described in
[WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md). The observer was exercised
on native wifi2; the HT20 variant actually selected 20 MHz but did **not** fix the
three status-3 authentication completions. Neither patch establishes association,
DHCP, Internet, persistent enablement, charging safety or stability.
