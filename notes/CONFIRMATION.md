# Picasso：新内核真机确认（2026-10-27） / Picasso: New-kernel Hardware Confirmation (2026-10-27)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录；“当前”等状态按原记录时间理解，反引号中的代码及证据路径相对于仓库根目录。 / Historical stage record; “current” refers to the recorded stage. Code and evidence paths in backticks are relative to the repository root.

## 中文

## 结论

**Linux 6.18.58 + Fedora Server 44 minimal 已在真机 RAM 中运行；nftables/firewalld 和
ZRAM 不再只是编译通过，已完成功能测试。** 仍不是持久安装或稳定成品。

- 镜像：`out/boot-picasso.img`，32,899,072 字节，SHA256
  `59784cc401cad3d1b245e8a403b80abd0176e02e9f6891b31daabe9423a1e801`。
- rootfs gzip SHA256：
  `${PRIVATE_ROOTFS_SHA256_1}`。
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
2. 只为 MAC 匹配的主机 USB 网卡临时配置 `${HOST_USB_IP}/24`。专用 HTTP 目录只提供
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
USB 来源 `${LAN_SUBNET}` 使用 picasso-usb zone，只允许 SSH 服务。
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

在 `${REPO_ROOT}`：

```sh
ssh -F /dev/null -i ${SSH_PRIVATE_KEY} \
  -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=${SSH_KNOWN_HOSTS} \
  -o StrictHostKeyChecking=yes ${DEVICE_USER}@${PHONE_USB_IP}
```

当前只保留 Fedora RAM 系统与 SSH；临时 HTTP、测试监听和测试规则已清理。
重启后 rootfs、host keys 和一切修改丢失。没有自动重启，不适合无人值守充电运行。

证据目录 `out/confirmation-20261027/` 权限 0700：`result.json` 固定镜像、归档、
配置和证据文件 hash；包括 `final-state.json`、防火墙与 ZRAM probe JSON、启动串口及
服务日志。原 10 月 26 日 Fedora/M1 证据保留，不覆盖旧失败记录。
最新 unit tests：59 个，58 通过、1 个可选 QEMU 测试跳过；最终 rootfs 与本轮运行不用 QEMU。

## English

## Conclusion

**Linux 6.18.58 + Fedora Server 44 minimal ran in RAM on the actual phone; nftables/firewalld and
ZRAM passed functional tests, rather than merely compiling successfully.** This was still neither a
persistent installation nor a stable finished system.

- Image: `out/boot-picasso.img`, 32,899,072 bytes, SHA256
  `59784cc401cad3d1b245e8a403b80abd0176e02e9f6891b31daabe9423a1e801`.
- Rootfs gzip SHA256:
  `${PRIVATE_ROOTFS_SHA256_1}`.
- The running kernel configuration and live FDT each matched the hashes of their packaged inputs.
  The live FDT was still the static mainline tree passed in by the shim; it **cannot** confirm the
  original ABL dynamic RAM layout or reserved regions.
- systemd was the real PID 1; virtualization detection returned none, with 8 CPUs online and
  3 schedutil policies.
- Public-key SSH, sudo, sshd, networkd, NetworkManager, and dbus worked normally.
- 274 packages, 275 RPM database records including the GPG key; the root was tmpfs capped at 3 GiB.
- The final snapshot showed MemAvailable of 4,676,452,352 bytes, approximately 4.36 GiB, and CPU
  temperatures of 33.1–34.4°C. No full-memory or thermal-control stress test was performed.

**systemd remained degraded.** The sole failed unit had changed from the old image's
`firewalld.service` to `dnf-makecache.service`: the phone had only a direct USB connection, with no
default route, DNS, or Internet egress. Failed states were not cleared and services were not disabled
to create an appearance of health; no host NAT or default route was configured.

## What was actually done in this session

At the start, the device was already running the new kernel temporarily booted in the preceding stage,
at the BusyBox rescue environment, with approximately 7.6 hours of uptime. This session sent no further
reboot, fastboot boot, flash, unlock, erase, or partition-modification commands. That lightly loaded
waiting period was not a stress test, nor had Fedora been running for 7.6 hours.

1. Used the physical USB ACM console to confirm `/init`, kernel #6, built-in NF_TABLES/ZRAM,
   the mount table, and temperatures.
2. Temporarily configured `${HOST_USB_IP}/24` only on the host USB network interface with the matching
   MAC. A dedicated HTTP directory served only the rootfs and initialization script, with no SSH
   private key; the server bound only to the USB address.
3. The phone verified SHA256 after downloading, extracted into `/newroot` tmpfs, and ran the
   initialization script natively.
4. Read and pinned the SSH host public key through the physical serial console, then explicitly
   requested PID 1 to `switch_root`. All rescue shells stopped; Fedora's serial console became an
   authenticated getty.
5. When Fedora took over the link, host network management removed the temporary IPv4 address,
   causing the first SSH attempt to time out. Restoring the address on the same USB interface allowed
   connection. SSH host-key verification was not disabled, and no Wi-Fi route was substituted.

