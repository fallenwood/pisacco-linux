# 屏幕恢复：定位fbcon覆盖画面，visual2已修补、待实际观察（准备记录）

**后续visual2已实际执行，用户确认“按音量上后，三色色条重新出现”，真实单键可见恢复通过。
已核对当前boot内按键/重绘/亮度日志、源码哈希和清理，最高采样33.4°C；单元inactive、模块卸载，旧命令不可重跑。
正式单键验收见 [DISPLAY-VISUAL2.md](DISPLAY-VISUAL2.md)。三键、60秒idle、持久开启和整机suspend仍未通过。
下文保留当时准备状态。**

2026-10-28。当前仍为已安装wifi2 #10；无boot/DTBO/供电/面板reset/原生DSI变更。
本阶段继[DISPLAY-HANDOFF.md](DISPLAY-HANDOFF.md)。**已找到并复现软件画面丢失路径，但不能把新修补说成已通过目视亮屏。**

## visual1用户澄清与原生记录

用户回复 **A**，明确确认：

- 第一段三色色条可见。
- 随后确实关灯。
- 短按音量上后没有可见恢复。

Linux日志已记录真实KEY_VOLUMEUP，进入的是真实按键分支而不是定时亮屏，off开始后约1.098秒执行亮屏。
actual_brightness依次64→0→64→0，最后卸载成功、单元inactive/success；最高采样35.4°C。
**单元成功只说明控制程序完成，不能覆盖用户报告的物理恢复失败。**
第一段可见和关灯已确认，意味着本机bootloader scanout/帧缓冲输出及首次背光控制至少曾实际工作；
仍不证明具体panel ID、原生DSI初始化、三键/自动空闲/整机suspend或长期稳定。

## 找到的软件问题：解空白会重绘控制台

visual1只在开始绘制一次图案。恢复时执行fb0 unblank与背光64，却没有重新绘制。
Linux6.18的fbcon路径在unblank调用`update_screen(vc)`，用VT文字控制台覆盖先前的图案。
因此可以出现“按键已识别、背光值64，但屏幕不再显示色条”。不能将其误判成音量键未上报。

源代码：`drivers/video/fbdev/core/fbcon.c:fbcon_blank()`、`drivers/tty/vt/vt.c:do_unblank_screen()`。

### 真机WLED关闭状态下复现

为避免反复亮屏，两个独立PID1有界探测都先加载已有**只读**WLED audit模块，确认module gate=off；
不加载handoff背光模块、不写PMIC寄存器，只使用已核对的DRM shadow `/dev/fb0`标准接口。

只在完整写入自造图案之后读回比较；不读取写入前的旧画面、不保存/传输像素，
不输出未知像素hash，只保留是否相等、与自造图案RGB匹配率。结束清零并恢复原fb blank，卸载只读模块。

| 步骤 | 与合成图案RGB匹配率 |
|---|---:|
| 写入已知图案 | 99.9951% |
| fb blank4（fbcon规范化为1） | 99.9951% |
| unblank0，不重绘 | **0%** |
| unblank之后显式重绘 | **99.9951%** |
| 重绘后再等待200ms | **99.9951%** |

先前完整图像SHA比较即使重绘后仍false，不能直接认为整幅图案丢失；
后续RGB匹配率分清了近似整幅保留与整幅覆盖。少量残差与fbcon光标活动相符，未将其冒充100%像素一致。
两个探测均正常结束、清理通过，真实WLED一直保持关闭；最高采样分别36.1°C和43.8°C，未触发45°C阈值。
第二次Python逐像素比较产生明显CPU热负载，**不重复探测**；可视修补不做这个高负载读回。

## 修补：每次亮屏前重新绘制

独立新版本 `tools/test-screen-handoff2.py`：

1. 解除framebuffer空白。
2. 完整重绘10,368,000字节合成图案；短写处理及温度检查，失败不执行亮灯。
3. 再请求亮度64并检查actual_brightness。

首次与按键恢复都使用这一共同路径；不依赖上一次图案在fbcon blank/unblank间保留。
不新增面板命令、调电压/电流/boost、提高亮度、改控制台模式或屏蔽Linux按键。
仍为相同已验证handoff模块，hardware4095/trial max256/实际64；kernel独立70秒到期，PID1 90秒超时与独立卸载。
原visual1脚本、consumed marker、日志及失败结论均保留，未重跑、reset-failed或改写成功。

## 请实际观察新的visual2

```sh
cd /home/vbox/droid
./picasso/tools/test-screen-handoff2.sh
```

这是**新的独占visual2**，不是重跑旧命令。准备好观察后按回车；不需要密码。
先看色条，随后提示息屏时只短按一次**音量上**，看色条是否恢复，最后自动关灯并卸载。
不要长按电源，本轮仍不测试电源/音量下。

- 开始必须<40°C，>=45°C立即关灯；持续监测所有可读传感器。
- 不保存/读取旧像素；可视试验只写自造图案。
- 有独立visual2 marker、unit、runtime与host日志，执行/中断后先查已有结果，不盲目再跑。
- 单元static/inactive、无开机target链接；**准备后尚未运行可视visual2**。

请反馈：**息屏后短按音量上，这次三色色条是否重新出现？**
只有用户实际确认恢复，才能将单键可见亮屏列为通过；电源/音量下、60秒空闲策略、持久开启仍待后续。

## 证据与当前边界

`out/display-visual2-20261028/`保存用户A澄清、两个native probe、原脚本快照、visual2 staging读回及测试。
离线250项：249通过、1可选QEMU跳过。新测试约束unblank→重绘→亮度顺序、短写、绘制失败不亮灯和独立命名空间。
无Wi-Fi/NV/密码访问，未启动DSP/WLAN、未刷任何分区，未启用默认屏幕服务。
前阶段boot/原静态文件/保留分区/GPT校验保留；本阶段新增的是普通根文件系统中的有界诊断和新试验文件。
