# 局域网SSH已放行、公钥已添加；Wi-Fi当前离线，SELinux内核仍Permissive

> 最新[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)：R2已enabled/active，原始CN位核验通过，Chaldea-2.4G取得192.168.1.64/24并通过CCMP/DHCP/DNS/证书HTTPS200和后续实时复核。原来源限定LAN22/drop规则、公钥仍在；新公钥从另一台机器登录尚未验收，IP/是否在线以后必须实时确认。
>
> 此前域切换见[WIFI-CN.md](WIFI-CN.md)：global CN和持久配置已核实，但新CN服务因5GHz室内限制标志核验失败而failed，当前WLAN/DSP已清理、无IPv4，LAN SSH仍不可用；原SSH规则/公钥/实际SELinux不变。
>
> 此前SG无线状态见[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)：一次指定2.4GHz NM激活返回0后触发监管域检查拒绝，radio服务enabled/failed并完整安全退出；当前WLAN absent/DSP offline/dirty absent，无Wi-Fi IPv4，不能经LAN SSH。此前UP/活跃dirty快照是历史，不能据此称仍运行。SSH规则、公钥及SELinux实际Permissive不变。

> 后续掉线重连已另获授权安装，新默认服务是`picasso-wifi-reconnect.service`，旧auto已disabled但failed保留。真机3次自动恢复成功，随后本boot初连＋3次耗尽，当前又离线且安全清理。最新[WIFI-RECONNECT.md](WIFI-RECONNECT.md)；本页SSH/SELinux事实不变，旧Wi-Fi状态是配置时快照。

用户请求：**“放行所有局域网ip, 关闭selinux, 使用./id_ed25519.pub”**。
仅修改普通文件与firewalld规则，没有重启、写boot、恢复Wi-Fi或读取任何私钥。

## 已应用

- 将上一轮实际DHCP网络`192.168.1.0/24`的所有IPv4来源放行到SSH **TCP22**。
  在原drop zone添加精确source/port accept rich rule，runtime与permanent均独立query通过。
  不把整个zone设trusted，不放行IPv6、其他网段或其他端口，不关闭firewalld，不reload既有网络/防火墙状态。
  两个NM配置仍是`connection.zone=drop`，下次无线恢复时继续使用该zone。
- 将主机`/home/vbox/droid/id_ed25519.pub`追加到手机`/home/picasso/.ssh/authorized_keys`。
  用户指定ED25519公钥指纹：`SHA256:M0OdVI8XdnKbdMbtzHxu2wTfGUoMrHDryiVIAlmMCeg`。
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

本轮变更前，自动连接session `c2d482b79523`已经因
`RuntimeError: Fallback link lost; no restart loop`退出。
新Wi-Fi服务仍**enabled/failed/exit-code**，没有wlan0或DHCP地址；上次地址`192.168.1.64`只是历史地址。
其安全清理完成：DSP offline、WLAN absent、CPU上限恢复、私有副本checkpoint提交，dirty标记不存在，原记录峰值38.4°C。
这次没有重启该failed unit、删除marker或自动重连。此前90/303/732秒在线检查仍是当时的真实快照，不是长期稳定证明。

网络恢复并确认新DHCP地址后，在拥有对应私钥的机器上使用：

```sh
ssh -i /path/to/corresponding_id_ed25519 picasso@PHONE_LAN_IP
```

不要上传私钥或开公网端口转发。首次导入主机密钥需通过可信渠道核对ED25519指纹：
`SHA256:ut+zsjpvH7RyUZTG8Zt7ocbzXhEWGJ4g/ENBlMDUxKs`，以后保持严格known_hosts验证，不绕过主机密钥校验。
若实际LAN网段改变，需明确更新source网段，而不是退回任意来源开放。

## 基线与恢复证据

原`authorized_keys`是15,285静态文件清单之一，不能继续假称整个原清单逐字节不变。
本次保留原清单，单独记录用户授权的一个公钥文件例外：

- 旧SHA256：`e3ce2487c86ccdff77ce4bc35afa593d0b4da96c33b8d197e78ba8622970c3ee`，97字节。
- 新SHA256：`3d6ea4672b924c5394cbd942c0a95bc21840ac7f588de1e04b8c590d19c419be`，197字节。
- `/etc/selinux/config`不在原静态文件清单，但新旧内容/摘要及备份已另存。

以该唯一明确例外执行完整检查：**15,285文件/543,194,605字节通过**，boot仍为已安装power镜像完整分区哈希`73d32de2…`，七保护分区/六GPT未变，最高35.7°C。
后续完整检查必须使用`out/lan-ssh-selinux-20261030T001611Z/integrity-request-authorized-key.json`或同等显式授权例外；不能直接把旧公钥哈希失败重写成成功。

主机证据：`out/lan-ssh-selinux-20261030T001611Z/`。
手机root私有备份与原生记录：`/var/lib/picasso-admin/lan-ssh-selinux-20261030T001611Z/`。
旧USB密钥、失败unit/history、原NV与凭据、屏幕15秒/音量上/内核租约及power待下次启动范围不变；未进行新的关机、休眠、RF启动或PMIC操作。
