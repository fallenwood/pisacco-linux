# 屏幕单键验收：音量上恢复可见色条通过

**后续用户授权“不要整机休眠，现在这样就行，写入手机”：已按15秒idle＋音量上策略写入租约模块和开机服务，重启前检查通过。
正常重启曾因宿主USB静态地址丢失/agent sudo受限阻塞；用户恢复后，开机服务/真实按键与idle日志/租约/完整性均复核通过，见 [DISPLAY-PERSISTENT.md](DISPLAY-PERSISTENT.md)。
不再扩大到电源/音量下或整机休眠。以下保留本次单键验收时的未持久化状态。**

2026-10-28。当前仍为已安装 `6.18.58-picasso-lts-wifi2 #10`，未刷boot/DTBO、未换内核、未改供电/面板reset/原生DSI。

## 实际通过的范围

用户在本机运行独占visual2后明确回复：**“按音量上后，三色色条重新出现”**。
结合当前boot内保存的原生结果，确认：

- 收到真实KEY_VOLUMEUP，走按键恢复分支，不是20秒后的定时亮屏。
- 恢复顺序为fb0解除空白→完整重绘合成色条→背光64；画面确实重新可见。
- 实际亮度读回依次64→0→64→0，恢复路径有完整重绘记录。
- off阶段开始至完成按键亮屏阶段约2.542秒，**包括用户反应与重绘，不是测得的纯按键延迟**。
- 本次最高采样33.4°C；最终actual_brightness=0，模块卸载成功、单元inactive/success。
- 源码/模块SHA、当前config/FDT均与准备时绑定值一致；原生脚本未记录用户眼睛的反馈，
  其`physical_visual_confirmed=false`原始字段**不改写**。本验收层单独记录用户确认。

visual1中用户此前已确认首段色条可见、确实关灯，但按键后没有可见恢复。
此历史失败保留；新visual2通过不把visual1改成成功。覆盖画面的fbcon原因和修补详见[DISPLAY-REDRAW.md](DISPLAY-REDRAW.md)。

## 当前状态

试验结束后两个诊断/背光模块均卸载，无backlight class owner；fb blank读取为0，
但不能用此推断LED亮着，结束前已读回实际亮度0并卸载fail-off。
visual2 unit为static、inactive、无开机target链接；consumed marker与一次性host日志保留。
**不要再次运行visual1/visual2命令，也没有将任何屏幕服务常驻或开机启用。**
USB SSH/firewalld可用，默认Wi-Fi仍disabled/DSP不启动。未读取NV/密码或写分区；本阶段只收集现有结果和保存普通文件。

## 尚未通过

- **音量下和电源键**：当前仍无对应真实input注册/三键物理验收。
- **60秒空闲自动息屏**：本轮为固定15秒显示/息屏窗口，不是完整idle策略验收。
- **持久/开机屏幕服务**：未启用；70秒内核fail-off和90秒PID1界限仍只用于试验。
- native DSI/panel初始化、实际panel ID、触摸/GPU、整机suspend/resume、充电/长期稳定均未认证。
- 这是短按屏幕唤亮，不是整机休眠唤醒；不测试或承诺阻止硬件长按复位。

## 下一阶段

准备与本机ROM核对的电源/音量下PON节点及输入试验，先审核驱动probe对PON配置的写操作与logind短按关机语义，
避免测试中误关机。使用隔离临时启动/匹配模块，保留默认#10、USB SSH、恢复路径，不直接持久刷写。
完整三键真实事件覆盖后，再验收60秒idle、屏幕off/on顺序和独立fail-off，最后才讨论常驻。

证据：`out/display-visual2-acceptance-20261028/`；准备目录及原始日志保留在`out/display-visual2-20261028/`。
