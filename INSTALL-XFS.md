# Picasso：Fedora 44 XFS 持久安装完成（实验性，原#8阶段）

**后续用户授权把已验证的wifi2 #10写入boot，并通过正常重启；XFS根和原文件保留，不是重新格式化。
当前默认#10、精确新哈希及#8回退边界见 [WIFI-INSTALL.md](WIFI-INSTALL.md)。以下为原#8安装时的历史快照。**

2026-10-27，用户先接受删除全部个人数据和实验性限制，再明确要求 **“使用xfs重新安装fedora”**。
本机已完成安装；不是仍运行 tmpfs，也不需要每次由电脑执行 `fastboot boot`。

## 已完成并在真机验证

- Redmi K30 5G / Picasso / SM7250 / 6 GB；内核 `6.18.58-picasso-lts #8`。
- Fedora Server 44 minimal aarch64：真正 systemd PID 1，虚拟化检测 `none`，277 个软件包、
  278 条 RPM 记录；8 CPU 在线。最终快照 MemAvailable 约 4.89 GiB，不是内存完整性验收。
- `userdata` 为 XFS 根：约 107 GiB，最终快照可用约 104.3 GiB。
- 临时启动 XFS 根后，15,285 个静态文件的长度、SHA256、UID/GID 和权限全部读回一致。
- 写入 `boot` 后校验整个 128 MiB；第一次**正常重启**成功，256 KiB `fsync` 测试文件保留。
- 清空 `super` 的全部 8.5 GiB，缓存 flush 后完整物理读回全零；然后第二次正常重启成功。
  第二次重启再次校验静态文件、测试文件、boot、受保护分区及 GPT。两次均未使用 fastboot boot。
- 在最终新镜像上重新执行 firewalld USB 阻断→放行→阻断、32 MiB ZRAM 换出/读回测试，均通过；
  临时端口、规则和监听进程已清理。ZRAM 为 1 GiB zstd，无磁盘后备/writeback。
- 原生 SELinux 标签初始化通过；省略主机安全 xattr 导致的 7 个 RPM file capabilities 已在手机
  按 RPM 元数据恢复并 `setcap -v` 验证，另一次重启后再次验证保留。未来镜像构造脚本已补齐此步骤。
- 最终采集时 systemd `running`，没有失败 unit；这**不表示已经解决无互联网、DNS、NTP 的限制**。
  未执行 reset-failed，也没有为掩盖问题停用服务。原先 RAM 阶段的 DNF 失败证据继续保留。
- 78 项测试：77 通过，1 个可选 QEMU BusyBox 测试跳过。实际构建和手机运行均未使用 QEMU。

## 实际写入范围

执行时均由唯一 PARTNAME、PARTUUID 和精确长度确认，不把 `/dev/sd*` 编号作为唯一身份。

| 分区 | PARTUUID | 字节数 | 最终用途 |
| --- | --- | ---: | --- |
| userdata | 32684d05-1c3b-836e-c936-7d4638bf1be9 | 114936492032 | Fedora XFS 根；先前 ext4 试装已被替换 |
| boot | 4aadcdf3-3aad-3318-a158-46642b851943 | 134217728 | Fedora 内核/内建 initramfs，镜像后补零 |
| super | f045b7f2-f351-5ead-1c36-47aefbfa6e16 | 9126805504 | 全部清零，不另改 GPT 回收容量 |

**Android 个人数据和系统已放弃。** 这是普通安装/逻辑清空，不承诺 UFS 物理介质的取证级安全擦除。

没有重分区、整 LUN 覆盖、全盘 discard、固件降级、解锁或 vbmeta 写入。六个 LUN 的保护 MBR、
主备 GPT header 和 entries 与备份逐字节一致。DTBO、recovery 和五个 vbmeta 分区的完整 SHA256
仍与备份相同。启动链、基带/DSP、校准/EFS、persist 等其余分区不在安装写入范围；不要把这一
写入范围约束夸大为已为所有固件做了全量内容备份/读回。

## XFS 与启动

- XFS 内置于内核，包含 POSIX ACL、quota；当前根挂载未启用 quota。
- xfsprogs 7.1.1，`lts_6.18` mkfs 配置，扇区和块均为 4096 B。
- 显式内核参数：`root=PARTUUID=32684d05-1c3b-836e-c936-7d4638bf1be9 rootfstype=xfs`。
- initramfs 先 `ro,norecovery` 挂载，禁止校验阶段日志回放；核验 V2 安装标记、文件系统类型、
  PARTUUID、Fedora Server 44 和原生初始化标记，才切换读写并交给 systemd。失配则进入救援。
