# 固定 USB 位置、弱信号下的 Wi-Fi TX 诊断

**后续用户指定不同的 SSID Chaldea-2.4G。新目标在 -60 dBm、2447 MHz/20 MHz 下已收到真实认证成功应答，
不再是所有目标均认证失败；但 WPA2/关联/联网尚待本地重新录入凭据后测试。
最新见 [WIFI-CHALDEA-2G.md](WIFI-CHALDEA-2G.md)。本页保留此前 Chaldea 目标的诊断结论。**

用户说明手机不能移动，接受现有弱信号。**不再把移动手机作为继续诊断的前置条件。**
仍限定 SG、SSID `Chaldea`、本机 DMS 默认 MAC、不随机。以下是真机限时试验，
结论仍是 **802.11 认证未通过，尚未关联/DHCP/DNS/联网**，不是低速联网成功。

## 新证据

1. **管理帧完成状态观测模块实际加载并执行。**
   - 单独编译 ath10k_core，仅增加默认关闭、只读的 `picasso_mgmt_status`。
     日志仅有 frame control、descriptor、固件原始 status、ACK RSSI 原字段和长度；
     不记录地址、帧内容、密码、NV，也不改变原有成功/失败处理。
   - Picasso + SNOC 双重作用域。三个 auth 帧均 `fc=00b0`、长度 30、固件返回 `status=3`。
   - ath10k 对所有非零 status 清除 ACK 标志；因此这里没有成功 ACK 报告，
     不只是 nmcli 等待超时。但缺少匹配的厂商枚举定义，**不把 3 擅自命名为某种特定错误**。
     ACK RSSI 原字段 0 也不作为实际信号强度解释。
   - 信号约 -85 dBm。观测模块 SHA256：
     `27083cef2fa3bd62c0935c539d740d61b9a773a5d919a42dfd4b0b75e86dd15e`。

2. **运行时省电 on/off 对照没有改善。**
   - `iw` 初始显示 on，随后设置 off 并读回；两次均三帧 status 3，认证超时。
   - MAC 调试信息表明两次认证的 vdev 启动后其实都已发送 psmode disable。
     因此这个用户层开关没有改善，不证明所有固件省电问题都被排除。

3. **20 MHz 保守能力限制已实际验证，但没有修复认证。**
   - 调试发现原认证 vdev 使用 160 MHz；先前监管审计只覆盖 20 MHz，不将其扩展为宽信道验收。
   - 新的独立 core 额外提供默认关闭、只读、仅本机 SNOC 的 `picasso_ht20_only`：
     只移除 HT40/SGI40 和 VHT 能力。不更改 regdb、信道保护标志、功率、天线、SCM/SMMU、BDF/校准或固件。
   - 参数 Y、PHY 无 HT40/VHT；实际 chanctx width **1（20 MHz）**，vdev 为 **11na-ht20**。
     同次 SG 有效信道/EIRP/DFS 审计和当前/永久 MAC 校验通过。
   - 仍在 5240 MHz、约 -85 dBm 收到三次 status 3；认证超时，不能把宽度当作已确认根因。
   - HT20 core SHA256：`5bc0036228c2d076c89f772269edd9bb5b7217c50d51bc380dcb99f026968b76`。

4. **同名 2.4 GHz 网络当前未发现。**
   - 仅扫描 SG 实际启用的 2.4 GHz 信道，三次被动扫描未发现精确 SSID Chaldea。
   - 没有向其他 SSID 发送认证、没有自动连接其他网络，也不把短扫未见等同于网络绝对不存在。

## 扫描解析修复

之前实验脚本使用 `split('BSS ')`，会把记录内部的 `BSS Load:` 或
`Overlapping BSS scan params:` 当作新记录，导致目标的 HT/VHT 信息截断、聚合记录数可能高估。
旧证据不改；其此类聚合计数不再作为准确 AP 数量使用。

新增 `tools/wifi-bss.py` 按 **行首 `^BSS `** 分割，只保留授权目标的完整记录。
现在能看到 AP 的完整 HT/VHT/HE 信息，包含 160 MHz 广告；因此早先截断输出不代表 AP 没有 HT/VHT。
4 个回归测试覆盖内部 BSS 标题、精确 SSID 过滤、多频段和空/非法输入。

## 清理与完整性

- 每次使用独立 PID-1 单元，45 秒上限，DSP 手动启动、自动恢复关闭；正常控制器另有 35 秒预算。
  等待期间检查温度/时限；启动要求低于 40°C，中止阈值不变为 45°C。
  本组观测最大采样 **44.4°C**，未以接受弱信号为由提高温度或发射功率。
- 独立 ExecStopPost 停止无线、DSP、私有 RMTFS/TFTP，清零经验证的 2.5 MiB 共享 RAM，
  卸载诊断 core，重新加载原 installed core。四次收尾均验证成功。
- `/lib/modules` 原 core 一直未替换，完整哈希保持
  `ed2f66c7646c43c4b3106bed4c8a33e811d81a7aa1207775f4fabeb350900862`；诊断参数均已消失。
- 诊断不需密码。前轮 `/run` 临时凭据仍不存在，持久连接无 psk 键。
  最终 DSP offline、无 WLAN 接口/默认 IPv4 路由；USB SSH/firewalld active，温度回落约 36.4°C。
- 三个原 NV 分区完整 O_DIRECT 只读比对和 0400 原始私有备份一致；
  原 15,285 个静态文件、完整 boot、七个保留分区、六个 GPT 再次通过。
  没有读取 persist/fsc、写原 NV、修改主机 Wi-Fi/NAT、开启 IPA/蜂窝数据，或隐藏历史 failed units。
- 主机临时更改的 C 源文件和原 core 工件已恢复，canonical #8 boot 不变。
  公共诊断补丁在 `kernel/diagnostics/`，**不加入正常 patch series**；仅复现实验，不是默认修复。
- 离线测试 **176 项：175 通过，1 项可选 QEMU 跳过**。这些不能覆盖或替代失败的真机连接结果。

## 后续方向

不要求移动手机，不立即要求重输密码。后续只在限定信号/温度下核对管理帧 WMI ABI、
FW TX 路径和 AP MAC 准入；不猜校准文件、不伪造 ACK，不扩大受保护分区读取。
若用户愿意指定一个已有的 2.4 GHz SSID，可另行测试其较强传播条件；**未获指定前不关联其他 SSID**。
若需要 USB 共享主机互联网，属于另一种网络方案，必须先征得授权，不能当作原生 Wi-Fi 已修复。

最新 NV 工作副本 checkpoint：
`out/wifi-24ghz-20261027/result.json` 的 `private_copy_final_hashes`，不能再用早期扫描/主备份哈希。

独立证据目录（各自新结果，不覆盖旧失败）：

- `out/wifi-tx-status-20261027/`
- `out/wifi-powersave-ab-20261027/`
- `out/wifi-ht20-20261027/`
- `out/wifi-24ghz-20261027/summary-result.json`（本组收尾汇总）

前序连接记录：[WIFI-CONNECTION-TEST.md](WIFI-CONNECTION-TEST.md)。
