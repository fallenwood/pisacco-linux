# 来源、版本及许可 / Sources, Versions, and Licensing

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录；来源及版本按原检索、构建时间理解，反引号中的代码及证据路径相对于仓库根目录。 / Historical stage record; sources and versions refer to the recorded research/build stage. Code and evidence paths in backticks are relative to the repository root.

## 中文

## 参考实现（2026-10-26 检索）

1. [`14sea/sunstone-linux`](https://github.com/14sea/sunstone-linux)：本地
   `sunstone-linux`。参考分阶段启动、USB gadget、内建救援与发行版 rootfs 分离的设计。
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

## English

## Reference implementations (researched 2026-10-26)

1. [`14sea/sunstone-linux`](https://github.com/14sea/sunstone-linux), local path
   `sunstone-linux`. Referenced its staged-boot, USB gadget, and separation of built-in rescue
   from distribution rootfs design. Its shim source was not copied: that repository did not claim
   authorization for the shim. Its hardware patches were not applied either.
2. [`sm7250-mainline/linux_kernel`](https://github.com/sm7250-mainline/linux_kernel):
   pinned tip **`9272a06bfd3f2bb5eb952b41c70f0686a340e897`**; original baseline
   **`51e2945e2d192d40c7cad65626da03b453ab342e`** (7.3-rc series).
   The final diff across that range was selected rather than applying early dirty/debug commits
   one at a time to LTS. Original file attribution and SPDX were retained, including Sreeshankar K's
   SM7250 work and the community Picasso adaptation.
3. [`sm7250-mainline/docs`](https://github.com/sm7250-mainline/docs): referenced
   `copydown-shim-port.md`, `build-boot-manual.md`, `porting-filelist.md`, and `picasso.md`.
   Their information on stock Picasso ABL/DTBO, RAM carveouts, WDT, and the v2 header informed
   the design. The newly written shim is not that project's hardware-verified shim.
4. [`lazybrar/avicii-mainline`](https://github.com/lazybrar/avicii-mainline): checked only the bring-up
   status for the same SoC; no OnePlus board DTS or signed firmware was used.

## Inputs

- kernel.org [`releases.json`](https://www.kernel.org/releases.json) listed `6.18.58` as the latest LTS
  when queried; it is not the same version line as the local Fedora 44 host's 7.2 kernel.
- Linux `6.18.58` kernel.org tarball: SHA256 checked against kernel.org's `sha256sums.asc` and
  pinned in `sources.json`. PGP signatures were not independently verified here; SHA256 checking
  must not be described as signature authentication.
- Alpine 3.23 AArch64 `busybox-static 1.37.0-r30`: the entire APK SHA256 is pinned in the manifest,
  and only `bin/busybox.static` is extracted. This binary belongs to initramfs; Alpine is not used
  as the Fedora root. BusyBox source is available in the corresponding Alpine aports and at
  [busybox.net](https://busybox.net/), GPL-2.0.
- The final Fedora rootfs is cross-installed from signed RPMs by host-native DNF inside a Podman
  rootless user namespace: `@core` + Fedora Server 44 identity packages, targeting aarch64,
  without an OCI ARM image or QEMU. By default it uses the HTTPS USTC Fedora releases/updates
  mirrors, keeps RPM gpgcheck enabled, and uses the host's Fedora 44 public key. Repository
  configuration, key SHA256, exact package list, and build method are separately saved in out/;
  the software repositories are not permanently frozen by date. Ordinary scripts/triggers are
  skipped, with necessary initialization performed natively on the phone. Early ARM-container
  probes are not part of the final rootfs provenance; they were later stopped at the user's request
  and were not used to export the final system.
- **Packaging baseline at this stage**: user-provided
  `crDroidAndroid-13.0-20231215-picasso-v9.12.zip` in the working directory,
  1,684,898,436 bytes, SHA256
  `e8f0a1951cd2b04c3f733b1cc5eea5acf171a2094992abeb920661ec76210d3b`.
  Package metadata matches read-only ADB's picasso / incremental 1702661267 / SDK 33 /
  patch 2023-12-05. The package's own post-build fingerprint is Pixel husky; this must not be used
  to identify the hardware as a Pixel.
  boot.img SHA256 `8d29b7ebfdc1c5dd8f58b59f95218e6df43197181259dc7a490e1c32d9650070`;
  dtbo.img SHA256 `6e285dbd96d0dd83f1a56179ed9a9c89cd327e68a94cf679254bd1432cc6c112`.
  Only boot/dtbo/vbmeta/metadata are extracted, with ZIP CRC32 and pinned member hashes checked;
  no package code is executed. The full archive hash is a local record, not publisher-signature
  authentication. Later read-only measurements of actual partitions from rescue showed complete
  DTBO agreement and matching boot header/kernel/ramdisk/DTB, but a different complete boot hash;
  the ROM boot cannot be treated as a full-partition backup.
- **Historical comparison source, no longer used for packaging at this stage**:
  the user-specified stock-image source,
  [the Picasso package from `benjaminforras/mi-vendor-updater`](https://github.com/benjaminforras/mi-vendor-updater/releases/download/picasso-stable/fw-vendor_picasso_miui_PICASSO_V12.0.6.0.QGICNXM_adf9e45b32_10.0.zip),
  MIUI `V12.0.6.0.QGICNXM` / Android 10. Only the ZIP directory and `boot.img` member were read,
  checking CRC32 `49f32a8e`. Member SHA256
  `36a0ae150970092b7a1752a2b8fc1c0f2d75f39fede232ee127c49eb8aec75c2`
  is pinned in `device.json`. The full archive was not downloaded/verified, nor was a publisher
  signature verified. The stock image is stored only in ignored `downloads/stock/`; it is excluded
  from source distribution, and none of its firmware was flashed.

## LTS adjustments relative to the community tip

`kernel/patches/0001-sm7250-picasso-headless-6.18.patch` targets **clean 6.18.58** and includes:

- GCC/clock headers, TLMM and its secure GPIO mask, RPMh clocks/domains.
- NoC uses the 6.18 `.link_nodes = (struct qcom_icc_node *[]) {...}` and `.alloc_dyn_id = true`,
  rather than retaining the old global node IDs.
- GCC `qcom_cc_driver_data` / CBCR arrays drop const qualifiers incompatible with the 6.18 API.
- UFS/QMP PHY platform data, 32-bit DMA, QPHY, pinctrl reset, and SAVECONFIGTIME.
  6.18 does not have all the reference tip's link-startup post-change mechanisms;
  the UFS core is not replaced wholesale.
- SM7250 watchdog uses the APCS_TMR layout with a bring-up-only stop.
- Community board/SoC DTS files are used unchanged as the base, with separate `dts/` overlays
  pruning peripherals, fixing the `dr_mode` property, and adding CPU cooling maps. Retaining
  descriptions of disabled devices does not mean their drivers have been backported.
- Comparison with the user-specified Q firmware's Lito v1/v2 DTBs adds conservative retention of
  CVP `0x86f00000 + 0x500000`. The runtime DT covers all fixed reserved regions of that historical
  source's two static base DTBs.
- The crDroid package at this stage contains 12 base DTBs and 21 DTBOs; libfdt performs an offline
  merge of DTB 9 / DTBO 19 according to the ADB indexes. The overlay root ID is Picasso
  (`qcom,board-id=0x24`); all 21 fixed reserved-memory regions in the merged result are covered
  by the runtime DT, including no-map wherever required. Dynamic allocations, extra
  bootloader-written RAM/carveouts, and the actual phone partitions were still unverified at this
  recorded stage. Packaging retains the complete 12-DTB blob rather than passing the merged
  vendor DT to the mainline kernel.

Dirty-stage SCSI/UFS core, generic DMA, and SMMU debug patches were not included. Unported
GPU/display/audio/touch Kconfig entries were not enabled.

The new shim uses the EL1/EL2 handover permitted by ARM64 and does not actively lower the EL.
copydown uses a forward byte copy, cleans caches to PoC, and retains the embedded DTB.
Its physical addresses, cache behavior, and ABL behavior still require actual hardware verification
at this recorded stage.

## Licensing

- New scripts, tests, initramfs init, and shim: **GPL-2.0-only**, see `LICENSE`.
- Each file in the kernel patch retains its original SPDX/copyright declaration. Device trees and
  some bindings are BSD-licensed; inclusion in a patch does not change their licenses.
- No signed firmware, Android images, or private keys are included, nor is there a promise of
  redistribution under commercial authorization.
