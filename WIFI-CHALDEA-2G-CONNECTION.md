# Chaldea-2.4G：WPA2 与 DHCP 已通过；监管域收尾验证后待重测联网（历史过程）

**后续 connect4 已同轮通过 WPA2/DHCP、实际SG限制、实时DNS及显式wlan0 HTTPS，HTTP200且证书验证通过。
本轮已完成并按约定断开/删除临时凭据/恢复模块及频率，不需再次录入或重复已用的一次性命令。
最新见 [WIFI-NETWORK.md](WIFI-NETWORK.md)。以下保留早期失败、修复和当时准备状态。**

本轮用户完成本地凭据录入并要求继续。固定 USB 位置、SG、本机永久 MAC、HT20 和 WPA2/CCMP 要求不变。
**已通过真实 WPA2 握手与 DHCP，但 DNS/互联网仍未验证，当前无线已停止。**

## 第一次完整激活：不是密码错误

- 只检查 `/run/picasso-chaldea-2g.passwd` 的普通文件/root/0600/单链接/大小元数据，不读取或显示其内容。
  native nmcli 通过 passwd-file 使用临时 PMK；无密码 argv、聊天或日志。
- 当前/永久 MAC 与本机 DMS 一致；初始 SG 实际信道限制审计通过；真实接口宽度 20 MHz。
- nmcli 激活成功、设备状态 100；supplicant 原始生命周期日志明确记录：
  **Key negotiation completed，PTK=CCMP、GTK=CCMP，CTRL-EVENT-CONNECTED**。
- NetworkManager 日志明确记录 DHCP 获得新租约，并完成 activated。这是实际 WPA2/DHCP 成功，不是仅扫描或 Open System auth。
- 紧接着的关联后监管复核失败：AP 的 Country IE 为 **CN**，内核实际全局域从 SG 变为 CN。
  检查拒绝接受外国全局域，没有把当前 2.4 GHz 信道可用等同于全 PHY 满足 SG。
- 因此在 DNS/HTTPS 测试之前主动中止、断开并删除临时凭据。失败单元和原始 CN 结果保留；不改用 CN、不修改 AP、regdb 或 regulatory 保护标志。

证据：`out/wifi-chaldea-2g-connect-20261028/connect-result.json`、`network-lifecycle.log`。
旧 `out/wifi-chaldea-2g-20261028/` 准备结果/校验集保持不变，新激活原始输出另有副本。

## SG 正常请求的无密码验证

不为了继续试验而提取缓存 PSK 或尝试假密码。新诊断先做 Open System auth，再用标准 RSN IE 宣告 WPA2/CCMP/PSK 能力并请求关联；
**不提供密钥、不回应四次握手、不安装 key、不授权数据端口**。这仅触发该真实 AP 的 Country IE，station 状态实际验证 authorized=no。

- 第一轮在无线初始化等待时采样到 **45.1°C**，立即按原 45°C 线中止并清理。该失败保留，未提高阈值或忽略传感器。
- cpu7-thermal 为主要热点。仅绑定控制器到 CPU0–3 不足以约束内核其他工作。
- 后续试验在确认 qcom-cpufreq-hw、CPU6/7 身份、硬件频率表、原 min/max 后，临时将两核 **scaling_max_freq 降为 1,094,400 kHz**。
  不修改 governor、最小频率、电压、热管理策略或射频功率；仍检查全部传感器。
- 第一次限频试验的即时读回断言失败，恢复检查也报错；旧结果 `cleanup_requires_attention` 不改。
  后续原生读回确认原上限，代码改为有限等待 QoS 读回稳定后验证，不把 sysfs write 成功当作限制已生效。
- 最终限频诊断实际收到 auth/assoc completion status 0；观察到 AP 真实 CN 域，然后发送正常 **`iw reg set SG`**。
  Linux 根据 `reg.c` 的 COUNTRY_IE → user-request 路径生成交集域 **98**，不是用户伪造/手工设置 98。
- 实际 PHY 的 **24 个启用的 20 MHz 信道**逐一通过 SG 频率/EIRP/DFS 子集审计，且数据端口保持未授权。
  这验证了关联后“再请求 SG 并检查真实交集”的收尾方法，不是只看标签或忽略 AP 信息。
- 该最终诊断最高采样 **37.4°C**。这是一次短时结果，不是长期热稳定/充电安全认证。
- 独立 ExecStopPost 验证 DSP/无线停止、2.5 MiB RMTFS RAM 清零、原 core 恢复、CPU6 原 **2,208,000 kHz** 和 CPU7 原 **2,400,000 kHz** 上限恢复。

原始独立诊断目录均保留：

