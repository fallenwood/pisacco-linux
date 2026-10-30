# 屏幕/自动息屏/三键亮屏：准备完成，真实背光与原生DSI仍阻塞（阶段记录）

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
