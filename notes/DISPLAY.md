# 屏幕/自动息屏/三键亮屏：准备完成，真实背光与原生DSI仍阻塞（阶段记录） / Display, automatic screen-off, and three-key screen-on: preparation complete; real backlight and native DSI still blocked (stage record)

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

**后续已完成本机只读WLED boot-state核对及受限背光handoff驱动，真机低亮度0/64、内核到期关灯和禁止过期再亮通过。
新的可视色条/音量上试验已准备、尚未执行，见 [DISPLAY-HANDOFF.md](DISPLAY-HANDOFF.md)。
仍未目视确认画面/按键，电源与音量下未注册；以下保留早期准备状态。**

2026-10-28，用户暂缓Wi-Fi掉线排查，要求先实现屏幕驱动、自动息屏及音量键/电源键唤醒。
**当前没有完成屏幕点亮或物理按键亮屏验收，仍运行已安装wifi2 #10；没有刷boot、启用背光或常驻息屏服务。**
本阶段的“息屏/唤醒”范围是屏幕与背光，不是整机suspend；不把黑屏、wakeup-source属性或模拟事件当作休眠/唤醒成功。

## 真机现状

- `/proc/fb`: `simpledrmdrmfb`，1080×2400，32bpp、stride4320，bootloader splash保留区内。
  这是bootloader scanout接管，不是原生MDSS/DSI驱动或面板初始化成功。
- `/sys/class/backlight`没有设备，内核未配置QCOM WLED；原生DRM_MSM关闭，DSI/GPU也关闭。
- 当前只注册一个`gpio-keys`输入设备，具有音量上KEY_VOLUMEUP；PM8150电源键和音量下未注册。
  尚未观察用户实际按键事件；不能把设备注册等同于物理键工作。
- 已验证既有fb0 sysfs接受写入，但`blank=4`第一次会因fbcon递归归一化读成1。
  第一次严格读回断言失败原样存档；复测记录0→0、4→1，最后恢复原blank=4。
  这只是虚拟blank行为，不证明背光关闭/屏幕可见。

## 从本机ROM DTB9+DTBO19确认的硬件

输入固定为本机已审计的merged DTB，SHA256
`f75e1bf1af964147ee929b97a6b857516a4591b7bc096fe31e73d9ed8b8dc6f6`，不是其他手机的参数。

| 功能 | 实际factory wiring/值 |
|---|---|
| WLED5 | PM8150L USID5，control0xd800、sink0xd900 |
| 灯串 | string-cfg0x7，主线enabled-strings 0/1/2 |
| LED满量程电流 | 22,500µA |
| OVP | 28,000mV，不可默用主线默认32.5V |
| CABC | select1，12bit亮度范围0..4095 |
| 电源 | PM8150 USID0 / PON0x800 / IRQ0，KEY_POWER116，双边沿 |
| 音量下 | 同PON / IRQ1，KEY_VOLUMEDOWN114，双边沿 |
| 音量上 | PM8150L USID4 GPIO5，active-low，KEY_VOLUMEUP115，wakeup |

本机ROM同时包含`xiaomi 38 0a 0a`、`36 02 0c`、`37 02 0b`、`37 02 0a`等面板。
静态factory dsi-default-panel指向**sw43404 WQHD AMOLED**节点，不能作为实际屏幕身份；
社区参考DTS则写了`mdss,g7a-37-02-0a-dsc`，但没有本机当前实际panel ID证明。
此前原Android /proc/cmdline读取被拒绝，现有mainline live FDT又是shim提供的静态树，不能冒充原Android live选择。
因此**不猜具体面板、不发送另一型号初始化指令，不读persist去猜身份**。

## 新代码和隔离构建

### 硬件准备DTS / config

- `dts/sm7250-xiaomi-picasso-screen-handoff.dts`：继承原headless保护区；
  按本机IRQ补PON电源/音量下，保留音量上；提供准确WLED electrical properties，default-brightness=0。
  **WLED仍disabled，MDSS/DPU/DSI/GPU/LCDB仍disabled**，不让probe静默覆盖未核准的boost/供电设置。
- `kernel/picasso-screen-handoff.config`：配置输入/帧缓冲/主线WLED准备；隔离构建另行设置screen1模块版本，非原生DSI实现。
- `tools/audit-display.py`：固定vendor DTB身份、PMIC/IRQ/GPIO/亮度范围/保留内存/帧缓冲跨度，
  拒绝其他板参数、未核准背光probe或原生DSI启用；输出actual_panel_identity_proven=false。

