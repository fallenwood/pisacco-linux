# 项目阶段总记录 / Project Stage Log

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页保存整理前 README 的项目细节与阶段快照，不是实时设备状态或待执行操作授权。
> This page preserves the former README's detailed stage snapshots, not live device status or authorization to repeat operations.
> 文中代码、构建产物及证据路径均相对于仓库根目录；同目录 Markdown 链接相对于 `notes/`。
> Code, build-output and evidence paths are repository-root-relative; sibling Markdown links are relative to `notes/`.

## 中文

### Picasso：Fedora 44 + Linux 6.18 LTS（实验性移植）

目标设备是 **Redmi K30 5G，`picasso`，SM7250 / Snapdragon 765G**。用户已确认 **6 GB 内存**，
设备信息、当前 crDroid ROM 包及历史 MIUI 对照源均固定在 `device.json`。

**已按用户授权将 Fedora Server 44 minimal 持久安装到 userdata 的 XFS，Android 用户数据和
super 系统内容已清除；仍不是稳定成品 ROM。**

**最新：自动熄屏与开机WLAN连接已持久写入并启用。** `picasso-screen.service`仍为原生tty1、
15秒idle关灯/音量上亮屏、不整机休眠；新`picasso-wifi-autoconnect-cn.service`沿用原始CN监管
校验与所有无线保护，开机${PRIMARY_SSID}优先、普通超时后回退${FALLBACK_SSID}。当前两服务enabled/active，
2.4G为${PHONE_LAN_IP}/24，15.09秒熄屏及联网已实测。此次发现新boot旧服务因启动高温保护退出，
新增最多300秒、连续三次<40°C的硬件启动前等待，不放宽原45°C运行中止。
旧R2单元disabled/failed保留，旧重连预算不变；普通掉线仍保留网卡UP，**本阶段不新增自动重连**。
本次未重启/刷boot，所以下次开机尚未实际复核；证据`out/boot-screen-wlan-20261030T152618Z/`。
以下各阶段的“当前”快照均以本段最新状态为准。

**最新用户会话修复**：补齐同版本`systemd-pam-259.10-1.fc44`，未升级systemd核心或改PAM/SSH原配置；picasso linger、真实用户manager/runtime及用户D-Bus已启用，新SSH下`podman ps -a`无警告，info=`systemd v2 true`。旧终端需退出重连；未拉镜像/创建启动容器。安装合法变动RPM数据库，未来完整静态检查必须先处理明确DB转移，不能照旧manifest声称全字节不变。见[PODMAN-USER-SESSION.md](PODMAN-USER-SESSION.md)。Wi-Fi R2仍active/NM100/${PHONE_LAN_IP}、屏幕租约健康。

**此前Wi-Fi修复已在真机通过并持久启用**：新`picasso-wifi-radio-cn-raw.service` enabled/active，直接核验同PHY原始INDOOR_ONLY等属性，41频点/24启用CN20MHz通过，未删保护；一次${FALLBACK_SSID}激活0.713秒，${PHONE_LAN_IP}/24、CCMP/DHCP/DNS/证书HTTPS200，随后90秒87关联UP样本及实时复核通过。活跃dirty属于session${SESSION_3}不可删除，旧失败/预算保留。412离线411通过1跳过；不承诺长期稳定、下次开机或物理室内/RF/充电安全，见[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)。

**此前只读排查：已确认CN审计器的取证逻辑有确定缺陷**。手机匹配的签名iw6.17源码不会在info/list/channels文本打印`INDOOR_ONLY`，所以我用`indoor only`字符串作正向核验会错误拒绝，即使原始bit存在也一样；这不是已证明驱动/硬件缺少室内限制。已准备GET-only原始nl80211采集器并通过396项离线/395通过1跳过及原生空PHY传输测试，未部署替换旧服务、未启动无线，实际运行时bit仍未测，当前仍WLAN absent/DSP offline/CN服务failed。见[WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md)。

**此前明确重试仍失败**：独立新单元`picasso-wifi-cn-attended-20261030T083536.service`/session${SESSION_4}，一次CN初始化仍在5180MHz室内限制标志校验处拒绝，未管理UP/激活SSID；完整安全cleanup及独立checkpoint/assets审计通过，当前WLAN不存在/DSP offline/dirty absent，global仍CN。旧失败/预算保留，无循环/放宽检查/再试，证据`out/wifi-cn-retry-20261030T083536Z/`。

**此前国家码阶段：已按请求将国家码配置切换CN，内核global CN已核实，CN配置/严格审计器已写入手机**。新`picasso-wifi-radio-cn.service`虽然enabled，但一次原生启动因5180MHz缺少可核验的室内限制标志而保护退出；当前failed/MainPID0、WLAN absent/DSP offline/dirty absent，未激活任何SSID，不是已联网或已保持UP。旧SG服务disabled/failed保留，没有删NO-OUTDOOR/DFS保护、改BDF/功率、再试RF或刷boot/重启。见[WIFI-CN.md](WIFI-CN.md)；384项离线383通过/1跳过。

**此前指定${FALLBACK_SSID}一次连接未维持成功**。在既有UP网卡上`nmcli`0.672秒返回0，随后常驻控制器报`ValueError: Neither SG nor verified intersection candidate`并完整安全退出；**当前radio服务enabled/failed、WLAN不存在/DSP offline/dirty absent，没有Wi-Fi IP/互联网验收**。失败/预算保留，未绕过监管、重启无线或再试。错误时实际域原文未捕获，不能猜成CN/US；见`out/wifi-connect-2g-20261030T072042Z/result.json`及[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)。

**此前常驻UP启动验收**，`picasso-wifi-radio.service`已持久enabled/active，普通未关联/掉线不再触发卸载无线；当前未关联SSID、无IPv4/Internet证明，`operstate DOWN/NO-CARRIER`不等于UP flag关闭。新模式暂不自动尝试连接，旧重连默认服务已disabled但failed/预算保留，温控45°C/后端/租约/DSP等安全故障仍必须关闭。45秒85次UP原生样本通过，372项离线371通过/1跳过；见[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md)。

**此前${PRIMARY_SSID}单独试连**：按用户要求只尝试5GHz ${PRIMARY_SSID}，nmcli约20.449秒超时；没有初始/运行期2.4G回退，当前离线且已安全清理。只收窄activate回调，原worker/安全/清理代码未改，363项离线362通过/1可选跳过；未重置自动预算/重启手机。见`out/wifi-${PRIMARY_SSID}-only-20261030T051818Z/result.json`。

**此前同位置Wi-Fi信号采样**：电脑${PRIMARY_SSID}/5GHz信道48实时RSSI中位−75dBm（−76～−74，偏弱）；手机${FALLBACK_SSID}/信道8已验证连接RSSI中位−55dBm（−56～−54，不弱）。频段/BSSID不同，手机5GHz本轮无有效RSSI，不能当作同频接收能力对比，也不能仅凭距离解释2.4G频繁失联。限时手机测量后安全停止，主机网络未改、预算未重置；见`out/wifi-signal-compare-20261030T020112Z/result.json`。

**此前手动试连**：USB地址恢复后确认仍是同一boot；按用户新请求单独运行session `${SESSION_5}`，5GHz超时后2.4G/DHCP/DNS/HTTPS成功，但随后又fallback link loss，当前离线且已安全清理。自动预算摘要未变，无第二次手动尝试。见`out/wifi-attended-20261030T012324Z/result.json`。

**掉线自动重连已持久安装并设为开机启用**，新`picasso-wifi-reconnect.service`监管未改worker，每boot初连＋最多3次，退避10/30/60秒；真机三次自然失联→安全清理→自动恢复联网已验证，无人为断网。
第四轮后来也掉线，本boot4次预算已耗尽，当前enabled/failed并安全清理、无WLAN/dirty，不继续第五轮。底层链路未修复，不刷新预算/failed状态；本次未刷boot/重启。峰值43.4°C，严格<40°C启动/45°C中止不变，359项离线测试。见[WIFI-RECONNECT.md](WIFI-RECONNECT.md)。

