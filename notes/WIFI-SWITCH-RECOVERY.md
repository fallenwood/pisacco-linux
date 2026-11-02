# Wi-Fi 切换后断连与受控恢复 / Wi-Fi Switch Loss and Reviewed Recovery

> 隐私 / Privacy: 网络、设备及运行标识仅保存在受保护的本地证据中。
> `${...}` 为占位符，示例不能原样执行。代码和证据路径相对于仓库根目录，
> 通用手机系统路径除外。
> Network, device and run identifiers remain in protected local evidence.
> `${...}` denotes placeholders, not replayable configuration. Code and evidence
> paths are repository-relative except generic phone system paths.

## 中文

### 现象与证据边界

用户报告手动切换首选网络后断连，重启也未自动连接。USB 严格主机密钥 SSH 确认：
实际仍为 `7.3.1-picasso-wifi2`，屏幕服务正常；Wi-Fi 服务开机启用但启动失败，
错误为 `Unclean NV lifecycle; operator review required`。

上一启动的 NetworkManager 日志显示：已有连接先被新激活请求断开，随后首选
5 GHz 配置进入 `need-auth`，等待凭据。两个既有配置的 SSID、频段、永久 MAC、
WPA2/CCMP、`drop`、不自动连接及不保存秘密等属性没有变化，没有证据指向新增
未授权 SSID 或密码错误。

此前提供的 `nmcli --ask connection up` 建议不适合直接在 Wi-Fi SSH 上执行：
旧连接可能在密码提示完成前断开。既有凭据实际由 root 私有 `passwd-file` 提供，
不能假设 NetworkManager 会自行保存或再次取得它们。

旧 dirty 属于上次启动，普通 NV 工作副本中一个文件不同于干净 checkpoint。
上个射频会话有 ready 记录，但没有完整 result/cleanup；没有发现 pstore 崩溃记录。
这些只证明生命周期未正常收尾，不能据此确定强制重启、内核崩溃或固件故障。
失败启动显示的 `safe_cleanup_complete` 也只描述本次未启动射频的清理，
不能否认上次遗留的 dirty 或接受变化副本。

### 经明确授权的恢复

先核验原只读普通备份的来源、root/0400/单链接/大小和摘要，再取得本次新授权：
保留三个现有工作副本、旧 checkpoint、旧 dirty，然后仅从这些已有备份恢复
Linux 普通工作文件。恢复前核对本启动、精确旧标记、当前摘要、所有射频所有者停止、
DSP 离线、WLAN 不存在、MPSS/WLAN/RMTFS 模块未加载和没有打开的工作文件描述符。

先保存变化副本和元数据，再逐个原子替换并读回，提交新的工作 checkpoint，
最后归档旧 dirty。没有读取或写入原始 NV 分区，没有修改只读原备份、固件或 `boot`。
没有把变化副本直接登记为“干净”，也没有关闭生命周期保护。

随后只启动一次 `picasso-wifi-autoconnect-cn-7.3.1.service`，沿用已有优先/回退策略。
首选 5 GHz 仍超时，2.4 GHz 回退完成授权关联、DHCP、DNS 与证书 HTTPS 校验；
服务 active/enabled、自动重启次数为零，并保持至少 45 秒受保护就绪。
实际非 USB 路由的严格主机密钥 LAN SSH 与同一启动匹配。
已加载 QRTR 身份仍匹配此前修复版本。

当前 dirty 属于新的活跃射频会话，是预期状态，不可删除；射频运行时不要拿变化中的
工作副本与上次干净 checkpoint 作比较。服务保留开机启用，但本轮没有再次重启验收，
没有宣称修复 5 GHz、自动失联重连或长期稳定性。

### 后续命令的安全边界

优先从 USB SSH 操作。只切换已经授权且已有安全配置的网络；新 SSID 仍需同步审查
白名单、凭据和完整性绑定。不要在唯一的 Wi-Fi SSH 通道中交互等待密码，
不要通过命令参数传递密码，也不要显示、复制或导出凭据文件内容。

例如，以下仅说明在已有受保护射频所有者 active 时，如何让 native nmcli 使用
已存在的回退凭据；占位符必须从受保护配置取得，不是额外试验授权：

```sh
sudo systemctl is-active picasso-wifi-autoconnect-cn-7.3.1.service
sudo nmcli --wait 25 connection up id "picasso-auto-${FALLBACK_SSID}" ifname wlan0 \
  passwd-file "/var/lib/picasso-wifi/credentials/${FALLBACK_SSID}.passwd"
```

使用凭据文件只能避免交互取密，不能保证 5 GHz 成功或 SSH 不断。
如果只能远程使用 Wi-Fi，切换任务还须独立于 SSH 生命周期并设计有界失败回退；
本轮未实现或验收这种通用切换入口。
不要启动旧版本所有者或另一套完整 worker 与现有服务争用。

需要正常重启时，应先通过 USB 停止当前版本 Wi-Fi 服务，确认 checkpoint 已提交、
DSP/WLAN 已退出、旧活跃 dirty 已消失；仅看 stop 返回值不足。
若清理未通过，先诊断，不删标记强行继续。本轮没有执行新的 stop/reboot 试验。

## English