真实LLVM AArch64隔离构建产物在 `out/display-preparation-20261028/`：

- `Image-screen1`，distinct release **6.18.58-picasso-lts-screen1**。
- `kernel-screen1.config`、`screen-handoff.dtb`、`qcom-wled-screen1.ko`。
- 这是内核Image/选定模块，不是已打包/临时启动/刷入的Android boot镜像；**完整新版本模块树未构建完**。
- 首次Image+全部modules构建600秒超时保留；随后Image单独恢复成功。
  首次独立模块构建缺symbol表失败保留，随后使用**该次真实vmlinux生成的符号表**解决，未忽略undefined symbols。
- qcom-wled只完成编译和ELF/vermagic检查，**没有在手机加载**，不等于验证其probe、背光或保护IRQ。
- `out/kbuild`的wifi2构建配置、当前#10 boot及canonical #8恢复镜像不覆盖。

### 屏幕控制层

`tools/screen-idle-policy.py`与`tools/screen-idle.py`：

- 默认60秒无三键活动则息屏；音量上/下或电源键在息屏时亮屏，重新计时。
- 亮屏时短按电源息屏；音量键只延后空闲计时。按住重复/重复keydown不反复切换；忽略其他键。
- 仅接受真实、准确资源/电流/OVP属性的PM8150L backlight，以及全部三个预期键设备。
  不将普通键盘/触摸事件作为输入，不注入uinput假事件，不记录非目标键。
- 打开屏幕：fb unblank0后设置低亮度默认64/4095，试验限制≤256。
  息屏：**先真实backlight brightness0并读回，再fb blank**；后者允许fbcon合法归一化1或4，不能只看虚拟DPMS算物理关灯。
- 打开前<40°C、任何传感器>=45°C关灯；异常/停止finally及独立ExecStopPost fail-off，释放按键grab。
- 用单调时钟、设备锁和精确evdev节点；EVIOCGRAB防止被选中的短按电源传给logind导致关机。
  **硬件长按复位无法靠这个屏幕进程阻止，不测试/宣称长按语义。**
- `tools/picasso-screen-trial.service.in`是未渲染模板：135秒上限、watchdog8秒、Restart=no、
  精确设备权限/只读系统/只放开所需sysfs文件，禁止访问Wi-Fi凭据/NV目录；没有Install默认启用段。
- 这些程序不会调用system suspend/poweroff/reboot、写PMIC raw寄存器或/dev/mem。

手机只安装了 `/opt/picasso-screen-preparation/` 的脚本供预检，未安装服务。
原生`--probe`已实际验证：**因没有真实背光而在任何blank/brightness写入前拒绝**。
236项离线测试：235通过、1可选QEMU跳过。状态机/模拟后端测试不是物理显示或真实按键验收。

## 当前阻塞与后续顺序

1. 以受控方式确定本机实际panel身份；不能用未验证社区compatible或factory默认指针顶替。
2. 决定安全的bootloader framebuffer/背光接管方式，核对WLED5 boost/保护IRQ/probe行为；
   或补齐真正SM7250 MDSS/DPU/DSI/dispcc/PHY/面板驱动链。当前6.18没有SM7250原生显示匹配，不能只改status=okay或冒充SM6350。
3. 隔离完整匹配的屏幕试验内核/模块并验证镜像、恢复材料和内存，再temporary boot；不先覆盖默认boot。
4. 先低亮度实际画面与关灯/恢复，再真实短按三键事件和自动空闲测试；保持USB SSH，温度保护，用户可见确认。
5. 只有上述通过才讨论持久启用；整机suspend/resume、触摸/GPU/充电和长期稳定另行验收。

仍运行原#10，原fb blank=4已恢复，USB SSH可用；本阶段未启动WLAN/DSP。
原15,285个静态文件、boot、七保留分区、六GPT再次验证未变；未读取或修改NV/保存密码。
先前Wi-Fi凭据和掉线证据原样保留，不把屏幕准备当作Wi-Fi修复。
证据：`out/display-preparation-20261028/`。

## English

