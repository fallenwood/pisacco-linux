# Wi-Fi 版内核已写入手机 boot，正常重启验证通过 / Wi-Fi Kernel Written to the Phone's boot Partition; Normal Reboot Verified

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页是原 #10 安装及正常重启的历史字节记录；后续安装状态见更新链接，旧哈希不是当前分区声明。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This is a historical exact-byte record of the original #10 installation and normal reboot; linked updates cover later installation, and old hashes do not assert the current partition contents. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

> 本页是原#10安装/正常重启的历史字节记录。后续用户接受自行启动限制，另授权写入同一#10 Image/config/模块的电源键DTB版，原#10与#8仍保留回滚；新boot读回通过但未重启。当前安装见[POWER-PERSISTENT.md](POWER-PERSISTENT.md)，勿把本页旧boot哈希当作当前分区哈希。

2026-10-28，用户要求“写入手机存储”并在说明范围后要求“继续”。
**当前默认及实际运行内核已是 `6.18.58-picasso-lts-wifi2 #10`，不再只是电脑临时 fastboot boot。**
Fedora Server 44 继续使用原有 userdata / XFS；没有重装、格式化或清除原 Linux 文件。

## 已实际执行

1. 将先前原生启动且已通过 WPA2/DHCP/SG/DNS/HTTPS 的**同一份字节镜像**，以及#8回退镜像，
   写入手机 XFS 的 `/boot/picasso/wifi-install-20261028/`。目录0700，镜像root0600，fsync及完整哈希读回通过。
2. 再次核验原15,285个静态文件、当前完整#8 boot、七个保留分区、六个LUN GPT；
   三份原授权 NV 以 O_DIRECT/O_RDONLY/O_EXCL 读取验证及0400私有备份一致；744个匹配模块及两个实验模块再次验证。
3. 唯一PARTNAME=boot、原GPT PARTUUID、精确134,217,728字节、实际块设备major/minor共同识别目标；
   排除挂载/swap/holders、检查XFS标记/UUID及实际运行#10 config/FDT，验证原boot仍为#8。
4. 通过PID1管理的独占写入程序，仅更新boot，补零至分区末尾、fsync、BLKFLSBUF后**完整128MiB读回一致**。
   未写GPT、DTBO、recovery、vbmeta、modem固件或原NV；未再清空super。
5. 实际 `systemctl reboot`，**没有 fastboot boot**；USB SSH重新连接、boot ID变化，
   `uname`、`/proc/config.gz`及运行FDT均匹配#10，原生systemd/XFS/sshd/firewalld可用。
6. 重启后再次核验：15,285个原静态文件（543,194,505字节）、**新boot完整分区**、七个保留分区、六GPT；
   三份原NV及0400备份一致，NV普通工作副本跨重启完全未变，744个模块、回退镜像及实验模块仍一致。

写入程序的起止最高温度采样为37.8°C；重启后首次检查最高39.4°C，后续最终检查38.8°C。
写入开始<40°C、写入循环全部传感器45°C中止线保持，没有提高温度/发射功率。
这些检查不是持续热稳定、电池或充电安全证明。

## 新默认镜像与#8回退基线

| 角色 | SHA256 |
|---|---|
| 当前#10镜像，33,820,672字节 | `61022763880509ece9c87f1815b36c841bff4a0f08a4545f6c5f4f639a148304` |
| 当前完整boot，134,217,728字节（含零padding） | `f091833a8d4844d14d055de8e9b3cfce523c3a6889ade6c422b3bd0d9b853ce9` |
| 回退#8镜像，33,820,672字节 | `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c` |
| 回退#8完整boot应有的哈希 | `312e42f3c590faa3c7988b8e02e15f7bee1952dee785a0d0acb218f088a1a696` |

手机：

- `/boot/picasso/wifi-install-20261028/boot-wifi2.img`
- `/boot/picasso/wifi-install-20261028/boot-lts8-rollback.img`
- 同目录保存提交结果、请求/范围说明、刷入前失败状态和网络验收摘要；**没有凭据或原NV payload**。

主机：

- 当前：`out/wifi-install-20261028/boot-installed-wifi2.img`。
- 原#8：`out/install-xfs-20261027/boot-xfs.img`及`out/boot-picasso.img`，**两者仍原样保留为#8，不能再叫当前默认镜像**。
- canonical #8 Image/config/DTB/boot产物不覆盖；当前#10对应源镜像/审计仍在 `out/wifi-rmtfs-20261027/`。

本机非A/B：备份文件不意味着有自动fallback、boot菜单或已验证的回滚流程。
如新内核不能启动，先使用已记录的设备身份/序列号进入受控fastboot恢复，
核对#8哈希后可临时启动该镜像获取原XFS/SSH；再按相同分区身份和全读回规则恢复boot。
不要对任意`/dev/sd*`直接dd，不改GPT/vbmeta/DTBO。恢复#8也不会恢复已删除的Android及个人资料。

