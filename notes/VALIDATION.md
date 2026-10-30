# 验证记录 / Validation Record

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 按原时间点保留的历史阶段记录；“最新”“当前”等不代表此后的实时状态，反引号中的代码及证据路径相对于仓库根目录。 / Historical stage records preserved at their original times; “latest” and “current” do not establish later live status. Code and evidence paths in backticks are relative to the repository root.

## 中文

最新[PODMAN-USER-SESSION.md](PODMAN-USER-SESSION.md)：单独签名同版本systemd-pam安装/依赖预检/RPM文件与DB验证通过，systemd核心版本、PAM/SSH配置字节不变；真实PAM新SSH有XDG/DBUS，用户manager/bus/linger就绪，UID1000 `podman ps -a`无警告，info=`systemd v2 true`。首轮离线enable缺运行目录的拒绝保留，独立续作成功无重装/reset。**软件安装会变动manifest中的RPMDB：本轮不是全部静态/保护分区全检，未来须明确处理DB/包集转移；旧manifest和请求未静默更新。** 未拉镜像/创建启动容器、刷boot或重启，Wi-Fi/屏幕不变。

最新[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)：412离线411通过/1跳过；新R2只替换取证方法，原始同PHY完整dump确认8个真实INDOOR_ONLY位，41库存/24 CN20MHz启用验证通过，45秒85UP样本；一次2G激活0.713秒、CCMP/DHCP/HT20/DNS/TLS200，90秒87关联UP样本及之后实时HTTPS通过。持久enabled/active、旧failed/预算保留，活跃dirty正常。没有本轮强制掉线/完整stop/下次开机/RF或充电长期验收，历史失联根因不因此自动视作修好。

最新[WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md)：只读核对本机iw RPM和匹配签名SourceRPM、Linux6.18.58路径，确认iw6.17信息文本不输出原始INDOOR_ONLY，故旧CN字符串核验存在确定取证缺陷；合成bit存在仍旧拒绝的离线复现通过。GET-only原始采集器支持split/完整dump/原始attr14，396项离线395通过1跳过及native空PHY查询通过，**不是实际live bit/RF/联网验收**。手机服务/政策hash、failed状态、预算和离线安全状态未改，本轮零RF/SSID尝试。

最新[WIFI-CN.md](WIFI-CN.md)：请求SG→CN，内核global CN及当前签名regdb参考核实，独立CN配置/审计器持久写入。唯一CN radio初始化在5180MHz室内标志严格检查处failed、完整cleanup和独立checkpoint/assets审计通过，未管理UP/激活SSID/再试RF。不能把配置CN当作已联网/射频安全/驱动根因已确诊。384项离线383通过、1可选跳过；原语法错误和首轮Python类元数据断言失败日志保留，修正未削弱审计/租约/温控。

最新一次明确${FALLBACK_SSID}请求：既有radio上NM激活0.672秒返回0，但紧接监管域白名单检查失败，常驻服务enabled/failed且WLAN/DSP完整安全退出；独立工作checkpoint/assets/CPU/core/dirty审计通过，无第二次RF/回退/重启/监管绕过。**不是持续联网成功**，旧45秒UP样本仍是历史。原始错误域未捕获，不推断具体国家或硬件根因。证据`out/wifi-connect-2g-20261030T072042Z/`，服务细节[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)。

最新[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)：持久radio服务enabled/active，真实wlan0管理UP且未关联/无IPv4；45秒85次UP原生样本通过，旧重连预算/failed保留并切换默认所有者。普通失联保持UP逻辑离线覆盖，45°C/租约/DSP/安全故障仍cleanup，不伪造carrier或Internet。372项离线371通过/1可选跳过；本次未再激活SSID/重启/刷boot，旧offline/cleanup快照不代表当前活跃radio状态。

最新[WIFI-RECONNECT.md](WIFI-RECONNECT.md)：持久有界重连监管器已启用，真机3次自然掉线→完整安全清理/检查点→10/30/60秒退避→新PID1 worker恢复DHCP/DNS/HTTPS已通过；本boot第四轮又掉线，预算耗尽后正常策略退出并安全清理，无第五轮/重置。峰值43.4°C，热限/租约/四FD/原NV边界不变；359项离线358通过/1可选跳过。未修复底层失联，未做新boot或人为断网试验。

最新[LAN-SSH.md](LAN-SSH.md)：LAN${LAN_SUBNET} TCP22 runtime/permanent规则、公钥追加/旧key保留通过；SELINUX配置disabled但实际内核仍Permissive，未改boot/重启。显式授权一个公钥文件基线例外后15,285文件/543,194,605字节及boot/七保护/六GPT通过，峰值35.7°C。Wi-Fi在此前在线快照之后已fallback link loss并安全退出，未自动恢复；LAN新key登录和完全SELinux Disabled尚未验收。

最新Wi-Fi自动连接见[WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md)：保留旧watchdog失败，新独立控制器45秒完整成功/安全清理后由root0400原生证据gate启用常驻；当前2.4G已连，DNS/HTTPS、90秒观察及约303秒快照通过。342项离线341通过/1可选跳过。原beacon根因、新boot及长期/RF安全仍未验收；不放宽8秒watchdog/40–45°C/租约/无循环保护。

最新受限电源键安装见[POWER-PERSISTENT.md](POWER-PERSISTENT.md)：用户接受自动启动限制后，boot128MiB完整读回及15,285基线文件/七保护分区/六GPT通过；常驻服务enabled/inactive，未重启，开机激活/实键仍未验收。334项离线测试333通过/1项可选QEMU跳过。两次写前沙箱拒绝、旧failed units和marker保留；保持关机/手动冷开机仍失败，充电/触发/复位未改。

## 最新：XFS 持久安装（2026-10-27）

已按用户授权将 Fedora 44 Server minimal 安装到 userdata 的 XFS，写入 boot 并清空 super。
精确镜像 `81f28d44…`（33,820,672 B），内核 `6.18.58-picasso-lts #8`；两次正常重启及
fsync 文件保留通过，第二次在清除 Android super 后进行。15,285 个静态文件的内容/权限、
整个 boot、7 个保留分区及六个 LUN GPT 读回一致。新镜像重新通过 firewalld 与 ZRAM 功能测试。

详细记录、SHA256、SSH、恢复和安全限制见 [INSTALL-XFS.md](INSTALL-XFS.md)，最终证据：
`out/install-xfs-20261027/result.json`。277 包、RPM 278 条；最后快照 systemd running、无失败
unit，但无互联网/DNS/NTP 的问题未解决，也没有重置失败以制造健康状态。SELinux Permissive。
完整内存、闭环温控/充电/watchdog/挂起/关机、掉电与长稳仍未验收。全 super 读回后记录 46.8°C，
随后冷却到 40°C 以下；不是热保护验收。78 项测试，77 通过、1 可选 QEMU 测试跳过。

以下“没有刷写/格式化、根为 tmpfs”等描述均按各自时间点保留，不是当前安装状态。

## RAM 确认（历史，2026-10-27 安装前）

**新镜像 `59784cc4…` 已在真机进入 Fedora，nftables/firewalld 和 ZRAM 功能测试通过。**
完整步骤、登录和边界见 [CONFIRMATION.md](CONFIRMATION.md)，证据为
`out/confirmation-20261027/result.json`，硬件结果仍绑定精确镜像 hash/大小。