**LAN SSH配置**：LAN${LAN_SUBNET}的TCP22已runtime/permanent放行，用户指定ED25519公钥已追加，旧USB密钥/密码禁用/root禁用保留。** 但Wi-Fi后来已掉线并安全退出，当前无WLAN，不能通过历史地址连接；未自动重启失败服务。
SELINUX配置已设disabled，**实际内核仍Permissive/enforce0**；完全禁用需要另行授权boot改动与重启，本次未做。完整检查使用一个明确授权公钥文件例外，15,285文件/543,194,605字节和boot/保护分区/GPT通过。见[LAN-SSH.md](LAN-SSH.md)。

**此前Wi-Fi自动连接启用阶段**：新独立`picasso-wifi-auto.service`按${PRIMARY_SSID}优先→普通超时后${FALLBACK_SSID}回退，当时2.4G/`${PHONE_LAN_IP}`，DHCP/DNS/HTTPS通过；45秒完整验收后转常驻，90秒观察、303秒及最终732秒快照仍连接，之后才出现新的fallback link loss。
旧服务清理watchdog失败保留，新控制器以STOPPING状态通知修正退出流程；看门狗8秒/热限/租约/无重启循环不变。
**beacon失联根因未修复或证实，长期及新boot开机联网未验收**；新配置只准原#10和已审计power DTB。见[WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md)。

**原Wi-Fi版 `6.18.58-picasso-lts-wifi2 #10` 曾写入boot并通过正常重启验证**；本次相同Image/config/模块的电源键DTB版已另获授权写入，见下段。
仍为原生systemd/XFS，USB SSH/sudo可用；原#10与#8回滚镜像完整保留。历史Wi-Fi写入边界见 [WIFI-INSTALL.md](WIFI-INSTALL.md)。
**屏幕阶段记录（历史）**：真实WLED boot-state只读审计、受限背光handoff驱动和原生0/64亮度/内核到期关灯测试已通过，电气配置保留。
用户已确认首段色条/关灯正常，visual1按键后未恢复；真机定位到fbcon在unblank覆盖图案。
visual2改为unblank→重绘→背光64后，用户已确认短按音量上可恢复三色色条；原生日志/清理核对通过，最高采样33.4°C，旧试验不重跑。
**屏幕现已改为Fedora原生tty1文字控制台，不再显示测试色条；15秒idle＋音量上亮屏与内核租约保护保留，服务已写入并启用。**
**用户回复“接受”已知自行启动限制后，测试过的电源键DTB版已写入boot，128MiB完整读回一致；常驻长按服务已enabled，但当前inactive，待下次正常启动。**
本次没有重启/关机；当前仍在原#10/FDT `62ac…`，下次才使用power FDT `ecbf…`。常驻服务的开机激活和实键验收尚未进行。
新服务只接受真实KEY_POWER按住2～3秒后松开，再请求标准PID1正常关机；不启用已消耗的trial脚本。
15,285基线文件、七保护分区/六GPT写后通过；实际写入峰值33.4°C，原#10/#8回滚保留。屏幕PID527/15秒idle/内核租约健康；电源写入阶段Wi-Fi disabled，后续已按用户新请求启用独立自动连接服务。
**保持关机直到手动按键的目标仍未通过，自动启动并未修复。** 此次仅在知情接受限制后固化已验证部分，不改充电、复位计时器或CBL/USB触发，不假冒硬件关机验收。
最新安装、两次写前沙箱拒绝及其保留记录、334项离线测试见 [POWER-PERSISTENT.md](POWER-PERSISTENT.md)。
历史实键：disarmed 1.697253秒忽略、2.221647秒识别；第一次armed 4.559807/1.682461秒均无效、超时无请求；guided2真实2.361172秒松开请求正常关机，用户随后明确“自行启动的”。所有失败与marker保留，不重放。
20秒USB静默、PID1接受和systemd作业完成均不证明PMIC保持断电。失败事实见 [POWER-AUTOSTART.md](POWER-AUTOSTART.md)，旧启动复核见 [POWER-CYCLE-POSTBOOT.md](POWER-CYCLE-POSTBOOT.md)。
此前授权的一次只读PON采样已完成并卸载：**PON=0x40 CBL_POWER、POFF=0x02 PS_HOLD、warm=0**；CBL不等于USB_CHARGER，锁存新鲜度/固件模式和根因未证实。见 [POWER-PON-REASON.md](POWER-PON-REASON.md)；本次未重读。
旧观察/冷却/方案见 [POWER-KEY-OBSERVED.md](POWER-KEY-OBSERVED.md)、[POWER-KEY-COOLDOWN.md](POWER-KEY-COOLDOWN.md)、[POWER-KEY.md](POWER-KEY.md)，原生控制台见 [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md)。
**此前色条后端的持久化曾通过正常重启复核；以下保留这段历史，不表示新控制台/电源方案已目视或冷开关机通过。**
用户恢复主机USB后，已核对变化boot ID、enabled/active服务、健康3秒租约、新boot真实音量上事件→约15秒关灯及全部15,285静态文件/boot/保留分区/GPT未变。
主机sudo受NoNewPrivs的历史阻塞保留；新boot最高采样39.4°C，目视反馈与原生日志分开，不新增电源/音量下、不改#10 boot。
原生DSI仍未实现。当前见 [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md)、[POWER-KEY.md](POWER-KEY.md)；此前持久化见 [DISPLAY-PERSISTENT.md](DISPLAY-PERSISTENT.md)，此前目视验收见 [DISPLAY-VISUAL2.md](DISPLAY-VISUAL2.md)，定位/修补见 [DISPLAY-REDRAW.md](DISPLAY-REDRAW.md)。
此前同一份#10字节镜像已真实通过 **${FALLBACK_SSID} WPA2/CCMP、DHCP、实时DNS及明确经wlan0的HTTPS（HTTP200、证书验证通过）**。
永久MAC、实际20MHz、关联后SG交集24个信道/EIRP/DFS均通过，网络试验最高采样37.1°C；见 [WIFI-NETWORK.md](WIFI-NETWORK.md)。
**用户已明确同意并保存两SSID独立凭据；${PRIMARY_SSID}优先→失败回退${FALLBACK_SSID}已真实执行，回退后DNS/HTTPS通过。**
前序约18秒掉线后，两轮只观测模块已确认：**固件BEACON_MISS先触发失联，-110是随后DISABLE_KEY删钥超时，不是初始装钥失败**。
关联期无扫描，主机可见beacon稀疏；新两轮51.0秒/22.1秒掉线，非固定18秒。空口漏收或固件过滤/监测差异仍待查，见 [WIFI-LINK-LOSS.md](WIFI-LINK-LOSS.md)。
原受保护服务**disabled/failed/watchdog保留**；新独立自动连接服务启用时曾enabled/active，后来fallback link loss后当前enabled/failed且已安全清理、DSP offline/WLAN absent。没有循环重启或宣称beacon修复/重启验收；凭据保留无需再次录入。
回退实测/故障保护阶段记录见 [WIFI-AUTOCONNECT.md](WIFI-AUTOCONNECT.md)。
没有重装/格式化userdata，没有写原NV、GPT、DTBO或vbmeta；新boot全128MiB读回及重启后文件/模块/原NV/GPT检查通过。
固定USB、不提高温度/发射功率；持久联网服务及长期稳定性仍待单独处理，不应重复旧一次性命令。
约 107 GiB XFS 根、277 个软件包（RPM 278 条）、8 CPU 在线。boot 已写入并完整读回，
两次无需 `fastboot boot` 的正常重启和文件持久化验证通过，第二次在清除 super 后进行。
新镜像上重新通过 firewalld 阻断/放行/再阻断与 32 MiB ZRAM 换出/读回测试。
安装阶段历史快照曾为systemd running、无failed unit、无互联网/DNS出口；后续Wi-Fi失败及本轮限时联网成功均另存新结果，不能混为当前全局健康状态。
持续NTP和电池/充电监控仍未验收；本轮HTTPS不表示历史DNF任务已恢复。没有reset-failed或为隐藏失败关闭服务。

