# 屏幕进展：真实背光接管与内核到期关灯通过，待观察画面/音量上亮屏 / Display progress: real backlight handoff and kernel deadline shutoff passed; image and volume-up screen-on awaiting observation

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

**最新：用户回复A，已确认首段色条可见、确实关灯，但按键后未可见恢复。
已真机复现fbcon在unblank覆盖图案，修补为每次unblank后重绘再亮背光；新visual2准备完成但未目视验收。
请用 [DISPLAY-REDRAW.md](DISPLAY-REDRAW.md) 中的新命令，不重跑旧visual1。以下保留早期记录。**

**后续visual1已实际运行：Linux确实收到音量上，约1.10秒后进入按键亮屏分支，actual_brightness由0恢复64；
但用户报告没有亮屏，因此物理可见恢复未通过。第一段色条/是否确实关灯尚待明确，不能代用户填“通过”。
一次性命令已消耗，不要重跑；先检查已有结果并区分画面/背光链路问题。新复核：`out/display-visual1-review-20261028/result.json`。
下文保留原准备状态及当时操作说明。**

2026-10-28。仍运行已安装wifi2 #10；本阶段**没有刷boot、复位面板、启用原生DSI或重设供电参数**。
用户要求屏幕/自动息屏/三键唤醒；当前先完成安全的bootloader scanout背光接管。
**背光硬件控制已真机通过；可见画面和物理按键尚未确认，电源/音量下也尚未注册，不能称为全功能完成。**

## 已完成：只读核对真实PM8150L状态

`kernel/display/picasso-wled-audit.c`通过标准SPMI device/regmap接口，只读固定清单的WLED运行寄存器。
无任意地址参数、写接口、OTP/校准/分区读取；默认拒绝加载，需要read-only显式确认，限定Picasso/PM8150L/USID5/既有D800-D900节点。
PID1有界运行、独立卸载；snapshot root0400。

真机只读值确认：

| 项目 | 实际boot-state |
|---|---|
| WLED资源 | USID5，control0xd800，sink0xd900 |
| 有效灯串 | 0/1/2（0xd946=0x70） |
| 有效灯串满量程 | 0x09 = **22,500µA** |
| OVP | 0x07 = **28,000mV** |
| boost限流 | 0x05 = **1,400mA** |
| switching | 0x0b = 800kHz |
| MOD_A | enable0x80、source0（内部亮度）、12bit宽度 |
| MOD_B | 未启用 |
| 启动时亮度 | 0x03ff = 1023/4095，module gate已开 |
| 观察时故障状态 | fault/status均为0 |

这些与本机DTB9/DTBO19的electrical值一致。故可避免主线WLED全setup，直接保留真实boot配置控制亮度。
原始面板具体ID仍未知，不以此宣称已完成原生面板初始化。

## 已完成：受限背光handoff驱动

`kernel/display/picasso-wled-handoff.c`：

- 默认拒绝，需`confirm_handoff=1`；既有PMIC node/USID/资源及全组已核对electrical配置必须完全一致。
- **可写仅四个字节对应的亮度/控制位置**：MOD_A亮度LSB/MSB、MOD_A sync bit0、WLED module-enable bit7。
  不修改boost、OVP、LED电流、灯串/源选择、IRQ/保护、LCD bias、reset或DSI。
- 每次亮屏前重新校验固定配置和故障状态；配置变化/故障导致拒绝并关灯。
- 真实class `/sys/class/backlight/picasso-handoff`，trial max=256，硬件尺度4095；加载后低亮度64。
- 只读duration参数1..90秒；内核delayed_work独立到期关灯，**亮度写入不能续期**。到期后拒绝再亮，卸载fail-off。
- 当前只用于有界有人值守试验，没有常驻/开机启用或充电/长期安全认证。

真机已实际验证：

1. `brightness=0` → `actual_brightness=0`。
2. `brightness=64` → `actual_brightness=64`。
3. 不发关灯命令，等待内核5秒deadline，实际亮度自行变0。
4. 之后再写64，收到ETIMEDOUT（110），实际仍为0。
5. 卸载模块后再用只读模块复核：仅gate与亮度字节变化，**OVP/boost/电流/灯串/保护配置全部保留**。

