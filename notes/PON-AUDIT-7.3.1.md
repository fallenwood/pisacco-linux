# 7.3.1 PON 原因审计模块：已适配并旁路存放，未加载 / 7.3.1 PON reason audit: ported and staged separately, not loaded

> 范围 / Scope：2026-11-06 阶段记录；仓库代码和 `out/` 路径相对于仓库根目录。私有摘要、启动标识及原始证据仅保留在受保护的本地产物中。本页不是实机采样或电源操作许可。 / Dated 2026-11-06 stage record; code and `out/` paths are repository-root-relative. Private digests, boot identifiers and raw evidence remain in protected local artifacts. This page does not authorize hardware sampling or power operations.

> 后续 / Follow-up：用户随后明确“继续”，已完成同一启动上的一次受控原生采样并卸载，独立清理通过，许可已消耗；PON=`0x41` HARD_RESET+CBL_POWER、POFF=`0x02` PS_HOLD、warm=0，不宣称根因或新重启。本页“未加载”是准备阶段快照，最新见 [PON-READ-7.3.1.md](PON-READ-7.3.1.md)。
> A later explicit “continue” completed one guarded native capture in the same boot, unloaded with independent cleanup; permission consumed. PON=`0x41` HARD_RESET+CBL_POWER, POFF=`0x02` PS_HOLD, warm=0, without a causality or new-reboot claim. “Not loaded” below is the preparation snapshot; latest details are in the linked note.

## 中文

### 结果与边界

用户要求“添加到当前7.3.1上面”。本阶段完成适配、离线编译、软件测试和手机普通文件旁路存放；**没有加载模块，没有读取 PON 寄存器**，也没有重启、关机、刷写、PMIC 写入或 NV 操作。当前 Fedora 45 / `7.3.1-picasso-wifi2` 内核未被替换。

新增文件：
- `kernel/power-7.3.1/picasso-pon-reason-audit731.c`、同目录 `Makefile`。
- 离线构建工具 `tools/build-pon731.py` 和测试 `tests/test_pon731.py`。
- 已编译模块 `out/pon-731/build-accepted/module/picasso-pon-reason-audit731.ko`。

手机的独立备用目录为 `/opt/picasso-pon-audit-7.3.1/`，保存模块、源码、既有离线解码器、构建清单及明确标为未加载的存放记录；目录 root0500、文件 root0400。未写入系统模块目录、未安装服务或开机加载配置。

原 6.18 采样器源码、旧手机采样目录和已消耗 marker 均保留。当前版本化运行时中那个旧的、仅替换过 release 的 7.3.1 模块也保留原字节，**不覆盖已固定的资产**。`tools/build-extra-modules.py` 今后离线构建改用真正的新适配；若将来生成新运行时清单，仍须重新审查，不能复用当前清单的授权或证明。

### 为什么不是只改 release

当前设备树已有启用的 `/soc@0/spmi@c440000/pmic@0`，标准 `pmic-spmi` 驱动已经绑定。旧采样器遇到 primary 节点会拒绝，避免使用未注册命令描述对象与驱动探测竞争；修改 release 字符串不能解决这一差异。

新模块要求明确 `confirm_readonly`、精确 release、Picasso 兼容、固定 primary/PM8150L 锚点、USID0/5 和同一 OF 控制器。它只查找既有设备，以 `device_trylock` 拒绝繁忙绑定，确认 primary 已绑定 `pmic-spmi` 后使用 `dev_get_regmap`；读取期间持有设备锁，避免其 devm regmap 被移除。不创建或注册新设备，不触发 probe，不改已有 regmap 的配置或缓存模式。该固定内核的 PMIC regmap 默认 `REGCACHE_NONE`，每个字节经既有 regmap 锁读取。

代码中的固定计划保持旧审计范围：
- 身份 `0104`、`0105`、`0805` 必须为 PMIC type `0x51`、subtype `0x1e`、PON Gen2 primary subtype `0x04`，然后才读原因。
- 公共原因 `08c0`、`08c2`、`08c7`。
- 仅按 OFF_REASON 的 bit7/bit6/bit5，分别读 `08c5`、`08c8`+`08c9`、`08ca`；未选银行保留 null。
- 不读 Gen1 原因、PS_HOLD 控制、复位计时器、触发使能或 NV，不允许地址参数，不重试失败的读取。
- 无 PMIC 写接口、IRQ 操作、reboot notifier 或计时器。模块 init 只捕获一次；root0400 的 `/sys/kernel/picasso_pon_reason_audit731/snapshot` 只呈现缓存，再读不访问总线。