安装范围仅 userdata、boot、super；GPT、DTBO、recovery、vbmeta、OEM 启动链及设备固件保留。
**当前#10默认boot及回退见 [WIFI-INSTALL.md](WIFI-INSTALL.md)；原XFS安装、登录及#8历史见 [INSTALL-XFS.md](INSTALL-XFS.md)。**
**Wi-Fi 历史阶段1见 [WIFI-BRINGUP.md](WIFI-BRINGUP.md)：当时独立#9只通过MPSS/QRTR，受RMTFS/NV阻塞并返回#8；不是最新联网结果。**
用户随后已授权三份 NV 只读私有副本；FD-only 代理、原厂固件/BDF 和受限固定 MSA 模式已在
wifi2 真机通过 WLAN 注册与 49 条 AP 广播扫描，见 [WIFI-SCAN.md](WIFI-SCAN.md)。
准备历史见 [WIFI-RMTFS.md](WIFI-RMTFS.md)；这些早期准备/扫描本身不证明关联联网。后续限时网络验收见 [WIFI-NETWORK.md](WIFI-NETWORK.md)，持久启用/长期稳定仍未通过。
早先 RAM 确认与失败证据保留在 [CONFIRMATION.md](CONFIRMATION.md)、[RAM-FEDORA.md](RAM-FEDORA.md)，
其中 tmpfs、未刷写、重启丢失等描述仅是历史阶段，不再是本机当前安装状态。

基线为匹配 ADB 构建信息的 crDroid 9.12 / Android 13 包，12 个 DTB / 21 个 DTBO；
索引 9/19 离线合并及 21 个固定保留区审计通过，不再使用历史 MIUI Q boot。
安装前原 Android boot 的 header/kernel/ramdisk/DTB blob 及整个 DTBO 与该包一致；但整个
原 boot 分区 hash 不同，不能把 ROM boot 当完整备份。真实原 boot 已另存恢复材料；当前
boot 已替换成 Fedora，仍原样保留 12-DTB blob 和 DTBO。
BL 查询确认 picasso/unlocked=yes，与 Android 的 locked/green 报告不同。
导出的当前 live FDT 与内嵌 mainline DTB 相同，**不是原始 ABL/Android live RAM map**。
限定持久写入/重启已验证；完整内存、温控、休眠、长期写入耐久和其他外设仍待验证，
证据及告警见 [VALIDATION.md](VALIDATION.md)。
Fedora 44 没有一个固定的“Fedora 44 LTS kernel”；本项目使用 **Fedora 44 aarch64
用户空间 + kernel.org Linux 6.18.58 LTS + 本地 SM7250 补丁**，不是 Fedora 官方
内核 RPM，也不继承 Fedora 内核补丁集或签名。版本和下载 SHA256 固定于 `sources.json`。

## 已实现的范围

- 从社区 Picasso 7.3-rc 适配回移植 GCC、TLMM、RPMh clocks/domains、NoC、UFS host/PHY。
- 对接 6.18 的 interconnect 指针数组/动态 ID 和 CC const API，重写 UFS 版本相关的
  link-startup 通知；包含 32-bit DMA、QPHY vote、首次 link 前避免 device reset 等修复。
- `dts/` 的 headless DTS：继承 **Picasso 自己的**保留内存和供电，禁用 DSI/GPU、
  触摸、ADSP/音频等未回移植设备；保留 splash simpledrm，补 CPU thermal cooling maps。
- 内建 AArch64 静态 BusyBox initramfs；USB NCM + ACM；默认救援、不挂载磁盘。
  显式请求且验证 tmpfs、Fedora Server 44、原生初始化标记后，停止全部救援 shell，再由
  PID 1 `switch_root` 到 systemd；没有留下跨入 Fedora 的无密码 root 串口 shell。
- 独立的 copydown shim 和 **boot header v2** 打包器：从原厂镜像解析参数，原样保留
  stock DTB blob 供 ABL 应用原厂 DTBO，再交给内嵌主线 DTB。不需要擦除 `dtbo`。
- Fedora 44 rootfs 归档构建脚本，SSH 公钥登录、USB 固定地址、匹配的自定义内核 modules。

以上仅部分功能已完成真机验证，不代表完整硬件支持；测试边界见 [VALIDATION.md](VALIDATION.md)。

## 与 sunstone-linux 的关系

参考相邻 `sunstone-linux` 的“分阶段 bring-up、内建救援 initramfs、USB NCM/ACM、
发行版用户空间独立于内核”的组织方式。**不复制其 SM4375 DTS、驱动补丁、内存地址、
看门狗地址、boot_a 分区假设、v3 打包参数或未明确授权的 shim 源码。**

硬件代码来源及本地差异见 [SOURCES.md](SOURCES.md)。Wi-Fi 已通过临时驱动注册/扫描，关联与持久启用未验收；
蓝牙、原生显示/GPU/触摸、充电、电量计、蜂窝、相机、挂起、开机成功标记仍未移植/验收；
simpledrm的合成色条及短按音量上可见恢复已限时验收，仍非完整显示栈/长期验证。

## 构建内核（无需 root）

Fedora 主机需要 LLVM/Clang、LLD、make、gcc（host tools）、bison、flex、bc、
OpenSSL 开发包、elfutils 开发包、Python 3、git、tar、xz。示例依赖安装命令：

```sh
sudo dnf install clang lld llvm make gcc bison flex bc openssl-devel elfutils-libelf-devel python3 git tar xz
cd "${REPO_ROOT}"
python3 tools/fetch-sources.py
python3 tools/prepare-kernel.py  # 已存在 src/linux-6.18.58 时拒绝覆盖
JOBS=8 tools/build-kernel.sh
```

主要产物：`out/Image`、`out/picasso.dtb`、`out/kernel.config`、`out/modules/`。
配置每次从 arm64 defconfig + `kernel/picasso.config` + `kernel/fedora-server.config` 重建，
检查首启驱动及 nftables/ZRAM 必须为 `=y`，ZRAM writeback 必须关闭。
可在 `src/linux-6.18.58/` 调试源码，但交付前须将修改同步回 `kernel/patches/`。
不要把旧 modules 配给新内核。

## 从当前 crDroid ROM 包核对与打包（无需手机 root）

用户提供的 `${ROM_ARCHIVE}` 与 ADB 的设备、增量
版本 `1702661267`、SDK 33、安全补丁 2023-12-05 及指纹匹配。归档与选定成员的大小、
CRC32、SHA256 已固定在 `device.json`；这不是发布者签名认证，也不是已安装分区的转储。
首次 RAM 测试中采集的实际分区/组件 hash 另记在验证记录，不覆盖 ROM 包的来源信息。

```sh
# 在 picasso/ 下；只提取并检查 boot/dtbo/vbmeta/metadata，不执行安装脚本。
python3 tools/inspect-rom.py
# -> out/rom-audit/compatibility.json，DTB 9 + DTBO 19 离线合并及固定内存审计
tools/mkboot.sh downloads/crdroid-9.12/boot.img
# -> out/boot-picasso.img + out/boot-manifest.json + out/boot-picasso.sha256
```

打包前拒绝不匹配的 boot、DTBO，或因 runtime DT 改动而失效的审计报告。修改 DTS 并
重新构建后，必须重跑 `inspect-rom.py`，不能继续复用旧报告。

