# Picasso：新内核真机确认（2026-10-27）

## 结论

**Linux 6.18.58 + Fedora Server 44 minimal 已在真机 RAM 中运行；nftables/firewalld 和
ZRAM 不再只是编译通过，已完成功能测试。** 仍不是持久安装或稳定成品。

- 镜像：`out/boot-picasso.img`，32,899,072 字节，SHA256
  `59784cc401cad3d1b245e8a403b80abd0176e02e9f6891b31daabe9423a1e801`。
- rootfs gzip SHA256：
  `9222f5ad11a27bf5b1c7d9ea3b2c6c6469da277497e18a51f33b752717042d28`。
- 实际运行的 kernel config 和 live FDT 分别与打包输入 hash 一致。live FDT 依然是
  shim 传入的主线静态树，**不能**据此确认原始 ABL 动态 RAM/保留区。
- systemd 为真实 PID 1，虚拟化检测 none，8 CPU 在线，3 个 schedutil policy。
- 公钥 SSH、sudo、sshd、networkd、NetworkManager、dbus 正常。
- 274 个软件包，RPM 数据库 275 条（含 GPG key）；根为 3 GiB 上限 tmpfs。
- 最后快照 MemAvailable 4,676,452,352 字节，约 4.36 GiB；CPU 温度 33.1–34.4°C。
  没有做全内存或温控压力测试。

**systemd 仍为 degraded。** 唯一失败项已从旧镜像的 `firewalld.service` 变成
`dnf-makecache.service`：手机只有 USB 直连，没有默认路由、DNS 或互联网出口。
没有清除失败状态或禁用服务来伪装健康，也没有配置主机 NAT/默认路由。

## 本次实际做了什么

开始时设备已运行前一阶段临时启动的新内核，停在 BusyBox 救援，uptime 约 7.6 小时。
本次没有再发送 reboot、fastboot boot、flash、unlock、erase 或分区修改命令。
这段轻载等待不能称为压力测试，也不是 Fedora 已运行 7.6 小时。

1. 从物理 USB ACM 确认 `/init`、内核 #6、NF_TABLES/ZRAM 内建、挂载表和温度。
2. 只为 MAC 匹配的主机 USB 网卡临时配置 `192.168.7.1/24`。专用 HTTP 目录只提供
   rootfs 和初始化脚本，不含 SSH 私钥；服务只绑定 USB 地址。
3. 手机下载后校验 SHA256，解包到 `/newroot` tmpfs，原生执行初始化脚本。
4. 通过物理串口读取并固定 SSH host public key，显式请求 PID 1 `switch_root`。
   救援 shell 全部停止；Fedora 的串口变为认证 getty。
5. Fedora 接管链路时，主机临时 IPv4 地址曾被网络管理移除，首次 SSH 超时；恢复同一
   USB 网卡地址后连接成功。没有关闭 SSH host key 校验，也没有改走 Wi-Fi 路由。

### firewalld：真实阻断 / 放行 / 再阻断

新内核内建 nftables 及 conntrack、NAT、reject、fib 等所需功能。初次启动 firewalld 已能
运行，但因跨安装跳过 RPM posttrans，缺少 Fedora Server 配置和 Polkit 两个 ghost 链接，
使用了 fallback 设置。

依据手机上 `rpm -q --scripts firewalld` 显示的 Fedora Server 逻辑，在 **tmpfs** 内补齐
两个相对符号链接，restorecon、check-config 并 reload。随后默认 zone 为 FedoraServer，
USB 来源 `192.168.7.1/32` 使用 picasso-usb zone，只允许 SSH 服务。
`tools/mkrootfs-fedora.sh` 已补上同一链接生成逻辑，并有 3 个回归测试。**测试的 rootfs
归档没有重新生成**，仍是上面的原始 hash；当前运行系统的修复另外记录。

在手机 USB 地址上启动有时限的 TCP 18080 测试监听：