以上是代码和离线审计结论，**不是本轮在手机读到的身份或原因值**。解码继续使用 `tools/power-pon-reasons.py`，保留全部位和歧义，不把旧锁存位升格为根因。

### 构建、测试与保留的失败

使用 `sources-7.3.1.json` 固定的上游归档、`kernel/patches/7.3/series` 既有四个补丁和已回收的原生配置。Clang/LLVM/LLD 均为 22.1.8；主机使用 Fedora 45 包，原内核来自 Fedora 44 包，不宣称编译器包或二进制完全相同。下载 RPM 保持原有签名校验；不完整下载保留且未使用，没有 GPG 绕过或替换信任密钥。

ABI 参考配置仅允许编译器版本文本、initramfs 输入路径和**未启用 Rust 时的工具链探测元数据**差异，拒绝已编译功能配置漂移。手机实际配置未变。完整离线 `vmlinux` 生成真实 `vmlinux.symvers`，`modules_prepare` 生成模块链接所需文件；模块使用真实内建导出表，经严格 modpost、完整 vermagic 和 23 个精确导入白名单检查，没有忽略未解析符号或伪造符号表。该 ABI 参考内核不被打包或安装到手机。

下列准备失败均保留，不把最终通过改写为首次成功：
1. 私有前缀缺少匹配 Clang builtin resource headers，host fixdep 编译失败；补齐既有受信任的 22 版资源路径，并新增预检。
2. 缺少 OpenSSL CLI 导致 `CONFIG_OPENSSL_SUPPORTS_ML_DSA` 漂移，被配置门拒绝；取得并验证对应签名包，恢复原能力，而非放宽该门。
3. 原 gzip CPIO 文件名不符合 Kbuild 的 `*.cpio[.*]` 规则，被当文本文件清单解析；停止该主机构建，增加 magic/大小检查并规范化副本后重新构建。
4. 只构建 `vmlinux` 尚缺 `scripts/module.lds`，模块最终链接拒绝；保留失败，使用正常 `modules_prepare`，在新模块输出目录复用已审阅的完整匹配 Kbuild。

`tests/test_pon731.py` 的 **13 项全部通过**。其中用模拟 regmap 执行实际 C 读取计划，覆盖全部 256 种 OFF_REASON 字节、身份不符、每个读取点失败、非字节及重复/越界 slot；没有硬件读取。全量主机测试 **523 项：502 通过、21 跳过、零失败/错误**。此前缺失的旧 `.ko` 从手机普通文件取回并匹配原固定摘要，未重编或修改旧 pin；旧阶段的 510 项测试错误记录仍保留为当时事实。新克隆没有这些被忽略的本地产物，不保证同样的可用测试资产。

构建示例（仅本地普通文件；先准备固定源码和匹配工具链，源目录已存在时不要重跑源码解包）：

```sh
python3 tools/build-pon731.py \
  --reference-config out/fedora45-boot/installed-config.txt \
  --initramfs out/fedora45-boot/installed-cpio.gz \
  --output out/pon-731/rebuild-example --jobs 6
python3 -m unittest discover -s tests -p test_pon731.py -v
```

输入是本阶段已有的受保护普通文件，不是获取它们的设备操作指令。输出目录必须全新；`--reuse-kbuild` 只用于已独立审阅的完整匹配主机构建，仍执行配置、正常 Kbuild 和符号检查。可选本地构建收据测试检查本阶段 `build-accepted` 产物；没有该收据时该项跳过。

### 手机复核与下一道门

首次普通文件存放预检错误地把 `manifest.files` 当作全部 93 个资产，在创建目标目录前拒绝。独立检查确认实际上为 47 个版本化文件加 46 个共享文件，合计 93，全部匹配、目标目录不存在、两个采样器均未加载。保留 v1 程序/输出，只修正本次存放核对器的计数和完整并集校验，没有改手机运行时守卫。

随后存放成功，独立进程再次确认：新文件摘要/属主/权限正确，同一启动与原服务 owner 未变，93 个原资产、运行时清单、原生 config/FDT 匹配；systemd running、零 failed，当前最热采样 35.4°C，两个采样模块与 snapshot 均不存在。这不是新开机、屏幕实键、视觉、射频 probation 或耐久验收。没有重新读写原始 boot 分区；本阶段未改 boot 文件或分区，不能冒称新增完整读回证明。