**Follow-up work completed the on-device read-only WLED boot-state check and a restricted backlight handoff driver. Real-device low brightness 0/64, kernel deadline shutoff, and rejection of reillumination after expiry passed.
A new visible color-bar/volume-up trial was prepared but had not yet run; see [DISPLAY-HANDOFF.md](DISPLAY-HANDOFF.md).
The image/keys had not been visually confirmed, and power/volume-down were not registered. The early preparation state is preserved below.**

On 2026-10-28, the user paused Wi-Fi disconnect investigation and requested display drivers, automatic screen-off, and wake by the volume/power keys first.
**At this stage, neither display illumination nor physical-key screen-on acceptance was complete. The installed wifi2 #10 was still running; no boot was flashed, backlight enabled, or persistent screen-off service activated.**
“Screen-off/wake” here means the screen and backlight, not whole-system suspend. A black screen, a wakeup-source property, or simulated events do not count as successful suspend/wake.

### Real-device state

- `/proc/fb`: `simpledrmdrmfb`, 1080×2400, 32bpp, stride4320, inside the reserved bootloader splash region.
  This is bootloader scanout takeover, not successful native MDSS/DSI driving or panel initialization.
- `/sys/class/backlight` has no device; the kernel has no QCOM WLED configuration. Native DRM_MSM, DSI, and GPU are disabled.
- Only one `gpio-keys` input device is registered, with volume-up KEY_VOLUMEUP. The PM8150 power key and volume-down are not registered.
  No actual user key events had been observed; device registration is not proof that physical keys work.
- Existing fb0 sysfs writes were verified, but the first `blank=4` read back as 1 because of recursive fbcon normalization.
  The initial strict read-back assertion failure was archived unchanged; a repeat check recorded 0→0 and 4→1, then restored original blank=4.
  This is only virtual blanking behavior, not proof of backlight shutoff or a visible screen.

### Hardware confirmed from this device's ROM DTB9+DTBO19

The input is fixed to the audited merged DTB from this device, SHA256
`f75e1bf1af964147ee929b97a6b857516a4591b7bc096fe31e73d9ed8b8dc6f6`, not another phone's parameters.

| Function | Actual factory wiring/value |
|---|---|
| WLED5 | PM8150L USID5, control0xd800, sink0xd900 |
| LED strings | string-cfg0x7, mainline enabled-strings 0/1/2 |
| LED full-scale current | 22,500µA |
| OVP | 28,000mV; do not silently use the mainline 32.5V default |
| CABC | select1, 12bit brightness range 0..4095 |
| Power | PM8150 USID0 / PON0x800 / IRQ0, KEY_POWER116, both edges |
| Volume-down | Same PON / IRQ1, KEY_VOLUMEDOWN114, both edges |
| Volume-up | PM8150L USID4 GPIO5, active-low, KEY_VOLUMEUP115, wakeup |

This device's ROM includes panels such as `xiaomi 38 0a 0a`, `36 02 0c`, `37 02 0b`, and `37 02 0a`.
The static factory dsi-default-panel points to a **sw43404 WQHD AMOLED** node and cannot establish the actual screen identity.
A community reference DTS uses `mdss,g7a-37-02-0a-dsc`, but there is no proof of this device's currently installed panel ID.
An earlier read of the original Android /proc/cmdline was denied; the existing mainline live FDT is also a static tree supplied by the shim, not the original Android live selection.
Therefore, **do not guess the specific panel, send another model's initialization commands, or read persist to guess its identity**.

### New code and isolated build

#### Hardware-preparation DTS / config

- `dts/sm7250-xiaomi-picasso-screen-handoff.dts`: inherits the original headless protected regions;
  adds PON power/volume-down using this device's IRQs, retains volume-up, and supplies accurate WLED electrical properties with default-brightness=0.
  **WLED remains disabled; MDSS/DPU/DSI/GPU/LCDB remain disabled**, preventing probe from silently overwriting unapproved boost/power settings.
- `kernel/picasso-screen-handoff.config`: prepares input/framebuffer/mainline WLED configuration. The isolated build separately sets the screen1 module version; this is not native DSI implementation.
- `tools/audit-display.py`: pins vendor DTB identity, PMIC/IRQ/GPIO/brightness range/reserved memory/framebuffer span;
  rejects another board's parameters, unapproved backlight probe, or native DSI enablement; outputs actual_panel_identity_proven=false.

