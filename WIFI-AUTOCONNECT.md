# 开机Wi-Fi：优先/回退已实测，约18秒掉线阻塞默认启用（阶段记录）

> 后续用户请求启用自动连接：原服务新轮45秒链路通过但整体watchdog失败，保留该failed unit；独立新控制器声明STOPPING后再通过45秒完整联网/清理/unit success，才按root0400原生证据启用常驻。当前2.4G联网、服务enabled/active；原掉线根因与冷启动/长期验收仍未通过。最新[WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md)。以下为旧阶段，包括当时disabled/45秒限制与失败事实，不代表新配置当前状态。

**后续仅元数据观测已确认：固件BEACON_MISS先触发失联处理，-110发生在后续DISABLE_KEY清理，不是初始装钥失败。
加入观测后的掉线时间为51.0秒/22.1秒，不是固定18秒；关联期无扫描，底层beacon为何稀疏仍待查。
最新见 [WIFI-LINK-LOSS.md](WIFI-LINK-LOSS.md)，默认联网仍未启用。以下保留本阶段原结果。**

2026-10-28。用户指定 **Chaldea（5GHz）优先，失败回退 Chaldea-2.4G**；
随后已在本地TTY明确同意长期保存及运行范围，输入共同口令，分别派生两个SSID的PMK。
**持久凭据已保存；受保护服务已实现，但默认开机启用仍关闭。不能把短时联网成功说成持续联网通过。**

当前默认内核仍为已安装并正常重启验证的wifi2 #10；见 [WIFI-INSTALL.md](WIFI-INSTALL.md)。
本阶段没有再次写boot、格式化userdata或更改原NV/GPT/固件分区。

## 实际完成的运行和对照

| 试验 | 实际结果 |
|---|---|
| 独立原生租约沙箱 | 指定root控制器PID可持续保活超过3秒；其他root PID不能续租，3秒失效退出。负向失败单元保留；未启动RF |
| probation1 | 冷启动缺少显式qrtr_smd传输依赖，WLFW未出现，未激活SSID；安全清理 |
| probation2 | 传输已补齐，RMTFS真实请求到达；新TFTP StateDirectory名称破坏既有jail的/readwrite绑定，server_check.txt为只读；未激活SSID，安全清理 |
| probation3 | 恢复原已验证的tqftpserv scratch绑定后，Chaldea约19.8秒超时；回退2.4GHz约3.2秒激活，WPA2/DHCP/SG/DNS/HTTPS通过；延时观察掉线，安全清理 |
| probation4 | 明确禁用省电、5秒网关ICMP保活；Chaldea约20秒超时，回退约0.7秒激活及联网通过；仍掉线，安全清理 |
| isolated2g | 不尝试5GHz，直接2.4GHz，约5秒激活且联网通过；仍掉线，安全清理。**这不是优先/回退验收** |

三次实际连上的2.4GHz均通过：

- 新本轮CCMP PTK/GTK握手及实时station授权、精确SSID，设备DMS当前/永久MAC一致；实际20MHz。
- AP CN后正常用户SG请求形成内核98交集，**24个启用20MHz信道/EIRP/DFS为SG子集**。
- DHCP及wlan0默认路由、drop防火墙区域；绑定wlan0的新DNS查询及系统解析路由检查。
- 明确wlan0/no-proxy的HTTPS，**HTTP200、证书验证0、577字节**，并非使用USB/主机NAT代替。

但三次CONNECTED→DISCONNECTED分别仅 **17.778、17.774、17.607秒**。
内核在掉线前出现 `failed to install key ... -110`、`failed to remove key ... -110` 和连接丢失。
这是事实相关性，**尚未确定唯一根因**；不能因此说密码错误、路由器坏了或只因5GHz失败污染回退。
2.4GHz独立对照仍重现，关闭省电/网关保活没有解决。没有要求移动USB手机、提高RF功率或改BDF/校准。

probation3最初错误文字“Live width changed”来自掉线后接口不再显示width，并非已证明发生宽信道切换。
原结果保留；新代码先检查实时连接/授权，再解释宽度，不把错误标签当硬件根因。

## 服务实现及保护（尚未验收为默认开启）

源文件：`tools/wifi-service.py`、`tools/picasso-wifi.service`、`tools/wifi-fallback-policy.py`、
`tools/rmtfs-supervised.py`及两个supervised unit模板。

- 精确有界次序：Chaldea band a、20秒；普通激活失败后断开，再尝试Chaldea-2.4G band bg、25秒。
  成功回退不周期性抢回弱5GHz；两个均失败不循环。安全错误致命关停，不伪装成普通失败换SSID。
