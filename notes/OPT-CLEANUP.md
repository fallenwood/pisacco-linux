# 手机 /opt Picasso 脚本清理 / Phone /opt Picasso Script Cleanup

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

## 范围与结果 / Scope and outcome

中文：按本次会话日期 **2026-10-31** 记录。用户要求清理手机 `/opt` 下 Picasso 脚本，
并在明确的清单与归档/删除选项中选择了**永久删除已确认废弃脚本**。
本次删除 32 个脚本、14 个引用它们的未启用试验单元、4 个对应 Python 缓存，
再用非递归 `rmdir` 删除 6 个确认已空的目录。保留 26 个有用脚本，
未建立被删除脚本的手机归档，仅保存清单、哈希和操作结果。

English: Recorded against the session date, **2026-10-31**. The user requested
cleanup of Picasso scripts under the phone's `/opt` and explicitly selected
**permanent deletion of confirmed obsolete scripts** after receiving the scope
and archive/delete options. Removed 32 scripts, 14 non-enabled trial units
referencing them, four matching Python cache files and, using nonrecursive
`rmdir`, six confirmed-empty directories. Retained 26 useful scripts. No phone-side
archive of deleted script contents was created; only manifests, hashes and
operation results were saved.

中文：通过 Wi-Fi `${DEVICE_USER}@${PHONE_LAN_IP}` 连接，继续严格核验已固定的设备 SSH 主机密钥，
不因地址变化接受新密钥。设备时钟当时返回 2026-10-28，因此手机证据目录名中的
`20261028T101234Z` **不是可信的本次实际日期**。未修改时钟、NTP 或现有历史记录。
下列代码、命令与本地证据路径相对于仓库根目录；手机绝对路径另行标明。

English: Connected over Wi-Fi as `${DEVICE_USER}@${PHONE_LAN_IP}`, retaining strict
verification against the pinned device SSH host key rather than trusting a new
key for the changed address. The phone clock returned 2026-10-28, so the phone
evidence-directory timestamp `20261028T101234Z` **is not a trusted date of this
operation**. No clock, NTP or historical-record changes were made. Code, commands
and local evidence paths below are repository-root-relative; absolute phone
paths are identified separately.

## 为什么保留旧 Wi-Fi 目录 / Why older Wi-Fi directories remain

中文：当前开机自动连接服务不是独立单文件，仍使用以下精确固定的导入链：

English: The current boot-association service is not standalone; it still uses
this exact pinned import chain:

```text
/opt/picasso-wifi-autoconnect-cn/wifi-autoconnect-cn-service.py
  -> /opt/picasso-wifi-cn-raw/wifi-cn-raw-radio-service.py
  -> /opt/picasso-wifi-cn/wifi-cn-radio-service.py
  -> /opt/picasso-wifi-radio/wifi-radio-service.py
  -> /opt/picasso-wifi/wifi-auto-service.py
```

中文：旧单元 disabled 不代表这些源码无用。`config-auto.json` 还固定了
`/opt/picasso-wifi/wifi-service.py` 的哈希，即使当前入口不直接执行它，也必须保留。
`picasso-wifi-trial` 中的 Python jail、RMTFS 代理、QRTR 用户空间、库、模块及
TFTP 环境仍被当前无线所有者使用，不能整目录删除。两个凭据录入工具作为维护入口保留，
但本次没有执行，也没有读取、哈希或导出凭据内容。

English: Disabled older units do not make these sources obsolete.
`config-auto.json` also pins `/opt/picasso-wifi/wifi-service.py`, which must remain
even though the current entry point does not execute it directly.
The Python jail, RMTFS proxy, QRTR userspace/libraries, modules and TFTP environment
under `picasso-wifi-trial` still serve the current wireless owner; deleting the
whole directory would break it. Two credential-entry tools remain as maintenance
entry points, but neither was executed and no credential contents were read,
hashed or exported.

## 保留的 26 个脚本 / The 26 retained scripts