这证明背光寄存器与硬件门控路径，不是用户已目视确认玻璃面板亮/暗，也不证明framebuffer对应实际scanout。
无需为这一阶段更换内核：模块与当前 `6.18.58-picasso-lts-wifi2` ABI匹配，仅依赖原有backlight class。
通用QCOM WLED全setup驱动仍未加载，原screen1候选也没有启动。

## 待用户实际执行：色条/关灯/音量上亮屏试验

本地交互终端：

```sh
cd "${REPO_ROOT}"
tools/test-screen-handoff.sh
```

按提示确认后观察手机，不用移动USB、输入密码或重新保存Wi-Fi凭据。

- 第一段应见低亮度灰底及红/绿/蓝横条，约15秒。
- 随后关灯。在提示的20秒窗口内**只短按一次音量上**。
- 收到真实音量上事件就立即再次亮屏；没收到则到时自动亮，日志会明确区分，不把定时亮屏算按键通过。
- 最后关灯并卸载模块。内核独立70秒deadline、PID1 90秒超时及独立ExecStopPost卸载，温度<40°C开始、>=45°C关灯。

**不要长按电源。本轮不测试电源/音量下，尚不能保证它们的Linux事件语义。**
命令完成后请反馈：是否看见三色色条、是否确实关灯、音量上短按后是否亮屏。
本次exclusive单元与持久consumed marker只能用一次；执行过/中断后先查既有结果，不盲目再跑。
用户尚未运行时，不把准备状态说成显示或真实键唤醒成功。

### 可视试验如何避免假证据

- 只打开`gpio-keys`且键位图**仅KEY_VOLUMEUP115**的真实evdev字符设备，exclusive grab；不注入事件或收集键盘/触摸。
- 原生ioctl已确认 `/dev/fb0` 是simpledrmdrmfb、1080×2400/stride4320、32bit RGB，**smem_start=0的DRM shadow**，不是物理映射。
- 只经fb_write/pwrite写入10,368,000字节合成图案；不读取旧像素、不用/dev/mem/mmap物理RAM、不截图用户内容。
- 这是bootloader scanout接管，不是MDSS/DPU/DSI重建；实际色条是否可见仍需本人观察。
- 试验模块/脚本哈希、实际kernel/FDT、温度和独占状态不匹配即拒绝；非允许亮度或过期即拒绝。

## 历史失败保留

- 只读模块v1把`of_get_child_by_name`参数错误地包含unit-address，返回ENODEV，未产生写操作；
  改为严格完整OF路径后新单元成功，旧失败不改。
- visual准备阶段把`is-enabled`的退出码当作是否开机启用，遇static=0断言失败；
  随后只检查现有文件/状态/target链接，确认static且inactive、无wants链接，未重跑独占staging/未启动可视试验。
- 没有reset-failed、删除旧journal或覆盖失败结论。

## 当前状态与边界

- 两个试验模块均已卸载，无backlight class owner；已用只读快照验证module gate关闭。
- 原fb blank=4、当前wifi2 #10、USB SSH/firewalld可用；WLAN/DSP仍离线，密码/NV未读取或修改。
- boot、15,285个原静态文件、七保留分区、六GPT再次验证未变；canonical #8恢复镜像保留。
- `picasso-display-visual1.service`是static、inactive、无默认启动链接；尚未执行、没有consumed marker。
- 244项离线测试：243通过、1可选QEMU跳过。原生低亮度/expiry结果与目视/物理按键验收分开。

仍待：目视色条/真实息屏及音量上，再完整匹配的按键DT/模块试验以注册电源和音量下；
之后才能验收三键+自动空闲策略和持久启用。原生DSI/实际panel ID、触摸/GPU、整机suspend/resume、充电/长期稳定仍另行处理。

证据：`out/display-handoff-20261028/`；前阶段[DISPLAY.md](DISPLAY.md)保留原准备/未点亮状态。

## English