当前已安装#10镜像：`out/wifi-install-20261028/boot-installed-wifi2.img`，33,820,672字节，SHA256：
`61022763880509ece9c87f1815b36c841bff4a0f08a4545f6c5f4f639a148304`；正常重启及完整分区读回通过。
`out/boot-picasso.img`仍原样保留为#8回退基线（SHA256 `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c`），
不能再称为当前已安装默认镜像。两者均显式选择原XFS根、核验安装标记并保留救援入口；不代表全外设/稳定性验收。
先前 `59784cc4…` 仅 RAM 确认的救援镜像留在 `out/install-20261027/rescue-before-install/`。
默认不设置 ROOT_PARTUUID 的构建仍是救援；复现持久构建还需 `ROOT_FSTYPE=xfs`，
任何改变字节的新构建均须重新临时启动测试，不能继承现有验收。
首个 M1 救援镜像 `4f408992...` 已单独保存在测试目录及 `out/archive/rescue-m1-verified/`。

真机通过记录只绑定这个 hash/大小；`mkboot.sh` 不会把它继承给不同字节的新构建。

**12 个 ROM 原始 DTB 的完整 blob 全部原样保留给 ABL。** 离线合并后的 vendor DT
只用于审计，不能替代给主线内核使用的 `out/picasso.dtb`。不刷写或擦除 dtbo 分区。
ROM 静态 memory/reg 仍是 bootloader 占位值；**离线合并不能替代 live RAM 验证**。

旧 MIUI Q 候选及 manifest 归档在 `out/archive/miui-q-offline/`，不再作为当前入口。
`tools/fetch-stock-boot.py` 仅用于历史 MIUI 对照；当前基线检查会拒绝拿它直接打包。
来自早期对照的 CVP 额外 5 MiB 保留暂时保守保留，不因 crDroid 未列出它就贸然释放。

打包器读取 v2 的 page size、地址和 DTB blob，不使用网上示例的固定文件偏移。
initramfs 内建，因此最终镜像不带外部 Android ramdisk。检查 shim 的 Image/DTB 字节、
2 MiB 源对齐、copy trampoline 位置、输出大小及 hash。

**仓库没有自动刷机脚本。** 在确认 product、原厂内存布局和恢复路径后，可手工选择
`fastboot boot out/boot-picasso.img` 做 RAM 临时启动；是否支持取决于这台设备的 ABL。
若拒绝启动，先收集错误，不要改成盲刷或擦除 `dtbo` / `vbmeta`。
离线匹配 ROM 包不等于整分区一致；本机实测 DTBO 相同，而 boot 仅 header/组件相同、
整分区不同。不要把组件相同误记成整个 boot 相同。
不要为了此镜像降级固件，或执行 ROM 包中的安装脚本、刷写 bootloader/vbmeta。
即使只临时启动，错误的设备树/MMIO 也可能导致挂死或硬件风险。

## 首启救援与日志

- UART：GENI SE2 `0x888000`，115200。需要相应硬件接口，不是 USB 串口本身。
- USB：救援阶段 `/dev/ttyACM*` 是**本地无密码 root shell**，不要接不可信主机。
  进入 Fedora 后这些 shell 全部终止，串口改为需要认证的 getty；使用 USB SSH 公钥登录。
- USB NCM：手机 `${PHONE_USB_IP}/24`；主机手工配置 `${HOST_USB_IP}/24`。
  **救援环境不含 SSH 服务**；Fedora rootfs 才提供 SSH。
- 没有 UDC 就退回 UART。无自动重启、无 `userdata` 自动发现或写入。
- 内核日志、`/sys/kernel/debug/devices_deferred`（先挂 debugfs）、块设备列表、
  `/proc/iomem`、thermal/cpufreq 状态应先采集，再考虑 Fedora root。

## Fedora Server 44 minimal（RAM 试运行）

```sh
# Fedora 44 x86_64 主机：使用 Podman user namespace 和原生 DNF；不用 Docker/QEMU。
tools/mkrootfs-fedora.sh ${SSH_PUBLIC_KEY}
# -> out/fedora-44-aarch64-rootfs.tar{,.gz}，不是可刷的磁盘镜像
```

最终构建从签名 RPM 交叉安装 `@core` + `fedora-release-server`；`--forcearch=aarch64`，
跳过目标架构的普通脚本/触发器，RPM sysusers 使用主机原生工具的 `--root`。主机不执行
ARM64 ELF，不安装这些包到主机 RPM 数据库。软件源、签名 key hash、包清单及构建方法
记录在 `out/fedora-rootfs-build.json`、`out/fedora-packages.txt`。默认 HTTPS 中科大 Fedora
镜像，`FEDORA_MIRROR` 可改；保持 `gpgcheck=1`，不靠取消签名校验解决网络问题。

归档只解包到手机 `/newroot` 的 tmpfs；`tools/fedora-native-init.sh` 在手机上原生完成
ldconfig、authselect local、加密/CA 配置、SSH keys、SELinux policy/标签。不使用 chroot
作为最终系统：随后 PID 1 显式 `switch_root`，Fedora systemd 才成为真正的 init。

账号 `${DEVICE_USER}`，SSH 公钥登录、sudo；USB 手机 `${PHONE_USB_IP}/24`，主机 `${HOST_USB_IP}/24`。
SELinux 当前 **Permissive**、已加载策略且有文件标签，不是 disabled 或 enforcing 验收通过。
只有 USB 直连网络，没有配置手机互联网网关/NAT。登录方式、重现步骤及故障见
[RAM-FEDORA.md](RAM-FEDORA.md) 及 [CONFIRMATION.md](CONFIRMATION.md)。firewalld 已通过限定
USB 功能测试，但仍只接可信主机；不能据此当作公网生产服务器。

以上归档构建/RAM 试运行步骤本身不格式化 userdata，不可将 tar 归档 `dd` 到块设备。
后来另行授权的 XFS 安装已完成，流程见 [INSTALL-XFS.md](INSTALL-XFS.md) 和
[INSTALL-PLAN.md](INSTALL-PLAN.md)。init 的磁盘入口要求显式 PARTUUID 和 rootfstype，
ext4 先 ro,noload，XFS 先 ro,norecovery，再验证 V2 安装标记/Fedora/systemd；
RAM 专用 `fedora-native-init.sh` 的 tmpfs 保护没有被绕过。enforcing 和长期稳定仍未验收。

## 安全边界 / 下一步

- 目标已确认为 **6 GB RAM**；DTS 的 RAM 地址包络是 6 GiB，保留其原有地址空洞。
  原厂 boot DT 的 RAM `reg` 是 bootloader 占位值，仍需 live DT / `/proc/iomem`
  核对真实 banks 和 secure carveouts，不能仅靠容量确认完整布局。
- bring-up 暂停 APSS watchdog，保留 clk/pd/regulator_ignore_unused；不能作为无人值守服务器。
- CPU 温度读取成功，采集时约 32.4–35.4°C，但**未实测闭环温控**；不长时满载或无人看管充电。
- 当前仍有 kernel image misaligned、PSCI PC mode=-3、RNG 延迟初始化等告警，须后续处理。
- 不继承参考项目 7.3 的验收；本机已验证限定 XFS 安装/重启，不能扩大为 UFS 长期耐久、
  掉电安全、全内存或外围设备验收。
- 用户先前称为魔趣，ADB 实际报告 **crDroid 9.12 / Android 13**，内核为 Driftwood 4.19。
  当前 boot/dtbo 是单分区，不得套用 `boot_a` / `dtbo_a`。Android ADB 无 root，原始 live DT
  仍受权限限制；不修改 Android SELinux、不安装 root 或刷回 MIUI 来绕过它。
  历史 RAM 阶段用户授权 BL 查询、救援及完整 Fedora RAM 试运行，该阶段没有刷机。
  之后用户另行授权删除 Android 并最终改用 XFS，已完成上述三分区操作；没有解锁或刷固件。
  诊断见 `out/device-audit/`、`out/boot-test/m1-2yx5ysu7/`、`out/fedora-ramtest/` 及
  `out/confirmation-20261027/`（权限 0700）。10 月 27 日确认沿用已运行的新救援内核，
  只做 RAM-root 交接和功能测试，本次没有再重启或发送 fastboot boot。
  当前 Linux 可导出自己的 DTB，但 shim 替换了 ABL DTB，不能据此确认原厂动态 RAM carveouts。
  私有固件仅从自己设备提取，不能用 sunstone/OnePlus/Pixel 的签名固件替代。

