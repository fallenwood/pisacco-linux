# Linux 7.3.1 默认内核与 6.18 救援 / Linux 7.3.1 Default and 6.18 Rescue

## 中文

### 最新状态：启动修复已验收，7.3.1 为默认

后续明确授权的修复已完成：屏幕在控制器内部等待降温，QRTR 恢复首次对端 HELLO
的单次回复，新的原生 45 秒 CN Wi-Fi 试验及独立清理通过，完整临时重启和默认重启
均实际自动启动屏幕与 Wi-Fi，并通过非 USB 路由的严格主机密钥局域网 SSH。
用户也确认默认启动后音量上键可唤醒终端。

只写入了 `boot`，读回前缀与已验收镜像一致；已验证的 6.18 镜像、源码、模块和
恢复材料仍保留。当前只授权屏幕与持续 Wi-Fi，7.3.1 电源服务禁用；
这不是充电、整机温控或长期稳定性验收。详细过程见本语言部分的“后续阶段”。
下面此前的候选、拒绝授权和恢复记录均保留为历史快照，不代表当前服务状态。
此后一次手动 Wi-Fi 切换停在取密阶段，重启后被未收尾且变化的 NV 工作状态拦住；
经新授权保留副本、恢复普通工作文件后，2.4 GHz 与 LAN SSH 已恢复。见
[后续 Wi-Fi 切换恢复](WIFI-SWITCH-RECOVERY.md)；5 GHz 仍未解决，本轮没有新增重启验收。
再后的同启动 IPv6 部署采用隔离双栈 profile 和新原生证明，公网 IPv6 HTTPS、
IPv4 与 LAN SSH 已通过；入站限制和旧救援配置保持不变。见
[Wi-Fi IPv6](WIFI-IPV6.md)，该变更没有新增重启/自启动验收。
随后按新授权把现有 Wi-Fi、USB 和默认防火墙区域设为 ACCEPT，放行所有端口连接，
保留 firewalld 内建检查与同一 RF 所有者/证明；见
[防火墙开放策略](FIREWALL-OPEN.md)。此前入站限制属于历史阶段，未新增重启验收。
再后的[路由器国家码更新](WIFI-ROUTER-COUNTRY.md)已部署但未验收：
5 GHz 连接超时、2.4 GHz 宣告 CN，与审阅的 US 不一致。
用户选择统一路由器为 US 后暂缓调整；RF 安全关闭，新持续 Wi-Fi 授权未启用，
旧证明未复用。默认内核及救援未变。
2026-11-02 新授权选择[固定 CN](WIFI-FIXED-CN.md)，取代等待统一路由器 US：
两个批准频段都请求 CN，新的原生 45 秒证明及独立清理通过，2.4 GHz 持续运行、
同 SSID 重关联和双栈非 USB LAN SSH 已恢复。5 GHz 仍连接超时；
没有新增重启/冷启动验收，默认内核与救援保持不变。

### 上一恢复阶段：默认仍为 6.18（历史快照）

7.3.1 已完成一次临时原生启动和部分有界实机试验，**没有写入持久 `boot`，
没有完成重复启动或默认切换验收**。用户另行重启后，手机实际返回原有 6.18；
后续报告的黑屏和局域网 SSH 不通分别定位到背光控制冲突和旧启动遗留的
Wi-Fi 生命周期保护，并已在用户明确授权后恢复。未证实 sshd 引发整机关机。

恢复后已实际通过局域网严格主机密钥 SSH 登录，用户确认音量上键可以亮屏显示终端。
所有 7.3.1 服务仍禁用，临时功能授权已关闭。下面的离线段落和最初 USB 阻塞记录
是历史快照；后面的实机、故障与恢复记录才是本次设备阶段结果。

### 初始离线范围与边界（历史快照）

目标是在保留已验证的 `6.18.58-picasso-lts-wifi2` 的前提下，适配官方
Linux **7.3.1**。7.3.1 是 stable 版本，不称为 LTS。用户选择先完成已有功能的
代码、配置、设备树与服务适配，再进行首次启动；只有后续实机验收通过，才考虑切换默认内核。
离线编译或审计通过不能证明新内核上的硬件功能可用。

本阶段只操作主机仓库：没有连接手机、启动射频、安装文件、重启、临时启动或写分区。
没有新增 GRUB、Syslinux、A/B 启动或自动回退。原厂启动链、copydown shim、
内置 initramfs 与 XFS 根文件系统交接方式保持不变。
现有 5 GHz、掉线、关机后自行启动及电源服务失败记录不因本次适配而消失。

### 初始离线结果（历史快照）

| 项目 | 结果 |
| --- | --- |
| 内核及启动镜像 | 已构建 `7.3.1-picasso-wifi2`；`out/linux-7.3.1/boot-picasso.img` 为 35,348,480 字节，尚未启动 |
| 模块 | 875 个普通模块及 6 个独立附加变体；附加模块 ABI 一致，普通 core 恢复路径保持独立 |
| 归档 | `modules-7.3.1.tar`、`runtime-7.3.1.tar` 已生成；只含新版本路径，不带旧目录权限元数据、启用链接或真实授权 |
| 旧资产保留 | 原清单 115,778 项及外部源码/模块清单 61 项均为 0 差异 |
| 主机回归 | 431 项中 430 通过，1 项可选 QEMU 测试跳过；不代表实机测试 |
| 新内核硬件验收 | 未执行；没有切换手机默认内核 |

归档、摘要与构建清单均保存在被忽略的 `out/linux-7.3.1/`。
`offline-candidate.json`、`runtime-offline-verification.json`、
`extra-modules/manifest.json` 和 `preservation-verification.json` 保存对应结果。
初期主机测试曾发现共享只读目录迁移的边界匹配问题，以及合成打包测试缺少新依赖，均已修复。
保留检查首轮的 14 项差异则来自检查器对链接文本的规范化及目录链接的清单范围不一致，
不是旧文件被改写；保留首轮报告后，按原始链接文本与原文件清单范围复核为 0 差异。

### 来源与补丁

`sources-7.3.1.json` 固定官方归档与社区参考版本；原 `sources.json` 仍固定 6.18。
本次除清单 SHA256 外，还使用隔离密钥环验证了 kernel.org 的上游分离签名。
验证结果保存在被忽略的 `out/linux-7.3.1/source-authenticity.json`；
自动下载工具的摘要检查不能代替这一步签名验证。

