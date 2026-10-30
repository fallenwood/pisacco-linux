# 屏幕单键验收：音量上恢复可见色条通过 / Single-key display acceptance: volume-up restores visible color bars

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

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

## English

**Follow-up authorization: “不要整机休眠，现在这样就行，写入手机” (“Do not suspend the whole system; this is fine as it is; write it to the phone”). The leased module and startup service were installed with15-second idle+volume-up policy, and pre-reboot checks passed.
Normal-reboot verification was initially blocked by loss of the host USB static address/agent sudo restrictions. After the user restored it, startup service/real-key and idle logs/lease/integrity were all checked successfully; see [DISPLAY-PERSISTENT.md](DISPLAY-PERSISTENT.md).
Do not broaden to power/volume-down or whole-system suspend. The not-yet-persistent state at this single-key acceptance is preserved below.**

2026-10-28. Still installed `6.18.58-picasso-lts-wifi2 #10`; no boot/DTBO flashing, kernel replacement, power/panel-reset/native-DSI change.

### Scope actually passed

After running exclusive visual2 on this device, the user explicitly replied: **“按音量上后，三色色条重新出现”** (“After pressing volume-up, the three-color bars reappeared”).
Together with saved native results from the current boot, this confirms:

- Real KEY_VOLUMEUP received; the key-recovery branch ran, not automatic screen-on after20 seconds.
- Recovery order: fb0 unblank→complete synthetic color-bar redraw→backlight64; the image really became visible again.
- Actual brightness read-back sequence64→0→64→0, with a complete redraw record in the recovery path.
- About2.542 seconds from off-stage start to completion of key-screen-on stage, **including user reaction and redraw, not a measured pure key latency**.
- Peak sampled temperature33.4°C; final actual_brightness=0, module unloaded successfully, unit inactive/success.
- Source/module SHA and current config/FDT matched preparation-pinned values. The native script did not record the user's visual feedback;
  its original `physical_visual_confirmed=false` field is **not rewritten**. This acceptance layer records user confirmation separately.

For visual1, the user earlier confirmed initial bars and actual light-off, but no visible recovery after the key press.
That historical failure remains; visual2 passing does not make visual1 successful. fbcon's overwrite cause/fix: [DISPLAY-REDRAW.md](DISPLAY-REDRAW.md).

### State at this stage

After the trial, both diagnostic/backlight modules were unloaded with no backlight class owner; fb blank read0.
That does not imply the LEDs were on: actual brightness0 was read back before completion and unload failed off.
visual2 unit static/inactive with no startup target links; consumed marker and one-shot host logs retained.
**Do not run visual1/visual2 commands again. No screen service had been made persistent or boot-enabled at this stage.**
USB SSH/firewalld available; default Wi-Fi still disabled and DSP not started. No NV/password reads or partition writes; this stage only collected existing results and saved ordinary files.

### Not yet passed at this stage

- **Volume-down and power key**: no corresponding real input registration/three-key physical acceptance yet.
- **Automatic screen-off after60-second idle**: this round used a fixed15-second display/off window, not acceptance of the complete idle policy.
- **Persistent/startup screen service**: not enabled then; kernel70-second fail-off and PID190-second limits remained trial-only.
- Native DSI/panel initialization, actual panel ID, touch/GPU, whole-system suspend/resume, charging, and long-term stability not certified.
- This is short-press screen illumination, not whole-system suspend wake. Hardware long-press reset prevention is neither tested nor promised.

### Next stage as planned then

Prepare power/volume-down PON nodes and input trials checked against this device's ROM. First audit PON-configuration writes during driver probe and logind's short-press shutdown semantics,
avoiding accidental shutdown during testing. Use isolated temporary boot/matching modules, retain default #10, USB SSH, and recovery path; do not directly flash persistently.
After complete real three-key event coverage, accept60-second idle, screen off/on order, and independent fail-off; only then discuss persistence.

Evidence: `out/display-visual2-acceptance-20261028/`; preparation directory and raw logs preserved in `out/display-visual2-20261028/`.