- fstab：`PARTUUID=32684d05-1c3b-836e-c936-7d4638bf1be9 / xfs defaults,noatime 0 0`。
  不启用 discard，不自动探测/挂载其他 Android 分区。XFS 不能原地缩小。
- 保留 ROM 的完整 12-DTB blob 供 ABL 使用，DTBO 未写入；主线 runtime DTB 未替换成 vendor merged DT。

## 当前产物与证据

证据目录：`out/install-xfs-20261027/`，权限 0700。`result.json` 是最终结论；
`preparation-status.json`、`boot-xfs-manifest.json` 是准备阶段快照，不是最终状态。
最终打包状态为 `out/boot-manifest.json` 和 `out/install-xfs-20261027/boot-installed-manifest.json`。

| 产物 | SHA256 |
| --- | --- |
| boot 镜像，33,820,672 B | `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c` |
| boot 完整分区，含零 padding | `312e42f3c590faa3c7988b8e02e15f7bee1952dee785a0d0acb218f088a1a696` |
| 初始 XFS sparse 镜像，574,804,228 B | `9b83521354c27f181042b8d053ad72deb055563cba29479a1a6f479707adfa54` |
| 运行内核配置 | `78d5a451ed01af58807e1add0cc42506255b5fd03bd46e974a7db595b1813589` |
| 最终 result.json | `43e1690717251494b433eab417e3e5d7e11438389a0bee612f1b1c897f524206` |

原始 XFS 镜像和 sparse 还原图均通过 `xfs_repair -n`，整个 114,936,492,032 B 逻辑镜像相同。
镜像包括手机的私有 SSH host keys，**不可公开分发**。原始镜像与运行根的原生 filecap、SELinux
标签、时间种子、日志和测试文件等运行期调整分开记录，不把初始文件摘要说成整个活动文件系统摘要。

## USB SSH 登录

在 `/home/vbox/droid` 下：

```sh
ssh -F /dev/null -i picasso/out/fedora-server-test/id_ed25519 \
  -o BatchMode=yes -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=picasso/out/confirmation-20261027/known_hosts \
  -o StrictHostKeyChecking=yes -o ConnectTimeout=10 \
  picasso@192.168.7.2
```

账号 `picasso`，可 `sudo -n`。Host key 原先由物理 USB 串口固定，并与构造镜像的公钥比较一致；
没有关闭 host-key 检查。不要公开客户端私钥或镜像内的 host 私钥。

主机 USB 地址为 `192.168.7.1/24`，MAC `02:50:49:00:00:01`。若 USB 重枚举或主机重启后地址丢失，
先识别该 MAC 对应的接口；本次为 `enp3s0f3u2`。只对核对后的 USB 接口临时取消主机 NetworkManager
管理并配置地址，避免其 DHCP 清除手工地址；不能误改 Wi-Fi，也没有配置 NAT/默认路由。

```sh
IF=enp3s0f3u2
[ "$(< /sys/class/net/$IF/address)" = 02:50:49:00:00:01 ] || exit 1
sudo nmcli device set "$IF" managed no
sudo ip link set "$IF" up
sudo ip addr replace 192.168.7.1/24 dev "$IF"
```

## 恢复材料与限制

原 boot/recovery/DTBO/vbmeta 及六个 LUN GPT 备份位于 `out/install-preflight-20261027/`，
302,817,280 B tar 的 SHA256 为 `319051e3cdb5d6d050a2c6096d536b2a4960325e6eb81cda55ae8de806b184d4`。
这不是个人数据或整机备份，也不含 super/EFS/persist；恢复 Android 可能需要完整 ROM 重装和重新
格式化 userdata，不能认为只恢复原 boot 就能恢复被删除的 Android/个人文件。恢复步骤未全部验收。

仍是 headless 实验系统：显示/GPU/触摸、Wi-Fi、音频、蜂窝、相机等未验收；Linux 电池/充电遥测为空。
本次 fastboot 读取 4297 mV，电量百分比不提供；不能用旧 99% 记录声称当前电量或充电正常。
全 super 读回 SHA256 后观测到 46.8°C，随后降到 40°C 以下；最终快照 34.4–36.8°C，
**不是闭环温控、长期压力或充电安全验收**。watchdog、完整内存/原始 ABL RAM map、关机、挂起、
掉电恢复和耐久仍未验收；对齐/PSCI/UFS/TRNG 告警没有消失。SELinux 为 Permissive。

无互联网/DNS 出口和持续 NTP；校时只来自可信 USB 主机，并保存 PID 1 的下次启动时间下限，
没有写 RTC。启动时回退到保存时间、journal 因时钟回退轮转仍是已观察到的限制。
不能当作日常手机、公网生产或无人值守充电服务器。
