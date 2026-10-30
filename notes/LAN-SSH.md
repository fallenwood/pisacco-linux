# 局域网SSH已放行、公钥已添加；Wi-Fi当前离线，SELinux内核仍Permissive / LAN SSH Allowed and Public Key Added; Wi-Fi Offline at This Stage, Kernel SELinux Still Permissive

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录；“当前”等状态按原记录时间理解，反引号中的代码及证据路径相对于仓库根目录。 / Historical stage record; “current” refers to the recorded stage. Code and evidence paths in backticks are relative to the repository root.

## 中文

> 最新[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)：R2已enabled/active，原始CN位核验通过，${FALLBACK_SSID}取得${PHONE_LAN_IP}/24并通过CCMP/DHCP/DNS/证书HTTPS200和后续实时复核。原来源限定LAN22/drop规则、公钥仍在；新公钥从另一台机器登录尚未验收，IP/是否在线以后必须实时确认。
>
> 此前域切换见[WIFI-CN.md](WIFI-CN.md)：global CN和持久配置已核实，但新CN服务因5GHz室内限制标志核验失败而failed，当前WLAN/DSP已清理、无IPv4，LAN SSH仍不可用；原SSH规则/公钥/实际SELinux不变。
>
> 此前SG无线状态见[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)：一次指定2.4GHz NM激活返回0后触发监管域检查拒绝，radio服务enabled/failed并完整安全退出；当前WLAN absent/DSP offline/dirty absent，无Wi-Fi IPv4，不能经LAN SSH。此前UP/活跃dirty快照是历史，不能据此称仍运行。SSH规则、公钥及SELinux实际Permissive不变。

> 后续掉线重连已另获授权安装，新默认服务是`picasso-wifi-reconnect.service`，旧auto已disabled但failed保留。真机3次自动恢复成功，随后本boot初连＋3次耗尽，当前又离线且安全清理。最新[WIFI-RECONNECT.md](WIFI-RECONNECT.md)；本页SSH/SELinux事实不变，旧Wi-Fi状态是配置时快照。

用户请求：**“放行所有局域网ip, 关闭selinux, 使用./id_ed25519.pub”**。
仅修改普通文件与firewalld规则，没有重启、写boot、恢复Wi-Fi或读取任何私钥。

## 已应用

- 将上一轮实际DHCP网络`${LAN_SUBNET}`的所有IPv4来源放行到SSH **TCP22**。
  在原drop zone添加精确source/port accept rich rule，runtime与permanent均独立query通过。
  不把整个zone设trusted，不放行IPv6、其他网段或其他端口，不关闭firewalld，不reload既有网络/防火墙状态。
  两个NM配置仍是`connection.zone=drop`，下次无线恢复时继续使用该zone。
- 将主机`${SSH_PUBLIC_KEY}`追加到手机`${DEVICE_HOME}/.ssh/authorized_keys`。
  用户指定ED25519公钥指纹：`${SSH_KEY_FINGERPRINT_1}`。
  保留原97字节USB公钥，新增100字节，总197字节，owner1000:1000/mode0600，`.ssh`权限保护保持。
- sshd仍监听22，公钥登录yes，密码/交互密码/root登录仍no；不重启sshd。
  **尚未从持有新私钥的另一台机器实测登录**，只验证公钥格式、安装、权限及服务策略。

## SELinux：配置已设disabled，不等于内核已经Disabled

`/etc/selinux/config`已从`SELINUX=permissive`改为`SELINUX=disabled`，保留`SELINUXTYPE=targeted`。
**当前实际仍`getenforce=Permissive`、enforce0，即不执行SELinux访问拦截，并非彻底Disabled。**

精确6.18内核`selinuxfs.c:sel_write_disable()`只是已废弃兼容stub：写入只打印不支持消息并返回字节数，不关闭LSM。
本次没有写该节点、卸载selinuxfs或用伪造状态冒充关闭。
当前`CONFIG_CMDLINE_FORCE=y`、固定命令行只有`enforcing=0`，没有`selinux=0`。
完全禁用需要另行明确范围地修改受保护boot启动参数/相关校验并重启；**仅改config或直接重启现有镜像都不能保证Disabled**。
本阶段未授权执行该新boot变更，仍保留原#10/#8及已安装power镜像。

## 当前不能通过Wi-Fi登录的原因

本轮变更前，自动连接session `${SESSION_1}`已经因
`RuntimeError: Fallback link lost; no restart loop`退出。
新Wi-Fi服务仍**enabled/failed/exit-code**，没有wlan0或DHCP地址；上次地址`${PHONE_LAN_IP}`只是历史地址。
其安全清理完成：DSP offline、WLAN absent、CPU上限恢复、私有副本checkpoint提交，dirty标记不存在，原记录峰值38.4°C。
这次没有重启该failed unit、删除marker或自动重连。此前90/303/732秒在线检查仍是当时的真实快照，不是长期稳定证明。