| 手机目录 / Phone directory | 保留文件 / Retained files | 用途 / Purpose |
| --- | --- | --- |
| `/opt/picasso-power-button` | `power-button-daemon.py`, `power-hold-policy.py` | 已安装电源键服务及策略，保留其现有失败状态 / Installed power-key service and policy, preserving its existing failure |
| `/opt/picasso-screen` | `screen-console.py`, `screen-service.py`, `screen-volume-policy.py` | 原生 tty1、15 秒熄屏、音量上亮屏与租约 / Native tty1, 15-second idle, volume-up wake and lease |
| `/opt/picasso-startup` | `wait-for-cool.py` | 启动前冷却保护 / Startup cooldown guard |
| `/opt/picasso-wifi` | `audit-wifi-regulatory.py`, `enter-wifi-autoconnect.py`, `fdt.py`, `provision-wlan-mac.py`, `rmtfs-supervised.py`, `wifi-auth-evidence.py`, `wifi-auto-service.py`, `wifi-bss.py`, `wifi-fallback-policy.py`, `wifi-service.py` | 无线控制器、固定资产、审计、后端及凭据维护 / Wireless controllers, pinned assets, auditing, backend and credential maintenance |
| `/opt/picasso-wifi-autoconnect-cn` | `wifi-autoconnect-cn-service.py` | 当前 CN 开机连接入口 / Current CN boot-association entry point |
| `/opt/picasso-wifi-cn` | `audit-wifi-regulatory-cn.py`, `wifi-cn-radio-service.py` | 被继承的 CN 适配及规则解析 / Inherited CN adapter and rule parsing |
| `/opt/picasso-wifi-cn-raw` | `audit-wifi-regulatory-cn-raw.py`, `wifi-cn-raw-radio-service.py`, `wifi-nl80211-channels.py` | 同 PHY 原始监管属性采集与核验 / Same-PHY raw regulatory collection and validation |
| `/opt/picasso-wifi-radio` | `wifi-radio-service.py` | 普通未关联/掉线仍保持 UP 的父控制器 / Parent controller retaining UP on ordinary unassociated/link-loss states |
| `/opt/picasso-wifi-trial` | `${WIFI_CREDENTIAL_HELPER}` | 受限凭据录入维护工具 / Bounded credential-entry maintenance tool |
| `/opt/picasso-wifi-trial/python-jail/proxy` | `rmtfs-private-proxy.py`, `rmtfs-supervised.py` | 当前私有 FD-only RMTFS 后端 / Current private FD-only RMTFS backend |

## 永久删除的 32 个脚本 / The 32 permanently deleted scripts

| 手机目录 / Phone directory | 删除文件 / Deleted files | 原因 / Reason |
| --- | --- | --- |
| `/opt/picasso-display-trial` | `handoff-cleanup.py`, `handoff-controller.py`, `probe-screen-redraw.py`, `probe-screen-redraw2.py`, `readonly-cleanup.py`, `readonly-controller.py`, `readonly-controller2.py`, `readonly-controller3.py`, `run-screen-visual.py`, `run-screen-visual2.py`, `test-screen-handoff.py`, `test-screen-handoff2.py` | 已结束的显示审计、交接、色条与重绘试验，共 12 个 / Completed display audits, handoff, color-bar and redraw trials; 12 files |
| `/opt/picasso-power` | `power-hold-policy.py`, `power-key-guided2.py`, `power-key-service.py`, `power-observe-current.py`, `power-shutdown-cancel-guided2.py`, `power-shutdown-cancel.py`, `power-shutdown-current.py`, `power-shutdown-guided2.py` | 旧一次性输入/关机试验；已安装服务使用独立目录，共 8 个 / Old one-shot input/shutdown trials; the installed service uses its own directory; eight files |
| `/opt/picasso-power/pon-read1` | `collect-pon-reason.py`, `power-pon-reasons.py` | 已完成且不应重放的一次 PON 采样，共 2 个 / Completed one-time PON sampling that must not be replayed; two files |
| `/opt/picasso-screen` | `probe-kernel-lease.py`, `visual-render.py` | 已结束的租约探针与不再使用的色条 renderer，共 2 个 / Completed lease probe and unused color-bar renderer; two files |
| `/opt/picasso-screen-preparation` | `screen-idle-before-fbcon-fix.py`, `screen-idle-policy.py`, `screen-idle.py` | 被常驻文字控制台替代的准备版本，共 3 个 / Preparation versions superseded by the persistent text console; three files |
| `/opt/picasso-wifi` | `diagnose-wifi-link.py` | 已结束的独立掉线观测试验 / Completed independent link-loss observation trial |
| `/opt/picasso-wifi-reconnect` | `wifi-reconnect-service.py` | 已禁用且不属于当前所有者依赖的旧重连入口 / Disabled old reconnect entry point outside the current owner's dependencies |
| `/opt/picasso-wifi-trial` | `provision-wlan-mac.py` | 重复副本；实际使用 `/opt/picasso-wifi/provision-wlan-mac.py` / Duplicate; the live path is `/opt/picasso-wifi/provision-wlan-mac.py` |
| `/opt/picasso-wifi-trial/python-jail/proxy` | `fd-selftest.py`, `fd-selftest-2.py` | 已完成的 FD sandbox 自测，不是运行期代理，共 2 个 / Completed FD-sandbox self-tests, not runtime proxies; two files |