- 真正 systemd PID 1，USB SSH/sudo 正常，274 个软件包、RPM 275 条。
- firewalld 修复 Fedora Server ghost 配置链接后 reload，USB 测试端口阻断/放行/再阻断通过。
- 1 GiB zstd ZRAM：32 MiB 匿名页换出并读回 SHA256 一致，无磁盘后备。
- systemd 仍 degraded，唯一失败项为没有互联网/DNS 导致的 dnf-makecache；未清除失败。
- 校时解决 RPM 查询的签名“尚未生效”，未关闭签名校验。修复均在 tmpfs；构建脚本补齐
  firewalld ghost 链接，59 个测试中 58 通过、1 个可选 QEMU 测试跳过。
- 本次沿用已经运行的新救援内核，没有发送重启/boot/刷写命令。只解包 tmpfs 并交给 systemd，
  未挂载 Android 文件系统、未向 Android 分区发出写入命令。临时 HTTP 与功能测试监听已停止。
- 原始动态 RAM、对齐/PSCI/UFS 告警、温控/充电/watchdog/挂起/持久化等限制没有因此消失。

---

**下文为 2026-10-26 历史快照。** 其中“当前镜像”、缺 nftables/ZRAM、旧 SSH/归档 hash
均指首轮 Fedora 测试，不是 10 月 27 日新镜像的当前状态；保留原始失败证据。

## 首轮结论（历史）

**在首次救援 RAM boot 后，又成功从 RAM 启动 Fedora Server 44 minimal，systemd 为真正的 PID 1。**
当前镜像 SHA256 为 `ce33154bb4f3ed9662aca740e4b327da603c018a1377fdc12fa721323e13b144`。
USB SSH 公钥登录、sudo、DNF/RPM、8 CPU、约 4.4 GiB 可用内存已验证；根为 tmpfs。
**systemd 为 degraded：内核缺 NF_TABLES，firewalld 失败；不能称为完整健康/生产验收。**
默认 ZRAM 也因内核无驱动超时，后已明确覆盖为不使用 swap。SELinux 为 Permissive，
策略和文件标签已加载，不是 disabled 或 enforcing 验收通过。

Linux 测试没有挂载 Android 文件系统，没有解锁、刷写、擦除、格式化或分区操作。
本轮曾从旧救援正常重启回 Android，再经 ADB 进 fastboot 临时启动新内核，Android 自身
正常启动与 Linux 测试的挂载边界分开记录。当前保留 Fedora SSH，没有自动重启。

实际 boot 的 header/kernel/ramdisk/12-DTB blob 与 ROM 包一致，整个 DTBO 也一致；
但整个 boot 分区 hash 不同，padding/trailer 的差异未定位，不能声称整分区相同。
导出的 live FDT 只是 shim 内嵌的 mainline DTB，不能代替原始 ABL/Android live RAM map。

## 当前 ROM 包与提取

用户先前称系统为魔趣；ADB 报告 `crDroidAndroid-13.0-20231215-picasso-v9.12`。
随后用户提供的同名 ROM ZIP 与 ADB 的设备、增量、SDK、安全补丁和指纹匹配：

- 设备 `picasso`；Android 13 / SDK 33；增量 `1702661267`；补丁 `2023-12-05`。
- 包的 post-build 本身就是 Pixel husky Android 14 指纹。该指纹不能用来判断硬件或
  厂商固件版本，但它与当前 ROM 的报告一致。
- ZIP 大小 1,684,898,436 字节；SHA256：
  `e8f0a1951cd2b04c3f733b1cc5eea5acf171a2094992abeb920661ec76210d3b`。
- 只提取 boot.img、dtbo.img、vbmeta.img、OTA metadata；成员 CRC32 与固定 SHA256 检查通过。
  未执行 update-binary、updater-script、backuptool，也未解包/挂载 Android 用户数据。
- hash 是本地固定的输入身份，不是发布者签名认证。离线 ROM 匹配与后续实测分区比对分开记录。

| ROM 成员 | 字节数 | SHA256 |
| --- | ---: | --- |
| boot.img | 134217728 | `8d29b7ebfdc1c5dd8f58b59f95218e6df43197181259dc7a490e1c32d9650070` |
| dtbo.img | 33554432 | `6e285dbd96d0dd83f1a56179ed9a9c89cd327e68a94cf679254bd1432cc6c112` |
| vbmeta.img | 8192 | `3aecbf9aebeeaed50cc350cbf8c2c84c9314f935872381dc86ead77fe74fca7a` |

原始 boot 为 header v2 / 4096 页，DTB 字段偏移 `0x31cd000`，大小 1,744,734 字节，
包含 **12 个 FDT**；DTBO table v0 有 **21 项**。包中 vbmeta flags=3，不代表已确认 BL 解锁，
它只作为包内容被分析，绝不作为需要刷写的建议。

## 离线设备树核对

运行 `tools/inspect-rom.py`，根据 ADB 的 `dtb_idx=9` / `dtbo_idx=19`：

1. 从完整 12-DTB blob 取 base 9：Lito v2，MSM ID `0x190/0x20000`。
2. 从 DTBO table 取 overlay 19：Picasso，board ID `0x24/0`。
3. 内核自带 libfdt `fdtoverlay` 应用成功，合并结果另存审计，不传给 mainline。
4. 合并后 **21 个固定 reserved-memory 区域全部被 runtime DT 覆盖**；源要求 no-map 的
   区域也有 no-map 覆盖。当前 6.18 Image、DTS 和 modules 不需因此修改或重编。
5. 合并后的 memory/reg 仍是全零 bootloader 占位值，因此实际 RAM banks/动态 carveouts
   **没有**完成验证，不能把离线结果称为 live DT。

报告 `out/rom-audit/compatibility.json` 保存完整归档/成员 hash、索引、合并结果及 runtime DT
hash、区间和限制。`mkboot.sh` 会在改动输出前拒绝旧 MIUI boot、不同 DTBO、错误索引，
以及 runtime DT 改动后过期的报告。修改 DTS 后须重跑审计。

## 构建、打包与测试

- Fedora 44 x86_64；Clang/LLVM/LLD 22.1.8；`ARCH=arm64 LLVM=1`。
- Linux 6.18.58 tarball、AArch64 BusyBox APK 固定 SHA256 检查通过。
- 首次从另一份干净 tarball 验证补丁可应用；26 个补丁涉及文件与构建树逐字节一致。
  驱动补丁仍未改变；离线阶段增加 ROM 工具/基线检查，Fedora 阶段只更新内建 initramfs
  的显式 RAM-root 交接和用户空间工具，没有顺便改硬件驱动或假装补齐 nftables。
- 内核 release **6.18.58-picasso-lts**；Image、707 个 `.ko`、modules_install、DTS/DTB 构建通过。
- **离线/M1 阶段 41/41 测试通过**：v2 header/对齐/legacy ID、真实汇编链接 shim、模拟输入完整打包、
  Range/ETag/CRC/hash、FDT/DTBO 边界、no-map 覆盖、ROM metadata/成员校验。
  回归测试还覆盖：旧基线拒绝、过期 runtime DT 审计拒绝、失败不覆盖旧产物；
  硬件通过状态绑定镜像 hash/大小，新内核字节不能继承旧镜像的真机通过记录。
- `mkboot.sh downloads/crdroid-9.12/boot.img` 成功；shim 的 header、2 MiB 源对齐、
  trampoline 位置、Image/DTB 字节校验均通过。
- 独立复核：**12 个 crDroid 原始 FDT 的完整 blob 未改变**；外部 ramdisk 为零
  （救援 initramfs 内建）；M1 镜像 32,030,720 字节，后续 RAM-hook 镜像 32,096,256 字节，
  均低于 128 MiB 上限。