测试：`python3 -m unittest discover -s tests -v`。

## English

### Picasso: Fedora 44 + Linux 6.18 LTS (experimental port)

The target is **Redmi K30 5G, `picasso`, SM7250 / Snapdragon 765G**. The user confirmed
**6 GB RAM**. Device information, the matching crDroid package and the historical
MIUI comparison input are pinned in `device.json`.

**Fedora Server 44 minimal has been persistently installed on userdata as XFS with
the user's authorization. Android user data and the contents of super were cleared.
This is still not a stable, finished ROM.**

#### Latest recorded update: screen idle and boot WLAN association

Automatic screen-off and boot WLAN association were installed persistently and
enabled. `picasso-screen.service` still displays native tty1, turns the backlight
off after 15 seconds of inactivity and wakes it with volume-up; it does not suspend
the entire phone. The new `picasso-wifi-autoconnect-cn.service` retains raw CN
regulatory validation and all radio protections. At boot it tries ${PRIMARY_SSID} first,
then ${FALLBACK_SSID} after an ordinary timeout. Both services were enabled/active;
2.4 GHz had `${PHONE_LAN_IP}/24`, and connectivity and 15.09-second screen-off were
measured.

Earlier services had exited under startup-temperature protection on a new boot.
A pre-hardware wait now allows at most 300 seconds and requires three consecutive
samples strictly below 40°C, without relaxing the original 45°C running abort.
The old R2 unit remains disabled/failed and its earlier reconnect budget is
unchanged. Ordinary link loss leaves the interface UP; **this stage adds no
automatic reconnection**. No reboot or boot flash occurred, so the next boot has
not been verified. Evidence: `out/boot-screen-wlan-20261030T152618Z/`.
This update takes precedence over the older “current” snapshots below.

#### Earlier recorded stages, newest first

**User-session repair:** the matching `systemd-pam-259.10-1.fc44` package was added
without upgrading systemd core or changing the existing PAM/SSH configuration.
Linger, a real user manager/runtime and user D-Bus were enabled for picasso.
In a fresh SSH login, `podman ps -a` produced no warnings and info reported
`systemd v2 true`. Old terminals need a new login. No images were pulled and no
containers created or started. Installation legitimately changed the RPM database;
future complete static checks must account explicitly for that database transition,
not claim byte-for-byte equality with the old manifest. See
[PODMAN-USER-SESSION.md](PODMAN-USER-SESSION.md). At that stage Wi-Fi R2 remained
active/NM100 at `${PHONE_LAN_IP}`, and the screen lease was healthy.

**Raw CN R2 repair:** `picasso-wifi-radio-cn-raw.service` was enabled/active after
native validation of raw INDOOR_ONLY and other attributes on the same PHY:
41 frequencies inventoried, 24 enabled CN 20 MHz channels accepted, no safeguards
removed. One ${FALLBACK_SSID} activation took 0.713 seconds; WPA2/CCMP, DHCP, DNS and
certificate-verified HTTPS 200 passed at `${PHONE_LAN_IP}/24`. A subsequent 90-second
observation contained 87 associated/UP samples and a live recheck passed.
The active dirty marker belonged to session `${SESSION_3}` and must not be deleted;
old failures and budgets were retained. Of 412 offline tests, 411 passed and one
was skipped. This does not establish long-term stability, next-boot behavior,
physical indoor/RF safety or charging safety. See [WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md).

**Read-only CN diagnosis:** the auditor had a definite evidence-collection defect.
The signed iw 6.17 source matching the phone does not print INDOOR_ONLY in
info/list/channels text. Requiring the string `indoor only` therefore rejects even
when the raw bit exists; it does not prove that the driver/hardware lacks the
restriction. A GET-only raw nl80211 collector was prepared: 396 offline tests,
395 passed and one skipped, plus a native transport test with no PHY. It had not
yet replaced the old service or started the radio, and live bits had not been
measured. At that stage WLAN was absent, DSP offline and the CN service failed.
See [WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md).

**Explicit CN retry:** independent unit
`picasso-wifi-cn-attended-20261030T083536.service`, session `${SESSION_4}`,
again rejected initialization at the 5180 MHz indoor-flag check, before managed
UP or SSID activation. Safe cleanup and independent checkpoint/assets audits
passed; WLAN was absent, DSP offline, dirty absent and global country still CN.
Old failures/budgets remained; there was no loop, relaxed check or further retry.
Evidence: `out/wifi-cn-retry-20261030T083536Z/`.

**Country-code change:** configuration and the kernel global domain were changed
to CN as requested, and CN configuration plus the strict auditor were deployed.
Although enabled, `picasso-wifi-radio-cn.service` exited protectively on its first
native start because 5180 MHz lacked a text-verifiable indoor flag. It was
failed/MainPID0, WLAN absent, DSP offline and dirty absent, with no SSID activated.
This was neither connectivity nor sustained UP. The old SG service remained
disabled/failed. No NO-OUTDOOR/DFS protection was removed, no BDF/power changed,
no further RF retry, boot flash or reboot occurred. See [WIFI-CN.md](WIFI-CN.md);
384 offline tests, 383 passed and one skipped.

**Single requested ${FALLBACK_SSID} connection:** on the existing UP interface, nmcli
returned 0 after 0.672 seconds, but the persistent controller then raised
`ValueError: Neither SG nor verified intersection candidate` and safely exited.
The radio service was enabled/failed, WLAN absent, DSP offline and dirty absent;
there was no Wi-Fi IP/Internet acceptance. Failures and budgets were retained;
no regulatory bypass, radio restart or retry occurred. The actual domain text
was not captured at failure, so it cannot be guessed as CN/US.
See `out/wifi-connect-2g-20261030T072042Z/result.json` and
[WIFI-RADIO-UP.md](WIFI-RADIO-UP.md).

**Persistent interface UP:** `picasso-wifi-radio.service` was installed and
enabled/active. Ordinary unassociated/link-loss states no longer unloaded the
radio. There was no associated SSID or IPv4/Internet evidence;
`operstate DOWN/NO-CARRIER` is not equivalent to clearing the administrative UP flag.
This mode initially made no automatic connection attempt. The old reconnect
default service was disabled, retaining failed state and budget. Temperature
45°C, backend/lease/DSP and other safety faults still required shutdown.
Eighty-five native UP samples over 45 seconds passed; 372 offline tests,
371 passed and one skipped. See [WIFI-RADIO-UP.md](WIFI-RADIO-UP.md).

**${PRIMARY_SSID}-only trial:** only 5 GHz ${PRIMARY_SSID} was attempted at the user's request;
nmcli timed out after about 20.449 seconds. There was no initial or runtime
2.4 GHz fallback. The phone was offline and safely cleaned up. Only the activate
callback was narrowed; the original worker, guards and cleanup were unchanged.
Of 363 offline tests, 362 passed and one optional test was skipped. No automatic
budget reset or phone reboot occurred. See
`out/wifi-${PRIMARY_SSID}-only-20261030T051818Z/result.json`.

**Same-location signal sampling:** the computer on ${PRIMARY_SSID}/5 GHz/channel 48 had
median RSSI −75 dBm (−76 to −74, weak). The phone's verified ${FALLBACK_SSID}/channel 8
connection had median −55 dBm (−56 to −54, not weak). Bands/BSSIDs differed and
there was no valid phone 5 GHz RSSI in that round. This is not a same-band
receiver comparison and distance alone does not explain repeated 2.4 GHz loss.
The bounded phone measurement was safely stopped; host networking and budgets
were unchanged. See `out/wifi-signal-compare-20261030T020112Z/result.json`.

