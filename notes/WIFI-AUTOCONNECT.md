# 开机Wi-Fi：优先/回退已实测，约18秒掉线阻塞默认启用（阶段记录） / Boot-Time Wi-Fi: Priority/Fallback Tested; Disconnection at About 18 Seconds Blocked Default Enablement (Stage Record)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本页保留旧优先/回退阶段的失败与当时禁用状态，后续启用及掉线诊断见更新链接，不代表新配置当前状态。同级笔记链接相对于本目录；反引号中的源码与证据路径相对于仓库根目录（绝对路径除外）。 / This page preserves failures and disabled status in the old priority/fallback stage; linked updates cover later enablement and link-loss diagnostics, not the new configuration's current state here. Peer-note links are relative to this directory; source and evidence paths in backticks are relative to the repository root unless absolute.

## 中文

> 后续用户请求启用自动连接：原服务新轮45秒链路通过但整体watchdog失败，保留该failed unit；独立新控制器声明STOPPING后再通过45秒完整联网/清理/unit success，才按root0400原生证据启用常驻。当前2.4G联网、服务enabled/active；原掉线根因与冷启动/长期验收仍未通过。最新[WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md)。以下为旧阶段，包括当时disabled/45秒限制与失败事实，不代表新配置当前状态。

**后续仅元数据观测已确认：固件BEACON_MISS先触发失联处理，-110发生在后续DISABLE_KEY清理，不是初始装钥失败。
加入观测后的掉线时间为51.0秒/22.1秒，不是固定18秒；关联期无扫描，底层beacon为何稀疏仍待查。
最新见 [WIFI-LINK-LOSS.md](WIFI-LINK-LOSS.md)，默认联网仍未启用。以下保留本阶段原结果。**

2026-10-28。用户指定 **${PRIMARY_SSID}（5GHz）优先，失败回退 ${FALLBACK_SSID}**；
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
| probation3 | 恢复原已验证的tqftpserv scratch绑定后，${PRIMARY_SSID}约19.8秒超时；回退2.4GHz约3.2秒激活，WPA2/DHCP/SG/DNS/HTTPS通过；延时观察掉线，安全清理 |
| probation4 | 明确禁用省电、5秒网关ICMP保活；${PRIMARY_SSID}约20秒超时，回退约0.7秒激活及联网通过；仍掉线，安全清理 |
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

- 精确有界次序：${PRIMARY_SSID} band a、20秒；普通激活失败后断开，再尝试${FALLBACK_SSID} band bg、25秒。
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

## English

> The user later requested autoconnect enablement. A new run of the original service passed 45 seconds of link operation but failed its overall watchdog; that failed unit was retained. Only after an independent new controller declared STOPPING and then passed 45 seconds of complete networking/cleanup/unit success was continuous operation enabled based on root0400 native evidence. At that later update, 2.4G was connected and the service enabled/active; the original disconnection root cause and cold-start/long-term acceptance remained unresolved. See [WIFI-AUTO-ENABLED.md](WIFI-AUTO-ENABLED.md). The following is the old stage, including its then-disabled state, 45-second limit, and failures, not the new configuration's current state.

**Later metadata-only observation confirmed that firmware BEACON_MISS triggered loss handling first. -110 occurred during subsequent DISABLE_KEY cleanup, not initial key installation.
With observation added, disconnection occurred at 51.0 seconds/22.1 seconds, not a fixed 18 seconds. There was no scanning while associated; why underlying beacons were sparse remained undetermined.
See [WIFI-LINK-LOSS.md](WIFI-LINK-LOSS.md) for later results; default networking was still not enabled at that update. The following preserves this stage's original results.**

2026-10-28. The user specified **${PRIMARY_SSID} (5 GHz) first, falling back to ${FALLBACK_SSID} on failure**.
The user subsequently explicitly consented in a local TTY to long-term credential storage and the operating scope, then entered the common passphrase, deriving a PMK separately for each SSID.
**Persistent credentials were saved and the protected service implemented, but default boot enablement remained off. Short-lived networking success was not sustained-connectivity acceptance.**

The default kernel at this stage remained installed wifi2 #10, verified through a normal reboot; see [WIFI-INSTALL.md](WIFI-INSTALL.md).
This stage did not write boot again, format userdata, or change original NV/GPT/firmware partitions.