Actual isolated LLVM AArch64 build artifacts are in `out/display-preparation-20261028/`:

- `Image-screen1`, distinct release **6.18.58-picasso-lts-screen1**.
- `kernel-screen1.config`, `screen-handoff.dtb`, `qcom-wled-screen1.ko`.
- These are a kernel Image/selected module, not a packaged, temporarily booted, or flashed Android boot image. **The complete module tree for the new version was not finished.**
- The first Image+all-modules build timed out after 600 seconds and was preserved; building Image alone subsequently resumed successfully.
  The first separate module build failed for lack of a symbol table and was preserved; it was resolved using **the symbol table generated from that actual vmlinux build**, without ignoring undefined symbols.
- qcom-wled only passed compilation and ELF/vermagic checks; **it was not loaded on the phone**, so its probe, backlight, and protection IRQ were not verified.
- The wifi2 build configuration in `out/kbuild`, current #10 boot, and canonical #8 recovery image are not overwritten.

#### Screen-control layer

`tools/screen-idle-policy.py` and `tools/screen-idle.py`:

- By default, turn the screen off after 60 seconds without activity from the three keys. Volume-up/down or power turns an off screen on and restarts the timer.
- When on, a short power press turns it off; volume keys only defer the idle timer. Held-key repeats/repeated keydown do not repeatedly toggle it; other keys are ignored.
- Accept only a real PM8150L backlight with accurate resources/current/OVP properties and all three expected key devices.
  Ordinary keyboard/touch events are not input; no fake uinput events are injected and non-target keys are not logged.
- Screen-on: fb unblank0, then low brightness, default 64/4095 and trial limit ≤256.
  Screen-off: **first set real backlight brightness0 and read it back, then fb blank**. Legal fbcon normalization to 1 or 4 is accepted; virtual DPMS alone is not physical light-off.
- Require <40°C before turning on; any sensor >=45°C turns the light off. Exceptions/stopping use finally and an independent ExecStopPost fail-off, releasing key grabs.
- Use a monotonic clock, device lock, and exact evdev nodes. EVIOCGRAB prevents a selected short power press reaching logind and shutting the system down.
  **This screen process cannot prevent hardware long-press reset; long-press semantics are neither tested nor claimed.**
- `tools/picasso-screen-trial.service.in` is an unrendered template: 135-second limit, watchdog8 seconds, Restart=no,
  exact device permissions/read-only system/only necessary sysfs files writable; Wi-Fi credential/NV directories inaccessible; no default-enabling Install section.
- These programs do not call system suspend/poweroff/reboot, write raw PMIC registers, or use /dev/mem.

Only scripts for prechecks were installed on the phone in `/opt/picasso-screen-preparation/`; no service was installed.
Native `--probe` was actually verified: **it refused because there was no real backlight, before any blank/brightness write**.
236 offline tests: 235 passed, 1 optional QEMU skipped. State-machine/mock-backend tests are not physical display or real-key acceptance.

### Blockers at this stage and follow-up order

1. Establish this device's actual panel identity in a controlled manner; an unverified community compatible or factory default pointer cannot substitute.
2. Decide safe bootloader framebuffer/backlight takeover and check WLED5 boost/protection IRQ/probe behavior;
   or complete the real SM7250 MDSS/DPU/DSI/dispcc/PHY/panel driver chain. Current 6.18 has no native SM7250 display match; merely setting status=okay or impersonating SM6350 is insufficient.
3. Isolate a complete matching screen-trial kernel/module set, verify images, recovery material, and memory, then temporary boot; do not overwrite the default boot first.
4. First verify a real low-brightness image and light-off/recovery, then actual short presses of all three keys and automatic idle behavior; retain USB SSH, thermal protection, and user-visible confirmation.
5. Discuss persistent enablement only after those pass. Whole-system suspend/resume, touch/GPU/charging, and long-term stability need separate acceptance.

Original #10 was still running, original fb blank=4 restored, and USB SSH available. WLAN/DSP were not started in this stage.
The original 15,285 static files, boot, seven reserved partitions, and six GPTs were reverified unchanged; NV/saved passwords were not read or modified.
Earlier Wi-Fi credentials and disconnect evidence were preserved unchanged; display preparation is not a Wi-Fi fix.
Evidence: `out/display-preparation-20261028/`.