中文：删除的源码共 147,140 字节；加上试验单元与缓存共 215,258 字节。
这只是被删除文件的逻辑大小，不是 filesystem 可用空间增长承诺。
旧 `.ko`、试验结果、授权/消耗标记与历史 manifest 均未顺带删除。

English: Deleted source files totaled 147,140 bytes; including trial units and
caches, deleted files totaled 215,258 bytes. These are logical file sizes,
not a promise of filesystem free-space growth. Old `.ko` files, trial results,
authorization/consumed markers and historical manifests were not swept away.

## 试验单元与空目录 / Trial units and empty directories

中文：以下 14 个 `/etc/systemd/system/` 单元均在删除前确认 inactive/dead、
MainPID=0、static 或 disabled，且没有 RequiredBy/WantedBy/TriggeredBy 引用。
删除后仅执行 `systemctl daemon-reload`，没有 stop/start/restart 或 reset-failed。

English: Each of these 14 units under `/etc/systemd/system/` was confirmed
inactive/dead, MainPID=0, static or disabled, with empty
RequiredBy/WantedBy/TriggeredBy references before deletion. Only
`systemctl daemon-reload` followed removal; no stop/start/restart or reset-failed
was performed.

```text
picasso-display-handoff-test.service
picasso-display-readonly-audit.service
picasso-display-readonly-audit2.service
picasso-display-readonly-audit3.service
picasso-display-visual1.service
picasso-display-visual2.service
picasso-fb-redraw1.service
picasso-fb-redraw2.service
picasso-pon-reason-read1.service
picasso-screen-kernel-lease-probe.service
picasso-wifi-link-observe1.service
picasso-wifi-link-observe2.service
picasso-wifi-reconnect-check1.service
picasso-wifi-reconnect.service
```

中文：同时删除下列 4 个来源明确的 Python 缓存；随后仅对列出的 6 个空目录使用
`rmdir`，没有通配递归删除 `/opt/picasso*`：

English: Also removed these four source-specific Python cache files, then used
`rmdir` only on the six listed empty directories. No wildcard recursive deletion
of `/opt/picasso*` occurred:

```text
# Python caches / Python 缓存
/opt/picasso-display-trial/__pycache__/test-screen-handoff.cpython-314.pyc
/opt/picasso-power/__pycache__/power-hold-policy.cpython-314.pyc
/opt/picasso-screen-preparation/__pycache__/screen-idle-policy.cpython-314.pyc
/opt/picasso-wifi-reconnect/__pycache__/wifi-reconnect-service.cpython-314.pyc

# Empty directories / 空目录
/opt/picasso-display-trial/__pycache__
/opt/picasso-power/__pycache__
/opt/picasso-screen-preparation/__pycache__
/opt/picasso-screen-preparation
/opt/picasso-wifi-reconnect/__pycache__
/opt/picasso-wifi-reconnect
```

## 核对与保留边界 / Checks and retained boundaries

中文：删除前对完整 58 脚本清单核对哈希、root 所有权、普通文件和路径身份，
扫描运行进程以及 systemd、udev、cron、本地命令目录的引用。
一次无写入预检先因 session JSON 没有 `pid` 字段退出，另一次因保留的
`libqrtr.so.1` 是合法库符号链接而退出；修正采集器为从 systemd MainPID 取 PID，
仅对保留资产解析库链接，删除对象仍禁止符号链接。两次拒绝均未删除文件。
最终完整预检通过后才执行已批准的精确清单。

English: Before deletion, verified the complete 58-script inventory against
hashes, root ownership, ordinary-file and path identities, and checked live
processes and references from systemd, udev, cron and local command directories.
One no-write preflight exited because session JSON has no `pid` field; another
exited because retained `libqrtr.so.1` is a legitimate library symlink.
The collector was corrected to obtain PID from systemd MainPID and resolve
library links only for retained assets; deletion targets still reject symlinks.
Neither refusal deleted files. The approved exact list was executed only after
the complete final preflight passed.