**Latest update in this record: the user replied A, confirming the initial color bars were visible and the light actually turned off, but there was no visible recovery after the key press.
fbcon overwriting the pattern on unblank was reproduced on the real device; the fix redraws after every unblank before enabling the backlight. New visual2 preparation was complete, without visual acceptance yet.
Use the new command in [DISPLAY-REDRAW.md](DISPLAY-REDRAW.md), not the old visual1. The early record is preserved below.**

**Follow-up visual1 actually ran: Linux received volume-up, entered the key screen-on branch about1.10 seconds later, and actual_brightness recovered from0 to64.
But the user reported no screen-on, so physically visible recovery failed. Whether the initial bars were visible/the light truly turned off still awaited clarification at that point; “passed” cannot be supplied on the user's behalf.
The one-shot command was consumed; do not rerun it. Check existing results first and distinguish image versus backlight-chain problems. New review: `out/display-visual1-review-20261028/result.json`.
The original preparation state and operating instructions at that time follow.**

2026-10-28. Still running installed wifi2 #10. This stage **did not flash boot, reset the panel, enable native DSI, or reset power parameters**.
The user requested display/automatic screen-off/three-key wake; safe bootloader scanout backlight takeover was completed first.
**Backlight hardware control passed on the real device. Visible images and physical keys had not been confirmed, and power/volume-down were not registered; this cannot be called full completion.**

### Completed: read-only check of actual PM8150L state

`kernel/display/picasso-wled-audit.c` uses standard SPMI device/regmap interfaces to read only a fixed list of WLED runtime registers.
No arbitrary-address parameter, write interface, or OTP/calibration/partition reads. Loading is refused by default and requires explicit read-only confirmation, restricted to Picasso/PM8150L/USID5/existing D800-D900 nodes.
Bounded execution under PID1, independent unload, snapshot root0400.

Real-device read-only values confirmed:

| Item | Actual boot-state |
|---|---|
| WLED resources | USID5, control0xd800, sink0xd900 |
| Active strings | 0/1/2 (0xd946=0x70) |
| Active-string full scale | 0x09 = **22,500µA** |
| OVP | 0x07 = **28,000mV** |
| Boost current limit | 0x05 = **1,400mA** |
| Switching | 0x0b = 800kHz |
| MOD_A | enable0x80, source0 (internal brightness), 12bit width |
| MOD_B | Not enabled |
| Startup brightness | 0x03ff = 1023/4095, module gate already on |
| Fault state during observation | fault/status both0 |

These match the electrical values in this device's DTB9/DTBO19. This allows avoiding mainline WLED full setup and controlling brightness while preserving the actual boot configuration.
The original panel's specific ID is still unknown; this does not establish completion of native panel initialization.

### Completed: restricted backlight handoff driver

`kernel/display/picasso-wled-handoff.c`:

- Refuses by default; requires `confirm_handoff=1`. Existing PMIC node/USID/resources and the entire checked electrical configuration must match exactly.
- **Only brightness/control positions corresponding to four bytes are writable**: MOD_A brightness LSB/MSB, MOD_A sync bit0, and WLED module-enable bit7.
  No changes to boost, OVP, LED current, string/source selection, IRQ/protection, LCD bias, reset, or DSI.
- Revalidates fixed configuration and fault state before every screen-on; configuration changes/faults cause refusal and light-off.
- Real class `/sys/class/backlight/picasso-handoff`, trial max=256, hardware scale4095; low brightness64 after loading.
- Read-only duration parameter1..90 seconds. Kernel delayed_work independently turns the light off at expiry; **brightness writes cannot renew the deadline**. Reillumination after expiry is rejected; unload fails off.
- Used only for bounded attended trials at this stage, with no persistent/boot enablement or charging/long-term safety certification.

Actually verified on the real device:

1. `brightness=0` → `actual_brightness=0`.
2. `brightness=64` → `actual_brightness=64`.
3. Without issuing a light-off command, wait for the kernel 5-second deadline: actual brightness independently becomes0.
4. A subsequent write of64 receives ETIMEDOUT (110), with actual brightness still0.
5. After unloading, use the read-only module again to check: only gate/brightness bytes changed; **OVP/boost/current/strings/protection configuration were all preserved**.