网络恢复并确认新DHCP地址后，在拥有对应私钥的机器上使用：

```sh
ssh -i "${SSH_PRIVATE_KEY}" "${DEVICE_USER}@${PHONE_LAN_IP}"
```

不要上传私钥或开公网端口转发。首次导入主机密钥需通过可信渠道核对ED25519指纹：
`${SSH_KEY_FINGERPRINT_2}`，以后保持严格known_hosts验证，不绕过主机密钥校验。
若实际LAN网段改变，需明确更新source网段，而不是退回任意来源开放。

## 基线与恢复证据

原`authorized_keys`是15,285静态文件清单之一，不能继续假称整个原清单逐字节不变。
本次保留原清单，单独记录用户授权的一个公钥文件例外：

- 旧SHA256：`${AUTHORIZED_KEYS_HASH_OLD}`，97字节。
- 新SHA256：`${AUTHORIZED_KEYS_HASH_NEW}`，197字节。
- `/etc/selinux/config`不在原静态文件清单，但新旧内容/摘要及备份已另存。

以该唯一明确例外执行完整检查：**15,285文件/543,194,605字节通过**，boot仍为已安装power镜像完整分区哈希`73d32de2…`，七保护分区/六GPT未变，最高35.7°C。
后续完整检查必须使用`out/lan-ssh-selinux-20261030T001611Z/integrity-request-authorized-key.json`或同等显式授权例外；不能直接把旧公钥哈希失败重写成成功。

主机证据：`out/lan-ssh-selinux-20261030T001611Z/`。
手机root私有备份与原生记录：`/var/lib/picasso-admin/lan-ssh-selinux-20261030T001611Z/`。
旧USB密钥、失败unit/history、原NV与凭据、屏幕15秒/音量上/内核租约及power待下次启动范围不变；未进行新的关机、休眠、RF启动或PMIC操作。

## English

> Latest [WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md): R2 was enabled/active, raw CN bit verification
> passed, and ${FALLBACK_SSID} obtained ${PHONE_LAN_IP}/24, passing CCMP/DHCP/DNS/certificate-verified
> HTTPS 200 and subsequent live rechecks. The original source-restricted LAN22/drop rule and
> public key remained. Login from another machine using the new key had not passed acceptance;
> the IP and online state must be checked live in future.
>
> Earlier regulatory-domain switching: [WIFI-CN.md](WIFI-CN.md). Global CN and persistent configuration
> were verified, but the new CN service failed verification of the 5 GHz indoor-restriction flag.
> At that stage WLAN/DSP had been cleaned up with no IPv4; LAN SSH remained unavailable.
> The original SSH rules/public key and actual SELinux state were unchanged.
>
> Earlier SG wireless state: [WIFI-RADIO-UP.md](WIFI-RADIO-UP.md). One specified 2.4 GHz NM activation
> returned 0, then triggered rejection by the regulatory-domain check. The radio service was
> enabled/failed and fully exited safely. WLAN was absent, DSP offline, and dirty absent, with
> no Wi-Fi IPv4; LAN SSH was unavailable. Earlier UP/active-dirty snapshots were historical and
> cannot establish continued operation. SSH rules, the public key, and actual SELinux Permissive
> state remained unchanged.

> Later reconnect-on-drop installation received separate authorization. The new default service was
> `picasso-wifi-reconnect.service`; the old auto service was disabled but its failed state retained.
> Three automatic recoveries on the actual phone succeeded, then this boot's initial connection
> plus three retries were exhausted; it was offline again and safely cleaned up. See the latest
> [WIFI-RECONNECT.md](WIFI-RECONNECT.md). This page's SSH/SELinux facts remained unchanged;
> the old Wi-Fi state was a configuration-time snapshot.

User request: **“放行所有局域网ip, 关闭selinux, 使用./id_ed25519.pub” (“Allow all LAN IPs,
disable SELinux, and use ./id_ed25519.pub”).** Only regular files and firewalld rules were modified.
No reboot, boot write, Wi-Fi restoration, or reading of any private key occurred.

## Applied changes

- Allowed all IPv4 sources on the previous round's actual DHCP network, `${LAN_SUBNET}`,
  to SSH **TCP22**. An exact source/port accept rich rule was added to the original drop zone;
  runtime and permanent rules each independently passed query checks. The entire zone was not
  made trusted; IPv6, other subnets, and other ports were not allowed; firewalld was not stopped,
  and existing network/firewall state was not reloaded. Both NM profiles retained
  `connection.zone=drop` and would continue using that zone when wireless recovered.