## 明确没有自动启用无线

**本次持久化的是启动内核和已验证的支持文件，不是持续联网服务。**

- 新一次正常启动后 remoteproc/rmtfs/WLAN均未自动注册/启动，无默认IPv4路由。
- 原`ath10k_snoc`、`qcom_q6v5_pas`、`rmtfs_mem`黑名单保留，MPSS auto_boot=false，自动崩溃重启未启用。
- 同设备DMS→WLFW永久MAC、SG实际信道/EIRP/DFS检查、私有副本FD-only后端及HT20等依赖仍必须由受控流程执行。
- 没有读取或保存密码；旧PMK已按承诺删除。profile仍为不自动连接、permanent MAC、psk-flags2、drop。
- CPU6/7恢复原2,208,000/2,400,000kHz上限；没有把临时频率限制/observer模块设为默认自加载。
- 重启后未输入密码、未再次启动无线，因此**不把刷入前的网络成功说成重启后已联网复验**。
  刷入前的同字节#10真实网络验收见 [WIFI-NETWORK.md](WIFI-NETWORK.md)。

原一次性`${WIFI_2G_TEST_SCRIPT}`是已用试验，不能因/run重启消失就当作可重用正式联网工具。
旧runner的NV工作副本checkpoint、动态RAM地址/字符设备及运行目录均有试验语义；
后续联网需要新的受控流程重新发现和验证，不能直接把旧request.json或120秒代理常驻化。
若要开机自动联网、保存凭据或长期无人值守使用，仍是单独的设计/授权与实际验收。

## 保留历史与证据

正常重启自然结束/run临时单元；所有原失败的结果和刷入前failed-unit状态已存档，**没有 reset-failed 或删旧证据**。
当前离线/不连接不能被视为历史DNF任务已恢复。只做可信USB主机校时和PID1下次启动时间下限更新，未写RTC、未声称NTP持续工作。

仍是实验性headless手机：SELinux Permissive、Linux电池/充电遥测、RF行为/安全、长期热/内存/UFS/休眠/看门狗/掉电恢复和其他外设未验收。
无IPA/蜂窝数据启用；共享专有modem固件行为不保证完全静默。

证据：`out/wifi-install-20261028/`，包括写入全读回、正常重启结果、前后原NV/文件/GPT/模块检查及校验清单。
原始XFS安装历史：[INSTALL-XFS.md](INSTALL-XFS.md)。

## English

> This page is the historical exact-byte record of the original #10 installation/normal reboot. The user later accepted the self-start limitation and separately authorized writing a power-button DTB variant using the same #10 Image/config/modules. Original #10 and #8 were retained for rollback. The new boot passed readback but had not rebooted. For the later installation, see [POWER-PERSISTENT.md](POWER-PERSISTENT.md); do not treat this page's old boot hash as the current partition hash.

2026-10-28. The user requested “write it to phone storage” and, after the scope was explained, asked to “continue”.
**At this stage, the default and actually running kernel was `6.18.58-picasso-lts-wifi2 #10`, no longer merely a temporary computer-initiated fastboot boot.**
Fedora Server 44 continued using the existing userdata / XFS; original Linux files were not reinstalled, formatted, or cleared.

## What was actually done

1. The **same byte-for-byte image** previously booted natively and verified for WPA2/DHCP/SG/DNS/HTTPS, together with the #8 rollback image, was written to the phone's XFS under `/boot/picasso/wifi-install-20261028/`. Directory 0700, root0600 images, fsync, and full-hash readback passed.
2. The original 15,285 static files, current complete #8 boot, seven preserved partitions, and six LUN GPTs were rechecked. The three originally authorized NV partitions were verified through O_DIRECT/O_RDONLY/O_EXCL reads and matched 0400 private backups; 744 matching modules and two experimental modules were reverified.
3. The target was jointly identified by unique PARTNAME=boot, original GPT PARTUUID, exact size 134,217,728 bytes, and actual block-device major/minor. Mounts/swap/holders were excluded; XFS marker/UUID and actually running #10 config/FDT were checked, and existing boot was verified as #8.
4. An exclusive PID1-managed writer updated only boot, padded with zeros to the partition end, called fsync and BLKFLSBUF, and **read back the entire 128 MiB successfully**. It did not write GPT, DTBO, recovery, vbmeta, modem firmware, or original NV, and did not clear super again.
5. Actual `systemctl reboot`, **without fastboot boot**. USB SSH reconnected, boot ID changed, and `uname`, `/proc/config.gz`, and runtime FDT matched #10. Native systemd/XFS/sshd/firewalld were available.
6. Post-reboot rechecks again verified all 15,285 original static files (543,194,505 bytes), **the complete new boot partition**, seven preserved partitions, and six GPTs. The three original NV partitions and 0400 backups matched, regular NV working copies were completely unchanged across reboot, and 744 modules, rollback images, and experimental modules still matched.

