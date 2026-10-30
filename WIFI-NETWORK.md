# Wi-Fi 限时联网验收通过：Chaldea-2.4G / SG / 设备永久 MAC

**后续已按用户新授权把同一份wifi2 #10写入boot，并通过正常重启，见 [WIFI-INSTALL.md](WIFI-INSTALL.md)。
以下保留刷入前的网络试验及结束时状态；不代表当前仍是临时启动，也不宣称重启后已重新联网。**

2026-10-28，Redmi K30 5G Picasso，临时 **6.18.58-picasso-lts-wifi2 #10**，原生 Fedora 44 / XFS。
**本轮已真实通过 WPA2、DHCP、DNS 和经 wlan0 的 HTTPS。当前已按试验约定断开并清理，不是仍保持在线或持久启用。**

## 同一轮实际证据

用户在本地执行一次性入口，助手仅接收完成通知后检查现有结果，**没有重复启动已运行的 exclusive 控制器**。
原始状态为 `passed_wpa2_ccmp_permanent_mac_sg_dhcp_dns_https_over_wlan0`，PID-1 单元退出成功。

| 项目 | 实际结果 |
|---|---|
| 目标 | 精确 SSID **Chaldea-2.4G**；定向主动发现，2447 MHz / 信道8，约 **-56 dBm** |
| 链路宽度 | PHY HT20 保守能力，关联后的实际接口 **20 MHz** |
| 地址 | 同设备 DMS 默认 WLAN MAC，经 WLFW runtime provision；当前/永久 MAC 一致，联网测试结束前再次一致；不随机、生成或借用地址 |
| 加密/关联 | 活跃精确 SSID、station authorized=yes、NetworkManager activated；本轮原生 supplicant 日志确认 **RSN/WPA2-only + CCMP PTK/GTK** |
| IPv4 | DHCP server/租约选项、wlan0 IPv4 地址、经 wlan0 的默认路由均验证 |
| 防火墙 | wlan0 实际 firewalld zone 为 **drop**；USB SSH 配置不变 |
| DNS | 直接绑定 wlan0 向 DHCP DNS 服务器发新 A 查询，`example.com` 响应 **rcode=0，2 条 answer**；不是只使用本地缓存 |
| 系统解析 | 原生 `getent ahostsv4 example.com` 成功，解析结果路由明确为 wlan0 |
| HTTPS | `curl -4 --interface wlan0 --noproxy '*' ... https://example.com/`；**HTTP 200，ssl_verify_result=0，下载577字节，约0.92秒** |
| 温度 | 本轮最高采样 **37.1°C**；低于40°C启动、45°C中止线保持不变 |

HTTPS 正常验证系统 CA/服务器证书，无 `-k`、代理、主机 NAT 或主机默认路由修改。
这验证了手机自身无线数据路径，而不是用 USB/主机联网代替 Wi-Fi。未运行 DNF、测速或长时间负载测试。

## SG：不是把 AP 国家码当作用户地区

AP Country IE 为 CN，会覆盖初始化时的 SG。连接后通过正常 `iw reg set SG` 用户请求，让内核生成
**98-intersection**（SG 与 AP 国家码的交集，不是手工伪造/设置98）。

同一轮对实际 PHY **24 个启用的20 MHz信道**逐一验证频率/EIRP/DFS 均为观察到的 SG 规则子集。
不是仅看命令成功或全局标签；没有修改 regdb、BDF、校准、regulatory 保护标志或启用测试绕过。
此验收仅覆盖实际20 MHz，不扩展为宽信道、RF/SAR/充电认证。

## 本轮仍使用的试验依赖

- 临时 wifi2、独立模块目录、原厂固件/BDF、标准 metadata-only firmware-5.bin。
- 原授权三份 NV 的只读原始备份和普通可写工作副本；RMTFS 后端仍是受限 DynamicUser、无 capabilities、精确字符设备权限、四个预开 FD。
  没有把原 NV 分区交给代理，没有读取 persist/fsc、写原 NV 或扩大受保护读取范围。