- Appended host public key `${SSH_PUBLIC_KEY}` to the phone's
  `${DEVICE_HOME}/.ssh/authorized_keys`. The user-specified ED25519 public-key fingerprint:
  `${SSH_KEY_FINGERPRINT_1}`.
  The original 97-byte USB public key was retained, with 100 bytes added for a total of 197 bytes;
  owner1000:1000/mode0600 and `.ssh` permission protection were preserved.
- sshd still listened on 22, public-key login remained yes, and password/interactive-password/root
  login remained no. sshd was not restarted. **Login had not yet been tested from the other machine
  holding the new private key**; only public-key format, installation, permissions, and service policy
  were verified.

## SELinux: configuration set to disabled does not mean the kernel is Disabled

`/etc/selinux/config` was changed from `SELINUX=permissive` to `SELINUX=disabled`, retaining
`SELINUXTYPE=targeted`. **The actual state remained `getenforce=Permissive`, enforce0:
SELinux access blocking was not enforced, but SELinux was not completely Disabled.**

In the exact 6.18 kernel, `selinuxfs.c:sel_write_disable()` is only a deprecated compatibility stub:
writing prints an unsupported-operation message and returns the byte count without disabling the LSM.
This session did not write that node, unmount selinuxfs, or fabricate status to impersonate disabling.
`CONFIG_CMDLINE_FORCE=y` was active; the fixed command line contained only `enforcing=0`,
not `selinux=0`. Fully disabling requires a separately and explicitly scoped change to protected boot
parameters/related verification and a reboot. **Changing only the configuration, or simply rebooting
the existing image, cannot guarantee Disabled.** That new boot change was not authorized at this
stage; the original #10/#8 and installed power image were retained.

## Why Wi-Fi login was unavailable at this stage

Before this round's changes, automatic-connection session `${SESSION_1}` had already exited with
`RuntimeError: Fallback link lost; no restart loop`. The new Wi-Fi service remained
**enabled/failed/exit-code**, with no wlan0 or DHCP address; the previous `${PHONE_LAN_IP}` was only a
historical address. Safe cleanup had completed: DSP offline, WLAN absent, CPU limits restored,
the private-copy checkpoint committed, and no dirty marker; the originally recorded peak was 38.4°C.
This session did not restart the failed unit, delete a marker, or automatically reconnect. Earlier
90/303/732-second online checks remained genuine snapshots of those times, not proof of long-term
stability.

After network recovery and confirmation of the new DHCP address, use the machine with the
corresponding private key:

```sh
ssh -i "${SSH_PRIVATE_KEY}" "${DEVICE_USER}@${PHONE_LAN_IP}"
```

Do not upload the private key or enable public-Internet port forwarding. On first host-key import,
verify the ED25519 fingerprint through a trusted channel:
`${SSH_KEY_FINGERPRINT_2}`.
Thereafter retain strict known_hosts verification; do not bypass host-key checks. If the actual LAN
subnet changes, explicitly update the source subnet rather than falling back to access from any source.

## Baseline and recovery evidence

The original `authorized_keys` was one of the 15,285 static files, so the entire original manifest
could no longer honestly be described as byte-for-byte unchanged. This session retained that
manifest and separately recorded the one public-key-file exception authorized by the user:

- Old SHA256: `${AUTHORIZED_KEYS_HASH_OLD}`, 97 bytes.
- New SHA256: `${AUTHORIZED_KEYS_HASH_NEW}`, 197 bytes.
- `/etc/selinux/config` was not in the original static-file manifest; old/new contents and digests,
  plus a backup, were saved separately.

With this single explicit exception, a full check passed: **15,285 files / 543,194,605 bytes**.
boot remained the installed power image with full-partition hash `73d32de2…`; seven protected
partitions and six GPTs were unchanged, with a maximum temperature of 35.7°C.
Subsequent full checks must use
`out/lan-ssh-selinux-20261030T001611Z/integrity-request-authorized-key.json`
or an equivalent explicit authorized exception; an old-public-key hash failure cannot simply be
rewritten as success.

Host evidence: `out/lan-ssh-selinux-20261030T001611Z/`.
Phone root-private backups and native records:
`/var/lib/picasso-admin/lan-ssh-selinux-20261030T001611Z/`.
The old USB key, failed units/history, original NV and credentials, screen 15-second/volume-up/kernel
lease behavior, and power scope pending the next boot were unchanged. No new shutdown, suspend,
RF start, or PMIC operation was performed.