- `out/wifi-sg-postassoc-20261028/`（45.1°C 中止）
- `out/wifi-sg-postassoc-capped-20261028/`（即时读回/恢复断言失败）
- `out/wifi-sg-postassoc-capped2-20261028/`（有限等待、真实 CN→SG/98 子集验证成功）

## 首次中止后的状态与当时重测计划（后续见下节）

- DSP offline、无 WLAN 接口/默认 IPv4 路由；sshd/firewalld active。临时凭据不存在，持久连接无 psk 键。
- 原 `/lib/modules` core 完整哈希不变，诊断参数消失；CPU6/7 原上限再次原生读回一致。
- 三个原 NV 分区 O_DIRECT 只读完整比对、0400 私有备份、原 15,285 个静态文件、boot、七个保留分区、六个 GPT 全部一致。
  没有读取 persist/fsc、写原 NV、修改主机 Wi-Fi/NAT/默认路由、启用 IPA/蜂窝数据，或 reset-failed。
- 离线测试 **181 项：180 通过，1 项可选 QEMU 跳过**。增加 AP CN 不能充当 SG、98 标签仍必须接受真实信道/功率/DFS 检查的回归。

下一轮脚本已准备但未执行：
`out/wifi-chaldea-2g-connect2-20261028/{connect-trial.py,cleanup-connect.py,run-connect.py,connect-controller.service}`。
它整合临时 CPU 上限及有界读回/恢复、WPA2 后的正常 SG 再请求/交集审计、实际 20 MHz、永久 MAC、DHCP/DNS/显式 wlan0 HTTPS。
仍保留 75 秒控制器预算/90 秒 PID-1 上限、45°C 中止、独立清理和临时凭据删除。整合路径尚待真实联网测试，不能用独立诊断替代。

最新 NV 工作副本 checkpoint 必须用：
`out/wifi-sg-postassoc-capped2-20261028/result.json:private_copy_final_hashes`，不是第一次激活或准备阶段的旧值。

密码已证实可用，但第一轮按承诺清理了文件，需要用户在本地终端**再录入一次同一密码**：

```sh
cd /home/vbox/droid
./picasso/tools/enter-chaldea-2g-password.sh
```

不要把密码发到聊天中；录入后回复“已录入”。此工具不启动无线。
正常重启仍回未改的已安装 #8；当前仍是临时 wifi2 #10，不是持久启用/生产稳定验收。

## 第二轮整合测试：SG、WPA2、DHCP、限频通过，检查工具中止

用户重新录入后执行了 connect2。实际 CPU 频率上限及恢复均通过，最高采样 **37.1°C**。
关联后正常重发 SG 并对内核 `98` 交集的 **24 个启用的 20 MHz 信道**审计通过；永久 MAC 和实际 20 MHz 保持。
同一轮 supplicant 日志再次有 PTK/GTK=CCMP、CONNECTED；NM 生命周期明确有 DHCP 新租约、activated。
**这次不是无线连接或 SG 失败**，但检查工具错误地假定存在每接口 wpa_cli 控制套接字：
`Failed to connect to non-global ctrl_ifname: wlan0`，故在 DNS/HTTPS 前提前中止。
NetworkManager 实际使用 supplicant D-Bus，此套接字不是必需配置。没有为了探测而开启 key dump 或读取 Network.Properties/PSK。

清理仍照常执行：凭据删除、无线/DSP 停止、原 core 和原 CPU 最大频率恢复，原 NV/master/静态文件/boot/保留分区/GPT 再次一致。
原始失败保留为 `out/wifi-chaldea-2g-connect2-20261028/connect-result.json`；不改成一次完整联网成功。
DNS/互联网至此仍未验证，也没有一直保留连接。

新 `tools/wifi-auth-evidence.py` 不要求控制套接字：仅检查本轮单调时钟截断后的原生 supplicant 日志、匹配同一 AP 的 CCMP PTK/GTK 和 CONNECTED。
调用者另行检查强制 RSN-only 配置、真实 SSID、活跃设备和 station authorized=yes；不读取秘密属性。
后来断开、旧日志、不同 peer/接口、TKIP 或混合 WPA 配置均拒绝。主机单元测试和原生隔离回放已通过：
只在旧试验清理前的真实时间片验证成功，清理后的断开快照明确拒绝；回放不算当前连接验收。

下一轮准备于 `out/wifi-chaldea-2g-connect3-20261028/`，采用此证据方式，仍保留全部 SG/限频/温度/永久 MAC/清理要求，整合网络路径尚未执行。
最新 NV checkpoint 改用 `out/wifi-chaldea-2g-connect2-20261028/connect-result.json:private_copy_final_hashes`。
离线测试 **186 项：185 通过，1 项可选 QEMU 跳过**。

为减少“录入后再等一轮聊天”的往返，新增明确命名的一次性试验入口：

