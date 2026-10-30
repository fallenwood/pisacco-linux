# Wi-Fi / RMTFS 第二阶段准备记录（历史） / Wi-Fi / RMTFS Stage 2 Preparation Record (Historical)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页是第二阶段试验前的历史准备快照，不代表后续或当前运行状态。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This is a historical pre-trial Stage 2 preparation snapshot, not a statement of later or current runtime status. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

**后续已临时启动 wifi2 并通过 wlan0 注册与 2.4/5 GHz 扫描，当前结果见 [WIFI-SCAN.md](WIFI-SCAN.md)。**
本页以下内容是试验前准备快照，不能再将“尚未启动”等描述当作当前状态。

用户在第一阶段说明之后明确回复“允许”：仅只读提取 `modemst1/modemst2/fsg` 为私有副本，
不挂载、不写回原分区，不读取 `persist/fsc`。第一阶段实测和限制见 [WIFI-BRINGUP.md](WIFI-BRINGUP.md)。
**当前仍运行已安装的 Fedora `6.18.58-picasso-lts #8` / XFS；Wi-Fi 仍不可用。**

## 已完成的准备

- 从先前已校验的原始 GPT 恢复归档独立取得三分区的 PARTUUID/长度，再与实际唯一 PARTNAME、
  设备 major/minor、块大小 ioctl、无挂载/swap/holders 核对。不以 `/dev/sdf*` 编号作为唯一身份。
- `tools/backup-radio-nv.py` 在 #8、无 DSP 注册时，只用 O_RDONLY/O_EXCL 源描述符复制各 8 MiB。
  第二次源读取、副本读回摘要均一致。原始私有副本在
  `/var/lib/picasso-wifi-nv/original-20261027/`，目录 0700、文件 0400。
- 主机只保存 GnuPG AES256 加密归档，并通过解密流校验三个文件及清单；没有写明文主机归档。
  密钥位于主机 `${PRIVATE_BACKUP_DIR}/`，不在项目/证据目录内，权限 0600。
  **备份、密钥和 NV 内容不得发布；不要丢失独立密钥。**
- 新的三个普通工作文件在 `/var/lib/picasso-wifi-nv/work-wifi2/`，目录 0700、文件 0600。
  初始内容与原始副本完全相同。之后 DSP 更新只能落到这些工作文件，不能写回原分区。
- 独立 `wifi-rmtfs` DTS/build profile、`-picasso-lts-wifi2` 模块，744 个模块文件已读回校验。
  #8 模块及安装镜像未被覆盖；原 NV 分区在准备结束时再次只读校验，仍与快照一致。
- 动态 RMTFS 预留总长 `0x282000`：主线驱动扣掉两端各 4 KiB 后提供原厂 `0x280000` 可用区。
  Memblock 选择空闲、未被固定保留区占用的 RAM；限定 2–4 GiB 地址范围以适配 32 位 IOVEC，
  不猜测固定物理地址。client-id 1、VMID MSS_MSA/15、no-map、guard pages 均有离线检查。
  仍未验证原始 ABL RAM map 或全部 RAM；实际分配地址和 SCM 访问需新内核实测。
- `qcom_rmtfs_mem` 和既有 MPSS/ath10k 驱动被自动加载黑名单阻止，需操作员核对后手动加载。
- 138 项测试：137 通过，1 项可选 QEMU 测试跳过。未在主机执行 AArch64 程序。

## FD-only 私有代理

`tools/rmtfs-private-proxy.py` 按固定上游 RMTFS QMI ABI 实现最小服务：
`linux-msm/rmtfs b30a3eb38f9af283f18dbd3c7755653efc52c094 / qmi_rmtfs.qmi`。
源码通过 HTTPS git 固定，不宣称发布者签名认证；没有直接部署上游宽泛的原始分区/`/dev/mem` 后端。

服务模板 `tools/rmtfs-private-proxy.service.in`：

- 独立 DynamicUser、零 capabilities、RootDirectory、ProtectSystem=strict、PrivateDevices。
- 仅只读绑定公共 `/usr`；隐藏真实 `/proc`、`/sys`、SSH/home，不挂载 NV 原件或裸 UFS 设备。
- PID 1 用 `OpenFile=` 传递四个已打开 FD：唯一 client-1 RMTFS 字符设备和三个 0600 普通工作文件。
  代理不按远端请求打开任何路径，也不需要暴露 `/dev/qcom_rmtfs_mem1` 节点给服务。
- 拒绝块设备、0400 原始备份、别名/重复 inode、错误设备号和错误 activation FD 集合。
- 只支持 fs1/fs2/fsg，拒绝其他路径；请求句柄、TLV、整批 IOVEC、共享缓冲及 8 MiB 文件边界均校验。
  短读直接失败，不用零填充冒充 NV；工作文件不得任意扩容。日志不打印 NV/DMA 内容。
- 运行 120 秒，systemd 上限 150 秒，无开机启用、无自动重启。仍需操作员监测、禁止 DSP 自动恢复。