### Symptom and limits of the evidence

The operator reported losing connectivity after manually switching to the preferred
network, followed by no automatic connection after reboot. Strict-pinned USB SSH
confirmed native `7.3.1-picasso-wifi2` and a healthy screen service. Wi-Fi remained
boot-enabled but startup failed with
`Unclean NV lifecycle; operator review required`.

The preceding boot's NetworkManager journal showed the existing connection being
disconnected for a new activation, then the preferred 5 GHz profile entering
`need-auth`. Both existing profiles retained their SSIDs, bands, permanent MAC,
WPA2/CCMP, `drop`, no-autoconnect and not-saved-secret properties. There was no
evidence of an added unauthorized SSID or an incorrect password.

The earlier `nmcli --ask connection up` advice was unsuitable for direct use over
Wi-Fi SSH: the old connection can disappear before the password prompt completes.
Existing credentials are supplied through a root-private `passwd-file`; do not
assume NetworkManager saves or automatically reacquires them.

The dirty marker belonged to the preceding boot, and one ordinary NV work file
differed from the clean checkpoint. The preceding radio session had a ready record
but no completed result/cleanup; no pstore crash record was found. This establishes
an unclean lifecycle, not whether a forced reboot, kernel crash or firmware fault
caused it. The failed startup's `safe_cleanup_complete` described only its own
unarmed cleanup, not clearance of the preceding dirty state or acceptance of
changed copies.

### Explicitly authorized recovery

First verify provenance, root/0400/single-link/size metadata and digests of the
existing ordinary read-only backups, then obtain fresh approval to preserve all
three work copies, checkpoint and dirty marker and restore only Linux ordinary
work files from those backups. Before restoration, check the exact current boot,
reviewed marker and work hashes, stopped radio owners, offline DSP, absent WLAN,
unloaded MPSS/WLAN/RMTFS modules, and no open work-file descriptors.

Preserve copies and metadata before atomic file replacement and readback. Commit
the restored work checkpoint before archiving the old marker. No raw NV partition
was accessed, and original read-only backups, firmware and `boot` were unchanged.
Changed copies were not simply declared clean, and lifecycle guards remained.

Start `picasso-wifi-autoconnect-cn-7.3.1.service` exactly once using the existing
priority/fallback policy. Preferred 5 GHz still timed out; 2.4 GHz fallback passed
authorized association, DHCP, DNS and certificate-verified HTTPS. The service was
active/enabled with zero automatic restarts and at least 45 seconds of guarded
readiness. Actual strict-pinned LAN SSH used a non-USB route and matched the same
boot. The loaded QRTR identity still matched the previously repaired version.

Current dirty state belongs to the new active radio session and must remain.
Do not compare actively changing work files with the preceding clean checkpoint.
Boot enablement remains, but no additional reboot acceptance was performed in this
round. This does not fix 5 GHz, enable automatic link-loss reconnection or qualify
long-term stability.

### Boundaries for subsequent commands

Prefer USB SSH. Switch only to an authorized network with an existing guarded
profile; new SSIDs still require coordinated whitelist, credential and integrity
review. Do not wait interactively for a password over the only Wi-Fi SSH channel,
put passwords in command arguments, or display/copy/export credential contents.

For example, the following only illustrates native nmcli consuming existing
fallback credentials while the guarded radio owner is active. Resolve placeholders
from protected configuration; this is not authorization for another experiment:

```sh
sudo systemctl is-active picasso-wifi-autoconnect-cn-7.3.1.service
sudo nmcli --wait 25 connection up id "picasso-auto-${FALLBACK_SSID}" ifname wlan0 \
  passwd-file "/var/lib/picasso-wifi/credentials/${FALLBACK_SSID}.passwd"
```

A credential file avoids interactive secret acquisition; it guarantees neither
5 GHz success nor uninterrupted SSH. A Wi-Fi-only remote switch also requires a
task independent of the SSH lifetime and bounded failure fallback. No such general
switching entry point was implemented or accepted in this round.
Do not start old owners or another complete worker alongside the active service.

Before a required normal reboot, use USB to stop the current-version Wi-Fi
service and verify checkpoint commit, DSP/WLAN shutdown and disappearance of its
active dirty marker. A successful stop command alone is insufficient. Diagnose
failed cleanup rather than deleting the marker. No new stop/reboot trial occurred.

## 本地证据 / Local evidence

以下证据含私有元数据，仅保存在被忽略的本地目录中，不随文档发布。
The following contain private metadata and remain in ignored local storage.

- `out/linux-7.3.1/device-acceptance/731-wifi-switch-loss-native.json`
- `out/linux-7.3.1/device-acceptance/731-wifi-switch-loss-diagnosis.json`
- `out/linux-7.3.1/device-acceptance/731-wifi-switch-loss-recovery-options.json`
- `out/linux-7.3.1/device-acceptance/731-wifi-switch-loss-recovery-consent.json`
- `out/linux-7.3.1/device-acceptance/731-wifi-switch-loss-nv-recovery.json`
- `out/linux-7.3.1/device-acceptance/731-wifi-switch-loss-wifi-recovery.json`
- `out/linux-7.3.1/device-acceptance/731-wifi-switch-loss-lan-ssh.json`