| 核对项 / Check | 结果 / Result |
| --- | --- |
| Boot | `${BOOT_ID_1}` 未变 / Unchanged |
| WLAN 所有者 / WLAN owner | `picasso-wifi-autoconnect-cn.service` enabled/active，PID879、session `${SESSION_2}` 未变 / Enabled/active; PID879 and session `${SESSION_2}` unchanged |
| 屏幕 / Screen | `picasso-screen.service` enabled/active，PID883、run `${RUN_ID_1}` 未变 / Enabled/active; PID883 and run `${RUN_ID_1}` unchanged |
| 无线子服务 / Wireless child services | RMTFS PID961、TFTP PID959 active，未重启 / RMTFS PID961 and TFTP PID959 active, not restarted |
| 链路 / Link | `wlan0` UP+LOWER_UP、`${PHONE_LAN_IP}/24`；新 SSH 成功，NM `100 (connected)` / `wlan0` UP+LOWER_UP at `${PHONE_LAN_IP}/24`; fresh SSH succeeded, NM `100 (connected)` |
| 背光租约 / Backlight lease | `owner_pid=883 expired=0`，3 秒租约健康 / `owner_pid=883 expired=0`, healthy three-second lease |
| 保留文件 / Retained files | 26 个脚本哈希/元数据未变；67 项固定/受保护资产指纹未变 / Hashes/metadata of 26 scripts and fingerprints of 67 pinned/protected assets unchanged |
| 无 RF 文件检查 / No-RF file check | 删除前后 `--check-files` 均返回 `CN_boot_autoconnect_files_verified_no_RF` / `--check-files` returned `CN_boot_autoconnect_files_verified_no_RF` before and after |
| 原有失败 / Existing failures | 电源键单元 enabled/failed 与旧 raw-CN 单元 disabled/failed 原样保留 / Power-key enabled/failed and old raw-CN disabled/failed states preserved |
| 温度 / Temperature | 最终无写入预检最高 35.7°C，删除后快照最高 37.4°C；不是连续峰值证明 / Final no-write preflight max 35.7°C, post-delete snapshot max 37.4°C; not proof of a continuous peak |

中文：没有重启手机、重启射频、重新连接 SSID、调用试验 cleanup、改 boot/PMIC、
访问原始 NV、导出凭据/SSH 私钥、改防火墙或调用 Podman。
现有 dirty、重连预算、失败/消耗标记与日志保持；不把旧试验删除解释为故障修复。
未修复电源键服务的既有失败，也没有进行物理按键或下次开机验收。
SSH 的既有 `.bashrc` 缺失 `mise` 告警未在本次处理。

English: No phone reboot, radio restart, SSID reconnection, trial cleanup,
boot/PMIC change, original-NV access, credential/SSH-private-key export,
firewall change or Podman command occurred. Existing dirty state, reconnect
budgets, failure/consumed markers and logs remain. Removing old trials is not a
hardware-fault fix. The pre-existing power-key failure was not repaired, and
physical-key or next-boot acceptance was not performed. The existing SSH
`.bashrc` missing-`mise` warning was outside this cleanup.

中文：这是对已列出旧脚本/单元的明确授权删除，历史文档中这些文件曾存在的路径仍保留为
历史证据，不应再按旧命令重放。旧 payload/static manifest 不应被改写成“全字节未变”；
后续检查须以此次精确删除清单解释差异，不能通配忽略其他文件。
当前服务的配置、源码哈希和保护并未为清理而放宽。

English: This explicitly authorized retirement applies only to the listed old
scripts/units. Their paths remain in historical notes as evidence, not commands
to replay. Old payload/static manifests must not be rewritten into claims of
complete byte equality. Future checks must account for this exact deletion list
without wildcard exclusions for other files. Current service configuration,
source hashes and protections were not relaxed for cleanup.

## 证据 / Evidence

中文：主机私有目录 `out/opt-cleanup-20261031/` 为 0700，JSON、日志与校验清单为 0600；
此日期来自本次会话，不继承手机错误时钟。手机 root-only 目录为
`/var/lib/picasso-admin/opt-cleanup-20261028T101234Z/`，名称仅按当时设备时钟生成。

English: The private host directory `out/opt-cleanup-20261031/` is 0700, with
0600 JSON, logs and checksum manifest. Its date follows this session, not the
incorrect phone clock. The root-only phone directory is
`/var/lib/picasso-admin/opt-cleanup-20261028T101234Z/`; its name was generated
from the phone's clock and carries no trusted real-date assertion.

| 文件 / File | 内容 / Contents |
| --- | --- |
| `intent.json` | 删除/保留精确路径、SHA256/元数据、67 项资产与执行前服务快照 / Exact delete/retain paths, SHA256/metadata, 67 assets and pre-operation service snapshot |
| `result.json` | 实际 50 个删除文件、删除后状态与无 RF 校验结果 / The 50 actual removed files, post-delete state and no-RF verification |
| `fresh-verification.json` | 新 Wi-Fi SSH 的独立复核与 6 个空目录清理结果 / Independent fresh Wi-Fi SSH verification and six empty-directory removals |
| `phone-opt-before.log` | 初始脚本、进程、单元与温度盘点，仅主机 / Initial script/process/unit/temperature inventory, host only |
| `phone-opt-dependencies.log` | 源码引用、固定文件与完整脚本哈希盘点，仅主机 / Source references, pinned files and complete script hashes, host only |
| `SHA256SUMS` | 主机五份证据文件校验清单 / Host checksum manifest for the five evidence files |