**实机加载仍未获授权。** 新模块本身不实现温度监控、PID 租约或独立回收。实际采样前须另行准备并确认新的一次性采集器：绑定当次 boot/config/FDT/模块与 owner，独占 consumed/load-intent、PID1 时限与独立清理，起始全传感器严格低于 40°C、45°C 中止，单次读取后卸载；不重用旧许可或 marker。不得因本次编译/存放而直接手工加载、读 PMIC、重启或做电源循环。

40°C 被动降频、110°C critical、现有 Wi-Fi/屏幕 65°C 软件门槛及监管/MAC/NV 保护均不变；65°C 门槛不适用于扩大 PON 采样许可。关机后自行启动、异常断电、充电/电量计和长期稳定性仍未解决。

证据入口：`out/pon-731/build-accepted/manifest.json`、`post-build-audit.json`、`targeted-tests-final.log`、`full-suite-final.log`、`native-stage.json`、`native-independent-verification.json`，均在 `out/pon-731/` 下；四次构建准备失败和首次存放拒绝也在同目录保留。历史采样及其已消耗许可见 [POWER-PON-REASON.md](POWER-PON-REASON.md)。

## English

### Result and boundaries

The user requested adding the audit to the current 7.3.1 kernel. This stage ported and built the module, tested it offline, and staged ordinary files separately on the phone. **No module was loaded and no PON registers were read.** There was no reboot, shutdown, flashing, PMIC write or NV operation. The running Fedora 45 / `7.3.1-picasso-wifi2` kernel was not replaced.

New files:
- `kernel/power-7.3.1/picasso-pon-reason-audit731.c` and its `Makefile`.
- Offline builder `tools/build-pon731.py` and tests `tests/test_pon731.py`.
- Compiled module `out/pon-731/build-accepted/module/picasso-pon-reason-audit731.ko`.

The separate phone directory `/opt/picasso-pon-audit-7.3.1/` contains the module, source, existing offline decoder, build manifest and explicitly unloaded staging record. The directory is root0500 and files root0400. No system module directory, service or boot-loading configuration was installed.

The original 6.18 sampler source, old native sampling directory and consumed marker remain. The old release-substituted 7.3.1 module in the current versioned runtime also retains its original bytes: **no pinned asset was overwritten**. Future offline `tools/build-extra-modules.py` builds select the actual new port. A future new runtime manifest still needs review and cannot inherit the current manifest's authorization or proof.

### More than changing the release

The current device tree already has an enabled `/soc@0/spmi@c440000/pmic@0` with `pmic-spmi` bound. The legacy sampler refuses a primary node to avoid racing a probe with its unregistered command descriptor. A release-string substitution does not resolve that difference.

The new module requires explicit `confirm_readonly`, the exact release, Picasso compatibility, fixed primary/PM8150L anchor, USID0/5 and the same OF controller. It only finds existing devices, rejects busy binding with `device_trylock`, confirms the primary is bound to `pmic-spmi`, and uses `dev_get_regmap`. Holding the device lock prevents removal of its devm regmap during capture. It creates/registers no device, triggers no probe and changes no map configuration or cache mode. This fixed kernel's PMIC map defaults to `REGCACHE_NONE`; each byte uses the existing map's lock.

The fixed source-level plan retains the legacy scope:
- Identity `0104`, `0105`, `0805` must match PMIC type `0x51`, subtype `0x1e`, PON Gen2 primary subtype `0x04` before any reasons are read.
- Common reasons `08c0`, `08c2`, `08c7`.
- OFF_REASON bit7/bit6/bit5 conditionally select `08c5`, `08c8`+`08c9`, `08ca`; unselected banks stay null.
- No Gen1 reasons, PS_HOLD controls, reset timers, trigger enables or NV. No address parameter or retry after read failure.
- No PMIC write API, IRQ operation, reboot notifier or timer. Module init captures once; root0400 `/sys/kernel/picasso_pon_reason_audit731/snapshot` serves only cached data, with no further bus access.

These are source/offline audit findings, **not identity or reason values measured on the phone in this stage**. Decoding still uses `tools/power-pon-reasons.py`, preserving every flag and ambiguity without promoting stale latched bits to causality.

### Build, tests and preserved failures

Inputs were the upstream archive pinned by `sources-7.3.1.json`, the four existing patches in `kernel/patches/7.3/series`, and the recovered native configuration. Clang/LLVM/LLD are 22.1.8. The host uses Fedora 45 packages whereas the native kernel used Fedora 44 packages; compiler packages/binaries are not claimed identical. RPM signature checks remained enforced; incomplete downloads were retained and not used. No GPG bypass or replacement trust key.

