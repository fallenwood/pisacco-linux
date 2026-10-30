# Rootless Podman的systemd用户会话已修复 / Rootless Podman's systemd User Session Repaired

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录；“当前”等状态按原记录时间理解，反引号中的代码及证据路径相对于仓库根目录。 / Historical stage record; “current” refers to the recorded stage. Code and evidence paths in backticks are relative to the repository root.

## 中文

用户在`picasso`下运行`podman ps -a`提示没有systemd用户会话、退回cgroupfs；随后明确“继续”，授权补齐会话组件并启用linger/用户D-Bus。

## 原因与修复

- 缺少`systemd-pam`，`pam_systemd.so`不存在。SSH虽然UsePAM=yes，现有PAM配置中的可选模块行会忽略缺失模块，因此没有注册用户会话/运行目录。
- 原`user@1000.service`和`user-runtime-dir@1000.service`inactive，`${XDG_RUNTIME_DIR}`及XDG环境不存在。
- 用户D-Bus socket未enable，`dbus.service`到dbus-broker的用户别名也未配置。
- 补充纠正最初只查`/etc/pam.d/systemd-user`的观察：**vendor配置原本在`/usr/lib/pam.d/systemd-user`，并不缺失**；实际缺的是PAM模块。原配置完全没重写。

只安装**`systemd-pam-259.10-1.fc44.aarch64`**，严格匹配现有systemd/systemd-libs/systemd-shared；没有升级核心systemd或安装其他依赖。
Fedora44 RPM签名/header/payload校验通过，手机签名校验/依赖`rpm --test`通过；无包内script/triggers且无已有普通payload文件冲突。
RPM SHA256 `ed726112e6bf524f69bfd2be9b83c45204be71a2e61ab79e1a9cfa8f8dbdfbac`。
`rpm -V systemd-pam`和`rpm --verifydb`均通过；现有PAM/SSH配置前后SHA完全一致。

在UID1000自己的配置目录启用：

```text
${DEVICE_HOME}/.config/systemd/user/dbus.service -> /usr/lib/systemd/user/dbus-broker.service
${DEVICE_HOME}/.config/systemd/user/sockets.target.wants/dbus.socket -> /usr/lib/systemd/user/dbus.socket
```

均由UID1000创建，没有对全系统所有用户执行global enable。
`loginctl enable-linger picasso`已执行，linger=yes；用户服务可在退出SSH后继续运行，这是有意的持久行为。
运行目录由logind/PAM创建，UID1000/0700，没有手造目录、chmod777、伪造session或改用root Podman/cgroupfs。

## 原生新SSH验证

- XDG_RUNTIME_DIR=`${XDG_RUNTIME_DIR}`
- DBUS_SESSION_BUS_ADDRESS=`unix:path=${XDG_RUNTIME_DIR}/bus`
- 新PAM session已注册；用户manager running，user@1000.service PID206079 active，dbus.socket与dbus.service均active。
- UID1000直接`podman ps -a`返回0且stderr空，无原警告，当前容器列表为空。
- `podman info --format '{{.Host.CgroupManager}} {{.Host.CgroupsVersion}} {{.Host.Security.Rootless}}'`输出：

```text
systemd v2 true
```

**现有旧终端环境不会自动刷新，请退出当前SSH再登录**，然后直接运行`podman ps -a`，不要改用`sudo podman`。
没有拉取镜像、创建/启动容器或进行容器CPU/存储/网络测试；上述结果不等于容器负载/用户命名空间/网络/持久化全面验收。
本次没有重启，因此下次开机/完全退出后长期用户服务行为未单独做生命周期验收。

## 错误保留与边界

首个配置器在包安装/校验成功后，尝试无XDG运行目录的`systemctl --user --no-reload enable`仍被systemd259客户端拒绝。
原`native-apply-result.json`失败原样保留。没有重装包、回滚掩盖或reset-failed。
新的SSH经已补齐PAM模块自动建立真正用户manager后，独立续作启用linger/用户bus，原生新SSH验证通过；原PAM/SSH哈希未改。

安装期间三组开始读数<40°C已保存在手机intent，配置器采样峰值36.4°C，45°C abort/CPU0–3保持；最终38.1°C是另一时刻读数，不当作开始温度。
Wi-Fi R2仍active/PID166423，NM100/${PHONE_LAN_IP}，屏幕527/租约健康；没有RF重新启动、预算重置、boot/PMIC/原始NV或凭据/SSH私钥读取导出。
SELinux实际Permissive、来源限定LAN22和publickey-only SSH设置不变。

## 后续完整性检查注意

原15,285文件静态manifest包含`/usr/lib/sysimage/rpm/rpmdb.sqlite{,-shm,-wal}`。
授权软件包安装会合法变动包数据库；这些是动态SQLite状态，**不能直接继续声称旧静态DB字节全部一致，也不能用本次单包操作推断此前所有软件变化**。
本轮未保存安装前整个RPMDB，不重构未知旧状态；记录安装日志、准确包版本/签名/验证及post-state指纹，仅作为快照而非永久新静态基线。
原manifest/authorized-key-adjusted完整性请求均保持不改。未来完整检查需显式处理这个软件包/动态RPMDB转移并另行验证数据库和包集，不可直接运行旧请求后把错误抹掉，也不可通配忽略其他文件。
本轮只验证包/数据库/指定PAM-SSH配置，没有重哈希全部静态文件、保护分区或原NV。

证据`out/podman-user-session-20261030T114234Z/`；手机`/var/lib/picasso-admin/podman-user-session-20261030T114234/`保存原PAM/SSH备份、intent和首轮失败/续作结果。

## English