| 状态 | 主机实际连接 |
| --- | --- |
| 不放行端口 | 被拒绝 |
| 临时放行（30 秒自动到期保护） | 成功，收到预期测试标记 |
| 撤销放行，监听仍在 | 再次被拒绝 |

测试后规则已撤销、监听已停止；没有更改永久规则或对公网开放服务。

### ZRAM：实际换出、压缩、校验读回

- `/dev/zram0`：1 GiB 逻辑设备、zstd、swap priority 100。
- `CONFIG_ZRAM_WRITEBACK` 未编译，`backing_dev` 属性不存在，无 Android 磁盘后备。
- 对独立 32 MiB 匿名映射执行 Linux `MADV_PAGEOUT`；该进程 VmSwap 达到 32768 KiB，
  ZRAM 压缩数据约 2.26 MB，之后读回 SHA256 一致，VmSwap 返回 0。
- Python mmap 未导出 MADV_PAGEOUT 常量，首次探测在调用前退出；核对运行内核 UAPI
  的值 21 后重试成功。不是重启或全内存压力测试，没有直接改写 ZRAM swap 内容。

### 时钟与剩余失败

没有可用 RTC/NTP，启动时系统日期落后，RPM 查询曾因“签名尚未生效”跳过部分记录。
本次只用可信主机时间设置手机系统时钟，没有写 RTC、关闭签名校验或修改 key。
校时后 RPM 查询正常，274 个软件包 + 1 条 key。重启后时间仍需重新设置/同步。

DNF makecache 的失败证据保留：没有联网出口，不把它归咎于 nftables 或包签名损坏。

## 仍待完成

- 原始 ABL live RAM/动态 carveouts、全内存完整性。
- `Kernel image misaligned at boot`、PSCI PC mode=-3、UFS 供电假定/对齐告警。
- RNG：CRNG 约 99 秒初始化；更晚加载的 qcom_rng 报 TRNG support not detected，
  不认为硬件熵源通过。
- watchdog、ignore-unused 依赖、闭环温控、充电/电量、挂起恢复和当前 Fedora 关机路径。
- Wi-Fi 已有固件提取/供电审计，但 `iw dev` 为空；`/sys/class/power_supply` 也为空。
- 原生显示/GPU/触摸、蓝牙、音频、蜂窝、相机等未验收。
- SELinux 仍为 Permissive；持久根文件系统和 UFS 写入未测试。

UFS/GPT 可见，最终采样 runtime_status 为 suspended，deferred probe 列表为空；这些都
不等于持久写入/PM 长稳验收。挂载表只有 RAM/API 文件系统，swap 只有 ZRAM，没有挂载
Android 文件系统或向 Android 分区发出写入命令。Fedora udev 仍可能读取块设备元数据。

`systemd-analyze` 的“kernel 时间”包含此前约 7.6 小时救援等待；用户空间约 6.35 秒，
不能当作整机冷启动时间。

## 登录与证据

在 `/home/vbox/droid`：

```sh
ssh -F /dev/null -i picasso/out/fedora-server-test/id_ed25519 \
  -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=picasso/out/confirmation-20261027/known_hosts \
  -o StrictHostKeyChecking=yes picasso@192.168.7.2
```

当前只保留 Fedora RAM 系统与 SSH；临时 HTTP、测试监听和测试规则已清理。
重启后 rootfs、host keys 和一切修改丢失。没有自动重启，不适合无人值守充电运行。

证据目录 `out/confirmation-20261027/` 权限 0700：`result.json` 固定镜像、归档、
配置和证据文件 hash；包括 `final-state.json`、防火墙与 ZRAM probe JSON、启动串口及
服务日志。原 10 月 26 日 Fedora/M1 证据保留，不覆盖旧失败记录。
最新 unit tests：59 个，58 通过、1 个可选 QEMU 测试跳过；最终 rootfs 与本轮运行不用 QEMU。
