# 屏幕内容修正：只显示Fedora本身的tty1控制台，不再画色条 / Screen-content correction: show only Fedora's own tty1 console, without color bars

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

> 2026-10-30持久化更新：新boot曾因启动时温度≥40°C而保护退出；现已加
> `/etc/systemd/system/picasso-screen.service.d/20-cooldown.conf`，用
> `/opt/picasso-startup/wait-for-cool.py`在加载硬件前最多等待300秒，要求连续三次温度<40°C。
> 无效/缺失传感器或等待超时仍失败，不放宽原运行45°C中止或开启自动重启。
> 原屏幕程序、模块、unit和15秒/音量上/原生tty1行为未改；当前enabled/active，
> 实际15.09秒关灯、亮度0及3秒租约健康。本次未重启；原高温失败记录已备份保留。
> 证据`out/boot-screen-wlan-20261030T152618Z/`，以下为此前控制台改造记录。

2026-10-28。用户指出日常亮屏不应显示测试色条；此前将测试图案沿用到常驻服务不合适，现已修正并写入。
仍为#10，同一boot ID内只重启屏幕服务，未重启手机/刷boot，未改背光模块、供电或面板。

## 当前行为

- 15秒无按键关灯，短按音量上亮屏/重新计时，不进行整机休眠。
- **画面由系统原生fbcon与既有getty@tty1.service提供**。Fedora Server无桌面，通常是原生文字控制台/登录提示。
- 不再导入、校验或调用visual-render.py，不生成/写入色条，不截图或保存像素。
- 不写TTY字符、ANSI伪界面或假登录提示，不读取终端内容/密码，不切VT或改变KD_TEXT/GRAPHICS模式。
- helper只核对tty1为当前KD_TEXT、fbcon已绑定；只做标准fb blank/unblank，让内核恢复自己的控制台，再开低背光64。

## 安全与持久化

`screen-console.py`读取tty1元数据只用KDGETMODE，TTY字符设备只读打开、立即关闭；
主进程的fb0 FD现在**只读**，只用于几何/driver ioctl，不读像素。
unit增加getty依赖与只读tty1，保留3秒内核owner-PID租约、8秒PID1 Watchdog、Restart=no、45°C关灯等约束。
若其他VT/图形程序接管，不覆盖其画面，而是失败关灯。

为用户新增的电源键试验，另明确接受一个已审核的DTB hash：原wifi2所有既有节点/属性完全不变，仅加本机PM8150/PON/KEY_POWER。
GPIO音量上允许event0或event1，但仍校验唯一gpio-keys及仅115位图；unit只允许这两个具体evdev节点，不放开整个input major。
这不表示电源键或候选DTB已在真机通过。

## 已核对

- 新服务active/enabled，原getty active且未重启。
- 会话标记native_tty1_fbcon；真实内核KD_TEXT/fbcon元数据通过。
- `/proc/<pid>/fdinfo`确认fb0访问模式为O_RDONLY；旧合成renderer未加载。
- 新版本实际完成15秒idle关灯，租约健康；最高采样约35°C。
- 当前boot ID未变，15,285个原静态文件/boot128MiB/七保留分区/六GPT重新验证未变。
- 离线269项（加入电源策略后总277项）：通过，1可选QEMU跳过。
- **屏幕的实际目视反馈仍需用户确认**，不以只读fd/元数据或brightness读回替代眼睛看到的内容。

旧色条服务、unit、测试版本在本机root-only部署备份及host独立证据目录保留，不把旧色条验收改写成系统控制台目视验收。
当前已启用的正常服务不会再绘制色条；请勿重跑任何visual1/visual2历史脚本。

证据：`out/display-console-20261028/`。电源键新增请求见[POWER-KEY.md](POWER-KEY.md)。

## English

> 2026-10-30 persistence update: the new boot previously exited protectively because startup temperature was ≥40°C. Added
> `/etc/systemd/system/picasso-screen.service.d/20-cooldown.conf`, using
> `/opt/picasso-startup/wait-for-cool.py` to wait at most 300 seconds before loading hardware, requiring three consecutive temperature samples <40°C.
> Invalid/missing sensors or timeout still fail; the original 45°C runtime abort is not relaxed and automatic restart is not enabled.
> The original screen program, module, unit, and 15-second/volume-up/native tty1 behavior are unchanged. At this update the service was enabled/active,
> actual shutoff occurred after 15.09 seconds, brightness was 0, and the 3-second lease was healthy. No reboot was performed; the original high-temperature failure was backed up and preserved.
> Evidence: `out/boot-screen-wlan-20261030T152618Z/`. The earlier console conversion record follows.

2026-10-28. The user pointed out that ordinary screen-on should not show test color bars; reusing the test pattern in the persistent service had been inappropriate and was corrected and installed.
Still #10: only the screen service restarted within the same boot ID. The phone was not rebooted, boot was not flashed, and the backlight module, power settings, and panel were not changed.

### Behavior at this stage

- Light-off after 15 seconds without key activity; a short volume-up press turns it on/restarts the timer. No whole-system suspend.
- **The system's native fbcon and existing getty@tty1.service provide the image.** Fedora Server has no desktop; normally this is the native text console/login prompt.
- visual-render.py is no longer imported, validated, or called. No color bars are generated/written and no screenshots or pixels are saved.
- No TTY characters, ANSI pseudo-interface, or fake login prompt are written. No terminal contents/passwords are read, VT switched, or KD_TEXT/GRAPHICS mode changed.
- The helper only checks that tty1 is currently KD_TEXT and fbcon is bound. It only performs standard fb blank/unblank so the kernel restores its own console, then enables low backlight64.

### Safety and persistence

`screen-console.py` reads tty1 metadata using only KDGETMODE; the TTY character device is opened read-only and immediately closed.
The main process's fb0 FD is now **read-only**, used only for geometry/driver ioctl, without reading pixels.
The unit adds a getty dependency and read-only tty1, retaining the 3-second kernel owner-PID lease, 8-second PID1 Watchdog, Restart=no, and 45°C light-off constraints.
If another VT/graphics application takes over, it fails with the light off rather than overwriting that application's image.

For the user's new power-key trial request, one additional audited DTB hash is explicitly accepted: every existing original wifi2 node/property remains identical; only this device's PM8150/PON/KEY_POWER is added.
GPIO volume-up may be event0 or event1, but a unique gpio-keys device and bitmap containing only115 are still validated. The unit permits only these two specific evdev nodes, not the entire input major.
This does not mean the power key or candidate DTB passed on real hardware.

### Checks completed

- New service active/enabled; original getty active and not restarted.
- Session marker native_tty1_fbcon; actual kernel KD_TEXT/fbcon metadata passed.
- `/proc/<pid>/fdinfo` confirmed fb0 access mode O_RDONLY; the old synthetic renderer was not loaded.
- The new version actually completed 15-second idle light-off with a healthy lease; peak sampled temperature about35°C.
- Boot ID unchanged; the original 15,285 static files/boot128MiB/seven reserved partitions/six GPTs reverified unchanged.
- 269 offline tests (277 total after adding power policy): passed, 1 optional QEMU skipped.
- **Actual visual feedback on the screen still requires the user to confirm**; read-only FDs/metadata or brightness read-back do not replace what the eye sees.

The old color-bar service, unit, and test versions are retained in the device's root-only deployment backup and a separate host evidence directory. Old color-bar acceptance is not rewritten as visual acceptance of the system console.
The enabled normal service no longer draws color bars; do not rerun any historical visual1/visual2 script.

Evidence: `out/display-console-20261028/`. The new power-key request is in [POWER-KEY.md](POWER-KEY.md).