When the user ran `podman ps -a` as `${DEVICE_USER}`, it warned that no systemd user session was available and
fell back to cgroupfs. The user then explicitly said “继续” (“Continue”), authorizing installation of the
missing session components and enabling linger/user D-Bus.

## Cause and repair

- `systemd-pam` was missing, so `pam_systemd.so` did not exist. Although SSH had UsePAM=yes,
  optional-module lines in the existing PAM configuration ignored the missing module, preventing
  user-session registration and runtime-directory setup.
- The original `user@1000.service` and `user-runtime-dir@1000.service` were inactive;
  `${XDG_RUNTIME_DIR}` and the XDG environment did not exist.
- The user D-Bus socket was not enabled, and the user alias from `dbus.service` to dbus-broker
  was not configured.
- Correction to the initial observation, which checked only `/etc/pam.d/systemd-user`:
  **the vendor configuration already existed at `/usr/lib/pam.d/systemd-user`; it was not missing**.
  The actual missing item was the PAM module. The original configuration was not rewritten at all.

Only **`systemd-pam-259.10-1.fc44.aarch64`** was installed, strictly matching the existing
systemd/systemd-libs/systemd-shared. Core systemd was not upgraded and no other dependencies
were installed. Fedora44 RPM signature/header/payload verification passed, as did on-phone signature
verification and dependency `rpm --test`. The package had no scripts/triggers and no conflict with
existing regular payload files.
RPM SHA256: `ed726112e6bf524f69bfd2be9b83c45204be71a2e61ab79e1a9cfa8f8dbdfbac`.
`rpm -V systemd-pam` and `rpm --verifydb` both passed. SHA hashes of existing PAM/SSH configurations
were identical before and after.

Enabled in UID1000's own configuration directory:

```text
${DEVICE_HOME}/.config/systemd/user/dbus.service -> /usr/lib/systemd/user/dbus-broker.service
${DEVICE_HOME}/.config/systemd/user/sockets.target.wants/dbus.socket -> /usr/lib/systemd/user/dbus.socket
```

Both were created by UID1000; no global enable was performed for all system users.
`loginctl enable-linger picasso` was executed, with linger=yes. User services may continue running after
SSH logout; this is intentional persistent behavior. logind/PAM created the runtime directory,
UID1000/0700. No directory was hand-made, no chmod777 or fake session was used, and there was
no switch to root Podman/cgroupfs.

## Native verification in a new SSH session

- XDG_RUNTIME_DIR=`${XDG_RUNTIME_DIR}`
- DBUS_SESSION_BUS_ADDRESS=`unix:path=${XDG_RUNTIME_DIR}/bus`
- A new PAM session was registered; the user manager was running, user@1000.service PID206079
  was active, and dbus.socket and dbus.service were both active.
- UID1000 directly ran `podman ps -a`, returning 0 with empty stderr and no original warning.
  The container list was empty at that time.
- `podman info --format '{{.Host.CgroupManager}} {{.Host.CgroupsVersion}} {{.Host.Security.Rootless}}'`
  output:

```text
systemd v2 true
```

**Existing terminal environments do not refresh automatically. Exit the current SSH session and log
in again**, then run `podman ps -a` directly; do not switch to `sudo podman`.
No image was pulled, no container created/started, and no container CPU/storage/network testing
performed. These results do not constitute comprehensive acceptance of container workloads,
user namespaces, networking, or persistence. No reboot occurred, so next-boot behavior and
long-term user-service behavior after complete logout had not separately undergone lifecycle acceptance.

## Retained errors and boundaries

After successful package installation/verification, the first configurator tried
`systemctl --user --no-reload enable` without an XDG runtime directory and was still rejected by
the systemd259 client. The failed original `native-apply-result.json` was preserved unchanged.
There was no package reinstallation, concealment through rollback, or reset-failed.
Once new SSH established a genuine user manager automatically through the newly installed PAM
module, an independent continuation enabled linger/user bus, and native verification in another
new SSH session passed. Original PAM/SSH hashes remained unchanged.

Three sets of starting readings below 40°C during installation were saved in the phone's intent.
The configurator sampled a peak of 36.4°C, retaining the 45°C abort/CPU0–3 constraints.
The final 38.1°C was a reading at another time, not a starting temperature.
Wi-Fi R2 remained active/PID166423, NM100/${PHONE_LAN_IP}, with screen527/lease healthy.
There was no RF restart, budget reset, boot/PMIC operation, or reading/export of original NV,
credentials, or SSH private keys. Actual SELinux Permissive, source-restricted LAN22,
and publickey-only SSH settings remained unchanged.

## Notes for future integrity checks

The original 15,285-file static manifest includes
`/usr/lib/sysimage/rpm/rpmdb.sqlite{,-shm,-wal}`.
Authorized package installation legitimately changes the package database. These are dynamic SQLite
states; **the old static DB bytes cannot simply continue to be claimed identical, and this one-package
operation cannot establish all earlier software changes**.
The entire pre-installation RPMDB was not saved in this round, and unknown old state is not reconstructed.
Installation logs, exact package version/signature/verification, and post-state fingerprints were recorded
only as snapshots, not as a permanent new static baseline.
The original manifest and authorized-key-adjusted integrity request were both retained unchanged.
A future full check must explicitly handle this package/dynamic-RPMDB transition and separately
verify the database and package set. Do not simply run the old request and erase its errors,
or use a wildcard to ignore other files.
This round verified only the package/database/specified PAM-SSH configurations; it did not rehash
all static files, protected partitions, or original NV.

Evidence: `out/podman-user-session-20261030T114234Z/`.
On the phone, `/var/lib/picasso-admin/podman-user-session-20261030T114234/` holds original PAM/SSH
backups, intent, and the first-round failure/continuation results.
