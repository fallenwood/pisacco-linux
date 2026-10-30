# 验证记录

最新[PODMAN-USER-SESSION.md](PODMAN-USER-SESSION.md)：单独签名同版本systemd-pam安装/依赖预检/RPM文件与DB验证通过，systemd核心版本、PAM/SSH配置字节不变；真实PAM新SSH有XDG/DBUS，用户manager/bus/linger就绪，UID1000 `podman ps -a`无警告，info=`systemd v2 true`。首轮离线enable缺运行目录的拒绝保留，独立续作成功无重装/reset。**软件安装会变动manifest中的RPMDB：本轮不是全部静态/保护分区全检，未来须明确处理DB/包集转移；旧manifest和请求未静默更新。** 未拉镜像/创建启动容器、刷boot或重启，Wi-Fi/屏幕不变。

最新[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)：412离线411通过/1跳过；新R2只替换取证方法，原始同PHY完整dump确认8个真实INDOOR_ONLY位，41库存/24 CN20MHz启用验证通过，45秒85UP样本；一次2G激活0.713秒、CCMP/DHCP/HT20/DNS/TLS200，90秒87关联UP样本及之后实时HTTPS通过。持久enabled/active、旧failed/预算保留，活跃dirty正常。没有本轮强制掉线/完整stop/下次开机/RF或充电长期验收，历史失联根因不因此自动视作修好。

最新[WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md)：只读核对本机iw RPM和匹配签名SourceRPM、Linux6.18.58路径，确认iw6.17信息文本不输出原始INDOOR_ONLY，故旧CN字符串核验存在确定取证缺陷；合成bit存在仍旧拒绝的离线复现通过。GET-only原始采集器支持split/完整dump/原始attr14，396项离线395通过1跳过及native空PHY查询通过，**不是实际live bit/RF/联网验收**。手机服务/政策hash、failed状态、预算和离线安全状态未改，本轮零RF/SSID尝试。

最新[WIFI-CN.md](WIFI-CN.md)：请求SG→CN，内核global CN及当前签名regdb参考核实，独立CN配置/审计器持久写入。唯一CN radio初始化在5180MHz室内标志严格检查处failed、完整cleanup和独立checkpoint/assets审计通过，未管理UP/激活SSID/再试RF。不能把配置CN当作已联网/射频安全/驱动根因已确诊。384项离线383通过、1可选跳过；原语法错误和首轮Python类元数据断言失败日志保留，修正未削弱审计/租约/温控。

最新一次明确Chaldea-2.4G请求：既有radio上NM激活0.672秒返回0，但紧接监管域白名单检查失败，常驻服务enabled/failed且WLAN/DSP完整安全退出；独立工作checkpoint/assets/CPU/core/dirty审计通过，无第二次RF/回退/重启/监管绕过。**不是持续联网成功**，旧45秒UP样本仍是历史。原始错误域未捕获，不推断具体国家或硬件根因。证据`out/wifi-connect-2g-20261030T072042Z/`，服务细节[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)。

最新[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)：持久radio服务enabled/active，真实wlan0管理UP且未关联/无IPv4；45秒85次UP原生样本通过，旧重连预算/failed保留并切换默认所有者。普通失联保持UP逻辑离线覆盖，45°C/租约/DSP/安全故障仍cleanup，不伪造carrier或Internet。372项离线371通过/1可选跳过；本次未再激活SSID/重启/刷boot，旧offline/cleanup快照不代表当前活跃radio状态。

最新[WIFI-RECONNECT.md](WIFI-RECONNECT.md)：持久有界重连监管器已启用，真机3次自然掉线→完整安全清理/检查点→10/30/60秒退避→新PID1 worker恢复DHCP/DNS/HTTPS已通过；本boot第四轮又掉线，预算耗尽后正常策略退出并安全清理，无第五轮/重置。峰值43.4°C，热限/租约/四FD/原NV边界不变；359项离线358通过/1可选跳过。未修复底层失联，未做新boot或人为断网试验。

最新[LAN-SSH.md](LAN-SSH.md)：LAN192.168.1.0/24 TCP22 runtime/permanent规则、公钥追加/旧key保留通过；SELINUX配置disabled但实际内核仍Permissive，未改boot/重启。显式授权一个公钥文件基线例外后15,285文件/543,194,605字节及boot/七保护/六GPT通过，峰值35.7°C。Wi-Fi在此前在线快照之后已fallback link loss并安全退出，未自动恢复；LAN新key登录和完全SELinux Disabled尚未验收。

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
| USB NCM | 手机 `192.168.7.2/24`，主机临时 `192.168.7.1/24`；4 发 4 收，0% 丢包 |
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
- rootfs gzip SHA256 `623ac7dc21225d81ff61148635d098ef65de9917dc6bf01aeb38c167ead4c5c9`，
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
