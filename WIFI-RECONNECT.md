# Wi-Fi掉线自动重连已持久安装：实测3次恢复，当前次数耗尽离线

> 后续用户要求不要关闭wlan，默认已切换为[常驻真实网卡UP模式](WIFI-RADIO-UP.md)。本页重连服务现disabled/failed，预算/失败保持；新radio服务enabled/active，只保持UP且无自动关联，不能再按本页旧服务判断是否运行。以下是重连阶段历史，特别是“WLAN absent/dirty absent”不是新radio活跃状态。

> 后续USB插拔未发生手机重启。用户另请求一次试连，独立手动session `91b3f9f767c3`短暂恢复2.4G/DHCP/DNS/HTTPS后又失联，已安全清理。自动预算文件SHA不变，没有删除/刷新预算或重跑旧failed unit；这是一次新的明确人工授权，不是自动第五轮。证据`out/wifi-attended-20261030T012324Z/`。

用户请求：**“开启掉线自动重连, 并且写入手机”**。
仅写入普通XFS程序/状态文件和systemd配置；没有刷boot、重启/关机、休眠、改变SELinux、NV原分区/masters、凭据或主机网络。

## 已安装及原生结果

- 新默认服务：`picasso-wifi-reconnect.service`，已enabled；本轮实际运行后次数耗尽，当前failed/exit-code，已安全退出。
- 程序：`/opt/picasso-wifi-reconnect/wifi-reconnect-service.py`，root0400。
- 沿用**未改字节**的已验收worker `wifi-auto-service.py`，SHA256=`428495f9e7007d9728b0df9887b630c62013622b9137af39d4afcf532191b725`；
  其config/probation gate、四FD后端、固件/BDF、模块、监管域和MAC逻辑均不修改。
- 原`picasso-wifi-auto.service`改为disabled，但原failed/exit-code保留；更早原`picasso-wifi.service`仍disabled/failed/watchdog。
  没有reset-failed，也没有重跑已消耗的旧诊断。
- 新控制器沙箱先完成**仅文件/安全清理状态/manager bus**原生检查，不开启RF、不消费重试预算。

随后真机自然失联触发了全部三次自动重试，**没有人为断网或注入失败**：

| 本boot轮次 | worker session | 本轮结果 |
|---|---|---|
| 初连 | `faba751a60a2` | Chaldea超时→2.4G成功，之后真实fallback link loss；完整安全清理 |
| 自动重试1 | `d82c43d090bf` | 同顺序恢复联网，之后再次真实失联；完整安全清理 |
| 自动重试2 | `ce38bb2f8098` | 同顺序恢复联网，之后再次真实失联；完整安全清理 |
| 自动重试3 | `7490c72abd88` | 同顺序恢复联网，曾connected_guarded/Chaldea-2.4G/192.168.1.64，随后也fallback link loss；完整安全清理 |

配置退避10/30/60秒；原生持久事件中的backoff→下轮启动intent实际为**11.292/31.291/61.281秒**，包括额外清理确认与冷启动检查，不少于规定间隔。
每次均验证DHCP、新wlan0绑定DNS和证书HTTPS200、永久MAC/实际20MHz/SG信道EIRP/DFS/drop区域。
**当前本boot初连＋3次名额已经全部用完，最后一轮也再次掉线，监管器已按预算规则停止**，错误`Initial plus3 retries exhausted for this boot`。
当前WLAN absent、DSP offline、CPU/core恢复、checkpoint提交、dirty absent，最终独立owned-child清理通过；没有第五轮，也未删除或重置预算。
之前第四轮在线快照仍是当时的实测记录，不是当前在线状态。

所有历史worker failed unit和原生result/cleanup仍保留，不把失败改名为成功。
三次断线后的安全清理都通过：DSP offline、WLAN absent、proxy/TFTP停止、2,621,440字节共享RAM清零、原core/CPU上限恢复、工作副本checkpoint提交。
最后一轮活跃时dirty标记曾属于正在工作的session，**当时不能拿上一轮cleanup.json宣称当前已清理，也不能删除live dirty**。
最终第四轮已退出，当前cleanup.json才属于该轮，native安全清理正常提交checkpoint并消耗自己的生命周期dirty标记；agent没有手工删除任何marker。

## 有界恢复规则

每boot最多4个worker会话，包括初次连接；剩余名额不是无限重启。
退避后先重新核验：

1. 前轮unit必须是exit-code1，且原生精确错误仅限：
   - `Fallback link lost; no restart loop`
   - `Both authorized SSIDs failed bounded activation`
   - `Runtime fallback failed`