Highest temperature sampled at the writer's start/end was 37.8°C; the first post-reboot check peaked at 39.4°C and the later final check at 38.8°C.
Writing started below 40°C, with all sensors checked against the unchanged 45°C abort line during the write loop. Temperature/transmit power limits were not raised.
These checks did not prove sustained thermal stability, battery safety, or charging safety.

## New default image and #8 rollback baseline at this stage

| Role | SHA256 |
|---|---|
| #10 image at this stage, 33,820,672 bytes | `61022763880509ece9c87f1815b36c841bff4a0f08a4545f6c5f4f639a148304` |
| Complete boot at this stage, 134,217,728 bytes including zero padding | `f091833a8d4844d14d055de8e9b3cfce523c3a6889ade6c422b3bd0d9b853ce9` |
| Rollback #8 image, 33,820,672 bytes | `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c` |
| Expected complete boot hash for rollback #8 | `312e42f3c590faa3c7988b8e02e15f7bee1952dee785a0d0acb218f088a1a696` |

On the phone:

- `/boot/picasso/wifi-install-20261028/boot-wifi2.img`
- `/boot/picasso/wifi-install-20261028/boot-lts8-rollback.img`
- The same directory held write-commit results, request/scope explanations, pre-flash failure state, and a network-acceptance summary; **no credentials or original NV payload**.

On the host:

- Installed at this stage: `out/wifi-install-20261028/boot-installed-wifi2.img`.
- Original #8: `out/install-xfs-20261027/boot-xfs.img` and `out/boot-picasso.img`, **both retained unchanged as #8 and no longer to be called the current default image**.
- Canonical #8 Image/config/DTB/boot artifacts were not overwritten. Corresponding #10 source image/audit remained in `out/wifi-rmtfs-20261027/`.

This phone is non-A/B. Backup files do not imply automatic fallback, a boot menu, or a verified rollback procedure.
If the new kernel cannot boot, first use the recorded device identity/serial number to enter controlled fastboot recovery.
After checking the #8 hash, temporarily boot that image to obtain the original XFS/SSH, then restore boot under the same partition-identity and full-readback rules.
Do not directly dd an arbitrary `/dev/sd*`, and do not alter GPT/vbmeta/DTBO.
Restoring #8 would not recover the deleted Android installation or personal data.

## Wireless was explicitly not enabled automatically

**What became persistent was the boot kernel and verified support files, not a continuously connected networking service.**

- After the new normal boot, remoteproc/rmtfs/WLAN did not automatically register/start; no default IPv4 route existed.
- The original `ath10k_snoc`, `qcom_q6v5_pas`, and `rmtfs_mem` blacklist remained. MPSS auto_boot=false, with no automatic crash restart enabled.
- Same-device DMS→WLFW permanent-MAC provisioning, actual SG channel/EIRP/DFS checks, private-copy FD-only backend, HT20, and other dependencies still had to be executed by a controlled process.
- No password was read or saved; the old PMK was deleted as promised. The profile still prohibited autoconnect and used permanent MAC, psk-flags2, and drop.
- CPU6/7 were restored to original maximums 2,208,000/2,400,000 kHz. Temporary frequency caps/observer modules were not set to autoload by default.
- No password was entered and wireless was not restarted after reboot. **Pre-flash network success was not claimed as post-reboot networking revalidation.** The pre-flash real network acceptance of the same #10 bytes is in [WIFI-NETWORK.md](WIFI-NETWORK.md).

The original one-off `${WIFI_2G_TEST_SCRIPT}` was an already-used experiment; reboot clearing /run did not make it a reusable production networking tool.
The old runner's NV working-copy checkpoint, dynamic RAM address/character device, and run directory had experimental semantics.
Later networking required a new controlled process to rediscover and verify them; old request.json or the 120-second proxy could not simply become a persistent service.
Automatic networking at boot, saved credentials, or long-term unattended use still required separate design/authorization and actual acceptance.

## Retained history and evidence

Normal reboot naturally ended /run temporary units.
All original failed results and pre-flash failed-unit states were archived; **no reset-failed or deletion of old evidence**.
The offline/disconnected state did not establish that historical DNF jobs had recovered.
Only trusted USB-host clock synchronization and updating PID1's lower bound for the next startup time were performed; RTC was not written and continuous NTP operation was not claimed.

This remained an experimental headless phone: SELinux Permissive; Linux battery/charging telemetry, RF behavior/safety, long-term thermal/memory/UFS/suspend/watchdog/power-loss recovery, and other peripherals had not passed acceptance.
IPA/cellular data were not enabled; complete silence of the shared proprietary modem firmware was not guaranteed.

Evidence: `out/wifi-install-20261028/`, including full-write readback, normal reboot results, before/after original-NV/file/GPT/module checks, and verification manifests.
Original XFS installation history: [INSTALL-XFS.md](INSTALL-XFS.md).