The ABI-reference configuration permits only compiler version text, initramfs input-path and **disabled-Rust toolchain-detection metadata** differences, rejecting compiled-feature drift. The actual phone configuration is unchanged. A complete offline `vmlinux` generated genuine `vmlinux.symvers`; `modules_prepare` generated the module-link prerequisites. Strict modpost, full vermagic and an exact 23-import allowlist were checked against real built-in exports, without ignoring unresolved symbols or fabricating a symbol table. The ABI-reference kernel is never packed or installed on the phone.

Preparation failures remain recorded rather than rewriting the final success as a first-attempt success:
1. The private compiler prefix lacked matching Clang builtin resource headers, failing host fixdep compilation. Connected the existing trusted version-22 resources and added preflight validation.
2. Missing OpenSSL CLI changed `CONFIG_OPENSSL_SUPPORTS_ML_DSA`, causing configuration refusal. Obtained and verified the signed package to restore the original capability instead of weakening the gate.
3. The original gzip CPIO filename did not match Kbuild's `*.cpio[.*]` pattern and was parsed as a text file list. Stopped that host build, added magic/size checks and normalized the copy before rebuilding.
4. A `vmlinux`-only build lacked `scripts/module.lds`, refusing the final module link. Preserved the failure, ran normal `modules_prepare`, and reused the reviewed complete matching Kbuild with a fresh module-output directory.

All **13 targeted tests passed**. A synthetic regmap executes the actual C read plan across all 256 OFF_REASON bytes, identity mismatches, every read failure, non-byte values and duplicate/out-of-range slots. No hardware reads. The full host suite is **523 tests: 502 passed, 21 skipped, no failures/errors**. The previously missing legacy `.ko` was recovered from an ordinary phone file and matched its original pin, without rebuilding or changing that pin. The earlier 510-test error record remains historical fact. A fresh clone lacks these ignored local artifacts and is not guaranteed the same test assets.

Build example, using ordinary local files only. Prepare the pinned sources and matching toolchain first; do not re-extract over an existing source tree:

```sh
python3 tools/build-pon731.py \
  --reference-config out/fedora45-boot/installed-config.txt \
  --initramfs out/fedora45-boot/installed-cpio.gz \
  --output out/pon-731/rebuild-example --jobs 6
python3 -m unittest discover -s tests -p test_pon731.py -v
```

Inputs are protected ordinary files already held during this stage, not instructions authorizing device operations to obtain them. The output directory must be fresh. `--reuse-kbuild` is only for an independently reviewed complete matching host build; configuration, normal Kbuild and symbol checks still run. The optional local build-receipt test checks this stage's `build-accepted` artifacts and skips when that receipt is absent.

### Native verification and the next gate

The first ordinary-file staging preflight incorrectly treated `manifest.files` as all 93 assets and refused before creating the destination. Independent inspection established 47 versioned plus 46 shared files, 93 total, all matching; the destination was absent and neither sampler loaded. The v1 program/output remain. Only this one-off staging verifier's count and complete-union check were corrected, not a phone runtime guard.

Staging then succeeded. An independent process rechecked new file hashes/ownership/permissions, the same boot and existing service owners, all 93 original assets, runtime manifest and native config/FDT. systemd was running with zero failed units; the hottest current sample was 35.4°C. Neither sampler nor snapshot existed. This is not new boot, physical/visual screen, radio probation or endurance acceptance. No raw boot partition was read or written again; this stage changed no boot file/partition and does not claim another complete readback proof.

**Native loading remains unauthorized.** The new module itself provides no thermal monitoring, PID lease or independent cleanup. A real sample first needs a separately prepared and confirmed fresh one-shot collector binding that boot/config/FDT/module/owner, exclusive consumed/load-intent, PID1 deadlines and independent cleanup. Start with every sensor strictly below 40°C, abort at45°C, read once and unload. Do not reuse the old permission or marker. Building/staging does not authorize manual loading, PMIC reads, reboot or a power cycle.

40°C passive cooling, 110°C critical protection, existing Wi-Fi/screen 65°C software limits and regulatory/MAC/NV protections remain unchanged. The 65°C limit does not expand PON sampling permission. Automatic startup after shutdown, abnormal power loss, charging/fuel gauge and long-term stability remain unresolved.

Evidence: `out/pon-731/build-accepted/manifest.json`, plus `post-build-audit.json`, `targeted-tests-final.log`, `full-suite-final.log`, `native-stage.json` and `native-independent-verification.json` under `out/pon-731/`. The four build-preparation failures and initial staging refusal are retained there. Historical sampling and its consumed permission: [POWER-PON-REASON.md](POWER-PON-REASON.md).