2. 没有unsafe NV stop；前轮记录温度峰值<45°C，cleanup全部必要字段成功。
3. 当前dirty不存在、DSP离线、WLAN卸载、旧proxy/TFTP不活跃、CPU6/7最大值恢复、原core匹配。
4. 三份**普通工作副本**owner/mode/nlink/大小/不别名且摘要与最新checkpoint吻合；只在手机内核验，不读取或恢复原NV/masters。
5. 所有可读传感器有效；连续三次<40°C，ready前再查<40°C；最多等待120秒降温。

watchdog、timeout、OOM、信号、DSP crash、热限、监管/MAC/内存/副本校验错误或其他未知错误均不重试，即使部分清理成功。
运行温度仍45°C中止，不提高任何阈值。普通失联只是恢复逻辑的入口，不会绕过内核/工作副本边界。

本轮supervisor全阶段记录峰值**43.4°C**，首个外部观察器采样峰值39.1°C，各worker的连接/监控记录峰值另存。
这些采样时点不同，不用低的覆盖高的；43.4°C低于45°C中止线，不代表RF启动时43.4°C。
当前代码每次启动均执行上述<40°C门槛，但各次具体起始温度未独立持久化，**不从阶段峰值或后测值反推起始读数**。

## 所有权、独立退出与预算

- 每次创建全新`picasso-wifi-session-<boot8>-<uuid12>.service`，不重启先前failed unit；不使用Restart=always或--collect。
- worker仍notify/watchdog8/TimeoutStart180/Stop45/Memory256MiB/CPU0–3、独立ExecStopPost，backend仍精确worker PID对象/3秒SCM_CREDENTIALS租约。
- worker通过BindsTo＋After绑定supervisor。supervisor自己的watchdog8、Restart=no、独立ExecStopPost、Stop75、Memory128MiB、空capability、AF_UNIX、禁止reboot/module/raw-io等调用保持。
- supervisor的READY只说明**监管器就绪**，不代表WLAN已连；在线必须看budget phase、当前worker与真实关联。
- 启动intent在任何worker创建/启动之前持久化。保存独占生成的unit名、文件dev/inode/内容及worker session；清理只停止已证明归属的本boot子unit。
  未创建或文件身份不符的计划名不能拿来停止未知服务。
- `/var/lib/picasso-wifi-reconnect/boots/<boot-id>.json`保存预算；`events/`保存每阶段不可覆盖证据和unit定义。
  不因稳定一段时间、服务停止/启动而清零。普通operator clean stop可在剩余预算内续用；安全错误、耗尽或不完整所有权需人工检查，不自动重放。
- `/run/picasso-wifi-reconnect/session.json`是监管状态；真实联网/清理记录仍在`/run/picasso-wifi/`和`/var/lib/picasso-wifi/history/`。

## 日常操作（手机内）

```sh
sudo systemctl status picasso-wifi-reconnect.service
sudo systemctl stop picasso-wifi-reconnect.service
# 关闭开机自动连接/重连：
sudo systemctl disable picasso-wifi-reconnect.service
```

不要同时启动旧auto/wifi服务；不要手工删预算/dirty/旧marker，不用重启或原NV复位来绕过本boot次数和安全错误。
若要改变次数或退避，需另行明确策略并保留旧证据，不给未经审核的无限重连。

## 不变边界与未完成项

底层beacon-miss/接收稳定性**没有修复**，本次三次自然失联正好再次说明这一点。实现并实测的是受保护恢复，不是稳定链路。
LAN192.168.1.0/24 TCP22和新公钥配置保留；另一台机器使用该私钥的SSH登录仍未实测。
SELINUX配置仍disabled但实际内核仍Permissive；当前boot仍原#10/FDT62ac，已写入power镜像待下次启动，**本次没有重启验收**。
两个精确FDT及config/Image/ABI的既有白名单不变。屏幕tty1/15秒idle/音量上/内核租约保持，不增加整机休眠。
不声明充电、RF安全、长期热/内存/UFS/掉电或保持关机验收。

证据：`out/wifi-reconnect-20261030T003551Z/`。
离线359项，358通过、1可选QEMU跳过；另有真实三次自然失联→安全清理→退避→新PID1 worker恢复联网的证据，不把模拟测试当原生实测。
本阶段只验证新普通文件/服务安装与原生运行，没有重新读取原NV或重新摘要保护分区；最近全盘/授权公钥例外检查仍见[LAN-SSH.md](LAN-SSH.md)。
