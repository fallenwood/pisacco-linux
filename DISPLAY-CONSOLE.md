# 屏幕内容修正：只显示Fedora本身的tty1控制台，不再画色条

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