**Attended manual trial:** after restoring USB addressing and verifying the
same boot, the newly requested session `${SESSION_5}` ran once. 5 GHz timed out;
2.4 GHz, DHCP, DNS and HTTPS succeeded, then another fallback link loss occurred.
The phone was offline and safely cleaned up. Automatic-budget summaries were
unchanged; there was no second manual attempt.
See `out/wifi-attended-20261030T012324Z/result.json`.

**Automatic reconnect installation:** `picasso-wifi-reconnect.service` supervised
the unchanged worker, with one initial connection plus at most three retries per
boot and 10/30/60-second backoff. Three natural link losses followed by safe
cleanup and automatic network recovery were verified without artificially
disconnecting the network. Round four subsequently lost the link too; all four
attempts for that boot were spent. The service was enabled/failed and safely
cleaned up, with no WLAN/dirty; no fifth attempt was made. The underlying loss
was not fixed. Budgets/failed state were not reset; no flash or reboot occurred.
Peak temperature was 43.4°C, retaining strict below-40°C startup and 45°C abort;
359 offline tests. See [WIFI-RECONNECT.md](WIFI-RECONNECT.md).

**LAN SSH:** TCP 22 was allowed runtime/permanently for `${LAN_SUBNET}` and the
user-specified ED25519 public key appended. Existing USB keys, password-disabled
and root-disabled policy remained. Wi-Fi later lost the link and safely exited,
so the historical address was not reachable and failed services were not
automatically restarted. SELINUX configuration was set disabled, but the running
kernel remained Permissive/enforce0. Fully disabling it needed separately
authorized boot changes/reboot, not performed. Complete checks used one explicitly
authorized public-key-file exception; 15,285 files/543,194,605 bytes, boot/protected
partitions/GPT passed. See [LAN-SSH.md](LAN-SSH.md).

**Earlier automatic association:** independent `picasso-wifi-auto.service` tried
${PRIMARY_SSID} first, then ${FALLBACK_SSID} after an ordinary timeout. At that stage 2.4 GHz
at `${PHONE_LAN_IP}`, DHCP, DNS and HTTPS passed. It became persistent after complete
45-second acceptance; 90-second observation, 303-second and final 732-second
snapshots remained connected before a later fallback link loss. An older
cleanup-watchdog failure was retained. The new controller corrected stop handling
by notifying STOPPING; the 8-second watchdog, thermal limits, lease and no-restart-loop
policy were unchanged. **Beacon-loss root cause was neither fixed nor proven;
long-term and fresh-boot connectivity were not accepted.** Configuration accepted
only the original #10 and audited power DTB. See
[WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md).

#### Boot, display and power stages

The original Wi-Fi `6.18.58-picasso-lts-wifi2 #10` image had been written to boot
and verified by a normal reboot. A power-key DTB variant using the same
Image/config/modules was later separately authorized and written. Native
systemd/XFS and USB SSH/sudo remained; original #10 and #8 rollback images were
preserved. See [WIFI-INSTALL.md](WIFI-INSTALL.md) for the historical Wi-Fi write boundary.

Read-only WLED boot-state audit, a bounded backlight-handoff driver, native
brightness 0/64 and kernel-expiry shutdown passed while retaining electrical
configuration. The user confirmed initial color bars/screen-off, but visual1
did not restore after the key. Native diagnosis found that fbcon overwrote the
pattern during unblank. Visual2 used unblank → redraw → brightness 64; the user
confirmed short volume-up restored three color bars. Native logs/cleanup passed,
peak sampled temperature 33.4°C, with no repeat of the old experiment.

**The screen was subsequently changed to Fedora native tty1 text console, not
test color bars.** Fifteen-second idle, volume-up wake and kernel-lease protection
were retained; the service was written and enabled.

After the user replied “接受” (“accept”) to the known self-start limitation, the
tested power-key DTB version was written to boot and the complete 128 MiB readback
matched. The persistent hold service was enabled but inactive, awaiting the next
normal boot. No reboot/shutdown occurred; the running system was still original
#10/FDT `62ac…`, with power FDT `ecbf…` due next boot. Boot activation and real-key
acceptance of the persistent service had not happened.

The new service accepts only real KEY_POWER held for 2–3 seconds and released,
then requests normal PID1 shutdown. It does not enable spent trial scripts.
The 15,285-file baseline, seven protected partitions and six GPTs passed after
writing. Flash-stage peak was 33.4°C; original #10/#8 rollback remained.
Screen PID527, 15-second idle and kernel lease were healthy. Wi-Fi was disabled
at the power-write stage, then separately enabled by the user's new automatic
connection request.

**Remaining off until manual power-on was still not accepted; automatic startup
was not fixed.** Only verified parts were persisted after informed acceptance,
without altering charging, reset timers or CBL/USB triggers, or claiming hardware
power-off acceptance. Latest installation, two preserved pre-write sandbox
refusals and 334 offline tests: [POWER-PERSISTENT.md](POWER-PERSISTENT.md).

Historical real-key trials: disarmed 1.697253 seconds was ignored, 2.221647 seconds
recognized; the first armed 4.559807/1.682461-second holds were invalid and timed
out without a request. Guided2's real 2.361172-second release requested normal
shutdown, then the user explicitly reported “自行启动的” (“it started by itself”).
All failures/markers remained and were not replayed. Twenty seconds of USB
silence, PID1 acceptance and completed systemd jobs do not prove retained PMIC
power-off. See [POWER-AUTOSTART.md](POWER-AUTOSTART.md) and the older
[POWER-CYCLE-POSTBOOT.md](POWER-CYCLE-POSTBOOT.md).

One separately authorized read-only PON sample was completed and the module
unloaded: **PON=0x40 CBL_POWER, POFF=0x02 PS_HOLD, warm=0**. CBL is not equivalent
to USB_CHARGER. Latch freshness, firmware mode and root cause were not proven.
See [POWER-PON-REASON.md](POWER-PON-REASON.md); it was not reread here.
Earlier observation/cooldown/plans: [POWER-KEY-OBSERVED.md](POWER-KEY-OBSERVED.md),
[POWER-KEY-COOLDOWN.md](POWER-KEY-COOLDOWN.md), [POWER-KEY.md](POWER-KEY.md).
Native console: [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md).

The older persistent color-bar backend had passed a normal-reboot check; that
history is not visual or cold-power-cycle acceptance of the new console/power
plan. After the user restored host USB, changed boot ID, enabled/active service,
healthy 3-second lease, real volume-up event and roughly 15-second screen-off were
verified in the new boot. All 15,285 static files, boot, retained partitions and
GPT remained unchanged. Historical host sudo blocking under NoNewPrivs was
retained. New-boot peak was 39.4°C; visual feedback was distinguished from native
logs. No new power/volume-down behavior or #10 boot change was introduced.
Native DSI remained unimplemented. See [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md),
[POWER-KEY.md](POWER-KEY.md), [DISPLAY-PERSISTENT.md](DISPLAY-PERSISTENT.md),
[DISPLAY-VISUAL2.md](DISPLAY-VISUAL2.md) and [DISPLAY-REDRAW.md](DISPLAY-REDRAW.md).

#### Network and installation background

The same exact #10 image bytes had passed ${FALLBACK_SSID} WPA2/CCMP, DHCP, live DNS and
HTTPS explicitly routed through wlan0 (HTTP 200, certificate verification).
Permanent MAC, actual 20 MHz width, 24 post-association SG-intersection channels,
EIRP and DFS passed; network-trial peak 37.1°C. See [WIFI-NETWORK.md](WIFI-NETWORK.md).
The user explicitly consented to saving separate credentials for both SSIDs.
${PRIMARY_SSID}-first → ${FALLBACK_SSID} fallback ran, with DNS/HTTPS passing afterward.

