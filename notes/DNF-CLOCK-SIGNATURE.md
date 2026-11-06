# DNF 签名失败与系统时钟 / DNF Signature Failure and System Clock

> 2026-11-06 UTC 日期快照，非实时状态或再次操作授权。仓库代码及 `out/` 路径
> 相对于仓库根目录，文档链接相对于 `notes/`；私有地址、账号、标识和摘要不公开。
> Dated snapshot, 2026-11-06 UTC; not live status or another operation grant.
> Code and `out/` paths are repository-root-relative; document links are relative
> to `notes/`. Private addresses, accounts, identifiers and digests are withheld.

## 中文

### 原因与诊断

用户报告 Fedora 44 aarch64 的 `less-color-710-2.fc44.aarch64.rpm` 在 DNF
`Running transaction` 阶段失败，外层信息为 `Signature verification failed` 和
`Problem occurred when opening the package`。这不足以判定缓存损坏、密钥缺失或
文件权限问题，必须先查看 `rpmkeys --checksig --verbose` 的具体原因。

手机的 RPM 6.0.2 / rpm-sequoia 1.10.3 返回：

```text
Header OpenPGP V4 RSA/SHA256 signature: BAD
Header SHA256 digest: OK
Payload SHA256 digest: OK
signature is not alive
Not live until 2026-11-02T11:08:52Z
```

包签名创建于 2026-11-02 11:13:52 UTC，但手机时间仍是 2026-11-01。
已 NTP 同步的主机与验证证书、无代理的 Fedora 官网 HTTPS `Date` 均为
2026-11-06，说明手机墙钟落后约四天半，而不只是显示时区差异。
文件是正常 RPM、普通文件和父目录权限可读，空间/inode 足够。
现有 Fedora 44 密钥无需替换；最终签名校验成功进一步排除了本包的签名损坏。

手机 `NTP=no`、`NTPSynchronized=no`，且没有可见 RTC。虽然 RPM 查询没有
`chrony` 或独立的 `systemd-timesyncd` 包记录，但实际已有可执行 timesyncd、
对应 unit、NTP unit 注册和服务账号；不能仅凭可选包查询失败就安装替代组件。

### 修复及结果

1. 保留错误、原 RPM 与当前 RF/屏幕所有者，未发现运行中的包管理事务。
2. 用严格主机密钥 SSH 接收已同步主机的时间，并再次以验证证书的 Fedora HTTPS
   时间交叉核对。仅将系统 realtime 时钟向前校正约 390,212 秒；没有 RTC/PMIC
   操作，monotonic 租约/超时不因校正被重置。
3. 对**同一个、内容摘要未变**的缓存 RPM 再运行完整签名检查：OpenPGP、header
   SHA256、payload SHA256 全部 OK，`rpm -qp` 正确返回包名/版本/架构。
4. 运行 `timedatectl set-ntp true` 启用已有服务；确认 timesyncd active/enabled、
   零重启、默认 Fedora NTP pool 已同步，`NTP=yes`、`NTPSynchronized=yes`。
5. Wi-Fi/屏幕的 systemd MainPID 与精确会话身份不变，当前有效 live dirty 内容
   摘要不变；未停止或重启这些服务，未更改[65°C 策略](THERMAL-LIMIT-65.md)。

没有清缓存、重新下载 RPM、导入/替换密钥、关闭 GPG/证书检查或修改 crypto policy；
本助手没有执行任何安装/升级事务或重启，也没有改动 NV。校时后原命令可以重试；
后续只读复核时，该版本已于 2026-11-06 07:07:01 UTC 安装，原缓存 RPM 已不在。
因此再次检查该路径以“文件不存在”拒绝，不是签名回退；安装与缓存变化并非本助手操作。
本次只验收了报错的这个 RPM，不代表所有其他包或后续完整事务均已通过。
没有进行校时后的真实重启、断网或长时间漂移验收。

诊断中的 `file` 工具缺失、可选 RPM 包查询非零退出，以及首次所有者预检假设
会话里存在 `pid` 字段导致的 `KeyError` 均保留。前两项改用现有工具继续；
第三项发生在任何校时/NTP 操作之前，改为核验 systemd MainPID 加精确会话身份。
这些提前停止不是隐去的修复成功，也没有触发恢复操作。

## English

### Cause and diagnosis

The operator reported Fedora 44 aarch64 `less-color-710-2.fc44.aarch64.rpm`
failing at DNF `Running transaction`, with outer errors `Signature verification
failed` and `Problem occurred when opening the package`. These alone do not
prove cache corruption, a missing key or file permissions; inspect the detailed
`rpmkeys --checksig --verbose` reason first.