已在真实 #8 上用 `/dev/zero` 验证 PID 1 向 DynamicUser 传递字符 FD、私有根内 Python/QRTR 库加载、
真实 proc/SSH 隐藏；代理本身在相同沙箱原生运行 `--help` 成功。**这不是实际 RMTFS 数据握手验证。**
第一份自测曾错误要求空 `/etc/ssh` 目录本身不存在，另有 oneshot RuntimeMaxSec 适用性警告；失败
unit/日志保留。第二份改为检查密钥不可见并使用 TimeoutStartSec，通过，没有 reset-failed。
DNF 无互联网失败也继续保留，不把当前 systemd 状态包装成健康验收。

## 下一次实机验证顺序

1. 手动进入 fastboot，重新确认 serial/product、电压、精确镜像摘要，仅 `fastboot boot`，不刷分区。
2. 核对 wifi2 config/FDT 和 XFS/SSH；DSP 保持 offline、recovery disabled，温度降到 40°C 以下。
3. 手动加载 RMTFS 内存驱动，核对实际 PA/size、Linux RAM bank、固定保留区不重叠、guard/client/device。
   对新分配缓冲区作有限读写回环验证；不能退回 `/dev/mem` 或随意物理地址。
4. 在隔离中先启动文件服务，检查 DynamicUser/零 capabilities/四个 FD 指向三份工作文件及指定字符设备。
5. 手动启动 MPSS，限时观察 RMTFS/NV、TFTP 和 WLFW 69；不运行 ModemManager/IPA/蜂窝数据栈。
   原厂共享 modem 固件内部行为不完全可控，不能承诺没有任何蜂窝射频行为。
6. 读到真实 chip/board ID 后准确选择本机原厂 BDF，再验证扫描、连接、DHCP/DNS/联网。
   新请求涉及 fsc/persist/其他保护分区时应停止确认，不提供假 NV 或空白校准。
7. 每次失败都停止 DSP/代理并保存证据；不把准备成功当成 Wi-Fi 成功，不直接持久刷入。

## 当前产物

- 独立测试镜像：`out/wifi-rmtfs-20261027/boot-wifi2-trial.img`。
- SHA256：`61022763880509ece9c87f1815b36c841bff4a0f08a4545f6c5f4f639a148304`。
- 新镜像**尚未在手机启动**；不继承 wifi1 或 #8 的实机结果。
- `out/boot-picasso.img` 仍为 #8：`81f28d44…fde043c`，完整安装/恢复边界见 [INSTALL-XFS.md](INSTALL-XFS.md)。
- 准备记录：`out/wifi-rmtfs-20261027/preparation-status.json`，证据目录 0700。
  加密 NV 备份同样属于隐私材料；不要盲目重复单机复制/staging 脚本。

## English

**wifi2 was subsequently temporarily booted, wlan0 registered, and 2.4/5 GHz scanning passed; see [WIFI-SCAN.md](WIFI-SCAN.md) for the later results.**
The following is a pre-trial preparation snapshot; descriptions such as “not yet booted” must not be treated as current status.

After the Stage 1 explanation, the user explicitly replied “allowed”: only read-only extraction of `modemst1/modemst2/fsg` into private copies, without mounting or writing back to the original partitions and without reading `persist/fsc`.
Stage 1 on-device findings and limitations are in [WIFI-BRINGUP.md](WIFI-BRINGUP.md).
**At this stage, the installed Fedora `6.18.58-picasso-lts #8` / XFS was still running, and Wi-Fi was still unavailable.**

## Completed preparation

- The three partitions' PARTUUIDs/lengths were independently obtained from the previously verified original GPT recovery archive, then checked against the actual unique PARTNAMEs, device major/minor numbers, block-size ioctl, and absence of mounts/swap/holders. `/dev/sdf*` numbering was not used as the sole identity.
- On #8, with no DSP registered, `tools/backup-radio-nv.py` copied 8 MiB per partition using only O_RDONLY/O_EXCL source descriptors. A second source read and readback hashes of the copies matched. Original private copies were placed in `/var/lib/picasso-wifi-nv/original-20261027/`, directory 0700 and files 0400.
- The host stored only a GnuPG AES256-encrypted archive, with all three files and the manifest verified through a decryption stream; no plaintext host archive was written. The key was in host `${PRIVATE_BACKUP_DIR}/`, outside the project/evidence directories, mode 0600. **Do not publish the backup, key, or NV contents; do not lose the separate key.**
- Three new regular working files were in `/var/lib/picasso-wifi-nv/work-wifi2/`, directory 0700 and files 0600. Initial contents exactly matched the originals. Subsequent DSP updates could write only to these working files, never back to the original partitions.
- Separate `wifi-rmtfs` DTS/build profile and `-picasso-lts-wifi2` modules; 744 module files were read back and verified. #8 modules and the installed image were not overwritten. The original NV partitions were reverified read-only at the end of preparation and still matched the snapshot.
- Dynamic RMTFS reservation totaled `0x282000`: after the mainline driver removed a 4 KiB guard at each end, it supplied the factory `0x280000` usable area. Memblock selected free RAM outside fixed reservations, constrained to 2–4 GiB for 32-bit IOVEC compatibility; no fixed physical address was guessed. client-id 1, VMID MSS_MSA/15, no-map, and guard pages had offline checks. The original ABL RAM map and all RAM remained unvalidated; the actual allocation address and SCM access required testing with the new kernel.
- An autoload blacklist blocked `qcom_rmtfs_mem` and the existing MPSS/ath10k drivers, requiring operator verification and manual loading.
- Of 138 tests, 137 passed and one optional QEMU test was skipped. No AArch64 program was executed on the host.

