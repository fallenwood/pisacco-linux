# 来源、版本及许可

## 参考实现（2026-10-26 检索）

1. [`14sea/sunstone-linux`](https://github.com/14sea/sunstone-linux)：本地
   `../sunstone-linux`。参考分阶段启动、USB gadget、内建救援与发行版 rootfs 分离的设计。
   未搬运其 shim 源码（该仓库未声称拥有 shim 的授权），也未套用其硬件补丁。
2. [`sm7250-mainline/linux_kernel`](https://github.com/sm7250-mainline/linux_kernel)：
   固定 tip **`9272a06bfd3f2bb5eb952b41c70f0686a340e897`**；原始基线
   **`51e2945e2d192d40c7cad65626da03b453ab342e`**（7.3-rc 系列）。
   选取该范围的最终差异，而不是把早期 dirty/debug 提交逐个应用到 LTS。
   保留原文件署名和 SPDX，包括 Sreeshankar K 的 SM7250 工作及 Picasso 社区适配。
3. [`sm7250-mainline/docs`](https://github.com/sm7250-mainline/docs)：参考
   `copydown-shim-port.md`、`build-boot-manual.md`、`porting-filelist.md`、`picasso.md`。
   其中 Picasso 原厂 ABL/DTBO、RAM carveouts、WDT 和 v2 header 信息用于设计，
   新写的 shim 并非该项目已真机验证的 shim。
4. [`lazybrar/avicii-mainline`](https://github.com/lazybrar/avicii-mainline)：仅检查
   同 SoC 的 bring-up 状态，不使用 OnePlus 板级 DTS 或签名固件。

## 输入

- kernel.org [`releases.json`](https://www.kernel.org/releases.json) 查询时最新 LTS 为
  `6.18.58`；与本地 Fedora 44 宿主的 7.2 内核不是同一版本线。
- Linux `6.18.58` kernel.org tarball：SHA256 对照 kernel.org 的 `sha256sums.asc`，
  已固定进 `sources.json`。这里没有另行验证 PGP 签名，不能把 SHA256 检查称为签名认证。
- Alpine 3.23 AArch64 `busybox-static 1.37.0-r30`：APK 整包 SHA256 固定在清单中，
  只提取 `bin/busybox.static`。此二进制属于 initramfs，不将 Alpine 作为 Fedora root。
  BusyBox 源码见其对应 Alpine aports 与 [busybox.net](https://busybox.net/)，GPL-2.0。
- 最终 Fedora rootfs 由 Podman rootless user namespace 内的主机原生 DNF 从签名 RPM
  交叉安装 `@core` + Fedora Server 44 身份包，目标 aarch64，不依赖 OCI ARM 镜像或 QEMU。
  默认 HTTPS 中科大 Fedora releases/updates 镜像，RPM gpgcheck 保持开启，使用主机的
  Fedora 44 公钥。仓库配置、key SHA256、精确包清单和构建方法另存 out/，不是按日期永久
  冻结的软件仓库。普通 scripts/triggers 跳过，必要初始化在手机原生完成。
  早期 ARM 容器探测不属于最终 rootfs 来源，后续按用户要求停止，未用它导出最终系统。
- **当前打包基线**：用户放在工作目录的 `crDroidAndroid-13.0-20231215-picasso-v9.12.zip`，
  1,684,898,436 字节，SHA256 `e8f0a1951cd2b04c3f733b1cc5eea5acf171a2094992abeb920661ec76210d3b`。
  包 metadata 与只读 ADB 的 picasso / 增量 1702661267 / SDK 33 / 补丁 2023-12-05 匹配；
  包本身的 post-build 就是 Pixel husky 指纹，不能据此把硬件识别为 Pixel。
  boot.img SHA256 `8d29b7ebfdc1c5dd8f58b59f95218e6df43197181259dc7a490e1c32d9650070`；
  dtbo.img SHA256 `6e285dbd96d0dd83f1a56179ed9a9c89cd327e68a94cf679254bd1432cc6c112`。
  只提取 boot/dtbo/vbmeta/metadata，并验证 ZIP CRC32 与固定成员 hash，不执行包内代码。
  完整归档 hash 是本地记录，不是发布者签名认证。后来救援中只读测量实际分区：整个
  DTBO 一致；boot header/kernel/ramdisk/DTB 一致，但整个 boot hash 不同，不能当完整分区备份。
- **历史对照源，已不用于当前打包**：用户指定的原厂镜像来源：[`benjaminforras/mi-vendor-updater` 的 Picasso 包](https://github.com/benjaminforras/mi-vendor-updater/releases/download/picasso-stable/fw-vendor_picasso_miui_PICASSO_V12.0.6.0.QGICNXM_adf9e45b32_10.0.zip)，
  MIUI `V12.0.6.0.QGICNXM` / Android 10。只读取 ZIP 目录及 `boot.img` 成员，检查
  CRC32 `49f32a8e`；成员 SHA256 `36a0ae150970092b7a1752a2b8fc1c0f2d75f39fede232ee127c49eb8aec75c2`
  已固定于 `device.json`。没有下载/验证完整归档或验证发布者签名。
  原厂镜像仅保存在被忽略的 `downloads/stock/`，不纳入源码分发，也未刷写其中固件。

## 相对社区 tip 的 LTS 调整

`kernel/patches/0001-sm7250-picasso-headless-6.18.patch` 针对**干净 6.18.58**，包含：

- GCC/clock headers、TLMM 和其安全 GPIO mask、RPMh clocks/domains；
- NoC 采用 6.18 的 `.link_nodes = (struct qcom_icc_node *[]) {...}` 和
  `.alloc_dyn_id = true`，不沿用旧的全局节点 ID；
- GCC 的 `qcom_cc_driver_data` / CBCR 数组去掉与 6.18 API 不兼容的 const；
- UFS/QMP PHY 的平台数据、32-bit DMA、QPHY、pinctrl reset、SAVECONFIGTIME；
  6.18 没有参考 tip 的全部 link-startup post-change 机制，不整体替换 UFS 核心；
- SM7250 watchdog 使用 APCS_TMR 布局，bring-up 专用 stop；
- 社区 board/SoC DTS 原样作为基础，另用 `dts/` overlay 裁剪外设、修正 `dr_mode`
  属性、添加 CPU cooling maps。保留未启用设备的描述不代表已经回移植其驱动。
- 对照用户指定的 Q 固件 Lito v1/v2 DTB，额外保留 CVP 的 `0x86f00000 + 0x500000`；
  runtime DT 覆盖该历史源两个静态 base DTB 的全部固定保留区域。
- 当前 crDroid 包有 12 个 base DTB、21 个 DTBO；根据 ADB 索引对 DTB 9 / DTBO 19
  进行 libfdt 离线合并。overlay 根 ID 为 Picasso (`qcom,board-id=0x24`)，合并结果的
  21 个固定 reserved-memory 区域均被 runtime DT 覆盖，要求 no-map 的区域也有 no-map。
  动态分配、bootloader 额外写入的 RAM/carveouts 和实际手机分区仍未验证。
  打包时保留完整 12-DTB blob，不把合并后的 vendor DT 交给主线内核。

没有带入 dirty 阶段的 SCSI/UFS core、通用 DMA、SMMU 调试补丁；没有启用未移植的
GPU/显示/音频/触摸 Kconfig 条目。

新 shim 采用 ARM64 允许的 EL1/EL2 交接，不主动降级 EL；copydown 前向字节拷贝，
清缓存到 PoC，保留内嵌 DTB。其物理地址、cache 和 ABL 行为仍须实际硬件验证。

## 许可

- 新脚本、测试、initramfs init、shim：**GPL-2.0-only**，见 `LICENSE`。
- 内核补丁内每个文件以其原 SPDX/版权声明为准；设备树/部分 binding 是 BSD 许可，
  不因装入补丁而改变许可。
- 不包含签名固件、Android 镜像、私钥或商业授权的再分发承诺。
