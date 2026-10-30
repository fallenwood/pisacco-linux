# Chaldea-2.4G：真实 802.11 认证成功，等待本地凭据做 WPA2/联网验证

**后续第一次激活已真实通过 WPA2/CCMP 和 DHCP；但关联后 AP 的 CN 国家码触发监管复核中止，未验证互联网。
正常 SG 再请求/98 交集和临时 CPU 限频已用无密码关联独立验证；临时凭据已删除，待本地重新录入做整合重测。
最新见 [WIFI-CHALDEA-2G-CONNECTION.md](WIFI-CHALDEA-2G-CONNECTION.md)。以下为试验前准备快照。**

2026-10-28。用户指定新 SSID **Chaldea-2.4G**，确认这是 2.4 GHz 网络、密码与此前 Chaldea 相同。
手机仍固定 USB 连接，不要求移动。当前仅临时 wifi2 #10；不是已安装 #8 的持久 Wi-Fi 功能。

## 已经实际通过的部分

- 使用原有 HT20 保守试验 core 和固定 MSA SNOC 模块，未改动其字节或新刷 boot。
  参数只读、仅本机；PHY 无 HT40/VHT；实际 chanctx width **1 / 20 MHz**，vdev **11ng-ht20**。
- DMS → WLFW 每次重新提供同设备默认 MAC；wlan0 当前/永久地址一致，无随机地址，扫描和认证后不变。
- driver 默认域完成后施加用户指定 **SG**，实际有效信道/EIRP/DFS 审计通过；不以 AP 的 Country IE 代替用户地区。
- 从合法启用的 2.4 GHz 信道被动扫描中发现精确 SSID Chaldea-2.4G：
  **2447 MHz / 信道 8，约 -60 dBm**。AP RSN、pairwise/group 均支持 **CCMP + PSK**。
- 不使用密码的 IEEE 802.11 Open System Authentication：第一帧 firmware completion **status=0**；
  nl80211 明确收到 `status: 0: Successful`，内核明确记录 **authenticated**。
  这与此前 Chaldea 5 GHz 三次 status=3/认证超时不同，证明当前 2.4 GHz 目标的认证请求/应答路径已工作。
- **尚未关联、尚未进行 WPA2 四次握手，DHCP/DNS/互联网均未测试**。Open System auth 成功不能等同于 WPA2 连接成功。

试验峰值采样 44.8°C（热点为 cpu7-thermal），没有提高 45°C 中止线。
结束后独立 ExecStopPost 验证无线/DSP/代理停止、2.5 MiB RMTFS RAM 清零、试验 core 卸载、原 core 恢复且文件哈希不变。
原 NV 三分区完整 O_DIRECT 只读比对、0400 私有备份、原 15,285 个静态文件、boot、七个保留分区、六个 GPT 再次一致。
没有读取 persist/fsc、写原 NV、修改主机网络/NAT，或隐藏此前失败单元。

## 新网络的非秘密配置

已创建并读回 **picasso-Chaldea-2.4G**：精确 SSID、band=bg、永久 MAC、WPA2/RSN + pairwise/group CCMP、
psk-flags=not-saved、禁止自动连接、IPv4 DHCP、初测 IPv6 关闭、入站 firewalld drop。旧 Chaldea/USB 配置未改。

先前 Chaldea 临时密码文件已经按约定删除，不能恢复或读取主机保存密码。
同一 **passphrase** 的 PMK 派生以 SSID 为盐，Chaldea 和 Chaldea-2.4G 的 PMK 通常不同；不能复用旧 SSID 的 PMK。
更新后的本地工具仅允许这两个固定 SSID，各自使用不同 /run 文件；仍只接受本地 TTY 隐藏输入两次。
输入 64-hex 时意味着操作者显式指定 raw PSK，而不是允许工具猜测/提取别处的密码。

在你的本地交互终端运行（不要把密码发到聊天中）：

```sh
cd /home/vbox/droid
./picasso/tools/enter-chaldea-2g-password.sh
```

此命令使用固定 SSH host key/原有 SSH 私钥，选择 `--ssid Chaldea-2.4G`。
密码不进 argv、聊天或日志；只在手机 root0600 的 tmpfs 文件 `/run/picasso-chaldea-2g.passwd` 暂存等效 PMK。
文件 O_EXCL|O_NOFOLLOW、不能覆盖已有文件。它不会启动无线或发起连接。
录入后回复“已录入”。**当前结果是录入前快照：凭据尚不存在。**

## 下一轮已准备、尚未执行的连接试验

`out/wifi-chaldea-2g-20261028/{connect-trial.py,cleanup-connect.py,run-connect.py,connect-controller.service}`
通过语法检查，但还没有因缺少本地凭据而执行。每个改动路径仍需真机实际验证，不能拿此处准备状态代替结果。

- 使用本轮最新 `result.json:private_copy_final_hashes`，不使用原 NV master 或老扫描 checkpoint。
- 先只检查凭据存在/类型/所有者/模式/大小，不读取其内容；由 native nmcli `passwd-file` 读取。
- 开始温度 <40°C、连续等待采样、45°C 中止；PID-1 RuntimeMaxSec=90，控制器预算75秒、独立 ExecStopPost、无自动重试/恢复。
- 下一轮控制器及子进程计划绑定 CPU0–3（原生 policy0 为 CPU0–5、1.8048 GHz cluster），减少诊断工具压到 2.4 GHz CPU7 的额外热量；
  不修改 governor/电压/温度阈值，也不忽略 CPU7 或其他传感器。实际 affinity 和效果须在下一轮验证。
- 仍重新验证 HT20、DMS 当前/永久地址和实际 SG。关联后再次审计 SG 和实际 20 MHz，防止仅靠初始化标签推断。
- 验证 WPA2/CCMP、DHCP、wlan0 路由、drop 防火墙、新 DNS 事务及显式绑定 wlan0 的 HTTPS（验证证书，不用代理/主机 NAT）。
- 有密码的阶段关闭 MAC/WMI/key dump 类调试，仅保留非秘密的 QMI 状态和受限 auth/assoc completion 观测。
- 无论成功/失败，断开新配置、恢复 unmanaged、删除临时凭据、卸载无线/诊断 core、停止 DSP/代理/TFTP、清共享 RAM，并复核完整性。
  成功也仅是限时联网测试，不自动持久化或留无线无人值守运行。

离线测试 **179 项：178 通过，1 项可选 QEMU 跳过**；新测试覆盖同密码按新 SSID 重新派生、目标白名单和新固定 SSH/TTY wrapper。

证据：`out/wifi-chaldea-2g-20261028/summary-result.json`、`result.json`、独立清理/原始完整性结果和 `secret-entry-ready.json`。
先前失败保留在 [WIFI-TX-DIAGNOSTICS.md](WIFI-TX-DIAGNOSTICS.md)。电源/充电、宽信道、长期稳定性等仍未验收。