- ROM dtbo 分区镜像只读取/校验/离线应用，未改动。没有把 merged vendor DT 直接给主线。
- BusyBox 已通过 qemu-aarch64 实际执行及 applet 检查。PARTUUID 使用内核 partition uevent，
  不依赖只支持 filesystem UUID/LABEL 的 BusyBox findfs。
- shell/Python 语法与 patch whitespace 检查通过，`sunstone-linux` 未修改。

## 当前产物

| 文件 | SHA256 |
| --- | --- |
| `out/Image` | `76ed44ba62665b569ab7f51f35aa04424ce1a6f812fbea61de21c147acfd516b` |
| `out/picasso.dtb` | `e41735965e94c10f5edeb2980d5e78e45e91fe2df5fc5f22fbdaad3e6d966b16` |
| `out/kernel.config` | `6963932c5197794c776713180aac39375596fb8b4d23567023bc42838637b1bb` |
| `out/boot-picasso.img` | `ce33154bb4f3ed9662aca740e4b327da603c018a1377fdc12fa721323e13b144` |

后续重建以 `out/SHA256SUMS`、`out/boot-picasso.sha256` 和 `out/boot-manifest.json` 为准。
旧 MIUI Q 候选 hash `87e26fcb...` 及其 manifest/日志已归档到 `out/archive/miui-q-offline/`。
历史 MIUI 成员与归档 pin 仍保留在 `device.json`，但不再被接受为当前打包基线。

## RAM 和历史保守保留

用户确认 6 GB；runtime 的 RAM banks 延续社区 6 GB 布局：

| 起始地址 | 大小 |
| --- | --- |
| `0x80000000` | `0x3cc00000` |
| `0xc0000000` | `0x40000000` |
| `0x100000000` | `0x100000000` |

地址包络 6 GiB，保留原有空洞，不等于已从手机证明这些 banks。
早期 MIUI Q 对照发现的 CVP `0x86f00000 + 0x500000` 仍保守 no-map；当前 ROM 虽未列出它，
也不贸然释放它。DTB 编译仍有继承的警告，未完成 dt-schema 检查，详见 dtc-warnings.log。

## 只读 ADB 结果（并非 Linux 真机测试）

- 主机官方 Platform Tools 37.0.1；仅临时 USB ACL，手机 RSA 授权后连接。
- 设备 picasso，crDroid 9.12 / Android 13，内核 `4.19.157-Driftwood-v2.2.0`。
- MemTotal 5,607,360 kB；非 A/B：boot → sde55，dtbo → sde45，recovery → sda29。
- Android 系统锁定属性为 locked/green；后续 bootloader 查询确认实际已解锁，见下节。
  不以 Android 的这些属性推断 BL 状态，也不执行解锁。
- UID 2000 shell，SELinux Enforcing，PATH 无 su；未调用 adb root、关闭 SELinux或提权。
- `/proc/config.gz` 已导出；`CONFIG_CMDLINE="ramoops_memreserve=4M"` 不能提供安全物理地址。
- live DTB、memory/reg、其他 DT 属性和 `/proc/cmdline` 拒绝访问。目录 pull 退出码虽为 0，
  实际 **0 files pulled**；没有将其误记为成功。该 ADB 阶段未读出 root-only boot/dtbo；
  后续授权救援内核阶段才进行了原始分区只读哈希。
- 原始记录位于被忽略、权限 0700 的 `out/device-audit/`，未读取用户文件/EFS。

## 用户授权的 bootloader 查询（不是候选内核启动）

用户明确允许重启至 fastboot，仅查询产品/解锁状态。确认 ADB 目标仍是同一 Picasso 后，
执行 `adb reboot bootloader`。USB 重新枚举后，只给同一序列号的 fastboot 设备节点
添加当前用户的临时主机 ACL，没有修改永久 udev 规则。

- `fastboot getvar product`：**picasso**。
- `fastboot getvar unlocked`：**yes**。
- `fastboot oem device-info`：Device unlocked=true、Device critical unlocked=true，
  Verity mode=true。这些都是读取，不是解锁命令；与 Android 的 locked/green 报告不同。
- 记录在 `out/device-audit/fastboot-status.txt` 和 `.json`，元数据已同步到 `device.json`。
- 此查询阶段结束时手机留在 fastboot，没有发送 boot；后续用户另行授权 RAM boot，见下节。
  全程没有发送 flash、erase、flashing unlock、oem unlock 或 reboot-to-Android。
- 离线 ROM 审计报告的 `bootloader_lock_state_verified=false` 只表示该离线脚本不验证 BL；
  当前实际查询结果以 device.json 的 bootloader 字段和上述日志为准。

## 用户另行授权的首次 LTS 救援 RAM boot（M1，历史）

此阶段镜像 SHA256 为 `4f408992bd5d647f186b53071c1b376a1499adc9a1a4727a49f67c1c521aa4cc`，
不是后来含 RAM-root hook 的当前镜像；M1 产物另存 `out/archive/rescue-m1-verified/`。
复核同一设备的 product=picasso、unlocked=yes，核对候选与 manifest 全部输入 hash 后，
仅执行一次 `fastboot -s <目标序列号> boot out/boot-picasso.img`，没有失败重试或刷写替代。
发送 31,280 KB 用时约 0.724 秒，Booting 返回 OKAY；主机约 21 秒后观察到
`1d6b:0104 / Picasso LTS rescue / picasso-bringup`，ACM 和 NCM 均出现。
内核日志显示约 2.20 秒执行 `/init`，2.28 秒设置 USB；主机枚举时间不等于内核启动用时。

| 项目 | 实测 |
| --- | --- |
| 内核/架构 | `6.18.58-picasso-lts` / aarch64，串口 UID 0 |
| CPU | `0-7` 在线；日志显示所有 CPU 从 EL1 启动 |
| 内存 | MemTotal 5,523,164 KiB，约 5.27 GiB；不是全内存完整性测试 |
| cpufreq | 3 个 schedutil policy，最高 1,804,800 / 2,208,000 / 2,400,000 kHz |
| 温度 | 8 个 CPU thermal zone 可读，采集时 32.4–35.4°C；未验证节流 |
| USB ACM | 主机 `/dev/ttyACM0`，root shell 可执行命令并完整导出日志/FDT |
| USB NCM | 手机 `${PHONE_USB_IP}/24`，主机临时 `${HOST_USB_IP}/24`；4 发 4 收，0% 丢包 |
| UFS | MICRON MT128GASAO4U21，6 个 LUN，GPT 扫描及原始 boot/dtbo 只读哈希成功 |
| deferred probes | 挂载内存中的 debugfs 后列表为空；不代表无 sync_state 告警 |
| 挂载 | 只有 rootfs/proc/sysfs/devtmpfs/devpts/tmpfs/configfs/debugfs；没有块设备文件系统 |
| 观察窗口 | 最后采集 uptime 761.19 秒；仅轻载诊断，不是压力/长稳测试 |

主机仅为匹配序列号/物理 USB 路径的 ACM 加临时 ACL，为匹配 MAC 的 NCM 加临时地址；
没有改 Wi-Fi/默认路由或永久网络配置。救援环境不含 SSH。
完整记录在权限 0700 的 `out/boot-test/m1-2yx5ysu7/`；`result.json` 固定证据文件 hash。
`device.json` 记录测试结果及精确镜像 hash；打包器只对相同 hash/大小标记已测试，
新字节的构建仍标记未测试，不自动运行任何手机命令。

