# 项目笔记索引 / Project Notes Index

## 阅读约定 / Reading conventions

中文：此目录集中保存实现、构建、安装、配置、诊断与验收细节。各笔记提供中文和英文，
保留原始阶段记录。文中“当前”、服务状态、地址、温度与测试数量属于各自记录时刻，
不是实时查询结果；失败、未验证项和授权边界不会因整理文档而改变。
较早的开机 WLAN 与熄屏更新见
[项目阶段总记录](PROJECT-LOG.md)、[文字控制台](DISPLAY-CONSOLE.md)及
[原始 CN 校验修复](WIFI-CN-RAW-FIX.md)的更新说明，下次开机仍未在该阶段实测复核。
后续 7.3.1 启动修复、重复首次射频/完整自启动验收，以及仅写 `boot` 后的
默认启动与局域网 SSH 复核，见[内核升级记录](KERNEL-7.3.1.md)。
默认现为 7.3.1，已验证的 6.18 救援镜像仍保留；早期试验与恢复记录不是当前状态。

English: This directory holds implementation, build, installation, configuration,
diagnosis and validation details. Each note provides Chinese and English while
preserving its original stage record. “Current” states, addresses, temperatures
and test counts describe that record's time, not a live query. Reorganization
does not change failures, unverified behavior or authorization boundaries.
Earlier boot-WLAN and screen-idle updates are in the update banners
of [the stage log](PROJECT-LOG.md), [the text console](DISPLAY-CONSOLE.md) and
[the raw CN repair](WIFI-CN-RAW-FIX.md); next-boot behavior was still unverified
at that stage.
See [the kernel upgrade record](KERNEL-7.3.1.md) for the subsequent startup
repair, repeated first-radio/full-autostart acceptance, and default boot/LAN SSH
verification after writing only `boot`. The default is now 7.3.1; verified 6.18
rescue images remain preserved. Earlier trial/recovery snapshots are not current state.

中文：除 Markdown 链接外，代码、命令与 `out/` 证据路径均相对于仓库根目录。
`out/`、`downloads/` 和 `src/` 是被忽略的本地产物，不保证存在于新克隆中。
涉及设备、分区、射频、电源或主机修改的历史操作不能直接重放。

English: Except for Markdown links, code, command and `out/` evidence paths are
relative to the repository root. Ignored `out/`, `downloads/` and `src/` artifacts
are local and may not exist in a fresh clone. Historical device, partition,
radio, power or host-modification operations must not be replayed blindly.

## 隐私与占位符 / Privacy and placeholders

中文：笔记内容、文件名及链接不公开真实 IP/网段、SSID、MAC、主机网卡名、
个人用户名、设备/分区/启动/会话标识、密钥及指纹、私有产物摘要，
或仓库外的本地文件路径。仓库相对路径、通用系统路径和公开上游引用可以保留。
隐私脱敏优先于历史字面值保真；技术结果、失败与授权边界仍按原阶段记录。

English: Note contents, filenames and links must not expose actual IP addresses
or subnets, SSIDs, MACs, host interface names, personal usernames,
device/partition/boot/session identifiers, keys or fingerprints, private-artifact
digests, or local file paths outside the repository. Repository-relative paths,
generic system paths and public upstream references may remain. Privacy redaction
takes precedence over literal preservation; technical outcomes, failures and
authorization boundaries retain their original historical meaning.

| 占位符 / Placeholders | 含义 / Meaning |
| --- | --- |
| `${PHONE_LAN_IP}`, `${PHONE_USB_IP}`, `${HOST_USB_IP}`, `${LAN_SUBNET}` | 设备/主机地址及局域网范围 / Device/host addresses and LAN range |
| `${PRIMARY_SSID}`, `${FALLBACK_SSID}`, `${USB_HOST_MAC}`, `${HOST_USB_INTERFACE}` | 网络名称、主机 USB MAC 与网卡 / Network names, host USB MAC and interface |
| `${DEVICE_USER}`, `${DEVICE_HOME}`, `${USER_HOME}`, `${REPO_ROOT}` | 本地账号及目录 / Local accounts and directories |
| `${SSH_PRIVATE_KEY}`, `${SSH_PUBLIC_KEY}`, `${SSH_KNOWN_HOSTS}`, `${SSH_KEY_DIR}`, `${PRIVATE_BACKUP_DIR}`, `${ROM_ARCHIVE}` | 本地密钥、主机密钥记录、备份及归档路径 / Local key, known-hosts, backup and archive paths |
| `${PARTUUID_*}`, `${BOOT_ID_N}`, `${SESSION_N}`, `${RUN_ID_N}` | 已脱敏的设备与运行标识 / Redacted device and run identifiers |
| `${SSH_KEY_FINGERPRINT_N}`, `${AUTHORIZED_KEYS_HASH_*}`, `${PRIVATE_*_SHA256*}` | 已隐藏的密钥指纹及私有产物摘要 / Withheld key fingerprints and private-artifact digests |
| `${WIFI_*}` | 含原始网络名称的脚本或文件名 / Script or file names containing original network names |

