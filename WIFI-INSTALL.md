# Wi-Fi 版内核已写入手机 boot，正常重启验证通过

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

原一次性`test-chaldea-2g.sh`是已用试验，不能因/run重启消失就当作可重用正式联网工具。
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