This proves the backlight register and hardware gating path, not that the user visually confirmed the glass panel light/dark or that the framebuffer corresponds to actual scanout.
No kernel replacement was needed for this stage: the module matches current `6.18.58-picasso-lts-wifi2` ABI and depends only on the existing backlight class.
The generic QCOM WLED full-setup driver remained unloaded, and the screen1 candidate had not booted.

### Awaiting user execution at that stage: color bars/light-off/volume-up screen-on trial

Local interactive terminal:

```sh
cd "${REPO_ROOT}"
tools/test-screen-handoff.sh
```

After confirming the prompt, observe the phone without moving USB, entering a password, or saving Wi-Fi credentials again.

- The initial stage should show a low-brightness gray background and red/green/blue horizontal bars for about15 seconds.
- Then the light turns off. Within the prompted 20-second window, **short-press volume-up exactly once**.
- A real volume-up event immediately turns the screen on again; if none arrives, it turns on automatically at timeout. Logs distinguish these explicitly; timed screen-on is not key acceptance.
- Finally turn the light off and unload the module. Independent kernel70-second deadline, PID190-second timeout, and independent ExecStopPost unload; start below40°C, light-off at >=45°C.

**Do not long-press power. This round does not test power/volume-down; their Linux event semantics cannot yet be guaranteed.**
After the command, report whether you saw the three-color bars, whether the light truly turned off, and whether a short volume-up press turned it on.
This exclusive unit and persistent consumed marker are one-use only. After execution/interruption, check existing results rather than blindly rerunning.
Before the user has run it, preparation must not be described as successful display or real-key wake.

#### How the visual trial avoids false evidence

- Opens only a real evdev character device named `gpio-keys` whose key bitmap is **only KEY_VOLUMEUP115**, with exclusive grab; no event injection or keyboard/touch collection.
- Native ioctl confirmed `/dev/fb0` is simpledrmdrmfb, 1080×2400/stride4320, 32bit RGB, **a DRM shadow with smem_start=0**, not a physical mapping.
- Writes10,368,000 bytes of synthetic pattern only through fb_write/pwrite. No old-pixel reads, /dev/mem/mmap of physical RAM, or screenshots of user content.
- This is bootloader scanout takeover, not reconstruction of MDSS/DPU/DSI. Actual color-bar visibility still needs personal observation.
- Rejects mismatched trial module/script hashes, actual kernel/FDT, temperatures, or exclusivity. Rejects unapproved brightness or expiry.

### Historical failures preserved

- Read-only module v1 incorrectly included the unit-address in the `of_get_child_by_name` argument, returning ENODEV without writes.
  A strict complete OF path fixed it and a new unit succeeded; the old failure remains unchanged.
- Visual preparation treated the exit status of `is-enabled` as whether boot enablement existed, causing an assertion failure for static=0.
  It then checked only existing files/state/target links, confirming static and inactive with no wants links. Exclusive staging was not rerun and the visual trial was not started.
- No reset-failed, deletion of old journal, or overwrite of failure conclusions.

### State and boundaries at that stage

- Both trial modules unloaded, no backlight class owner; read-only snapshot verified module gate off.
- Original fb blank=4, current wifi2 #10, USB SSH/firewalld available. WLAN/DSP still offline; passwords/NV neither read nor changed.
- Boot, original15,285 static files, seven reserved partitions, and six GPTs reverified unchanged; canonical #8 recovery image retained.
- `picasso-display-visual1.service` static, inactive, no default startup link; at the original preparation stage it had not run and had no consumed marker.
- 244 offline tests:243 passed,1 optional QEMU skipped. Native low-brightness/expiry results are separate from visual/physical-key acceptance.

Still pending at that stage: visual color bars/real screen-off and volume-up, then a complete matching key-DT/module trial to register power and volume-down.
Only then can three-key+automatic idle policy and persistent enablement be accepted. Native DSI/actual panel ID, touch/GPU, whole-system suspend/resume, charging, and long-term stability remain separate work.

Evidence: `out/display-handoff-20261028/`; preceding [DISPLAY.md](DISPLAY.md) preserves the original preparation/not-illuminated state.