- MPSS 手动启动、自动恢复关闭；受限 Picasso 固定 MSA opt-in；没有全局 SCM/SMMU 放宽。
- 只读 opt-in 的 HT20/管理帧观测 core，普通 installed core 文件从未替换；每次新 MPSS 启动仍需先 DMS→WLFW MAC 提供。
- 控制器 CPU0–3；CPU6/7 最大频率在硬件可用表内临时限制为 **1,094,400 kHz**，有界读回验证。
  不修改 governor/min/电压/热策略/发射功率，检查全部传感器。此次低温不证明长期稳定。
- 明确精确SSID主动探测、profile band bg/hidden=yes（客户端探测策略，不是宣称或改动 AP 隐藏设置）、RSN/CCMP、永久 MAC、无自动连接、IPv4、入站drop。

## 凭据与结束后的真实状态

密码只在本地 TTY 隐藏输入，SSID-specific PMK 临时存手机 root0600 tmpfs；只有 native nmcli 通过 passwd-file 使用。
没有密码 argv、聊天、日志、秘密属性读取或旧缓存密钥恢复；未把 PMK 文件收集为证据。

正常 finally 及独立 PID-1 ExecStopPost 已实际验证：

- 连接断开，wlan0 unmanaged 后卸载，**DSP offline，无 WLAN 接口、无默认 IPv4 路由**。
- 代理/TFTP 停止，经验证的共享 RMTFS RAM **2,621,440字节**清零并读回。
- `/run/picasso-chaldea-2g.passwd` 已删除，持久连接文件没有 psk 键，禁止自动连接保持。
- 原 installed core 的完整哈希保持 `ed2f66c7646c43c4b3106bed4c8a33e811d81a7aa1207775f4fabeb350900862`，诊断参数消失。
- CPU6 原最大 **2,208,000 kHz**、CPU7 原最大 **2,400,000 kHz** 已恢复并读回。
- USB sshd/firewalld active。临时 wifi2 #10 仍在运行；正常重启回已安装 #8。

三份原 NV 各8MiB再次完整 O_DIRECT 只读比对及0400私有备份一致；
**原15,285个静态文件、完整boot、七个保留分区、六个LUN GPT 再次一致**。
canonical #8 boot image SHA256 保持 `81f28d44625ecd8337348132c7f4d83bdb817f966a41da151df0a5c27fde043c`。
没有刷写命令、原 NV 写回、GPT/DTBO/vbmeta 变更或主机网络改动。

## 验收边界及后续

这轮**已经完成，无需再录入密码或重复该一次性命令来验证同一结果**。
`tools/test-chaldea-2g.sh` 对应的 exclusive connect4 目录已用，重复执行会在录入前拒绝，这是预期保护。
后续助手应读现有结果，不盲目再启动。

仍不是“开机自动联网”或长期服务器验收：没有持久启用/保存Wi-Fi密码，已安装#8不继承临时#10实验支持。
再次正常使用需另行设计受控启动、私有副本生命周期、永久MAC/SG保持、热约束与凭据策略，并单独实际验证。
不能根据一次577字节HTTPS成功宣称吞吐、持续连接、漫游、休眠、断电恢复、充电/电池或RF安全通过。
Linux power-supply 遥测、长期温控/RAM/UFS/外设/watchdog等限制仍在；没有开启IPA/蜂窝数据，专有共享 modem 固件的RF行为不能保证静默。

## 不隐藏历史失败

5GHz Chaldea status3、关联后的 CN 域中止、45.1°C 热中止、即时QoS读回/恢复断言失败、wpa_cli套接字检查不兼容、单次被动漏检等原始结果均保留。
没有 reset-failed、删日志或把旧失败改成成功；当前成功不自动证明历史 DNF 任务恢复或长期状态健康。

证据：`out/wifi-network-acceptance-20261028/result.json`、原始 `connect-result.json`、独立清理、最终状态和完整性报告。
用户实际执行的源记录为 `out/wifi-chaldea-2g-connect4-20261028/`；原准备校验集保持，新运行文件另存 RUN4-SHA256SUMS。
离线测试 **190项：189通过，1项可选QEMU跳过**；不把这些主机测试冒充真机网络结果。
前序记录：[WIFI-CHALDEA-2G-CONNECTION.md](WIFI-CHALDEA-2G-CONNECTION.md)。