中文：`${...}` 是占位符，不是已提供的配置；上表的 `*`/`N` 表示一类名称。
同名占位符表示同一角色，不保证不同日期的实际值相同；编号只用于区分脱敏标识。
实际值必须从受保护的本地配置取得，不得把映射表写回笔记。
含占位符的历史命令、摘要和证据路径不能原样执行、校验或定位文件。
SSH 主机密钥仍须通过可信渠道核对，并保持严格的 `known_hosts` 验证。

English: `${...}` denotes a placeholder, not supplied configuration; `*`/`N` in
the table denote families of names. Repeated names describe the same role, not
necessarily the same value across dated snapshots; numeric suffixes distinguish
redacted identifiers only. Obtain actual values from protected local configuration
and never publish their mapping here. Historical commands, digests and evidence
paths containing placeholders cannot be executed, verified or located verbatim.
Verify SSH host keys through a trusted channel and retain strict `known_hosts`
checking.

## 项目与安装 / Project and installation

| 笔记 / Note | 内容 / Contents |
| --- | --- |
| [PROJECT-MAP.md](PROJECT-MAP.md) | 目录职责、构建与启动链、集成点 / Directory responsibilities, build/boot flow and integration points |
| [PROJECT-LOG.md](PROJECT-LOG.md) | 原 README 完整阶段记录、构建与打包步骤、安全边界 / Former README stage history, build/packaging instructions and safety boundaries |
| [OPT-CLEANUP.md](OPT-CLEANUP.md) | 手机 `/opt` 脚本保留/永久删除清单、依赖与在线复核 / Phone `/opt` retained/permanently deleted scripts, dependencies and live verification |
| [SOURCES.md](SOURCES.md) | 来源、版本固定、上游差异与许可 / Provenance, version pins, upstream differences and licensing |
| [KERNEL-7.3.1.md](KERNEL-7.3.1.md) | 7.3.1 启动修复、QRTR 握手、默认切换验收与 6.18 救援保留 / 7.3.1 startup/QRTR repair, accepted default switch and retained 6.18 rescue |
| [VALIDATION.md](VALIDATION.md) | 分阶段验收、失败证据与未验证项 / Stage validation, failure evidence and unverified behavior |
| [CONFIRMATION.md](CONFIRMATION.md) | 设备与 RAM 确认、授权范围和早期验证 / Device/RAM confirmation, authorization and early validation |
| [RAM-FEDORA.md](RAM-FEDORA.md) | RAM 根文件系统与原生 Fedora 交接 / RAM root filesystem and native Fedora handoff |
| [INSTALL-PLAN.md](INSTALL-PLAN.md) | 持久安装范围、分区布局与恢复材料 / Persistent-install scope, partition layout and recovery materials |
| [INSTALL-XFS.md](INSTALL-XFS.md) | XFS 安装、持久启动、登录和回退记录 / XFS installation, persistent boot, login and rollback records |
| [LAN-SSH.md](LAN-SSH.md) | LAN SSH、防火墙、公钥与 SELinux 状态 / LAN SSH, firewall, public keys and SELinux state |
| [PODMAN-USER-SESSION.md](PODMAN-USER-SESSION.md) | 用户 manager、D-Bus 与 Podman 会话修复 / User manager, D-Bus and Podman session repair |

## 显示 / Display

| 笔记 / Note | 内容 / Contents |
| --- | --- |
| [DISPLAY.md](DISPLAY.md) | 原始显示审计与准备 / Initial display audit and preparation |
| [DISPLAY-HANDOFF.md](DISPLAY-HANDOFF.md) | WLED 背光交接与受限试验 / WLED backlight handoff and bounded trial |
| [DISPLAY-REDRAW.md](DISPLAY-REDRAW.md) | fbcon 覆盖定位与重绘修补 / fbcon overwrite diagnosis and redraw correction |
| [DISPLAY-VISUAL2.md](DISPLAY-VISUAL2.md) | 第二轮单键色条目视验收 / Second single-key color-bar visual acceptance |
| [DISPLAY-PERSISTENT.md](DISPLAY-PERSISTENT.md) | 历史色条服务持久化与重启复核 / Historical color-bar persistence and reboot verification |
| [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md) | 原生 tty1、15 秒熄屏与启动冷却更新 / Native tty1, 15-second idle and startup-cooldown update |

## 电源 / Power