官方 7.3.1 本身没有 Picasso/SM7250 的完整支持。新系列位于
`kernel/patches/7.3/series`：从固定的
[SM7250 社区仓库](https://github.com/sm7250-mainline/linux_kernel)
提取受限的 headless 支持，保留 7.3 原生 clock/interconnect/UFS 接口，而非直接套用
6.18 的 API 回移补丁。继续保留 UFS 32 位 DMA、首次链路前不重置设备、
QPHY 与看门狗的既有处理；不引入原生 DSI/GPU 驱动。

另外移植 SM7250 PAS/PDM 映射及默认关闭的 `picasso_fixed_msa`。
MPSS 仍为 PAS 4、手动加载/启动，固定 MSA 仍限制板型、地址和大小，
不改变 SCM 所有权。普通 ath10k core 不含 HT20 诊断参数；
带只读 HT20 与管理帧观察参数的 core 单独构建，不能替换普通恢复用 core。

### 隔离与保留

| 项目 | 已有 6.18 | 新 7.3.1 |
| --- | --- | --- |
| 源码 | `src/linux-6.18.58/` | `src/linux-7.3.1/` |
| 构建与产物 | 原有 `out/` 布局 | `out/linux-7.3.1/` |
| 补丁系列 | `kernel/patches/series` | `kernel/patches/7.3/series` |
| 额外配置 | 原有配置片段 | `kernel/picasso-7.3.config` |
| Wi-Fi 内核发布名 | `6.18.58-picasso-lts-wifi2` | `7.3.1-picasso-wifi2` |

未指定 `KERNEL_VERSION` 时，工具仍选择 6.18。未知、空白或路径形式的版本不会回退。
新配置保留原 XFS 根绑定、启动参数及已用显示、按键、容器和签名 regdb 相关能力。
7.3 的配置符号变化另记于被忽略的 `config-comparison.json`，不能把所有旧符号机械复制。

6.18 的源码、构建目录、模块和恢复镜像在改动前已有完整文件清单；
`kernel/display/`、`kernel/power/`、`dts/` 的既有源码与二进制也有独立保留清单。
新外部模块仅在 7.3 输出目录的副本中构建，绝不在这些旧模块目录中执行构建。
权威的旧恢复镜像是 `out/power-install-20261028/boot-installed-power.img`；
不能把根 `out/` 的历史构建输入或任意试验镜像当作已安装版本。
另外在被忽略的 `out/linux-7.3.1/rollback-6.18/` 保存了八个逐字节相同的恢复资产副本，
包括主恢复镜像、较早的已验证镜像、Image、配置、power DTB 和匹配模块归档。
这不是新的手机验证，也不是自动回退机制。

### 离线构建与审计

显式选择 `KERNEL_VERSION=7.3.1`，使用 `DTS_PROFILE=power-trial`，
通过 `tools/build-kernel.sh` 构建；私有根分区绑定从受保护的本地基线读取，不写入笔记。
`tools/build-extra-modules.py` 生成独立 WLED/PON 与保守 ath10k 模块，
并检查 ABI、普通 core 不含 HT20 参数、普通模块字节未被改写。

新 power/Wi-Fi/RMTFS DTB 与保留的已安装 power DTB 比较，节点及属性没有差异。
本次 ROM 离线叠加审计覆盖全部 21 个固定保留区域。
DT 编译仍有社区树继承的警告，不能将其描述为完整 binding/schema 验收。
`tools/audit-wifi.py` 继续检查厂商布线、固件范围、RMTFS guard pages 和 MPSS 手动启动；
打包器要求新输出目录内与 Image、DTB、配置一致的审计，不能使用 6.18 的旧审计充数。
新镜像清单必须标记未实机验证，不继承 `device.json` 中旧镜像的成功状态。

### 版本化运行时与授权

`tools/prepare-kernel-runtime.py` 从本地保留的 Wi-Fi 配置、CN 策略与参考规则生成
私有 `runtime-bundle/`，不部署、不启用服务、不生成已授权的 `activation.json`。
新控制器位于通用目标路径 `/opt/picasso-kernel-7.3.1/`；
服务名、临时运行目录及显示/电源历史目录也与旧版本分离。
拒绝新服务时，其清理过程不能碰到旧服务的运行记录。

原有已固定摘要的只读用户空间 jail、固件、凭据和私有 NV 工作副本不改写。
NV dirty/checkpoint 生命周期仍共享原来的保护状态，避免 7.3 的不干净退出被 6.18 忽略。
依赖摘要在启动前重新检查；本地保留的参考材料不等于手机当前文件已重新核验。
温度门槛、精确 PID 租约、私有文件权限、真实按键、永久 MAC、
CN 原始 nl80211 监管证据与清理边界不放宽。

候选服务另加 root0400 授权，绑定内核发布名、配置、DTB、镜像及运行时清单，
分别控制显示、Wi-Fi 有界试验、持续 Wi-Fi 和电源服务。示例所有开关均为 false。
旧 6.18 的 Wi-Fi probation 证明不能用于新控制器；有界 CN 包装器运行原 worker 的
45 秒 probation 路径，不运行无界 radio loop。持续服务仍要求新证明。
电源服务另外保留独立授权文件；本阶段不会替用户接受或创建新授权。

### 后续设备阶段与救援

首次试验应保留持久 `boot` 分区的 6.18，只临时启动候选镜像。
之前必须确认现场可操作音量/电源键、USB 和原厂 fastboot，且电脑保存了旧镜像。
安装新模块前，还须核对既有 `ath10k_snoc`、`qcom_q6v5_pas`、`rmtfs_mem`
自动加载黑名单仍有效。恢复镜像不等于文件系统/用户数据备份；
回到旧内核也不会撤销新内核期间的数据写入或文件系统格式变更。
首次新内核启动时，旧服务会因内核保护条件拒绝运行，新服务也不会自动获得授权；
不能假设 Wi-Fi 会自动上线。
不能仅依赖远程 SSH：新内核网络失效时，Linux 内的远程恢复本身可能不可达。
USB SSH/串口也需要新内核实际工作，不能当作已经验证的保障。

临时启动、安装匹配模块/版本化服务，以及最后写默认 `boot`，
均属于后续另行确认的设备操作；本页及构建工具不构成授权。
需要逐项验证存储、USB、网络、显示、温控及按键，保留已知失败，
通过后才讨论默认切换。原厂 fastboot 不依赖 Linux 网络，但也不等于自动回退。

### 2026-10-31：设备阶段因 USB 不可见而阻塞

用户已授权在 USB Fastboot 下写入 7.3.1 并验收，但本次尚未执行任何设备操作。
重新连接后，主机的系统 USB 枚举与现有 Fastboot 工具仍未发现手机；
近期 15 分钟内核日志也未见 USB 相关事件。因此无法核对当前设备身份、解锁状态、
boot 分区大小或已安装模块，不能安全开始写入。

六个候选产物均与离线清单一致，主 6.18 回退副本也与保留的原镜像一致；
这些只是主机文件校验，不代表已核验当前手机。结果保存在被忽略的
`out/linux-7.3.1/device-acceptance/blocked-usb-preflight.json`。
没有发送启动、刷写或重启命令，没有安装模块/运行时，也没有开始硬件验收。
需先让本会话所在主机实际识别到目标 USB Fastboot 设备；不能将本次阻塞记为验收通过。
随后按用户要求再次检测，Fastboot 仍为 0 台且 USB 无新增设备，未发送设备命令；
此次结果另存于同目录的 `fastboot-retry-preflight.json`。

### 2026-10-31：隔离安装与临时原生试验

后续重试终于识别到目标原厂 Fastboot。通过现有非交互 sudo 核对设备身份、
解锁状态和分区大小后，只临时启动保留的 6.18 恢复镜像进行安装准备，
再临时启动精确核验的 7.3.1 镜像；**没有执行 `fastboot flash` 或其他分区写入**。
USB 网络仅恢复独立核验的目标链路，SSH 始终使用原有严格主机密钥固定。

现场提取两个镜像的内嵌配置，发现
`out/wifi-rmtfs-20261027/installed-baseline/` 是较早的 headless 基线，
不是当前 Wi-Fi 内核的匹配 Image/config。匹配的旧 Wi-Fi 输入是同目录上级的
`Image`、`kernel.config`，另存于
`out/linux-7.3.1/rollback-6.18/verified-wifi2/`。原有八个回退资产没有覆盖；
不能把其中较早的顶层 Image/config 误当作主恢复镜像的配套输入。

只安装新版本模块、`/opt/picasso-kernel-7.3.1/` 和四个版本化服务文件，
旧 730 个模块文件保持一致，新服务均未启用。起始温度达到 40°C 时先拒绝提取，
没有放宽门槛。GNU tar 的 `--keep-old-files` 与 `--no-overwrite-dir`
不兼容，也在实际提取前拒绝；去掉后者，保留前者和归档路径范围检查后完成安装。

| 临时 7.3.1 项目 | 实际结果与边界 |
| --- | --- |
| 原生启动 | systemd、XFS、八个 CPU、精确配置/DTB 与 USB SSH 已核验；持久 `boot` 仍为 6.18 |
| 存储 | 写入、fsync、读回一个 1 MiB 标记；保留标记供后续复核，不冒充已完成计划中的新内核正常重启 |
| Rootless Podman | 经单独授权，用已有缓存镜像运行并删除一个无网络容器；不拉取镜像，不改已有容器 |
| 显示与按键 | 用户确认原生终端、约 15 秒空闲熄屏和音量上唤醒；读取真实输入事件，并完成一次短电源键观察 |
| Wi-Fi | 经单独授权的 45 秒 CN 试验最终通过，随后完成安全清理；不是持续服务或冷启动自动连接验收 |
| 未执行 | 新内核默认写入、计划中的正常重启、关机/长按、充电与长期稳定性测试 |

Wi-Fi 首轮在 MPSS 启动前因共享 jail 仍执行旧版 supervisor 而拒绝。
只修改新运行时生成器：在新子进程的私有挂载命名空间中，将版本化 supervisor
只读绑定到 jail 内原入口；代码文件使用 0444，外层私有目录及 root0400 策略不放宽。
旧 jail、旧控制器与共享后端保持原字节，四个继承 FD、三秒租约、
温控与 NV 生命周期保护均保留。新增两项回归，七项运行时测试通过；
这不是重新运行全部主机测试。

修复后的下一次尝试已在约半秒内启动 DSP，但未发现唯一 WLFW 端点。
后续关闭等待超时、租约到期与八秒用户空间 watchdog SIGABRT 是清理阶段的后果，
不是最初未发现 WLFW 的原因，也不是内核 panic。独立 ExecStopPost 最终安全清理、
提交 checkpoint、关闭 DSP，并恢复普通模块和 CPU 上限。

随后只在被忽略的独立源码副本中构建 QRTR 日志模块，没有修改正式 Image、
补丁系列或 875 个普通模块。诊断模块试验和恢复普通模块后的另一次
45 秒试验均完成，通过 WPA2/CCMP、DHCP、DNS 与证书校验 HTTPS，
使用 2.4 GHz 回退及实际 20 MHz；普通模块最终恢复，普通模块试验最高记录温度为 36.4°C。
7.3 的 QRTR HELLO 初始化变化是调查线索，不是已证明的根因；
完整模块重载或时序变化可能影响结果，冷启动重复性仍未证明。

`Type=notify` 的 `systemctl start` 在 READY 时返回，不表示 45 秒试验已经结束。
初版诊断帮助程序因此过早检查并正确拒绝在 DSP/WLAN 活跃时恢复模块。
最终证据必须同时有终态 `passed_bounded_probation`、`safe_cleanup_complete`
和真实离线状态；不能使用中途快照或仅凭文件名认定完成。
最终记录是 `731-qrtr-diagnostic-final.json` 与
`731-ordinary-wifi-acceptance.json`，均在被忽略的设备验收目录内。

用户没有同意新内核屏幕/Wi-Fi 自启，也没有确认计划中的正常重启已准备好，
所以没有写默认 `boot`、启用新服务或发送该重启命令。后来的 USB 断开和返回旧内核
不能记成 agent 自动回退；用户随后确认自己另行重启过，且所见“关机”只是黑屏，
并未确认整机断电。

### 2026-10-31：重启回 6.18 后的黑屏与局域网恢复

只读检查确认当前发布名是 6.18，整个 128 MiB `boot` 分区仍与初始已验证基线
逐字节摘要相同；730 个旧模块和 42 条基线共享项也没有变化。
按精确启动记录查询，临时 7.3.1 在 sshd 启动后还有约 52 分钟的 SSH/试验日志。
其旧屏幕/电源服务只是按版本保护拒绝运行；没有找到这次试验的主动关机请求，
也没有 pstore 记录。不能从控制台最后一行或日志缺失推定 sshd、panic、
PMIC 或看门狗是整机关机原因。

返回 6.18 后的两个实际故障分别是：

| 现象 | 证据与处理 |
| --- | --- |
| sshd 后黑屏 | 开机约 13.8 秒，`systemd-backlight` 将自定义背光从 0 提高到 12；屏幕服务发现实际值不符，保护退出并卸载模块。用户授权后，只 mask `systemd-backlight@backlight:picasso-screen.service` 这一实例，不屏蔽模板或其他设备，不改旧屏幕代码、模块或自启设置 |
| 局域网 SSH 不通 | Wi-Fi 在预检报 `Unclean NV lifecycle; operator review required`，没有创建 WLAN。遗留标记属于中间一次被中断的 6.18 启动，不属于临时 7.3.1；当前启动不是整机断电，USB SSH 一直可用 |

NV 恢复不是删除标记后强行重试：先确认所有射频所有者停止、DSP 离线、
无 WLAN、相关模块卸载且没有进程持有工作副本 FD；核验三份普通 8 MiB
工作副本的属主、权限、链接数、大小、不别名，并确认全部摘要与已提交 checkpoint 相同。
在用户明确同意恢复已有持续 Wi-Fi 后，绑定当前启动、旧标记和 checkpoint
生成 root0400 审核记录，将旧标记保留归档到通用系统目录
`/var/lib/picasso-wifi/operator-reviews/`。没有读取原始 NV 分区，
没有手工改写工作副本或 checkpoint，没有放宽后续 dirty 拒绝规则。

随后只重新启动现有受保护的屏幕与 Wi-Fi 服务，均恢复 active/running。
屏幕记录了正常 15 秒空闲熄屏，用户确认音量上键可唤醒并看到终端。
主机通过非 USB 路由实际完成局域网 SSH，仍严格核对原有设备主机密钥，
并核对运行内核与启动身份一致。此时 Wi-Fi 正常持续运行，
新的 dirty 属于当前活跃会话，是正常生命周期标记，**不能删除**；
运行中受控更新普通工作副本不等于本次人工恢复改写了 NV。

原电源键服务另有开机 45°C 热保护退出记录，没有请求 PID1 关机；
未重启该服务或降低门槛。本次恢复没有重启手机、刷写或触碰固件/原始 NV。
下一次启动对本次背光策略的验收尚未执行，重复新内核启动、默认切换和长期稳定性
仍未验收，不能把当前恢复当作 7.3.1 全面验收通过。

收尾从当前 6.18 单独执行，不重跑绑定旧 7.3.1 启动身份的清理程序，
也不停止已恢复的旧内核 Wi-Fi/屏幕。核验候选运行时和依赖后，将四项临时功能授权
全部关闭，四个候选服务保持禁用；只按精确摘要删除四个本次上传/观察/诊断文件，
按原试验启动、PID 和单元身份删除私有 watchdog 内存转储，保留日志和验收元数据。
本次恢复证据位于被忽略的 `out/linux-7.3.1/device-acceptance/`：
`recovered-618-backlight-failure.json`、
`unclean-nv-lifecycle-readonly-review.json`、
`618-display-lan-recovery-result.json`、
`618-display-lan-recovery-verification.json`、
`618-recovered-lan-ssh-verification-stdin.json` 和
`731-trial-closeout-from-618-result.json`。这些记录和本页均不是下一次操作授权。

### 后续阶段：启动修复、重复自启动与默认切换

用户重新明确授权临时启动、屏幕/15 秒熄屏/音量上唤醒、新的 45 秒 CN Wi-Fi
验收及受保护的持续 Wi-Fi/局域网 SSH；仅在验收通过后将 7.3.1 写为默认，并保留
6.18 救援。此前关闭的授权没有被默认为仍有效。未授权新的长按关机、充电或容器试验。

#### 屏幕时序与版本选择

候选服务加入精确 `ConditionKernelVersion`；已有屏幕、Wi-Fi 和电源服务也通过
独立 drop-in 限定为 6.18，不改写其控制器。7.3.1 启动时旧服务在执行前跳过。
候选屏幕另核对只有 `systemd-backlight@backlight:picasso-screen.service`
这个实例被屏蔽，避免通用恢复器再次与 PID 租约背光所有者争用。

首次新的自动启动复现了另一问题：外部冷却步骤接受连续三个低于 40°C 的样本后，
控制器完成导入和校验时温度已经回升，报 `Start below 40C`，安全退出并卸载模块。
这不是之前的通用背光恢复冲突。修复仅作用于生成的 7.3.1 控制器：将有界冷却移动到
控制台/资产校验后、输入与模块启用前，立即保留最终 40°C 检查。
仍要求三个严格低于 40°C 的有效样本，最多等待 300 秒，服务启动上限 330 秒；
运行期 45°C 退出、3 秒 PID 租约、8 秒 watchdog、低亮度限制及 `Restart=no` 均未放宽。
后续实际开机温度超过 40°C 时，控制器正常等待后就绪；目视终端和音量上唤醒均已确认。

#### 变化的 NV 工作副本与单独恢复授权

一次中间返回 6.18、随后进入 Fastboot 后，遗留 dirty 对应旧启动，三个普通工作副本
已经不再匹配检查点。因此不能套用上一阶段“副本未变，只归档 marker”的恢复方式，
也没有把变化的摘要直接采纳为已验证检查点。

在新的明确授权下，先核验原有只读原始备份及其清单，再完整保留三个变化的 8 MiB
普通工作文件、旧检查点和旧 marker。只将 Linux 工作副本从这些已验证的普通备份
恢复，校验完整集合并提交新检查点后，才归档旧 marker。原始备份没有改写；
没有读取或写入原始 NV 分区。后续所有正常射频更新仍由原有租约/清理生命周期管理。

#### QRTR 首次握手恢复

修复屏幕后，这次启动的首次普通模块射频尝试仍因
`No unique local WLFW endpoint` 失败。独立复核确认已安全关闭 DSP/WLAN、
提交一致检查点并恢复 CPU 上限；单元 watchdog 是失败清理阶段的后续问题，
不能称为内核 panic 或 sshd 引发整机关机。早期仅日志模块和重载后成功不足以证明冷启动。

对照 6.18 与 7.3.1 发现了可复现的接收侧握手恢复缺口。上游
[端点注册时主动发送 HELLO 的改动](https://lore.kernel.org/r/20260827-qrtr-hello-on-ep-register-v3-1-ca289ff99abf@oss.qualcomm.com)
保留发送成功状态，却移除了收到远端 HELLO 后的回复。初次发送可以早于自动节点身份
获知或对端接收就绪；传输返回成功不等于远端完成握手。

不启用射频的真实 `qrtr_tun` 虚拟端点测试先确认：原模块先向未分配的目标发送 HELLO，
之后收到对端 HELLO 时没有回复。新补丁
`0004-qrtr-reply-to-first-peer-hello.patch` 保留主动发起，同时在名字服务中对每个
对端的首次 HELLO 回复一次，再公布本地服务；重复 HELLO 不重复回复，BYE 删除该状态，
发送失败保持错误且不消耗回复机会。两轮虚拟端点重建均验证首次回复一次、重复回复零次。
测试模块随后卸载，不留虚拟端点，也不启动 RF。

875 个普通模块中仅 `qrtr.ko` 发生功能变化，其余 874 个及六个附加变体保留。
运行时清单和三个 Wi-Fi 配置新增对普通 QRTR 模块的摘要固定。
QRTR 改动不改变 Image、配置、DTB 或启动镜像字节；旧模块/运行时归档分别保留后重新打包。
真实源码应用、模块编译、补丁格式检查及 39 项聚焦回归均通过。
这些证据不等于完整捕获了失败时固件内部的报文时序或证明长期 RF 稳定性。

主机曾发现一次手工 `git apply` 返回成功但因向上发现外层仓库而实际跳过补丁的情况：
源码及模块字节比较发现没有变化后，该轮结果被标记作废，没有部署。
随后与现有准备工具一样，将 `GIT_CEILING_DIRECTORIES` 限制为临时源码树的父目录，
确认源码实际变化并重编译后才部署；不能仅凭 Git 的退出状态认定补丁已应用。

#### 实机验收与持久默认

| 阶段 | 实际结果 |
| --- | --- |
| 新的临时启动首次 RF | 使用修复后的普通 QRTR；45 秒 CN probation 完成并终止成功，WPA2/CCMP、DHCP、DNS 与证书校验 HTTPS 通过 |
| 试验后独立清理 | dirty 不存在，检查点一致，DSP/WLAN 关闭，临时 CPU 上限恢复 |
| 新版本持续服务证明 | 从真实 native result/单元成功/安全清理生成 root0400 证明，绑定本次控制器及清单；不复用 6.18 证明 |
| 持续 Wi-Fi 与 LAN | 启用受保护的持续服务，实际通过非 USB 路由、原主机密钥 pin 的局域网 SSH，核对同一原生启动 |
| 再次完整临时重启 | 不手动启动屏幕/Wi-Fi，两者自动就绪并持续至少 45 秒，零自动重启，局域网 SSH 和目视唤醒通过 |
| 默认安装 | 清理无线并核验 NV/DSP 后，独立识别原厂 Fastboot，仅写 `boot`，随后普通重启而非 `fastboot boot` |
| 默认启动复验 | 原生 `7.3.1-picasso-wifi2`，屏幕/Wi-Fi 自动就绪至少 45 秒，旧单元按版本跳过，LAN SSH 和用户目视唤醒再次通过 |
| 持久读回 | 128 MiB `boot` 的前 35,348,480 字节与已验收镜像摘要一致；整分区摘要另记，未把未填充镜像摘要当成整分区摘要 |

全过程保留 6.18 的已验证镜像、源码、模块及恢复材料，没有写其他分区或改写固件、
原始 NV，也未执行 RTC 写入命令，没有引入 GRUB、Syslinux、A/B 或自动回退。
现有设备树没有注册 `bootloader` 重启目标；普通重启加按住音量下未可靠进入 Fastboot。
没有臆测软件重启目标或直接写 IMEM，而是每次先独立确认无线安全停止，再由现场用户
手动进入 Fastboot，主机重新核验唯一设备、产品、解锁状态、分区大小与当时电压。

当前屏幕与受保护持续 Wi-Fi 启用，probation 和电源授权关闭，电源服务禁用。
活跃 Wi-Fi 的 dirty 属于当前启动和当前所有者，是正常状态，**不得清除**。
仍无掉线自动重连，5 GHz、完整关机、充电及长期稳定性没有因此变为已实现。
本阶段没有重跑容器试验。后续救援仍需要现场 USB/原厂 Fastboot 和保留的 6.18 镜像，
不能把单 `boot` 分区当作有自动回退的双槽系统。
主机构建工具未指定版本时仍选择 6.18；构建新版本继续显式设置
`KERNEL_VERSION=7.3.1`。手机默认版本的切换没有覆盖旧构建流程。

收尾仅删除已卸载且摘要核对一致的虚拟测试模块，以及按本阶段已保存的启动、单元、
PID 和文件扩展属性精确核对的私有 watchdog 内存转储。首次历史 journal 查询因启动标识
格式被拒绝，错误保留，没有据此模糊匹配或批量删除。原始失败日志及受保护元数据仍保留，
没有清除当前活跃 dirty 或触碰 NV 工作文件；最后又实际通过局域网确认默认服务正常。

对应私有证据位于被忽略的 `out/linux-7.3.1/device-acceptance/`：
`qrtr-hello-unpatched-virtual-reproduction.json`、
`qrtr-hello-fixed-virtual-regression.json`、
`731-fixed-qrtr-cold-bounded-probation.json`、
`731-temporary-autostart-acceptance.json`、
`731-default-boot-install.json`、
`731-default-autostart-acceptance.json` 和
`731-default-screen-operator-confirmation.json`。更早失败、变化副本恢复及每次清理记录也保留；
文档不包含实际地址、网络名、私有标识、摘要或外部本地路径，也不构成下一次设备操作授权。

## English

### Latest state: startup repair accepted; 7.3.1 is the default

The subsequently authorized repair is complete: the screen owner waits for cooling
internally, QRTR replies once to the first peer HELLO, and a new native 45-second
CN Wi-Fi probation and independent cleanup passed. Both a complete temporary
reboot and the default reboot automatically started screen/Wi-Fi and passed
strict-pinned LAN SSH over a non-USB route. The operator also confirmed visible
volume-up terminal wake after the default boot.

Only `boot` was written, and its readback prefix matches the accepted image.
Verified 6.18 images, sources, modules and recovery assets remain preserved.
Only screen and continuous Wi-Fi are authorized; the 7.3.1 power service is
disabled. This is not charging, whole-device thermal or endurance qualification.
See the subsequent-phase section below. Earlier candidate, declined-consent and
recovery records remain historical snapshots, not current service state.
A later manual Wi-Fi switch stalled during secret acquisition; after reboot,
unclean, changed ordinary NV work state blocked startup. Newly authorized
preservation/restoration recovered 2.4 GHz and LAN SSH; see
[subsequent Wi-Fi switch recovery](WIFI-SWITCH-RECOVERY.md). 5 GHz remains
unresolved, and this round did not add reboot acceptance.
A subsequent same-boot IPv6 deployment uses isolated dual-stack profiles and a
fresh native proof; public IPv6 HTTPS, IPv4 and LAN SSH passed while inbound
restrictions and legacy rescue configuration were retained. See
[Wi-Fi IPv6](WIFI-IPV6.md); this change has no new reboot/autostart acceptance.
A later grant set the existing Wi-Fi, USB and default firewall zones to ACCEPT,
allowing all port connections while retaining built-in checks and the same RF
owner/proof; see [the open firewall policy](FIREWALL-OPEN.md). Earlier inbound
restrictions are historical; no new reboot acceptance was performed.
The later [router country update](WIFI-ROUTER-COUNTRY.md) is deployed but
unaccepted: 5 GHz connection timed out and 2.4 GHz advertised CN, conflicting
with reviewed US. The user chose consistent router US configuration, then
deferred it. RF is safely off, new continuous-Wi-Fi consent is not enabled and
old proof was not reused. Default and rescue kernels are unchanged.
A fresh 2026-11-02 grant selected [fixed CN](WIFI-FIXED-CN.md), superseding the
wait for consistent router US. Both authorized bands request CN. New native
45-second proof and independent cleanup passed; continuous 2.4 GHz, same-SSID
reassociation and dual-stack non-USB LAN SSH were restored. 5 GHz still times
out. No new reboot/cold-start acceptance occurred; default and rescue are unchanged.

### Previous recovery phase: 6.18 default (historical snapshot)

7.3.1 completed one temporary native boot and several bounded device trials.
**Persistent `boot` was not written; repeatable boot and default-switch acceptance
are incomplete.** After a separate operator reboot, the phone actually returned
to existing 6.18. The reported black screen and unavailable LAN SSH were traced
to competing backlight control and a Wi-Fi lifecycle guard from an interrupted
older boot, and were recovered with explicit consent. An sshd-triggered device
poweroff was not established.

Actual LAN SSH with strict host-key verification now works, and the operator
confirmed that volume-up wakes a visible terminal. All 7.3.1 units remain disabled
and temporary feature grants are closed. The offline sections and initial USB
block below are historical snapshots; the later device/recovery sections record
the subsequent device phase.

### Initial offline scope and boundaries (historical snapshot)

The goal is to adapt official Linux **7.3.1** while preserving the verified
`6.18.58-picasso-lts-wifi2`. Version 7.3.1 is stable, not LTS. The user chose
existing-feature code, configuration, DT and service adaptation before the first
boot; changing the default is conditional on later device acceptance.
Offline compilation/audits do not establish hardware functionality on the new kernel.

This phase operates only on the host repository: no phone connection, RF startup,
installation, reboot, temporary boot or partition write. No GRUB, Syslinux, A/B
boot or automatic rollback is added. The stock boot chain, copydown shim,
built-in initramfs and XFS handoff remain unchanged.
Existing 5 GHz, link-loss, self-start-after-shutdown and power-service failures
are not resolved or erased by this adaptation.

### Initial offline results (historical snapshot)

| Item | Result |
| --- | --- |
| Kernel and boot image | Built `7.3.1-picasso-wifi2`; `out/linux-7.3.1/boot-picasso.img` is 35,348,480 bytes and has not been booted |
| Modules | 875 ordinary modules and 6 separate extra variants; matching extra-module ABI and an isolated ordinary-core restoration path |
| Archives | `modules-7.3.1.tar` and `runtime-7.3.1.tar` generated; new-version paths only, with no old parent-directory permissions, enablement links or real consent |
| Old assets | Zero differences across the original 115,778 records and 61 external-source/module records |
| Host regressions | 430 passed and one optional QEMU test skipped out of 431; not device testing |
| New-kernel hardware acceptance | Not performed; the phone's default kernel was not changed |

Archives, checksums and receipts remain under ignored `out/linux-7.3.1/`.
Corresponding results are in `offline-candidate.json`,
`runtime-offline-verification.json`, `extra-modules/manifest.json` and
`preservation-verification.json`. Initial host tests caught a shared-read-only-path
boundary-matching bug and a missing new dependency in the synthetic packaging
fixture; both were fixed. The first preservation check's 14 differences were
checker issues: normalization of raw link text and inconsistent directory-link
inventory coverage, not rewritten old files. Its first report was retained;
matching the original raw link text and file-inventory scope yielded zero differences.

### Provenance and patches

`sources-7.3.1.json` pins the official archive and community reference;
`sources.json` retains the 6.18 pin. In addition to the manifest SHA256, this run
verified the upstream kernel.org detached signature using an isolated keyring.
Evidence is in ignored `out/linux-7.3.1/source-authenticity.json`; the automatic
fetcher's checksum verification does not replace that signature check.

Official 7.3.1 lacks complete Picasso/SM7250 support. The separate
`kernel/patches/7.3/series` takes a restricted headless subset from the pinned
[SM7250 community repository](https://github.com/sm7250-mainline/linux_kernel),
retaining native 7.3 clock/interconnect/UFS interfaces instead of mechanically
applying the 6.18 API backport. Existing UFS 32-bit DMA, deferred initial device
reset, QPHY and watchdog handling are retained; native DSI/GPU drivers are not added.

The SM7250 PAS/PDM mapping and default-off `picasso_fixed_msa` are also ported.
MPSS remains PAS 4 and manually loaded/started. Fixed MSA retains board/address/size
checks and does not change SCM ownership. The ordinary ath10k core has no HT20
diagnostic parameter. A separate core provides read-only HT20/management observer
parameters and must not replace the ordinary restoration core.

### Isolation and preservation

| Item | Existing 6.18 | New 7.3.1 |
| --- | --- | --- |
| Source | `src/linux-6.18.58/` | `src/linux-7.3.1/` |
| Build/output | Existing `out/` layout | `out/linux-7.3.1/` |
| Patch series | `kernel/patches/series` | `kernel/patches/7.3/series` |
| Additional configuration | Existing fragments | `kernel/picasso-7.3.config` |
| Wi-Fi kernel release | `6.18.58-picasso-lts-wifi2` | `7.3.1-picasso-wifi2` |

Without `KERNEL_VERSION`, tools still select 6.18. Unknown, empty and path-shaped
versions do not fall back. The new configuration retains the XFS root binding,
boot parameters and used display, key, container and signed-regdb capabilities.
Ignored `config-comparison.json` records symbol changes; old symbols cannot all
be copied mechanically across kernel versions.

Pre-change inventories cover the 6.18 source, build, modules and recovery images.
A separate inventory protects existing sources/binaries in `kernel/display/`,
`kernel/power/` and `dts/`. New external modules build only from copies under the
7.3 output directory, never in those old module directories.
The authoritative old recovery image is
`out/power-install-20261028/boot-installed-power.img`, not arbitrary historical
root-`out/` build inputs or experimental images.
Ignored `out/linux-7.3.1/rollback-6.18/` additionally contains eight byte-identical
recovery copies: the primary and older verified images, Image, configuration,
power DTB and matching module archive. This is neither new device validation
nor an automatic rollback mechanism.

### Offline build and audits

Build explicitly with `KERNEL_VERSION=7.3.1`, `DTS_PROFILE=power-trial` and
`tools/build-kernel.sh`. Read the private root binding from protected local
baseline material, not these notes. `tools/build-extra-modules.py` produces
isolated WLED/PON and conservative ath10k modules and checks ABI, absence of the
HT20 parameter in the ordinary core, and unchanged baseline module bytes.

The new power/Wi-Fi/RMTFS DTB has no node/property differences from the preserved
installed power DTB. This run's ROM offline overlay audit covers all 21 fixed
reserved regions. DT compilation still reports inherited community-tree warnings;
this is not full binding/schema acceptance. `tools/audit-wifi.py` retains vendor
wiring, firmware range, RMTFS guard-page and manual-MPSS checks. Packaging requires
fresh Image/DTB/config-bound audits in the new output directory, not old 6.18
audit evidence. The new image receipt must remain unverified and cannot inherit
successful old-image status from `device.json`.

### Versioned runtime and authorization

`tools/prepare-kernel-runtime.py` uses locally preserved Wi-Fi configuration,
CN policies and reference rules to generate a private `runtime-bundle/`. It does
not deploy, enable services or create an authorized `activation.json`.
New controllers use the generic target prefix `/opt/picasso-kernel-7.3.1/`.
Service names, transient runtime directories and screen/power history directories
are separate; refusing a new service must not clean an old service's session.

Existing hash-pinned read-only userspace jails, firmware, credentials and private
NV working copies are not rewritten. NV dirty/checkpoint protection remains shared,
so 6.18 cannot overlook an unclean 7.3 exit. Dependencies are hash-checked before
startup; saved local reference material is not a fresh verification of phone files.
Temperature thresholds, exact-PID leases, private-file permissions, physical keys,
permanent MAC, raw CN nl80211 regulatory evidence and cleanup boundaries remain strict.

Candidate services additionally require root0400 consent bound to the release,
configuration, DTB, image and runtime manifest, separately granting screen,
bounded Wi-Fi probation, persistent Wi-Fi and power operation. All example grants
are false. Old 6.18 Wi-Fi probation cannot validate the new controller. The bounded
CN wrapper uses the original worker's 45-second probation path, not its unbounded
radio loop; persistent service still needs new proof. Power retains its separate
authorization file. This phase does not accept or create new consent for the user.

### Later device phase and recovery

The first trial should temporarily boot the candidate while persistent `boot`
retains 6.18. First confirm physical buttons, USB and stock fastboot access and
save the old image on the computer. Before installing new modules, verify the
existing `ath10k_snoc`, `qcom_q6v5_pas` and `rmtfs_mem` autoload blacklist.
A recovery image is not a filesystem/user-data backup; returning to the old kernel
does not undo new-kernel data writes or filesystem-format changes.
On the first new-kernel boot, old services reject its release and new services
gain no automatic authorization; automatic Wi-Fi availability must not be assumed.
Do not rely solely on remote SSH: if the new kernel loses networking, in-Linux
remote recovery may itself be unreachable.
USB SSH/serial also require working new-kernel hardware and are not proven safeguards.

Temporary boot, installing matching modules/versioned services, and eventually
writing default `boot` are later, separately confirmed device operations.
Neither these notes nor build tools authorize them. Validate storage, USB,
networking, display, thermal handling and keys individually, retaining known
failures, before considering the default switch. Stock fastboot is independent
of Linux networking, but is not automatic fallback.

### 2026-10-31: device phase blocked by missing USB visibility

The user authorized writing 7.3.1 and accepting it through USB Fastboot, but no
device operation has occurred in this attempt. After reconnection, neither the
host's system USB enumeration nor its existing Fastboot tool detected the phone.
No USB-related events appeared in the previous 15 minutes of kernel logs either.
Current device identity, unlock state, boot-partition size and installed modules
therefore could not be verified, so writing could not safely begin.

All six candidate artifacts match their offline receipt, and the primary 6.18
rollback copy matches the preserved original image. These are host-file checks,
not verification of the currently connected phone. Evidence is retained in
ignored `out/linux-7.3.1/device-acceptance/blocked-usb-preflight.json`.
No boot, flash or reboot command was sent; no modules/runtime were installed,
and hardware acceptance did not start. The host running this session must first
detect the target USB Fastboot device. This blocked attempt is not acceptance.
A later user-requested retry still found zero Fastboot devices and no additional
USB devices; no device commands were sent. Its result is retained separately as
`fastboot-retry-preflight.json` in the same evidence directory.

### 2026-10-31: isolated installation and temporary native trials

A later retry detected the target stock Fastboot device. Existing noninteractive
sudo was used to verify identity, unlock state and partition size. The preserved
6.18 recovery image was temporarily booted for staging, followed by a temporary
boot of the exact verified 7.3.1 image. **No `fastboot flash` or other partition
write was performed.** Only the independently identified USB link was restored;
SSH retained the original strict host-key pin.

Extracting both images' embedded configurations established that
`out/wifi-rmtfs-20261027/installed-baseline/` is an earlier headless baseline,
not the matching current Wi-Fi Image/config. Correct old Wi-Fi inputs are
`Image` and `kernel.config` in its parent directory, additionally preserved under
`out/linux-7.3.1/rollback-6.18/verified-wifi2/`. The original eight rollback assets
were not overwritten; their earlier top-level Image/config must not be mistaken
for matching inputs to the primary recovery image.

Only new-version modules, `/opt/picasso-kernel-7.3.1/` and four versioned unit
files were installed. All 730 old module files stayed unchanged and new units
were not enabled. Extraction first refused temperatures at or above 40°C without
relaxing the threshold. GNU tar also rejected the incompatible combination of
`--keep-old-files` and `--no-overwrite-dir` before extraction; removing the latter
retained old-file protection and scoped archive validation.

| Temporary 7.3.1 item | Actual result and boundary |
| --- | --- |
| Native boot | Verified systemd, XFS, eight CPUs, exact config/DTB and USB SSH; persistent `boot` remained 6.18 |
| Storage | Wrote, fsynced and reread a 1 MiB marker, retained for later checks; not the planned normal-reboot acceptance |
| Rootless Podman | Separately authorized one networkless cached-image container and its removal; no pull or existing-container changes |
| Screen and keys | Operator confirmed native console, approximately 15-second idle-off and volume-up wake; real input events and one short power press observed |
| Wi-Fi | Separately authorized 45-second CN trials eventually passed and cleaned safely; not persistent-service or cold-start autoconnect acceptance |
| Not performed | Default-kernel write, planned normal reboot, shutdown/long-hold, charging or endurance tests |

The first Wi-Fi attempt refused before MPSS startup because the shared jail
still executed the old supervisor. Only new runtime generation changed: the new
child's private mount namespace read-only binds the versioned supervisor over
the jail entry point. Its code uses mode0444 while the private outer directory
and root0400 policies remain restrictive. The old jail, controllers and shared
backend bytes stayed unchanged, retaining four inherited FDs, the three-second
lease, temperature and NV lifecycle guards. Two regressions were added and all
seven runtime tests passed; the full host suite was not rerun.

The next attempt started the DSP in approximately half a second but found no
unique WLFW endpoint. Shutdown-ack timeout, lease expiry and an eight-second
userspace watchdog SIGABRT followed during cleanup; they did not cause the
initial endpoint absence and were not a kernel panic. Independent ExecStopPost
eventually cleaned safely, committed the checkpoint, stopped the DSP and restored
ordinary modules and CPU limits.

A logging-only QRTR module was then built from an ignored isolated source copy,
without changing the canonical Image, patch series or 875 ordinary modules.
Both its trial and a separately authorized 45-second trial after restoring
ordinary modules completed, passing WPA2/CCMP, DHCP, DNS and certificate-verified
HTTPS with the 2.4 GHz fallback and actual 20 MHz. Ordinary modules were restored;
the ordinary-module trial's peak was 36.4°C. Native 7.3 QRTR HELLO initialization changes
were an investigative lead, not a proven cause. Full module reload or timing
could affect results; cold-start repeatability remains unproved.

For `Type=notify`, `systemctl start` returns at READY, not at the end of 45 seconds.
The first diagnostic helper therefore checked too early and correctly refused
restoration while DSP/WLAN were active. Final evidence requires terminal
`passed_bounded_probation`, `safe_cleanup_complete` and actual offline state,
not intermediate snapshots or reassuring filenames. Final records are
`731-qrtr-diagnostic-final.json` and `731-ordinary-wifi-acceptance.json` in the
ignored device-acceptance directory.

The operator declined new-kernel screen/Wi-Fi autostart and did not confirm
readiness for the planned normal reboot. Default `boot` was therefore not
written, new units were not enabled, and that reboot command was not sent.
Later USB disconnection and return to the old kernel are not agent-managed
automatic rollback: the operator subsequently confirmed a separate reboot and
clarified that the apparent shutdown was a black screen, not confirmed power loss.

### 2026-10-31: screen and LAN recovery after returning to 6.18

Read-only checks confirmed current 6.18 and the complete 128 MiB `boot` partition
still matching the original verified baseline byte-for-byte digest. All 730 old
modules and 42 baseline shared entries were unchanged. The exact temporary
7.3.1 boot has approximately 52 minutes of SSH/trial records after sshd started.
Old screen/power services correctly rejected its release; no deliberate poweroff
request or pstore record was found for that trial. Neither a final console line
nor missing logs establish sshd, panic, PMIC or watchdog poweroff causality.

The two actual faults after returning to 6.18 were:

| Symptom | Evidence and action |
| --- | --- |
| Black screen after sshd | At approximately 13.8 seconds, `systemd-backlight` raised the custom backlight from 0 to 12; the screen owner's actual-value guard stopped and unloaded its module. With explicit consent, only `systemd-backlight@backlight:picasso-screen.service` was masked, not the template or other devices; old screen code, modules and enablement stayed unchanged |
| LAN SSH unreachable | Wi-Fi preflight refused with `Unclean NV lifecycle; operator review required`, before creating WLAN. The stale marker belonged to the interrupted intervening 6.18 boot, not temporary 7.3.1; the current phone was not powered off and USB SSH remained available |

NV recovery did not blindly delete a marker and retry. Review first established
inactive radio owners, offline DSP, absent WLAN, unloaded related modules and
no process holding work-copy FDs. Each ordinary 8 MiB work copy passed owner,
mode, link-count, size and non-aliasing checks; all three hashes matched the
committed checkpoint. With explicit consent to restore existing continuous
Wi-Fi, a root0400 review receipt bound the current boot, stale marker and
checkpoint, and preserved the old marker under the generic system directory
`/var/lib/picasso-wifi/operator-reviews/`. No original NV partition was read,
no work copy or checkpoint was manually rewritten, and future dirty-state
refusal was not weakened.

Only the existing guarded screen and Wi-Fi services were restarted, both reaching
active/running. Screen records show normal 15-second idle-off; the operator
confirmed volume-up wakes the terminal. The host actually completed LAN SSH
over a non-USB route using the original strict device host-key pin and checked
the same native release/boot identity. Wi-Fi now runs continuously. Its new dirty
marker belongs to the current active session and is normal lifecycle state:
**do not delete it**. Normal controlled work-copy updates during radio activity
are not manual NV rewrites by this recovery.

The original power-button service separately recorded a startup 45°C thermal
abort without requesting PID1 poweroff; it was not restarted and its threshold
was not lowered. Recovery did not reboot, flash or touch firmware/raw NV.
Next-boot acceptance of this backlight policy was not performed. Repeated
new-kernel boot, default switching and endurance remain unverified; this
recovery does not constitute complete 7.3.1 acceptance.

Closeout ran separately from current 6.18, not by replaying the helper bound to
the old 7.3.1 boot, and did not stop recovered old-kernel Wi-Fi/screen. After
verifying candidate runtime/dependency pins, all four temporary feature grants
were closed and all four candidate units remained disabled. Four exact
uploaded/observer/diagnostic files were removed after digest checks; the private
watchdog memory dump was removed using its original trial boot/PID/unit identity.
Journals and acceptance metadata were retained. Recovery evidence remains under
ignored `out/linux-7.3.1/device-acceptance/`:
`recovered-618-backlight-failure.json`,
`unclean-nv-lifecycle-readonly-review.json`,
`618-display-lan-recovery-result.json`,
`618-display-lan-recovery-verification.json`,
`618-recovered-lan-ssh-verification-stdin.json` and
`731-trial-closeout-from-618-result.json`. Neither these records nor this note
authorize another operation.

### Subsequent phase: startup repair, repeated autostart and default switch

The operator freshly authorized temporary boot, screen/15-second idle/volume-up
wake, a new 45-second CN Wi-Fi probation and guarded continuous Wi-Fi/LAN SSH,
then a default switch only after acceptance, retaining 6.18 rescue. Closed earlier
grants were not silently reused. New long-hold shutdown, charging and container
experiments were not authorized.

#### Screen timing and version selection

Candidate units gained exact `ConditionKernelVersion` selection. Separate
drop-ins similarly restrict existing screen, Wi-Fi and power units to 6.18 without
rewriting their controllers; old units skip before execution on 7.3.1.
Candidate screen activation also requires the mask of exactly
`systemd-backlight@backlight:picasso-screen.service`, preventing the generic
restore loader from competing with the PID-leased backlight owner.

The first new automatic startup exposed a different failure: after the external
cooldown accepted three samples below 40°C, imports/validation allowed temperature
to rebound. The owner refused with `Start below 40C`, safely exiting and unloading
its module. This was not the earlier generic-backlight restore conflict.
Only the generated 7.3.1 owner was adapted: bounded cooling now runs after
console/asset validation and before input/module arming, immediately followed by
the final 40°C guard. Three valid samples strictly below 40°C, the 300-second
cooling bound and 330-second startup limit remain. The running 45°C abort,
3-second PID lease, 8-second watchdog, low-brightness limit and `Restart=no`
were not weakened. Later actual boots starting above 40°C waited normally and
became ready; visible terminal and volume-up wake were confirmed.

#### Changed NV work copies and separate recovery consent

An intervening return to 6.18 followed by Fastboot entry left an older-boot dirty
marker and three ordinary work files that no longer matched their checkpoint.
The earlier unchanged-copy/marker-only recovery was therefore inapplicable.
Changed hashes were not simply adopted as a validated checkpoint.

With new explicit consent, the existing read-only original backup files and
manifest were verified first. All three changed 8 MiB ordinary files, the old
checkpoint and marker were preserved. Only Linux work copies were restored from
those verified regular backups; the complete restored set was checked and its
checkpoint committed before archiving the old marker. Originals were unchanged;
no raw NV partition was read or written. Subsequent normal RF updates remained
under the original lease/cleanup lifecycle.

#### First-peer QRTR handshake recovery

After screen repair, the first ordinary-module RF attempt in that boot still
failed with `No unique local WLFW endpoint`. Independent checks confirmed safe
DSP/WLAN shutdown, a matching checkpoint and restored CPU limits. The unit
watchdog was a downstream failed-cleanup issue, not a kernel panic or an
sshd-triggered whole-device poweroff. Earlier logging-only/reload success did
not establish repeatable cold startup.

Comparing 6.18 and 7.3.1 identified a reproducible receive-side recovery gap.
The upstream [HELLO-on-endpoint-registration change](https://lore.kernel.org/r/20260827-qrtr-hello-on-ep-register-v3-1-ca289ff99abf@oss.qualcomm.com)
latches successful transmission but removes the reply to a later peer HELLO.
The first send can precede automatic node identification or remote receive
readiness; transport success is not a completed remote handshake.

An RF-free real `qrtr_tun` virtual-endpoint test first reproduced an initial HELLO
to an unassigned destination followed by no reply to the peer's HELLO.
`0004-qrtr-reply-to-first-peer-hello.patch` retains proactive initiation and adds
one name-server reply to each peer's first HELLO before advertising local
services. Duplicate HELLOs do not get another reply, BYE destroys the state, and
failed sends remain errors without consuming the reply. Two virtual-endpoint
recreation rounds verified one initial reply and zero duplicate replies.
The test module was then unloaded, leaving no virtual endpoints and starting no RF.

Only `qrtr.ko` changed among 875 ordinary modules; the other 874 and six additional
variants were preserved. The runtime manifest and three Wi-Fi configurations now
pin the ordinary QRTR module digest. The QRTR change does not alter Image,
configuration, DTB or boot-image bytes. Previous module/runtime archives were
preserved before repackaging. Actual source application, module compilation,
patch-style checking and 39 focused regressions passed. This does not constitute
a complete firmware-side trace of the failed handshake or long-term RF qualification.

A manual host `git apply` initially returned success while actually skipping the
patch because it discovered the enclosing repository. Source/module byte checks
detected the unchanged output; that attempt was marked discarded and not deployed.
As in the existing preparation tools, Git discovery was then bounded to the staged
tree's parent with `GIT_CEILING_DIRECTORIES`. Actual source changes and the rebuilt
module were verified before deployment; Git exit status alone is not proof of application.

#### Device acceptance and persistent default

| Phase | Observed result |
| --- | --- |
| First RF in a new temporary boot | Fixed ordinary QRTR; the 45-second CN probation completed successfully, including WPA2/CCMP, DHCP, DNS and certificate-verified HTTPS |
| Independent post-probation cleanup | Dirty absent, checkpoint matching, DSP/WLAN off and temporary CPU limits restored |
| New-version continuous-service proof | Root0400 proof derived from actual native result/unit success/safe cleanup and bound to this controller/manifest; no 6.18 proof reuse |
| Continuous Wi-Fi and LAN | Guarded persistent owner enabled; actual original-key-pinned LAN SSH over a non-USB route verified the same native boot |
| Further complete temporary reboot | No manual screen/Wi-Fi start; both automatically ready for at least 45 seconds with zero automatic restarts; LAN SSH and visible wake passed |
| Default installation | Radio/NV/DSP safely cleaned first; independently identified stock Fastboot wrote only `boot`, then normally rebooted rather than using `fastboot boot` |
| Default-boot acceptance | Native `7.3.1-picasso-wifi2`; automatic screen/Wi-Fi ready for at least 45 seconds, old units version-skipped, LAN SSH and operator-visible wake passed again |
| Persistent readback | The first 35,348,480 bytes of the 128 MiB `boot` partition match the accepted image; the whole-partition digest is recorded separately, not equated with an unpadded image digest |

Verified 6.18 images, sources, modules and recovery assets remain preserved.
No other partition, firmware or raw NV was written, no RTC-write command was used,
and no GRUB, Syslinux,
A/B or automatic rollback was introduced. The existing device tree registers no
`bootloader` restart target; normal reboot while holding volume-down did not
reliably enter Fastboot. No unsupported software target or direct IMEM write was
used. Each transition first independently confirmed safe radio shutdown, then
the onsite operator manually entered Fastboot and the host rechecked the unique
device, product, unlocked state, partition size and contemporaneous voltage.

Screen and guarded continuous Wi-Fi are enabled; probation/power grants are
closed and the power unit is disabled. A live Wi-Fi dirty marker belongs to the
current boot/owner and is normal: **do not clear it**. Automatic link-loss
reconnection remains disabled. The 5 GHz, complete shutdown, charging and endurance
limitations are not resolved by this repair, and no container trial was repeated.
Recovery still needs onsite USB/stock Fastboot and the retained 6.18 image;
single `boot` is not an automatically rolling-back dual-slot system.
Host build tools still select 6.18 when no version is specified; new builds
continue to require explicit `KERNEL_VERSION=7.3.1`. Switching the device default
did not overwrite the old build workflow.

Closeout removed only the unloaded, digest-verified virtual test module and this
phase's private watchdog memory dump, matched against preserved boot/unit/PID
metadata and file extended attributes. An initial historical-journal query was
rejected for boot-identifier formatting; its error was retained without fuzzy
matching or bulk deletion. Original failure logs and protected metadata remain.
Neither current live dirty state nor NV work files were touched, and a final
actual LAN SSH check confirmed healthy default services.

Private evidence remains under ignored `out/linux-7.3.1/device-acceptance/`:
`qrtr-hello-unpatched-virtual-reproduction.json`,
`qrtr-hello-fixed-virtual-regression.json`,
`731-fixed-qrtr-cold-bounded-probation.json`,
`731-temporary-autostart-acceptance.json`,
`731-default-boot-install.json`,
`731-default-autostart-acceptance.json` and
`731-default-screen-operator-confirmation.json`. Earlier failures, changed-copy
recovery and every clean-stop receipt are also preserved. No actual addresses,
network names, private identifiers/digests or external local paths are published;
the record does not authorize another device operation.