### 实际 boot/dtbo 的只读比对

先检查 GPT PARTNAME 唯一性及分区大小，才使用 `sha256sum` 和仅带 `if=` 的 `dd`；
没有挂载 Android 文件系统，也没有读取 userdata/EFS。

- `/dev/sde45`：33,554,432 字节，SHA256
  `6e285dbd96d0dd83f1a56179ed9a9c89cd327e68a94cf679254bd1432cc6c112`，与 ROM DTBO 完全一致。
- `/dev/sde55`：134,217,728 字节，SHA256
  `f82a7bf0bb7e9d2776257b56b8ca9dcb7ed3a30c100493254b772d1b7dcf3b54`，**不同于 ROM 整个 boot.img**。
- 进一步核对：4096 字节 header page 相同；kernel、ramdisk、DTB 三个有效组件大小/hash 全同。
  DTB 字段 SHA256 `9b267207f13fd560f0deaea37b232b89dfdf61d327519916bc8e928cb007b4b2`，
  验证了当前打包保留的完整 12-FDT blob 与实际 boot 一致。
- second/recovery_dtbo 大小为零。差异在未覆盖的 padding/trailer 中，尚未定位或判断原因；
  不据此声称手机被 root、改过内核或发生损坏，不把 ROM 文件标为原始完整分区备份。
- 详见 `installed-boot-comparison.json`、`boot-dtbo-readonly-hashes.txt`。

### 当前 mainline live FDT 与剩余告警

`/sys/firmware/fdt` 已通过串口 base64 导出，解析长度/magic 成功；SHA256 与 `out/picasso.dtb`
相同：`e41735965e94c10f5edeb2980d5e78e45e91fe2df5fc5f22fbdaad3e6d966b16`。
**这是 shim 交给 mainline 的静态树，不是被替换前的 ABL vendor DT。** `/proc/iomem` 和
MemTotal 也反映这份输入，不能独立证明原始动态 carveouts 或所有物理 RAM 均正确。

本次末尾 dmesg 未见 panic/Oops/BUG/I/O error，但存在必须保留的限制：

- `Kernel image misaligned at boot`：shim 内部源偏移 2 MiB 对齐不等于最终装载物理地址对齐。
  目前能启动，仍需修正/重新验证 handoff，不能据此声称已符合完整 ARM64 boot 协议。
- PSCI 报 `failed to set PC mode: -3`；CPU 已上线，不表示 idle/suspend 及复位均可靠。
- GCC sync_state 等待 `793000.rng`；crng 约 192 秒才初始化，需要后续排查 RNG 驱动。
- UFS 报 physical-block/optimal-I/O 对齐告警，以及部分供电假定已开启；读取成功不代表
  写入、runtime PM、长稳已经验证，不据此改分区或跑写入测试。
- simpledrm/fb0 注册成功；屏幕实际是否可见尚无用户确认，更不是原生 DSI/GPU 验收。
- APSS watchdog 按 bring-up 配置停止，clk/pd/regulator_ignore_unused 保留；不能无人值守。

## 用户要求的完整 Fedora Server minimal RAM 启动（后续阶段）

用户要求实际运行完整 Fedora Server minimal，并最终要求 Podman、尽量不用 QEMU。
早期 ARM 容器探测已停止，最终从空目录以 `podman unshare` + 主机原生 DNF
`--installroot --forcearch=aarch64` 安装签名 RPM；没有用 QEMU 生成最终 rootfs。
普通 RPM scripts/triggers 跳过，RPM sysusers helper 按文档从 chroot 外使用主机原生工具。

- `@core` + `fedora-release-server`，270 个软件包；RPM 271 条（另 1 条 GPG key）。
- 处理了跨安装 usr-merge/ghost API mountpoints、authselect **local**（本版没有 minimal
  profile）、单独的 crypto-policies-scripts 包。需要执行的 ARM 工具均在手机原生运行。
- rootfs gzip SHA256 `${PRIVATE_ROOTFS_SHA256_2}`，
  通过只绑定 USB IP 的临时 HTTP 传入 `/run`，核对 hash 后解包到 `/newroot` tmpfs。
- 原生完成 ldconfig/sysusers/PAM/crypto/CA/SSH keys 和 SELinux policy/标签；没有
  `/.autorelabel` 自动重启。API bind 清理后才允许 marker，请求后停止全部救援进程再
  PID 1 switch_root；SSH 固定从物理串口取得的 host public key，未关闭主机密钥验证。
- `/proc/1/comm=systemd`、PID 1 executable=`/usr/lib/systemd/systemd`，虚拟化检测 none。
  `multi-user.target`、sshd、dbus、networkd、NetworkManager active；公钥登录及 sudo 成功。
- 根为 tmpfs，3 GiB 上限，无 swap；最后 MemAvailable=4,744,642,560 bytes，8 CPU 在线，
  温度快照 35.1–35.4°C。最终挂载表没有 Android 块设备文件系统。
- 当前 `degraded`，唯一 failed unit 为 firewalld。`CONFIG_NF_TABLES` 未启用，nft
  返回 Protocol not supported。保留失败证据，未用禁用服务/清空失败伪装健康。
- `CONFIG_ZRAM` 未启用，默认生成器曾导致设备超时；RAM 中已增加空配置覆盖（构建脚本
  也已补上），未通过重启验证新配置后的启动时间。systemd-analyze 的“kernel 时间”包含
  人工救援/传输/初始化等待，不等于实际内核启动耗时。
- qcom_rng 模块已加载但报告 TRNG support not detected；本轮 crng 在约 86 秒初始化，
  模块在约 387 秒才加载，不能把 CRNG 完成归功于该模块，更不能宣称硬件熵源通过。
- 本轮最新测试 50 个：49 通过、1 个可选 QEMU applet 测试跳过；BusyBox applets 在手机
  原生检查。新增 tmpfs/Server/native-marker/非 symlink 校验及串口完整边界测试。

证据：`out/fedora-ramtest/result.json` 及其 hash 固定的日志/测试镜像；其中明确记录 service
failures 和 RAM-only 边界，私钥不列入证据清单。镜像 hash/大小不匹配时不会继承通过状态。
原有 M1 结果不覆盖。完整重现/登录/限制见 [RAM-FEDORA.md](RAM-FEDORA.md)。

## 尚未验证与下一步

优先补齐 nftables 内核配置并重新验证 firewalld；若需要 ZRAM 再有计划启用。原始 ABL
live RAM/动态 carveouts、全内存完整性、正确装载对齐、WDT/idle/suspend、当前 Fedora
关机路径、闭环温控、UFS 持久写入、SELinux enforcing、原生显示/GPU/触摸、音频、充电
及其他外设仍未完成验收。没有通过修改 Android SELinux 或安装 Android root 来实现。

当前 Fedora 全在 RAM，重启丢失；临时 HTTP 已停止，USB SSH 仍可用。任何持久安装/
分区修改均需明确方案、备份及新的授权，不覆盖 Android 数据。不自动重启或继续刷写。

## English

Latest [PODMAN-USER-SESSION.md](PODMAN-USER-SESSION.md): separate installation of the signed,
same-version systemd-pam, dependency preflight, and RPM file/database verification passed.
Core systemd versions and PAM/SSH configuration bytes remained unchanged. A genuine new PAM-backed
SSH session had XDG/DBUS; the user manager/bus/linger were ready. UID1000 `podman ps -a` had no
warning, with info=`systemd v2 true`. The first offline-enable rejection due to the missing runtime
directory was retained; an independent continuation succeeded without reinstallation/reset.
**Software installation changes the RPMDB included in the manifest: this round was not a full check
of all static files/protected partitions. Future checks must explicitly handle the database/package-set
transition; the old manifest and requests were not silently updated.** No images were pulled,
containers created/started, boot flashed, or reboot performed; Wi-Fi/screen state was unchanged.