Phone RPM 6.0.2 / rpm-sequoia 1.10.3 reported:

```text
Header OpenPGP V4 RSA/SHA256 signature: BAD
Header SHA256 digest: OK
Payload SHA256 digest: OK
signature is not alive
Not live until 2026-11-02T11:08:52Z
```

The signature was created at 2026-11-02 11:13:52 UTC, but the phone still showed
2026-11-01. Both the NTP-synchronized host and direct, certificate-verified Fedora
website HTTPS `Date` showed 2026-11-06: the phone wall clock lagged about four and
a half days, not merely a display-timezone offset. The file had normal RPM magic,
readable regular-file/parent permissions and ample free space/inodes. Existing
Fedora 44 keys needed no replacement; successful final signature verification
also rules out a damaged signature for this package.

The phone reported `NTP=no`, `NTPSynchronized=no`, with no visible RTC. Although
RPM queries had no `chrony` or standalone `systemd-timesyncd` package record, an
executable timesyncd, unit, NTP-unit registration and service account already
existed. An optional-package query failure alone is not reason to install replacements.

### Repair and result

1. Preserve the error, original RPM and current RF/screen owners; no package
   transaction process was running.
2. Receive the synchronized host time over strict-pinned SSH and independently
   cross-check certificate-verified Fedora HTTPS time again. Advance only system
   realtime by about 390,212 seconds. No RTC/PMIC operation; monotonic leases/
   deadlines are not reset by this correction.
3. Fully verify the **same cached RPM with unchanged content digest**: OpenPGP,
   header SHA256 and payload SHA256 all OK; `rpm -qp` returns correct identity.
4. Run `timedatectl set-ntp true` for the existing service. Confirm timesyncd
   active/enabled, zero restarts, synchronization using default Fedora NTP pools,
   `NTP=yes` and `NTPSynchronized=yes`.
5. Preserve Wi-Fi/screen systemd MainPIDs and exact session identities, and the
   current valid live-dirty content digest. No stop/restart of these services or
   change to the [65°C policy](THERMAL-LIMIT-65.md).

No cache removal, RPM redownload, key import/replacement, GPG/certificate bypass
or crypto-policy change. The agent performed no installation/upgrade transaction, reboot or NV change.
The original command can be retried after correction. Later read-only checks
showed this version installed at 2026-11-06 07:07:01 UTC and the original cached
RPM absent. A repeated path check therefore refused with file-not-found, not a
signature regression; the agent did not perform that installation/cache change.
Acceptance covers this reported RPM, not every other package or subsequent whole
transaction. No actual post-correction reboot, disconnected-network or long-term
drift acceptance.

Preserve diagnostic early stops: absent `file` utility, nonzero optional-package
RPM query, and first owner-precheck `KeyError` from assuming a session `pid`
field. Continue the first two with existing tools; the third occurred before any
clock/NTP change and was corrected to systemd MainPID plus exact session identity.
These are not hidden successful repairs and triggered no recovery operations.

## 证据 / Evidence

受保护、被忽略的仓库相对入口 / Protected, ignored repository-relative directory:
`out/dnf-package-open/`. 可能不在新克隆中；含私有数据，不应公开或盲目重放辅助程序。
/ May be absent from fresh clones; contains private metadata, not for publication
or blind helper replay.

- `preflight.txt`, `diagnosis.txt`, `time-state.txt`, `ntp-inspection.txt`:
  原始包、错误、时间和现有服务检查 / Original package, error, time and service checks.
- `diagnostic-refusals.json`, `result.json`: 提前停止和空的首次结果，不是成功记录 /
  Early stops and empty first result, not a success record.
- `fix-time.py`, `clock-request.json`, `clock-request-v2.json`, `result-v2.json`:
  修订后的有界操作、可信时间输入与原包前后检查 / Revised bounded operation,
  trusted-time inputs and original-package before/after verification.
- `final-state.json`: 自动同步、持久时钟文件与服务状态快照 / Automatic
  synchronization, persistent clock-file and service snapshot.
- `final-state-verified.json`, `post-user-retry.json`, `transaction-followup.txt`:
  再次缓存检查提前停止的空结果、原文件已消失及目标版本已安装的后续只读记录；
  后续会话/PID 与此前基线一致 / Empty result from the repeated cache-check early
  stop, then read-only evidence of absent cache and installed target version;
  subsequent sessions/PIDs match the earlier baseline.