### firewalld: actual block / allow / block again

The new kernel included nftables and the required conntrack, NAT, reject, fib, and other functionality.
firewalld could run on initial boot, but the cross-installation had skipped RPM posttrans, leaving two
ghost links for the Fedora Server configuration and Polkit missing, so it used fallback settings.

Following the Fedora Server logic shown by `rpm -q --scripts firewalld` on the phone, the two relative
symbolic links were created in **tmpfs**, followed by restorecon, check-config, and reload. The default
zone then became FedoraServer; USB source `${LAN_SUBNET}` used the picasso-usb zone, allowing only
the SSH service. `tools/mkrootfs-fedora.sh` was updated with the same link-generation logic and
3 regression tests. **The tested rootfs archive was not regenerated** and retained the original hash
above; repairs to the running system were recorded separately.

A time-limited TCP 18080 test listener was started on the phone's USB address:

| State | Actual host connection |
| --- | --- |
| Port not allowed | Rejected |
| Temporarily allowed, with protective automatic expiry after 30 seconds | Succeeded; received the expected test marker |
| Allow rule removed, listener still running | Rejected again |

Afterward, the rules were removed and the listener stopped; permanent rules were not changed and no
service was exposed to the public Internet.

### ZRAM: actual swap-out, compression, and verified readback

- `/dev/zram0`: 1 GiB logical device, zstd, swap priority 100.
- `CONFIG_ZRAM_WRITEBACK` was not compiled in; the `backing_dev` attribute did not exist, and no
  Android disk backing was used.
- Linux `MADV_PAGEOUT` was applied to a separate 32 MiB anonymous mapping. The process's VmSwap
  reached 32768 KiB, ZRAM compressed data was approximately 2.26 MB, and subsequent readback
  matched SHA256 while VmSwap returned to 0.
- Python mmap did not expose the MADV_PAGEOUT constant, so the first probe exited before invoking
  it. A retry succeeded after checking value 21 against the running kernel's UAPI. This was neither a
  reboot nor a full-memory stress test; ZRAM swap contents were not directly overwritten.

### Clock and remaining failure

No usable RTC/NTP was available, and the system date at boot was behind, causing RPM queries to skip
some records because signatures were “not yet valid.” This session set only the phone's system clock
from trusted host time; it did not write the RTC, disable signature verification, or modify a key.
After the adjustment, RPM queries worked normally: 274 packages plus 1 key record. Time would still
need to be set or synchronized again after reboot.

Evidence of the DNF makecache failure was retained: no Internet egress was available, and the failure
was not attributed to nftables or damaged package signatures.

## Still outstanding

- Original ABL live RAM/dynamic carveouts and full-memory integrity.
- `Kernel image misaligned at boot`, PSCI PC mode=-3, and UFS assumed power/alignment warnings.
- RNG: CRNG initialized at approximately 99 seconds; qcom_rng loaded later and reported
  TRNG support not detected. This was not considered a hardware entropy-source pass.
- watchdog, ignore-unused dependencies, closed-loop thermal control, charging/battery state,
  suspend/resume, and the current Fedora shutdown path.
- Wi-Fi firmware extraction and power auditing existed, but `iw dev` was empty;
  `/sys/class/power_supply` was also empty.
- Native display/GPU/touch, Bluetooth, audio, cellular, cameras, and other peripherals had not passed acceptance.
- SELinux remained Permissive; persistent root filesystems and UFS writes were untested.

UFS/GPT were visible, the final sampled runtime_status was suspended, and the deferred-probe list was
empty; none of these meant persistent-write or long-term PM acceptance. The mount table contained
only RAM/API filesystems, swap contained only ZRAM, and no Android filesystem was mounted or write
command issued to an Android partition. Fedora udev could still read block-device metadata.

The “kernel time” reported by `systemd-analyze` included the preceding approximately 7.6 hours waiting
in rescue; userspace took approximately 6.35 seconds. This was not the phone's cold-boot time.

## Login and evidence

From `${REPO_ROOT}`:

```sh
ssh -F /dev/null -i ${SSH_PRIVATE_KEY} \
  -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=${SSH_KNOWN_HOSTS} \
  -o StrictHostKeyChecking=yes ${DEVICE_USER}@${PHONE_USB_IP}
```

Only the Fedora RAM system and SSH were left running; temporary HTTP, test listeners, and test rules
were cleaned up. Reboot would lose the rootfs, host keys, and all modifications. No automatic reboot
was performed; this was unsuitable for unattended operation while charging.

Evidence directory `out/confirmation-20261027/` had permissions 0700. `result.json` pinned hashes of the
image, archive, configuration, and evidence files, including `final-state.json`, firewall and ZRAM probe
JSON, boot serial output, and service logs. The original October 26 Fedora/M1 evidence was retained,
without overwriting old failure records. Latest unit tests: 59 total, 58 passed, 1 optional QEMU test
skipped; neither the final rootfs nor this session's runtime used QEMU.