Latest [WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md): 412 offline tests, 411 passed/1 skipped.
The new R2 replaced only the evidence-collection method. A complete raw dump of the same PHY
confirmed 8 actual INDOOR_ONLY bits; verification of 41 inventory entries / 24 CN-enabled 20 MHz
entries passed, with 85 UP samples over 45 seconds. One 2G activation took 0.713 seconds, with
CCMP/DHCP/HT20/DNS/TLS200; 87 associated-UP samples over 90 seconds and subsequent live HTTPS
checks passed. Persistently enabled/active; old failed states/budgets were retained, and active dirty
state was normal. This round did not include forced disconnection, a complete stop, next boot, or
long-term RF/charging acceptance; the historical loss-of-connectivity root cause was not automatically
considered fixed.

Latest [WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md): read-only checks of this
device's iw RPM, the matching signed SourceRPM, and Linux6.18.58 paths confirmed that iw6.17's
information text does not output raw INDOOR_ONLY. The old CN string-based verification therefore
had a definite evidence-collection defect. Offline reproduction passed: a synthetic bit was present but
the old check still rejected it. The GET-only raw collector supports split/complete dumps/raw attr14.
396 offline tests yielded 395 passed/1 skipped, and a native empty-PHY query passed;
**this was not acceptance of actual live bits/RF/connectivity**. Phone service/policy hashes, failed
state, budgets, and offline safe state were unchanged; zero RF/SSID attempts occurred in this round.

Latest [WIFI-CN.md](WIFI-CN.md): SG→CN was requested. Kernel global CN and the reference from
the current signed regdb were verified; independent CN configuration/auditor files were persistently
written. The sole CN radio initialization failed the strict indoor-flag check at 5180MHz;
complete cleanup and independent checkpoint/assets auditing passed. No management-UP step,
SSID activation, or RF retry occurred. Configuring CN cannot be treated as having achieved network
connectivity/RF safety or a confirmed driver root cause. 384 offline tests: 383 passed, 1 optional
skipped. Original syntax-error and first-round Python class-metadata assertion-failure logs were
retained; corrections did not weaken auditing/leases/thermal controls.

The latest explicit ${FALLBACK_SSID} request: NM activation on the existing radio returned 0 in 0.672 seconds,
but the immediate regulatory-domain whitelist check failed. The resident service was enabled/failed
and WLAN/DSP fully exited safely. Independent work checkpoint/assets/CPU/core/dirty auditing passed.
No second RF attempt, fallback, reboot, or regulatory bypass occurred. **This was not sustained
connectivity success**; old 45-second UP samples remained historical. The erroneous original
regulatory domain was not captured; no particular country or hardware root cause was inferred.
Evidence: `out/wifi-connect-2g-20261030T072042Z/`; service details:
[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md).

Latest [WIFI-RADIO-UP.md](WIFI-RADIO-UP.md): the persistent radio service was enabled/active,
with real wlan0 administratively UP but unassociated/no IPv4. 85 native UP samples over 45 seconds
passed; old reconnect budgets/failed states were retained, and default ownership switched.
Offline tests covered logic to keep UP after ordinary link loss; 45°C/lease/DSP/safety faults still
triggered cleanup, without fabricating carrier or Internet access. 372 offline tests: 371 passed/
1 optional skipped. No further SSID activation/reboot/boot flash occurred in this session.
Old offline/cleanup snapshots did not represent the active radio state at that stage.

Latest [WIFI-RECONNECT.md](WIFI-RECONNECT.md): a persistent bounded reconnect supervisor was
enabled. Three actual natural link drops→complete safe cleanup/checkpoint→10/30/60-second
backoff→fresh PID1 worker recovery of DHCP/DNS/HTTPS passed on the phone. This boot's fourth
round dropped again; once the budget was exhausted, the supervisor exited normally under policy
and cleaned up safely, with no fifth round/reset. Peak 43.4°C; thermal limit/lease/four-FD/original-NV
boundaries were unchanged. 359 offline tests: 358 passed/1 optional skipped. The underlying link-loss
problem was not fixed, and no new-boot or artificial-disconnection test was performed.

Latest [LAN-SSH.md](LAN-SSH.md): runtime/permanent LAN${LAN_SUBNET} TCP22 rules and public-key
append/original-key retention passed. SELINUX configuration was disabled but the actual kernel
remained Permissive; no boot change/reboot occurred. With an explicitly authorized baseline exception
for one public-key file, 15,285 files/543,194,605 bytes and boot/seven protected partitions/six GPTs
passed, peak 35.7°C. Wi-Fi suffered fallback link loss and safely exited after earlier online snapshots;
it did not automatically recover. LAN login with the new key and fully Disabled SELinux remained
unaccepted.

For the latest Wi-Fi automatic connection at that recorded stage, see
[WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md): the old watchdog failure was retained.
After the new independent controller's complete 45-second success/safe cleanup, a root0400 native
evidence gate enabled resident operation. At that stage 2.4G was connected; DNS/HTTPS, 90-second
observation, and an approximately 303-second snapshot passed. 342 offline tests: 341 passed/
1 optional skipped. The original beacon root cause, a new boot, and long-term/RF safety remained
unaccepted; the 8-second watchdog/40–45°C/lease/no-loop protection was not relaxed.

For the latest restricted power-key installation at that recorded stage, see
[POWER-PERSISTENT.md](POWER-PERSISTENT.md): after the user accepted automatic-start limitations,
full 128MiB boot readback and 15,285 baseline files/seven protected partitions/six GPTs passed.
The resident service was enabled/inactive; no reboot occurred, so activation at boot and the physical
key remained unaccepted. 334 offline tests: 333 passed/1 optional QEMU skipped. Two pre-write sandbox
denials, old failed units, and markers were retained. Shutdown/manual cold boot still failed;
charging/triggers/reset were unchanged.

## Latest: XFS persistent installation (2026-10-27)

Under user authorization, Fedora 44 Server minimal was installed on XFS in userdata, boot was
written, and super cleared. Exact image `81f28d44…` (33,820,672 B), kernel
`6.18.58-picasso-lts #8`; two normal reboots and fsync-file retention passed, with the second reboot
after Android super was cleared. Readback matched for 15,285 static files' contents/permissions,
the entire boot, 7 retained partitions, and six-LUN GPTs. The new image passed firewalld and ZRAM
functional tests again.

For detailed records, SHA256, SSH, recovery, and safety limitations, see
[INSTALL-XFS.md](INSTALL-XFS.md). Final evidence: `out/install-xfs-20261027/result.json`.
277 packages, 278 RPM records; final snapshot systemd running with no failed unit, but the
Internet/DNS/NTP problems were not resolved and failures were not reset to manufacture health.
SELinux Permissive. Complete memory, closed-loop thermal control/charging/watchdog/suspend/
shutdown, power-loss behavior, and long-term stability remained unaccepted. Full super readback
was followed by a 46.8°C reading, then cooling below 40°C; this was not thermal-protection acceptance.
78 tests: 77 passed, 1 optional QEMU test skipped.

Statements below such as “no flashing/formatting” and “root is tmpfs” are preserved at their own
historical times; they are not the installation state at this later stage.

## RAM confirmation (historical, before installation on 2026-10-27)

