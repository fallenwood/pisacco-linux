# Wi-Fi / RMTFS 第二阶段准备记录（历史）

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
  密钥位于主机 `~/.local/state/picasso-private/`，不在项目/证据目录内，权限 0600。
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