After an earlier approximately 18-second loss, two observer-only module rounds
established that **firmware BEACON_MISS triggered loss first; -110 was a later
DISABLE_KEY deletion timeout, not initial key-install failure**. There was no
scan during association; host-visible beacons were sparse. New losses occurred
at 51.0/22.1 seconds, not a fixed 18 seconds. Over-air reception versus firmware
filtering/monitoring differences remained unresolved. See [WIFI-LINK-LOSS.md](WIFI-LINK-LOSS.md).
The original guarded service retained disabled/failed/watchdog state. An independent
automatic service later enabled/active became enabled/failed after fallback link
loss, with DSP offline and WLAN absent after safe cleanup. There was no restart
loop or claimed beacon fix/reboot acceptance. Credentials remained, requiring
no new entry. See [WIFI-AUTOCONNECT.md](WIFI-AUTOCONNECT.md).

No userdata reinstall/formatting, original NV write, GPT/DTBO/vbmeta write occurred
in that Wi-Fi stage. Full 128 MiB boot readback and post-reboot files/modules/
original NV/GPT checks passed. USB stayed fixed and temperature/transmit power
was not increased. Persistent networking/long-term stability needed separate
work; old one-shot commands should not be repeated.

The root was approximately 107 GiB XFS, with 277 packages (278 RPM entries) and
eight CPUs online. Boot was written/read back completely; two normal reboots
without `fastboot boot` verified persistence, the second after super clearing.
On the new image, firewalld block/allow/block and 32 MiB ZRAM swap-out/readback
were reverified. An installation-stage systemd-running/no-failed-unit/no-Internet-DNS
snapshot must not be conflated with subsequent Wi-Fi failures or bounded network
success. Continuous NTP and battery/charging monitoring were unaccepted; HTTPS
does not establish that old DNF tasks recovered. No reset-failed or hiding
failures by disabling services occurred.

Installation scope was only userdata, boot and super. GPT, DTBO, recovery,
vbmeta, OEM boot chain and device firmware were retained.
Historical #10/default/rollback: [WIFI-INSTALL.md](WIFI-INSTALL.md).
Original XFS installation/login/#8: [INSTALL-XFS.md](INSTALL-XFS.md).
Wi-Fi stage 1: [WIFI-BRINGUP.md](WIFI-BRINGUP.md); independent #9 had only passed
MPSS/QRTR, was blocked by RMTFS/NV and returned to #8, not the later network result.
After separate authorization for three read-only private NV copies, an FD-only
proxy, stock firmware/BDF and constrained fixed-MSA mode registered WLAN and
scanned 49 AP advertisements on wifi2. See [WIFI-SCAN.md](WIFI-SCAN.md) and
preparation [WIFI-RMTFS.md](WIFI-RMTFS.md). Preparation/scanning does not prove
association/Internet; bounded network acceptance is in [WIFI-NETWORK.md](WIFI-NETWORK.md).
Earlier RAM confirmations/failures remain in [CONFIRMATION.md](CONFIRMATION.md)
and [RAM-FEDORA.md](RAM-FEDORA.md); their tmpfs/no-flash/reboot-loss statements
describe history, not the persistent installation.

The baseline matched ADB build information for crDroid 9.12/Android 13:
12 DTBs and 21 DTBOs. Offline DTB9/DTBO19 merging and 21 fixed-region audits
passed; historical MIUI Q boot was no longer used. Before installation, Android
boot header/kernel/ramdisk/DTB blob and the entire DTBO matched the package, but
the whole boot-partition hash differed. ROM boot is not a full backup; actual
original boot was saved separately. Fedora boot preserved the entire 12-DTB blob
and DTBO. Bootloader queries confirmed picasso/unlocked=yes, unlike Android's
locked/green report. Exported live FDT matched the embedded mainline DTB, **not
the original ABL/Android live RAM map**. Bounded persistent write/reboot was
verified; full memory, thermal control, suspend, endurance and other peripherals
remained unverified. See [VALIDATION.md](VALIDATION.md).

Fedora 44 does not have a fixed “Fedora 44 LTS kernel.” This project combines
**Fedora 44 aarch64 userspace + kernel.org Linux 6.18.58 LTS + local SM7250 patches**,
not an official Fedora kernel RPM, its patch set or signatures. Version/download
SHA256 pins are in `sources.json`.

#### Implemented scope

- Backport Picasso-community 7.3-rc GCC, TLMM, RPMh clocks/domains, NoC and UFS host/PHY.
- Adapt to 6.18 interconnect pointer arrays/dynamic IDs and CC const APIs; rework
  version-dependent UFS link-startup notifications, including 32-bit DMA, QPHY
  voting and avoiding device reset before the first link.
- Headless DTS in `dts/` inherits **Picasso's own** reserved memory/power topology,
  disabling unported DSI/GPU, touch and ADSP/audio, retaining splash simpledrm
  and adding CPU thermal cooling maps.
- Built-in static AArch64 BusyBox initramfs with USB NCM/ACM, rescue by default
  and no default disk mount. An explicitly requested tmpfs Fedora Server 44
  handoff validates native initialization, stops all rescue shells, then PID1
  switch_root enters systemd; no unauthenticated root serial shell survives.
- Independently written copydown shim and **boot header v2** packer parse stock
  parameters and preserve stock DTB blob for ABL's original DTBO application,
  then hand off to embedded mainline DTB. No DTBO erase is required.
- Fedora 44 rootfs archive builder, public-key SSH, fixed USB addresses and
  matching custom-kernel modules.

Only part of this scope has passed native tests; it is not complete hardware
support. See [VALIDATION.md](VALIDATION.md).

#### Relationship to sunstone-linux

The neighboring `sunstone-linux` inspired phased bring-up, built-in rescue,
USB NCM/ACM and userspace/kernel separation. **Its SM4375 DTS, driver patches,
memory/watchdog addresses, boot_a assumptions, v3 packaging parameters and shim
code without explicit permission were not copied.** Sources/local differences:
[SOURCES.md](SOURCES.md). Temporary Wi-Fi driver registration/scanning had passed
at that historical stage, not association or persistent enablement.
Bluetooth, native display/GPU/touch, charging, gauge, cellular, camera, suspend
and boot-success marking were unported/unaccepted. Bounded simpledrm synthetic
color bars and short-volume-up visible restoration passed, not a complete
display stack or long-term validation.

#### Kernel build (no root required)

A Fedora host needs LLVM/Clang, LLD, make, gcc for host tools, bison, flex, bc,
OpenSSL/elfutils development packages, Python 3, git, tar and xz:

```sh
sudo dnf install clang lld llvm make gcc bison flex bc openssl-devel elfutils-libelf-devel python3 git tar xz
cd "${REPO_ROOT}"
python3 tools/fetch-sources.py
python3 tools/prepare-kernel.py
JOBS=8 tools/build-kernel.sh
```

`prepare-kernel.py` refuses to overwrite an existing `src/linux-6.18.58/`.
Outputs: `out/Image`, `out/picasso.dtb`, `out/kernel.config`, `out/modules/`.
Each build reconstructs config from arm64 defconfig, `kernel/picasso.config` and
`kernel/fedora-server.config`; required early-boot/nftables/ZRAM options must be
`=y` and ZRAM writeback disabled. Debugging in the prepared source is allowed,
but deliverable changes must be synchronized back into `kernel/patches/`.
Never pair old modules with a new kernel.

#### Matching crDroid package and boot packaging (no phone root required)

The user-provided `${ROM_ARCHIVE}` matches ADB
device/build increment `1702661267`, SDK33, 2023-12-05 patch level and fingerprint.
Archive/member sizes, CRC32 and SHA256 are in `device.json`. These pins are
neither publisher-signature authentication nor installed-partition dumps.
Actual partition/component hashes from the first RAM test are separate evidence,
not replacements for package provenance.