## FD-only private proxy

`tools/rmtfs-private-proxy.py` implemented a minimal service against the pinned upstream RMTFS QMI ABI:
`linux-msm/rmtfs b30a3eb38f9af283f18dbd3c7755653efc52c094 / qmi_rmtfs.qmi`.
Sources were pinned via HTTPS git, without claiming publisher-signature authentication. The broad upstream raw-partition/`/dev/mem` backends were not directly deployed.

Service template: `tools/rmtfs-private-proxy.service.in`.

- Separate DynamicUser, zero capabilities, RootDirectory, ProtectSystem=strict, and PrivateDevices.
- Only the public `/usr` was bound read-only. Real `/proc`, `/sys`, SSH/home were hidden; original NV copies and raw UFS devices were not mounted.
- PID 1 passed four already-open FDs using `OpenFile=`: the unique client-1 RMTFS character device and three 0600 regular working files. The proxy did not open paths from remote requests, and the service did not need exposure of the `/dev/qcom_rmtfs_mem1` node.
- Block devices, 0400 original backups, aliases/duplicate inodes, wrong device numbers, and incorrect activation FD sets were rejected.
- Only fs1/fs2/fsg were supported; other paths were rejected. Request handles, TLVs, complete IOVEC batches, shared buffers, and 8 MiB file boundaries were checked. Short reads failed directly rather than filling zeros to impersonate NV; working files could not grow arbitrarily. Logs did not print NV/DMA contents.
- Runtime was 120 seconds, with a systemd cap of 150 seconds; no boot enablement or automatic restart. Operator monitoring and disabled DSP automatic recovery were still required.

On real #8, `/dev/zero` was used to verify PID 1 passing a character FD to DynamicUser, Python/QRTR library loading inside the private root, and hiding real proc/SSH. The proxy itself also ran `--help` natively in the same sandbox. **This was not verification of an actual RMTFS data handshake.**
The first self-test incorrectly required the empty `/etc/ssh` directory itself to be absent, and there was a warning about RuntimeMaxSec applicability to a oneshot service. The failed unit/logs were retained. A second version checked that keys were invisible and used TimeoutStartSec; it passed, without reset-failed.
DNF failures without internet access were also retained; the then-current systemd state was not presented as a healthy-system acceptance result.

## Sequence for the next on-device verification

1. Enter fastboot manually; recheck serial/product, voltage, and the exact image hash. Use only `fastboot boot`, with no partition flashing.
2. Verify wifi2 config/FDT and XFS/SSH; keep the DSP offline with recovery disabled, and cool below 40°C.
3. Manually load the RMTFS memory driver. Verify actual PA/size, Linux RAM bank, no overlap with fixed reservations, and guards/client/device. Perform a bounded read/write loopback on the newly allocated buffer; do not fall back to `/dev/mem` or arbitrary physical addresses.
4. Start file services in isolation first; verify DynamicUser/zero capabilities and that the four FDs point to the three working files and designated character device.
5. Start MPSS manually and observe RMTFS/NV, TFTP, and WLFW 69 under a time limit. Do not run ModemManager/IPA/the cellular data stack. Internal behavior of the factory shared modem firmware is not fully controllable; absence of all cellular RF activity cannot be promised.
6. After obtaining real chip/board IDs, select this phone's factory BDF precisely, then verify scanning, connection, DHCP/DNS/network access. Stop for confirmation on new requests for fsc/persist/other protected partitions; do not supply fake NV or blank calibration.
7. On every failure, stop the DSP/proxy and save evidence. Preparation success is not Wi-Fi success, and must not lead directly to persistent flashing.

## Artifacts at this stage

- Separate test image: `out/wifi-rmtfs-20261027/boot-wifi2-trial.img`.
- SHA256: `61022763880509ece9c87f1815b36c841bff4a0f08a4545f6c5f4f639a148304`.
- The new image **had not yet booted on the phone**; it did not inherit wifi1 or #8 on-device results.
- `out/boot-picasso.img` remained #8: `81f28d44…fde043c`. Full installation/recovery boundaries are in [INSTALL-XFS.md](INSTALL-XFS.md).
- Preparation record: `out/wifi-rmtfs-20261027/preparation-status.json`, evidence directory 0700. Encrypted NV backups are also private material; do not blindly repeat device-specific copy/staging scripts.