- 每次重新发现本次启动的RMTFS物理RAM、2×4KiB guards、内存bank/固定carveout排斥和字符major/minor；
  2.5MiB清零/读回/EOF测试。不复用旧/run地址或试验request.json。
- config/FDT及已固定代码、固件/BDF、模块/library哈希核验；普通NV工作副本元数据及checkpoint一致。
  MPSS auto_boot=false，显式加载qrtr_smd/pd_mapper/PAS，唯一原厂MPSS、手动start、恢复disabled。
- root控制器检查传感器及DSP，每0.2秒续租；<40°C启动、>=45°C关停、进度停顿则不再续租。
  PID1 watchdog8秒、Restart=no、独立ExecStopPost。控制器CPU0–3。
- CPU6/7仅无线运行期间最大1,094,400kHz，关闭恢复原2,208,000/2,400,000kHz；不改min/governor/电压/热保护。
- 代理保持独立DynamicUser、无capabilities、唯一个字符设备权限、**恰好四个预开FD**。
  使用未改的已验证RMTFS协议/FD引擎。新监督包装器只接受内核SCM_CREDENTIALS验证的指定root PID心跳；
  失效3秒退出并同步普通副本。没有用简单删去原120秒限制来伪装长驻支持。
- 原工厂固件TFTP jail/readwrite scratch绑定恢复原StateDirectory=tqftpserv，不增加原NV、SSH或其他设备访问。
- 每次MPSS启动先DMS→WLFW永久MAC，确认当前/永久地址，再扫描/激活。HT20 opt-in；管理帧observer关闭，QMI-only日志，无key/payload dump。
- 初始SG及每次关联后实际信道/EIRP/DFS审计，持续MAC/20MHz/SG/CPU cap/依赖/drop/授权检查。
  新控制器可在主SSID连接后丢失时尝试一次2.4GHz；回退连接再丢失则关闭，不重启MPSS循环。
- 先停止WLAN/DSP，再停代理/同步普通副本、清零经验证2,621,440字节RAM，恢复原core/CPU。
  clean stop才提交新work checkpoint；dirty标记或未核准变化导致下次拒绝启动，不自动重置为原NV。

**原NV分区和0400备份永不作为可写后端**，没有读取persist/fsc、SIM数据、扩展保护分区权限或写回原校准。

## 当前真实状态

- 全部五个连接/启动试验均已清理；DSP offline，无WLAN、无默认IPv4路由。
- 原core已恢复、诊断参数消失；CPU上限恢复；共享RAM已清零并读回，工作副本checkpoint正常提交，无dirty标记。
- `/etc/systemd/system/picasso-wifi.service`及诊断单元存在，**picasso-wifi.service disabled**；失败单元和每次独立history保留。
- 配置恢复为正常优先/回退次序，`diagnostic_2g_only=false`，仍限定45秒probation。
  不要手动删probation时限或enable来绕过掉线；也不能把独立2G对照设为最终策略。
- 持久凭据按用户明确同意保留在手机 `/var/lib/picasso-wifi/credentials/` root0700、各root0600；
  控制器只核验元数据，native nmcli通过passwd-file读取。无密钥内容收集、聊天/argv/日志泄露或主机缓存读取。
- **不需要再次输入密码。不要重复运行旧录入脚本**，它会拒绝覆盖。

## 完整性与证据

再次完整验证：三份原NV的O_DIRECT只读摘要及0400私有备份一致；15,285个原静态文件、
已安装#10完整boot、七个保留分区、六LUN GPT均未变化。主机canonical #8镜像继续保留，不覆盖。
试验最高采样38.1°C；没有温度超限、提高中止线或发射功率。

214项离线测试：213通过、1可选QEMU跳过。原生租约/故障保护与真实联网证据分开，不把主机测试冒充设备稳定运行。
没有reset-failed、删历史失败或把本次失败覆盖成成功；每次结果/清理/原生网络journal和代码revision均另存。
证据目录：`out/wifi-autoconnect-20261028/`，凭据payload不在其中。

## 阻塞及后续

尚未完成用户要求的默认开机自动联网，不能报告“已开启”。
下一步定位约18秒掉线的ath10k/WCN3990键操作/连接监测问题，必要时使用仅元数据的观测；
不得盲改校准/固件、伪造能力或关闭监管域/安全校验。修复后重新有界试验、再启用和正常重启验收。
已保存的凭据应继续直接经native nmcli使用，不应再次索取或读取其内容。

仍是实验性headless Linux：充电/电池、RF行为/安全、长期热/内存/UFS/休眠/看门狗/掉电恢复和其他外设未验收。
本阶段未增加IPA/蜂窝数据；专有共享modem固件行为不保证完全静默。