```sh
# Run from the repository; extract/check boot/dtbo/vbmeta/metadata only.
python3 tools/inspect-rom.py
# out/rom-audit/compatibility.json: DTB9 + DTBO19 merge/fixed-memory audit
tools/mkboot.sh downloads/crdroid-9.12/boot.img
# out/boot-picasso.img + out/boot-manifest.json + out/boot-picasso.sha256
```

Packaging rejects mismatched boot/DTBO or stale runtime-DT audits. After changing
DTS and rebuilding, rerun `inspect-rom.py`; never reuse a stale report.
Historical installed #10: `out/wifi-install-20261028/boot-installed-wifi2.img`,
33,820,672 bytes, SHA256
`61022763880509ece9c87f1815b36c841bff4a0f08a4545f6c5f4f639a148304`;
normal reboot/full-partition readback passed. `out/boot-picasso.img` remained
the #8 rollback baseline, SHA256
`81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c`,
not the later default installation. Both explicitly select XFS, validate the
installation marker and retain rescue; neither establishes all peripherals or
stability. Earlier RAM-rescue `59784cc4…` is in
`out/install-20261027/rescue-before-install/`.

Without ROOT_PARTUUID, a build remains rescue-default. Reproducing a persistent
build also requires `ROOT_FSTYPE=xfs`. Changed image bytes require fresh temporary
boot acceptance and cannot inherit previous results. Initial M1 rescue
`4f408992...` remains in the test directory and `out/archive/rescue-m1-verified/`.
Native acceptance is tied to exact hash/size; `mkboot.sh` never transfers it to
different bytes.

The entire stock blob of all 12 ROM DTBs is retained for ABL. Offline merged
vendor DT is audit-only, not a substitute for mainline `out/picasso.dtb`.
Do not flash/erase DTBO. Static stock memory/reg are bootloader placeholders;
offline merging cannot substitute for live RAM validation.
Old MIUI Q candidates/manifests are archived in `out/archive/miui-q-offline/`.
`tools/fetch-stock-boot.py` is historical comparison only; current checks reject
its direct packaging use. The earlier extra CVP 5 MiB reservation is conservatively
retained, not released merely because crDroid does not list it.

The packer reads v2 page size, addresses and DTB blob rather than fixed online
example offsets. Built-in initramfs means no external Android ramdisk in the
final image. Checks cover embedded Image/DTB bytes, 2 MiB source alignment,
copy-trampoline position, output size and hash.

**There is no automatic flashing script.** Only after confirming product, stock
memory layout and recovery route may an explicitly chosen
`fastboot boot out/boot-picasso.img` be used for temporary RAM boot, if the device's
ABL supports it. On rejection, collect errors rather than blind-flash or erase
DTBO/vbmeta. Package matching is not whole-partition equality: native DTBO matched,
but boot only matched header/components, not the entire partition. Do not
downgrade firmware, run package installation scripts or flash bootloader/vbmeta.
Even temporary boot with wrong DT/MMIO can hang the phone or create hardware risk.

#### Initial rescue and logs

- UART: GENI SE2 `0x888000`, 115200, requiring hardware access; not USB serial itself.
- Rescue `/dev/ttyACM*` is a **local unauthenticated root shell**: connect only
  trusted hosts. All rescue shells terminate before Fedora; serial becomes
  authenticated getty and USB SSH uses public keys.
- USB NCM: phone `${PHONE_USB_IP}/24`, manually configured host `${HOST_USB_IP}/24`.
  Rescue has no SSH server; Fedora rootfs provides it.
- Without UDC, use UART. No automatic reboot or userdata discovery/write.
- Collect kernel logs, `/sys/kernel/debug/devices_deferred` (mount debugfs first),
  block devices, `/proc/iomem` and thermal/cpufreq state before considering the
  Fedora root handoff.

#### Fedora Server 44 minimal (historical RAM trial)

```sh
# Fedora 44 x86_64 host: rootless Podman namespace and native DNF, no Docker/QEMU.
tools/mkrootfs-fedora.sh ${SSH_PUBLIC_KEY}
# out/fedora-44-aarch64-rootfs.tar{,.gz}, not a flashable disk image
```

The final builder cross-installs signed RPM `@core` plus `fedora-release-server`
with `--forcearch=aarch64`, skipping ordinary target scripts/triggers; RPM sysusers
uses native host tools with `--root`. It neither executes ARM64 ELF on the host
nor installs into the host RPM database. Repository configuration, signing-key
hash, package list and method are recorded in `out/fedora-rootfs-build.json` and
`out/fedora-packages.txt`. Default mirror is HTTPS USTC Fedora, configurable via
`FEDORA_MIRROR`; keep `gpgcheck=1`, never bypass signatures to solve networking.

The archive is unpacked only to phone `/newroot` tmpfs. Native
`tools/fedora-native-init.sh` completes ldconfig, authselect local, crypto/CA,
SSH keys and SELinux policy/labels on the phone. The final system is not a chroot:
PID1 explicitly switch_root makes Fedora systemd the true init.
Account `${DEVICE_USER}` uses public-key SSH and sudo, with the fixed USB addresses above.
At that RAM stage SELinux was **Permissive**, policy loaded and files labeled,
not accepted disabled/enforcing. Only direct USB networking existed, with no
Internet gateway/NAT. Login/reproduction/failures: [RAM-FEDORA.md](RAM-FEDORA.md)
and [CONFIRMATION.md](CONFIRMATION.md). Bounded USB firewalld tests passed, but
trusted-host-only use remained, not public production-server acceptance.

Archive/RAM steps do not format userdata; never dd the tar to a block device.
Later separately authorized XFS installation is in [INSTALL-XFS.md](INSTALL-XFS.md)
and [INSTALL-PLAN.md](INSTALL-PLAN.md). Disk init requires explicit PARTUUID/fstype,
first mounts ext4 ro,noload or XFS ro,norecovery, then validates V2 installation/
Fedora/systemd markers. RAM-only native-init tmpfs protection was not bypassed.
Enforcing and long-term stability remained unaccepted.

#### Safety boundaries and remaining work

- Confirmed RAM is **6 GB**; DTS has a 6 GiB address envelope preserving original
  holes. Stock boot RAM reg values are placeholders. Live DT and `/proc/iomem`
  must verify actual banks/secure carveouts; capacity alone does not prove layout.
- Bring-up stops the APSS watchdog and retains clk/pd/regulator_ignore_unused;
  this is not an unattended server.
- CPU temperature reads worked, about 32.4–35.4°C at sampling, but closed-loop
  thermal control was not tested. Avoid long full load or unattended charging.
- Kernel-image-misaligned, PSCI PC mode=-3 and delayed RNG initialization warnings
  remained for later work.
- Reference-project 7.3 acceptance is not inherited. Bounded XFS/reboot success
  does not establish UFS endurance, power-loss safety, full memory or peripherals.
- The user previously called the ROM MoKee; ADB actually reported crDroid 9.12/
  Android 13 with Driftwood 4.19. Boot/dtbo are single partitions, not boot_a/dtbo_a.
  Android ADB lacked root and original live DT remained permission-restricted;
  Android SELinux was not changed, root not installed and MIUI not reflashed to
  bypass this. Historical BL query/rescue/Fedora RAM trial were authorized and
  did not flash. Later separate authorization deleted Android and installed XFS
  within the three-partition scope, without unlock/firmware flashing.
  Evidence: `out/device-audit/`, `out/boot-test/m1-2yx5ysu7/`,
  `out/fedora-ramtest/`, `out/confirmation-20261027/` (0700).
  On October 27 the already running rescue kernel was reused for RAM-root handoff/
  functional tests, with no new reboot or fastboot boot in that stage. Linux can
  export its own DTB, but the shim replaced ABL's DTB, so this cannot verify original
  dynamic RAM carveouts. Private firmware comes only from this device, not signed
  sunstone/OnePlus/Pixel substitutes.

Offline test command: `python3 -m unittest discover -s tests -v`.