**New image `59784cc4…` entered Fedora on the actual phone and passed nftables/firewalld and
ZRAM functional tests.** For full steps, login, and boundaries, see
[CONFIRMATION.md](CONFIRMATION.md). Evidence: `out/confirmation-20261027/result.json`;
hardware results remained bound to the exact image hash/size.

- Real systemd PID 1, working USB SSH/sudo, 274 packages, 275 RPM records.
- firewalld reloaded after repairing Fedora Server ghost configuration links; USB test-port
  block/allow/block-again checks passed.
- 1 GiB zstd ZRAM: 32 MiB of anonymous pages swapped out with matching readback SHA256,
  no disk backing.
- systemd remained degraded; the sole failed unit was dnf-makecache due to no Internet/DNS.
  The failed state was not cleared.
- Clock adjustment resolved “not yet valid” signatures in RPM queries, without disabling signature
  verification. All repairs were in tmpfs. The build script added firewalld ghost links;
  of 59 tests, 58 passed and 1 optional QEMU test was skipped.
- This session reused the already-running new rescue kernel, sending no reboot/boot/flash commands.
  It only extracted into tmpfs and handed over to systemd. No Android filesystem was mounted,
  and no write command issued to Android partitions. Temporary HTTP and functional-test listeners
  were stopped.
- Original dynamic RAM, alignment/PSCI/UFS warnings, thermal control/charging/watchdog/suspend/
  persistence and other limitations did not disappear as a result.

---

**The text below is the historical snapshot from 2026-10-26.** “Current image,” missing
nftables/ZRAM, and old SSH/archive hashes refer to the first Fedora test, not the new image's state
on October 27. Original failure evidence is retained.

## First-round conclusion (historical)

**After the first rescue RAM boot, Fedora Server 44 minimal was also successfully booted from RAM,
with systemd as the real PID 1.** Image SHA256 at that stage:
`ce33154bb4f3ed9662aca740e4b327da603c018a1377fdc12fa721323e13b144`.
USB SSH public-key login, sudo, DNF/RPM, 8 CPUs, and approximately 4.4 GiB of available memory
were verified; root was tmpfs. **systemd was degraded: the kernel lacked NF_TABLES and firewalld
failed; this was not complete health/production acceptance.** Default ZRAM also timed out because
the kernel lacked its driver, then was explicitly overridden to use no swap. SELinux was Permissive,
with policy and file labels loaded; neither disabled nor enforcing passed acceptance.

Linux testing mounted no Android filesystem and performed no unlocking, flashing, erasure,
formatting, or partition operation. In this round, the phone normally rebooted from the old rescue
environment into Android, then entered fastboot through ADB to temporarily boot the new kernel.
Android's own normal startup and the Linux test's mount boundaries were recorded separately.
Fedora SSH was left available at that stage, with no automatic reboot.

The actual boot header/kernel/ramdisk/12-DTB blob matched the ROM package, as did the entire DTBO.
However, the full boot-partition hash differed; padding/trailer differences were not located,
so complete-partition identity could not be claimed. The exported live FDT was only the mainline
DTB embedded in the shim, not a substitute for the original ABL/Android live RAM map.

## ROM package and extraction at that stage

The user had previously described the system as Mokee; ADB reported
`crDroidAndroid-13.0-20231215-picasso-v9.12`.
The same-named ROM ZIP subsequently provided by the user matched ADB's device, incremental
version, SDK, security patch, and fingerprint:

- Device `picasso`; Android 13 / SDK 33; incremental `1702661267`; patch `2023-12-05`.
- The package's own post-build is a Pixel husky Android 14 fingerprint. This fingerprint cannot
  identify hardware or vendor-firmware version, but it matched the installed ROM's report.
- ZIP size 1,684,898,436 bytes; SHA256:
  `e8f0a1951cd2b04c3f733b1cc5eea5acf171a2094992abeb920661ec76210d3b`.
- Only boot.img, dtbo.img, vbmeta.img, and OTA metadata were extracted; member CRC32 and
  pinned SHA256 checks passed. update-binary, updater-script, and backuptool were not executed,
  and Android user data was not unpacked/mounted.
- Hashes are locally pinned input identities, not publisher-signature authentication.
  Offline ROM matching and subsequent actual-partition comparisons were recorded separately.

| ROM member | Bytes | SHA256 |
| --- | ---: | --- |
| boot.img | 134217728 | `8d29b7ebfdc1c5dd8f58b59f95218e6df43197181259dc7a490e1c32d9650070` |
| dtbo.img | 33554432 | `6e285dbd96d0dd83f1a56179ed9a9c89cd327e68a94cf679254bd1432cc6c112` |
| vbmeta.img | 8192 | `3aecbf9aebeeaed50cc350cbf8c2c84c9314f935872381dc86ead77fe74fca7a` |

Original boot used header v2 / 4096-byte pages. The DTB field was at offset `0x31cd000`,
size 1,744,734 bytes, containing **12 FDTs**; DTBO table v0 had **21 entries**.
Package vbmeta flags=3 does not establish that the bootloader was unlocked. It was analyzed solely
as package content, never as a recommendation to flash it.

## Offline device-tree checks

Run `tools/inspect-rom.py` according to ADB's `dtb_idx=9` / `dtbo_idx=19`:

1. Extract base 9 from the complete 12-DTB blob: Lito v2, MSM ID `0x190/0x20000`.
2. Extract overlay 19 from the DTBO table: Picasso, board ID `0x24/0`.
3. The kernel's bundled libfdt `fdtoverlay` applied successfully. The merged result was saved
   separately for auditing, not passed to mainline.
4. **All 21 fixed reserved-memory regions after merging were covered by the runtime DT**;
   regions requiring no-map in the source also had no-map coverage. The 6.18 Image, DTS, and modules
   at that stage needed no modification or rebuilding as a result.
5. Merged memory/reg still contained all-zero bootloader placeholders; actual RAM banks/dynamic
   carveouts were therefore **not** verified. Offline results must not be called a live DT.

Report `out/rom-audit/compatibility.json` saves full archive/member hashes, indexes, merged-result
and runtime-DT hashes, intervals, and limitations. Before changing outputs, `mkboot.sh` rejects
an old MIUI boot, a different DTBO, incorrect indexes, and reports made stale by runtime-DT changes.
After modifying DTS, rerun the audit.

## Build, packaging, and tests

- Fedora 44 x86_64; Clang/LLVM/LLD 22.1.8; `ARCH=arm64 LLVM=1`.
- Pinned SHA256 checks passed for the Linux 6.18.58 tarball and AArch64 BusyBox APK.
- Initial verification used another clean tarball to confirm patch applicability; all 26 files touched
  by the patch matched the build tree byte-for-byte. Driver patches remained unchanged.
  The offline stage added ROM tools/baseline checks; the Fedora stage updated only the built-in
  initramfs's explicit RAM-root handover and userspace tools. It did not incidentally modify hardware
  drivers or pretend to add nftables.
- Kernel release **6.18.58-picasso-lts**; Image, 707 `.ko` files, modules_install, and DTS/DTB
  builds passed.
- **Offline/M1 stage: 41/41 tests passed**: v2 header/alignment/legacy ID, the actually
  assembled/linked shim, complete packaging with simulated inputs, Range/ETag/CRC/hash,
  FDT/DTBO boundaries, no-map coverage, and ROM metadata/member verification.
  Regression tests also covered rejection of the old baseline, rejection of stale runtime-DT audits,
  and leaving old artifacts intact on failure. Hardware pass status is bound to image hash/size;
  new kernel bytes cannot inherit the old image's actual-hardware pass record.