## Actual runs and comparisons

| Trial | Actual result |
|---|---|
| Separate native lease sandbox | The designated root controller PID could keep the lease alive beyond three seconds; other root PIDs could not renew it, and expiry after three seconds caused exit. Negative-test failed units were retained; RF was not started |
| probation1 | Cold startup lacked an explicit qrtr_smd transport dependency; WLFW did not appear, no SSID activated; safe cleanup |
| probation2 | Transport was added and real RMTFS requests arrived; a new TFTP StateDirectory name broke the existing jail's /readwrite binding, leaving server_check.txt read-only; no SSID activated; safe cleanup |
| probation3 | After restoring the previously verified tqftpserv scratch binding, ${PRIMARY_SSID} timed out after approximately 19.8 seconds; fallback 2.4 GHz activated in approximately 3.2 seconds, passing WPA2/DHCP/SG/DNS/HTTPS; later observation saw disconnection; safe cleanup |
| probation4 | Power saving explicitly disabled, gateway ICMP keepalive every five seconds; ${PRIMARY_SSID} timed out after approximately 20 seconds, fallback activated in approximately 0.7 seconds and passed networking; still disconnected; safe cleanup |
| isolated2g | No 5 GHz attempt, direct 2.4 GHz activation in approximately five seconds and networking passed; still disconnected; safe cleanup. **This was not priority/fallback acceptance** |

All three actual 2.4 GHz connections passed:

- New CCMP PTK/GTK handshake in that run and live station authorization, exact SSID, matching current/permanent device DMS MAC; actual 20 MHz.
- After AP CN, a normal SG user request produced kernel 98 intersection; **24 enabled 20 MHz channels/EIRP/DFS were SG subsets**.
- DHCP and wlan0 default route, drop firewall zone, a new wlan0-bound DNS query, and system-resolution route check.
- Explicit wlan0/no-proxy HTTPS: **HTTP 200, certificate verification 0, 577 bytes**, not USB/host NAT substituted for Wi-Fi.

However, CONNECTED→DISCONNECTED lasted only **17.778, 17.774, and 17.607 seconds**, respectively.
Before disconnection, the kernel emitted `failed to install key ... -110`, `failed to remove key ... -110`, and connection loss.
This was a factual correlation, **not a determined sole root cause**.
It did not justify blaming the password, a broken router, or only a failed 5 GHz attempt contaminating fallback.
The independent 2.4 GHz comparison reproduced it; disabling power saving and adding gateway keepalive did not solve it.
There was no requirement to move the USB-connected phone, no RF-power increase, and no BDF/calibration change.

probation3's initial incorrect text “Live width changed” came from the interface no longer displaying width after disconnection, not a proven wide-channel switch.
The original result was retained; new code checked live connection/authorization before interpreting width rather than treating an incorrect label as a hardware root cause.

## Service implementation and protections, not yet accepted for default enablement

Sources: `tools/wifi-service.py`, `tools/picasso-wifi.service`, `tools/wifi-fallback-policy.py`, `tools/rmtfs-supervised.py`, and two supervised unit templates.