| 笔记 / Note | 内容 / Contents |
| --- | --- |
| [POWER-KEY.md](POWER-KEY.md) | 电源键输入与受限长按设计 / Power-key input and bounded hold design |
| [POWER-KEY-OBSERVED.md](POWER-KEY-OBSERVED.md) | 实键观察与失败记录 / Real-key observations and failures |
| [POWER-KEY-COOLDOWN.md](POWER-KEY-COOLDOWN.md) | 冷却与分阶段试验约束 / Cooldown and staged-trial constraints |
| [POWER-SHUTDOWN-GUIDED2.md](POWER-SHUTDOWN-GUIDED2.md) | 第二轮引导式正常关机试验 / Second guided normal-shutdown trial |
| [POWER-CYCLE-REVIEW.md](POWER-CYCLE-REVIEW.md) | 关机与开机证据复核 / Shutdown/power-on evidence review |
| [POWER-CYCLE-POSTBOOT.md](POWER-CYCLE-POSTBOOT.md) | 后续启动快照与待确认项 / Postboot snapshot and pending confirmation |
| [POWER-AUTOSTART.md](POWER-AUTOSTART.md) | 自行启动的已知失败与边界 / Known self-start failure and boundaries |
| [POWER-CHAIN-AUDIT.md](POWER-CHAIN-AUDIT.md) | 电源链只读审计与限制 / Read-only power-chain audit and limitations |
| [POWER-PON-REASON.md](POWER-PON-REASON.md) | PON/POFF 采样与解释边界 / PON/POFF sampling and interpretation limits |
| [POWER-PERSISTENT.md](POWER-PERSISTENT.md) | 接受已知限制后的 DTB 与服务固化 / DTB/service persistence after accepting known limitations |

## Wi-Fi

| 笔记 / Note | 内容 / Contents |
| --- | --- |
| [WIFI-BRINGUP.md](WIFI-BRINGUP.md) | MPSS/QRTR 早期启动与阻塞 / Early MPSS/QRTR bring-up and blockers |
| [WIFI-RMTFS.md](WIFI-RMTFS.md) | 私有 NV 副本、RMTFS 与固定 MSA 准备 / Private NV copies, RMTFS and fixed-MSA preparation |
| [WIFI-SCAN.md](WIFI-SCAN.md) | WLAN 注册与 AP 广播扫描 / WLAN registration and AP advertisement scan |
| [WIFI-CONNECTION.md](WIFI-CONNECTION.md) | 首次关联前的配置与保护 / Configuration and guards before first association |
| [WIFI-CONNECTION-TEST.md](WIFI-CONNECTION-TEST.md) | 认证失败的原生试验记录 / Native authentication-failure trial |
| [WIFI-DIAGNOSTIC-PATCHES.md](WIFI-DIAGNOSTIC-PATCHES.md) | 可选诊断补丁、独立构建和清理要求 / Optional diagnostic patches, separate build and cleanup requirements |
| [WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md) | 管理帧状态与 HT20 诊断 / Management-frame status and HT20 diagnosis |
| [WIFI-2G-PREPARATION.md](WIFI-2G-PREPARATION.md) | 2.4 GHz 试验准备 / 2.4 GHz trial preparation |
| [WIFI-2G-CONNECTION.md](WIFI-2G-CONNECTION.md) | 2.4 GHz 关联、掉线与后续试验 / 2.4 GHz association, loss and subsequent trials |
| [WIFI-NETWORK.md](WIFI-NETWORK.md) | WPA2、DHCP、DNS、证书 HTTPS 与监管核验 / WPA2, DHCP, DNS, certificate HTTPS and regulatory checks |
| [WIFI-INSTALL.md](WIFI-INSTALL.md) | 原 Wi-Fi #10 安装与回退镜像 / Original Wi-Fi #10 installation and rollback images |
| [WIFI-AUTOCONNECT.md](WIFI-AUTOCONNECT.md) | 双 SSID 优先/回退与故障清理 / Dual-SSID priority/fallback and fault cleanup |
| [WIFI-LINK-LOSS.md](WIFI-LINK-LOSS.md) | BEACON_MISS 与后续删钥超时的触发链 / BEACON_MISS and subsequent key-deletion timeout sequence |
| [WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md) | 历史自动连接服务启用与观察 / Historical automatic-association enablement and observation |
| [WIFI-RECONNECT.md](WIFI-RECONNECT.md) | 有界重连预算、退避与耗尽记录 / Bounded reconnect budget, backoff and exhaustion |
| [WIFI-RADIO-UP.md](WIFI-RADIO-UP.md) | 未关联/普通掉线仍保留网卡 UP / Interface UP during unassociated/ordinary-loss states |
| [WIFI-CN.md](WIFI-CN.md) | CN 切换与旧文本审计拒绝 / CN transition and old text-audit rejection |
| [WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md) | iw 文本取证缺陷与原始 nl80211 方案 / iw text-evidence defect and raw nl80211 approach |
| [WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md) | 原始 INDOOR_ONLY 修复与开机自动连接更新 / Raw INDOOR_ONLY repair and boot-association update |