- `mkboot.sh downloads/crdroid-9.12/boot.img` succeeded. Shim header, 2 MiB source alignment,
  trampoline position, and Image/DTB byte checks all passed.
- Independent recheck: **the complete blob of 12 original crDroid FDTs was unchanged**.
  External ramdisk was zero, because rescue initramfs is built in. The M1 image was 32,030,720 bytes;
  the later RAM-hook image was 32,096,256 bytes, both below the 128 MiB limit.
- The ROM dtbo partition image was only read/verified/applied offline, not modified.
  The merged vendor DT was not passed directly to mainline.
- BusyBox passed actual execution and applet checks under qemu-aarch64. PARTUUID uses the
  kernel partition uevent, not BusyBox findfs, which supports only filesystem UUID/LABEL.
- Shell/Python syntax and patch-whitespace checks passed; `sunstone-linux` was not modified.

## Artifacts at that stage

| File | SHA256 |
| --- | --- |
| `out/Image` | `76ed44ba62665b569ab7f51f35aa04424ce1a6f812fbea61de21c147acfd516b` |
| `out/picasso.dtb` | `e41735965e94c10f5edeb2980d5e78e45e91fe2df5fc5f22fbdaad3e6d966b16` |
| `out/kernel.config` | `6963932c5197794c776713180aac39375596fb8b4d23567023bc42838637b1bb` |
| `out/boot-picasso.img` | `ce33154bb4f3ed9662aca740e4b327da603c018a1377fdc12fa721323e13b144` |

For subsequent rebuilds, use `out/SHA256SUMS`, `out/boot-picasso.sha256`, and
`out/boot-manifest.json` as authoritative. The old MIUI Q candidate hash `87e26fcb...` and its
manifest/logs were archived under `out/archive/miui-q-offline/`. Historical MIUI member/archive pins
remain in `device.json`, but are no longer accepted as the packaging baseline at that stage.

## RAM and historical conservative reservations

The user confirmed 6 GB. Runtime RAM banks follow the community's 6 GB layout:

| Start address | Size |
| --- | --- |
| `0x80000000` | `0x3cc00000` |
| `0xc0000000` | `0x40000000` |
| `0x100000000` | `0x100000000` |

The address envelope is 6 GiB, retaining existing holes; this does not mean those banks were proven
from the phone. CVP `0x86f00000 + 0x500000`, found in early MIUI Q comparisons, remains conservatively
no-map. Although the ROM at this stage does not list it, it is not released rashly.
DTB compilation still has inherited warnings and dt-schema checking is incomplete;
see dtc-warnings.log.

## Read-only ADB results (not Linux hardware testing)

- Official host Platform Tools 37.0.1; only temporary USB ACLs, connected after the phone's
  RSA authorization.
- Device picasso, crDroid 9.12 / Android 13, kernel `4.19.157-Driftwood-v2.2.0`.
- MemTotal 5,607,360 kB; non-A/B: boot → sde55, dtbo → sde45, recovery → sda29.
- Android system lock properties were locked/green; a later bootloader query confirmed it was
  actually unlocked, as recorded below. These Android properties were not used to infer BL state,
  and no unlocking was performed.
- UID 2000 shell, SELinux Enforcing, no su in PATH; adb root, disabling SELinux, and privilege
  escalation were not attempted.
- `/proc/config.gz` was exported; `CONFIG_CMDLINE="ramoops_memreserve=4M"` does not provide
  a safe physical address.
- Access to live DTB, memory/reg, other DT properties, and `/proc/cmdline` was denied.
  Although directory pull exited with code 0, it actually reported **0 files pulled**; it was not
  incorrectly recorded as success. This ADB stage did not read root-only boot/dtbo; raw-partition
  read-only hashing occurred only during the later authorized rescue-kernel stage.
- Original records are in ignored `out/device-audit/`, permissions 0700. No user files/EFS were read.

## User-authorized bootloader query (not a candidate-kernel boot)

The user explicitly permitted reboot into fastboot solely to query product/unlock state.
After confirming the ADB target was still the same Picasso, `adb reboot bootloader` was executed.
Following USB re-enumeration, only the fastboot device node with the same serial number received
a temporary host ACL for the current user; permanent udev rules were not modified.

- `fastboot getvar product`: **picasso**.
- `fastboot getvar unlocked`: **yes**.
- `fastboot oem device-info`: Device unlocked=true, Device critical unlocked=true, Verity mode=true.
  These are reads, not unlocking commands, and differ from Android's locked/green report.
- Recorded in `out/device-audit/fastboot-status.txt` and `.json`; metadata was synchronized to
  `device.json`.
- At the end of this query stage, the phone remained in fastboot and no boot command had been
  sent. The user separately authorized RAM boot later, as recorded below. No flash, erase,
  flashing unlock, oem unlock, or reboot-to-Android command was sent throughout this query stage.
- `bootloader_lock_state_verified=false` in the offline ROM audit report means only that the
  offline script does not verify BL state. The actual queried result is represented by the bootloader
  fields in device.json and the logs above.

## First LTS rescue RAM boot, separately authorized by the user (M1, historical)

The image SHA256 in this stage was
`4f408992bd5d647f186b53071c1b376a1499adc9a1a4727a49f67c1c521aa4cc`,
not the later image at this recorded stage containing the RAM-root hook. M1 artifacts are saved
separately under `out/archive/rescue-m1-verified/`. After rechecking product=picasso and unlocked=yes
on the same device and checking every input hash in the candidate and manifest, exactly one
`fastboot -s <目标序列号> boot out/boot-picasso.img` was executed
(`<目标序列号>` means `<target serial number>`). No failed-attempt retry or flashing substitute was used.
Sending 31,280 KB took approximately 0.724 seconds and Booting returned OKAY. Approximately
21 seconds later the host observed `1d6b:0104 / Picasso LTS rescue / picasso-bringup`, with both
ACM and NCM present. Kernel logs showed `/init` executing at approximately 2.20 seconds and USB
setup at 2.28 seconds; host enumeration time is not kernel boot duration.

| Item | Measurement |
| --- | --- |
| Kernel/architecture | `6.18.58-picasso-lts` / aarch64, serial-console UID 0 |
| CPU | `0-7` online; logs showed all CPUs booting from EL1 |
| Memory | MemTotal 5,523,164 KiB, approximately 5.27 GiB; not a full-memory integrity test |
| cpufreq | 3 schedutil policies; maxima 1,804,800 / 2,208,000 / 2,400,000 kHz |
| Temperature | 8 readable CPU thermal zones, 32.4–35.4°C at collection; throttling unverified |
| USB ACM | Host `/dev/ttyACM0`; root shell executed commands and fully exported logs/FDT |
| USB NCM | Phone `${PHONE_USB_IP}/24`, host temporary `${HOST_USB_IP}/24`; 4 sent, 4 received, 0% loss |
| UFS | MICRON MT128GASAO4U21, 6 LUNs; GPT scanning and raw boot/dtbo read-only hashing succeeded |
| deferred probes | Empty list after mounting in-memory debugfs; does not mean no sync_state warnings |
| Mounts | Only rootfs/proc/sysfs/devtmpfs/devpts/tmpfs/configfs/debugfs; no block-device filesystem |
| Observation window | Uptime 761.19 seconds at last collection; only light-load diagnosis, not stress/long-term stability testing |