- Exact bounded order: ${PRIMARY_SSID} band a, 20 seconds; after an ordinary activation failure, disconnect and try ${FALLBACK_SSID} band bg for 25 seconds. Successful fallback did not periodically reclaim weak 5 GHz. Failure of both did not loop. Safety errors caused fatal shutdown, not disguised ordinary failures to switch SSIDs.
- Every run rediscovered that boot's RMTFS physical RAM, 2×4 KiB guards, memory-bank/fixed-carveout exclusions, and character major/minor; performed 2.5 MiB zero/readback/EOF tests; did not reuse old /run addresses or trial request.json.
- config/FDT and pinned code, firmware/BDF, module/library hashes were checked; regular NV working-copy metadata and checkpoint matched. MPSS auto_boot=false, explicit qrtr_smd/pd_mapper/PAS loading, unique factory MPSS, manual start, recovery disabled.
- The root controller checked sensors and DSP and renewed its lease every 0.2 seconds; start below 40°C, shutdown at >=45°C, stop renewing if progress stalled. PID1 watchdog eight seconds, Restart=no, independent ExecStopPost; controller CPU0–3.
- CPU6/7 maximums were 1,094,400 kHz only during wireless operation, restored to original 2,208,000/2,400,000 kHz on shutdown; no min/governor/voltage/thermal-protection changes.
- The proxy retained separate DynamicUser, no capabilities, permission for only one character device, and **exactly four preopened FDs**. The unchanged, verified RMTFS protocol/FD engine was used. The new supervision wrapper accepted heartbeats only from the designated root PID, verified by kernel SCM_CREDENTIALS. Expiry after three seconds caused exit and regular-copy synchronization. Long-running support was not feigned by simply deleting the original 120-second limit.
- The original factory-firmware TFTP jail/readwrite scratch binding restored original StateDirectory=tqftpserv, without added access to original NV, SSH, or other devices.
- Every MPSS startup did DMS→WLFW permanent-MAC provisioning before checking current/permanent addresses and scanning/activation. HT20 opt-in, management-frame observer off, QMI-only logs, no key/payload dumps.
- Actual channel/EIRP/DFS audits at initial SG setup and after every association, with continuous MAC/20 MHz/SG/CPU-cap/dependency/drop/authorization checks. The new controller could try 2.4 GHz once after losing a main-SSID connection. Losing fallback then shut down, without an MPSS restart loop.
- Stop WLAN/DSP first, then stop the proxy/synchronize regular copies, zero the verified 2,621,440 bytes of RAM, and restore original core/CPUs. Only a clean stop committed a new work checkpoint. A dirty marker or unapproved change caused the next startup to refuse, without automatically resetting to original NV.

**Original NV partitions and 0400 backups were never writable backends.**
There were no persist/fsc or SIM-data reads, expanded protected-partition permissions, or writebacks to original calibration.

## Actual state at this stage

- All five connection/startup trials were cleaned up; DSP offline, no WLAN, no default IPv4 route.
- Original core restored, diagnostic parameters gone, CPU limits restored; shared RAM zeroed/read back; working-copy checkpoint committed normally, with no dirty marker.
- `/etc/systemd/system/picasso-wifi.service` and diagnostic units existed; **picasso-wifi.service was disabled**. Failed units and each independent history were retained.
- Configuration was restored to normal priority/fallback order, `diagnostic_2g_only=false`, still limited to a 45-second probation. Do not manually remove the probation limit or enable the service to bypass disconnection; the isolated 2G comparison must not become the final policy.
- With explicit user consent, persistent credentials remained on the phone in `/var/lib/picasso-wifi/credentials/`, root0700 directory and root0600 files. The controller checked metadata only; native nmcli read through passwd-file. No key contents were collected or leaked via chat/argv/logs, and no host cache was read.
- **No further password entry was needed. Do not repeat the old entry script**; it would refuse to overwrite.

## Integrity and evidence

Full revalidation: read-only O_DIRECT hashes of the three original NV partitions and 0400 private backups matched.
The original 15,285 static files, complete installed #10 boot, seven preserved partitions, and six LUN GPTs were unchanged.
The host's canonical #8 image remained retained without overwrite.
Highest trial sample was 38.1°C; no temperature-limit breach, increased abort line, or increased transmit power.

214 offline tests: 213 passed, one optional QEMU test skipped.
Native lease/failure protections and real networking evidence were kept separate; host tests were not presented as stable device operation.
No reset-failed, deletion of historical failures, or overwriting of these failures as success.
Each result/cleanup/native network journal/code revision was separately saved.
Evidence directory: `out/wifi-autoconnect-20261028/`; credential payloads were not included.

## Blocker and next steps

The requested default automatic networking at boot was not yet complete; “enabled” could not be reported.
The next step was locating the approximately 18-second disconnection in ath10k/WCN3990 key operations/connection monitoring, using metadata-only observation if needed.
Do not blindly change calibration/firmware, fabricate capabilities, or disable regulatory/safety checks.
After fixing it, repeat a bounded trial, then enable and verify through a normal reboot.
Saved credentials should continue to be used directly by native nmcli rather than requested again or read by the controller.

This remained experimental headless Linux: charging/battery, RF behavior/safety, long-term thermal/memory/UFS/suspend/watchdog/power-loss recovery, and other peripherals had not passed acceptance.
This stage added no IPA/cellular data; complete silence of the proprietary shared modem firmware was not guaranteed.