```sh
cd /home/vbox/droid
./picasso/tools/test-chaldea-2g.sh
```

**此命令与仅录入工具不同：本地隐藏录入后会立即启动最多 90 秒的联网试验**，不是持久启用。
密码仍只进入手机的 root0600 tmpfs 文件，不进参数、聊天或日志。启动前会用固定 SSH host key 检查本轮目录未用、没有待用凭据，拒绝覆盖/重复试验。
PID-1 独立收尾在成功/失败时删除临时凭据、停止无线/DSP、恢复频率和模块；未启动试验前若手动中断，待用凭据仍可能留在 /run，需告知助手核对，勿反复覆盖。
原 `enter-chaldea-2g-password.sh` 仍只录入、不启动无线，行为未改。

请等待整个命令结束后再回复“已完成”；助手应先查看保存结果和服务状态，不盲目再执行同一 exclusive 控制器。
一次性入口已通过 shell 语法/守卫测试；当时用户交互执行及新的 DNS/HTTPS 网络结果尚待验证，后续见下节。

## 第三轮一次性测试：旧信道单次被动扫描未见目标

用户执行了一次性入口，控制器确实运行，助手没有重复启动。
该轮在 WPA2 激活之前因 `scan freq 2447 passive` 一次未见目标而中止，未调用 nmcli up；
临时凭据按约定删除，最高采样 36.8°C，独立清理恢复频率/core、停止 DSP/无线并清共享 RAM。
这不能判为密码错误、网络不存在、换信道或新的握手故障；前两轮已证明的 WPA2/DHCP/SG 成功不改。
原始结果保留在 `out/wifi-chaldea-2g-connect3-20261028/connect-result.json`。

随后不使用密码做限时发现：

- 所有合法启用 2.4 GHz 信道的三次被动扫描仍未发现精确 SSID，其他 BSS 数只作聚合，不保留邻居标识。
- 只向授权的 **Chaldea-2.4G** 定向主动探测、只用实际启用且可发起辐射的 2.4 GHz 信道：
  第二次发现目标，约 **-57 dBm，仍是 2447 MHz / 信道8**，Open System auth 第一帧 status0、应答成功。
- 这未证明 AP 隐藏 SSID 或某种特定驱动缺陷，也未观察到换信道。它证明不能依赖旧信道的一次被动扫描来否决连接。
- SG、HT20、设备当前/永久 MAC 校验通过；定向主动发现/认证最高采样37.1°C，结束后恢复原频率/core并停止 DSP/无线。
  没有启用 no-IR/disabled 信道、随机 MAC、调高功率或修改 AP。

发现证据分别在 `out/wifi-chaldea-2g-discovery-20261028/` 和
`out/wifi-chaldea-2g-active-discovery-20261028/`，各自失败/成功不覆盖。

新的 `tools/wifi-bss.py:active_2g_frequencies()` 从已经 SG 审计的真实 PHY 选择合法 2.4 GHz 可主动探测信道，
不绑定单一历史 AP 信道；disabled/no-IR/非2.4GHz/非标准频率均排除，无可用信道则拒绝。
单元测试和实际 PHY 原生离线回放通过。

新整合控制器为 `out/wifi-chaldea-2g-connect4-20261028/`，仍未执行有密码的完整网络路径：

- 最多两次覆盖合法2.4GHz的精确SSID主动探测；即使预扫描未见，也允许 NetworkManager 在25秒内仅尝试用户明确授权的同一 RSN-only/bg 配置。
  不把一次扫描空结果当作网络绝对不存在，也不会退到其他 SSID 或 WPA1。
- 该配置只新增客户端 `802-11-wireless.hidden=yes`，使已知SSID使用定向探测；这不是改AP设置或宣称AP确实隐藏。
  band bg、RSN/CCMP、永久MAC、不保存秘密、不自动连接、drop、IPv4等不变。
- 依旧使用真实握手日志/实时授权验证、不依赖wpa_cli套接字；保留关联后的正常SG再请求、实际交集审计、临时CPU上限、45°C中止及独立清理。
- 一次性入口 `tools/test-chaldea-2g.sh` 已指向此新 exclusive 试验，且在询问密码前先验证原生临时内核、DSP offline、温度低于40°C。
  仍须用户本地隐藏录入；**该命令录入后会立即启动限时试验**，请等整个命令结束再回复。

最新 NV 工作副本 checkpoint：
`out/wifi-chaldea-2g-active-discovery-20261028/result.json:private_copy_final_hashes`。
原 NV/master、15,285个静态文件、boot、七个保留分区、六个GPT再次一致，凭据不存在、原CPU频率/core恢复、当前无无线/默认路由。
离线测试 **190项：189通过，1项可选QEMU跳过**。DNS/互联网仍未验证，不能报告已经完成联网验收。