The host added only a temporary ACL for ACM matching the serial number/physical USB path and a
temporary address for NCM matching the MAC. Wi-Fi/default routes and permanent network settings
were not changed. The rescue environment did not include SSH.
Complete records are in `out/boot-test/m1-2yx5ysu7/`, permissions 0700; `result.json` pins evidence-file
hashes. `device.json` records test results and the exact image hash. The packager marks an image tested
only for the same hash/size; builds with new bytes remain untested and run no phone commands
automatically.

### Read-only comparison of actual boot/dtbo

GPT PARTNAME uniqueness and partition sizes were checked before using `sha256sum` and `dd`
with only `if=`. No Android filesystem was mounted, and userdata/EFS were not read.

- `/dev/sde45`: 33,554,432 bytes, SHA256
  `6e285dbd96d0dd83f1a56179ed9a9c89cd327e68a94cf679254bd1432cc6c112`,
  matching the ROM DTBO completely.
- `/dev/sde55`: 134,217,728 bytes, SHA256
  `f82a7bf0bb7e9d2776257b56b8ca9dcb7ed3a30c100493254b772d1b7dcf3b54`,
  **different from the ROM's entire boot.img**.
- Further comparison: the 4096-byte header page was identical; the kernel, ramdisk, and DTB
  effective components all had identical sizes/hashes. DTB-field SHA256
  `9b267207f13fd560f0deaea37b232b89dfdf61d327519916bc8e928cb007b4b2`
  verified that the complete 12-FDT blob retained in packaging at that stage matched the actual boot.
- second/recovery_dtbo sizes were zero. Differences were in uncovered padding/trailer areas,
  not yet located or explained. This does not establish that the phone was rooted, its kernel modified,
  or data damaged; the ROM file is not labeled an original complete-partition backup.
- See `installed-boot-comparison.json` and `boot-dtbo-readonly-hashes.txt`.

### Mainline live FDT and remaining warnings at that stage

`/sys/firmware/fdt` was exported as base64 through the serial console; length/magic parsing passed.
Its SHA256 matched `out/picasso.dtb`:
`e41735965e94c10f5edeb2980d5e78e45e91fe2df5fc5f22fbdaad3e6d966b16`.
**This is the static tree handed to mainline by the shim, not the ABL vendor DT before replacement.**
`/proc/iomem` and MemTotal also reflect that input and cannot independently establish correct
original dynamic carveouts or all physical RAM.

At the end of this session, dmesg showed no panic/Oops/BUG/I/O error, but limitations that must
be retained included:

- `Kernel image misaligned at boot`: 2 MiB alignment of the internal source offset in the shim
  does not mean the final physical load address is aligned. Boot succeeded, but handoff still needed
  correction/reverification; this does not establish full compliance with the ARM64 boot protocol.
- PSCI reported `failed to set PC mode: -3`; CPUs being online does not establish reliable
  idle/suspend or reset.
- GCC sync_state was waiting for `793000.rng`; crng initialized only at approximately 192 seconds,
  requiring further RNG-driver investigation.
- UFS reported physical-block/optimal-I/O alignment warnings and assumed some supplies already
  enabled. Successful reads do not establish writes, runtime PM, or long-term stability; they do not
  justify changing partitions or running write tests.
- simpledrm/fb0 registered successfully; the user had not confirmed whether anything was actually
  visible on the screen, much less native DSI/GPU acceptance.
- APSS watchdog was stopped under the bring-up configuration; clk/pd/regulator_ignore_unused
  remained. Unattended operation was not appropriate.

## Complete Fedora Server minimal RAM boot requested by the user (later stage)

The user requested actually running complete Fedora Server minimal, ultimately requiring Podman
and avoiding QEMU as much as possible. Early ARM-container probes were stopped. The final system
was installed from signed RPMs into an empty directory with `podman unshare` + host-native DNF
`--installroot --forcearch=aarch64`; QEMU was not used to generate the final rootfs.
Ordinary RPM scripts/triggers were skipped; the RPM sysusers helper used host-native tools outside
the chroot as documented.

- `@core` + `fedora-release-server`, 270 packages; 271 RPM records, including 1 additional GPG key.
- Cross-installation usr-merge/ghost API mountpoints, authselect **local** (this version has no
  minimal profile), and the separate crypto-policies-scripts package were handled.
  All ARM tools requiring execution ran natively on the phone.
- Rootfs gzip SHA256
  `${PRIVATE_ROOTFS_SHA256_2}`
  was transferred into `/run` through temporary HTTP bound only to the USB IP. After hash
  verification it was extracted to `/newroot` tmpfs.
- ldconfig/sysusers/PAM/crypto/CA/SSH keys and SELinux policy/labels were initialized natively;
  no `/.autorelabel` automatic reboot occurred. The marker was permitted only after API binds
  were cleaned up. After the request, all rescue processes stopped before PID 1 switch_root.
  SSH pinned the host public key obtained from the physical serial console; host-key verification
  was not disabled.
- `/proc/1/comm=systemd`, PID 1 executable=`/usr/lib/systemd/systemd`, virtualization detection none.
  `multi-user.target`, sshd, dbus, networkd, and NetworkManager were active;
  public-key login and sudo succeeded.
- Root was tmpfs capped at 3 GiB, with no swap. Final MemAvailable=4,744,642,560 bytes,
  8 CPUs online, temperature snapshot 35.1–35.4°C. The final mount table contained no Android
  block-device filesystem.
- State at that stage was `degraded`, with firewalld the only failed unit. `CONFIG_NF_TABLES`
  was not enabled, and nft returned Protocol not supported. Failure evidence was retained;
  services were not disabled or failure states cleared to fake health.
- `CONFIG_ZRAM` was not enabled, and the default generator had caused a device timeout.
  An empty configuration override was added in RAM and also to the build script, but startup time
  with the new configuration was not verified through reboot. The “kernel time” from
  systemd-analyze includes manual rescue/transfer/initialization waiting and is not actual kernel
  boot duration.
- qcom_rng loaded but reported TRNG support not detected. crng initialized at approximately
  86 seconds in this round, while the module loaded only at approximately 387 seconds.
  CRNG completion cannot be attributed to that module, nor can the hardware entropy source
  be claimed to have passed.
- Latest tests in this round: 50 total, 49 passed, 1 optional QEMU applet test skipped.
  BusyBox applets were checked natively on the phone. Added tests covered
  tmpfs/Server/native-marker/non-symlink verification and complete serial-console boundaries.

Evidence: `out/fedora-ramtest/result.json` and its hash-pinned logs/tested image. These explicitly
record service failures and RAM-only boundaries; private keys are excluded from the evidence
manifest. Pass status is not inherited if image hash/size do not match. Existing M1 results are not
overwritten. For full reproduction/login/limitations, see [RAM-FEDORA.md](RAM-FEDORA.md).

## Unverified items and next steps at that stage

Prioritize adding nftables kernel configuration and reverifying firewalld; if ZRAM is needed, enable
it in a planned manner. Original ABL live RAM/dynamic carveouts, full-memory integrity, correct load
alignment, WDT/idle/suspend, the Fedora shutdown path at that stage, closed-loop thermal control,
UFS persistent writes, SELinux enforcing, native display/GPU/touch, audio, charging, and other
peripherals had not completed acceptance. This was not achieved by modifying Android SELinux
or installing Android root.

Fedora at this stage was entirely in RAM and would be lost on reboot; temporary HTTP had stopped
and USB SSH remained available. Any persistent installation/partition change requires an explicit
plan, backups, and new authorization; do not overwrite Android data. Do not automatically reboot
or continue flashing.
