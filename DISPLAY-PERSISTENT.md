# 屏幕持久化：开机服务与正常重启复核通过（仅屏幕，不整机休眠）

**后续用户纠正：不应继续显示色条。当前服务已改为原生tty1/fbcon，fb0只读，不生成/写入图案，见 [DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md)。
长按电源的新请求正在独立隔离输入试验准备，见 [POWER-KEY.md](POWER-KEY.md)；尚未执行关机或刷boot。
以下是此前色条后端的持久化阶段记录，不把其目视/正常重启结果移植为新控制台或电源开关机验收。**

2026-10-28。用户明确要求：**“不要进行整机休眠,现在这样就行,写入手机”**。
仅保存已选择的屏幕行为：低亮度色条，**15秒无按键关灯，短按音量上亮屏/重新计时**。
不新增电源/音量下，不进行整机suspend/hibernate，不启用Wi-Fi。

## 已写入手机

- `/opt/picasso-screen/`：精确#10 ABI的租约背光模块、守护程序、单键策略及此前通过目视的冻结重绘helper。
- `/etc/systemd/system/picasso-screen.service`：已`enable --now`；正常重启后再次确认enabled/active及租约健康，开机自动亮屏后约15秒关灯。
- `/var/lib/picasso-screen/history/`：每次启动/停止的root-only记录；运行状态在`/run/picasso-screen/`。
- **不需要改boot**；保留已安装wifi2 #10、原#8恢复镜像、既有模块树。未写GPT/DTBO/vbmeta/原NV。

这里“写入”是持久保存普通XFS根文件系统中的模块与systemd服务，不是刷分区镜像。

## 常驻不是删除试验超时

原试验模块保持原样，不能靠去掉70/90秒界限变成无限亮灯。
独立 `kernel/display/picasso-wled-service.c`：

- 默认拒绝，需显式confirm；严格Picasso/PM8150L USID5/既有资源和完整electrical配置核对。
- **加载时关灯**，只写MOD_A亮度、sync bit0和module-enable bit7，不修改供电、电流、boost、保护或面板。
- 固定3秒租约、250ms内核检查。绑定实际insmod父进程的内核PID对象，不接收任意PID参数；PID复用不能冒充。
- 只有同一个root进程能写LIVE续约。到期关灯并永久拒绝该次加载的续约/亮灯，必须人工新启动/卸载处理。
- 正常调度下约3秒后关灯，非硬实时保证；PMIC总线/硬件失效不能由软件承诺绝对关灯。

`screen-service.py`的续约只在主循环温度/进度检查后进行，无独立“盲目续约”线程。
每次on沿用已目视验证的 **unblank→完整重绘→64/4095**；启动<40°C、>=45°C失败关灯。
重复/长按重复事件不续亮；只有音量上新press亮屏/重新计时，松开后才能认作下一次press。
丢失evdev事件、配置/读回错误等失败关灯且不自动重启。

服务有PID1 8秒Watchdog、Restart=no、独立ExecStopPost卸载、内存限制与小核进程亲和性；
仅允许fb0和已审核event0字符设备，禁止mount/reboot/swap/raw-io/clock修改系统调用，隐藏系统睡眠入口。
不调整全局CPU最大/最小频率、governor、温控或RF功率。

## 真机检查已通过（重启前）

- 正确父PID续约超过3秒保持实际低亮度64；不同root PID收到EPERM。
- 停止续约后内核独立实际归零；同一owner续约/重新开灯均收到ETIMEDOUT。
- 完整加固服务实际15秒idle关灯，限时停止并卸载成功。
- 对另名guard试验单元的**进程SIGSTOP**后，内核独立关灯；进程继续运行时因租约过期失败退出。
  这只是暂停屏幕进程，不是整机休眠。预期failed单元保留，没有reset-failed。
- 261项离线测试：260通过、1可选QEMU跳过。
- 全部15,285个原静态文件、当前boot128MiB、七保留分区、六GPT重新验证未变；带独立温度守护。
- `systemctl enable --now`之后服务active并实际完成15秒idle，`sync`后发出一次正常`systemctl reboot`。

重启前本阶段最高已采样36.4°C；无屏幕阶段NV/凭据读取。

## 正常重启后的复核已通过

操作者恢复主机USB后，使用原有严格pin的SSH主机公钥回连；boot ID确实变化，没有再次重启或fastboot/flash。

- 仍是原wifi2 #10；内核config/FDT、守护程序、单键策略、冻结renderer、模块及unit哈希全部匹配。
- 开机约10.03秒服务自行显示图案，约25.17秒记录idle关灯，间隔约15.14秒；unit enabled/active，Restart=no。
- 同一MainPID持续运行至复核时约900秒uptime，3秒租约未过期，不是70/90秒演示单元。
- 新boot内实际收到一次真实音量上事件，记录actual_brightness=64，约15秒后再次actual=0；没有合成按键。
- **新boot的目视结果尚未收到单独反馈**，不把事件/寄存器读回冒充目视验收；先前visual2目视通过的事实保持原范围。
- 新boot最高已采样39.4°C，复核时约31–33°C；完整性复核的独立温度守护最高35.1°C。
- 全部15,285个原静态文件、当前boot128MiB、七保留分区、六GPT再次校验未变；无NV/凭据读取。
- SSH/firewalld active；Wi-Fi仍disabled，没有为屏幕启动DSP/WLAN。
- 离线回归再次261项：260通过、1可选QEMU跳过。旧guard预期失败、主机sudo限制、pending结果和原checksum快照均保留。

## 曾遇到的主机USB阻塞（已恢复，历史记录）

USB已重新枚举为相同MAC/CDC-NCM/1d6b:0104，但主机NetworkManager尝试DHCP，丢失192.168.7.1/24。
agent宿主工具环境设置NoNewPrivs，`sudo`被拒绝，无法执行原本窄范围USB恢复。
未使用特权容器、提权绕过或扩大主机网络改动；没有重复重启或刷写手机。

当时尚不能确认新boot ID/开机服务/租约/完整性。操作者随后回复“已恢复”，本阶段已完成上述正常重启复核。
下面保留当时使用的恢复步骤；**当前不用再运行**。今后USB重新枚举且丢失地址时，可在正常主机本地交互终端使用：

```sh
cd /home/vbox/droid
./picasso/tools/restore-screen-usb.sh
```

helper先唯一核对USB MAC `02:50:49:00:00:01`、cdc_ncm及gadget VID/PID，然后只对此接口设置unmanaged/up/192.168.7.1/24，
不改主机Wi-Fi、默认路由、DNS、NAT。若sudo要求认证，只在本地终端输入，不在聊天/argv/日志中提供。
随后使用既有私钥路径、严格pin的主机公钥SSH打印手机boot ID与屏幕服务状态。
本次恢复及复核已完成；不重复执行visual1/visual2试验，也不为此再次重启。

## 边界

用户取消整机休眠及新增按键，本阶段不再以三键/60秒为持久化前置。
当前是15秒、音量上、低亮度色条，不是原生DSI/GPU/触摸或桌面；不承诺阻止硬件长按复位。
电池/充电、面板重新初始化、长期稳定或物理RF静默均未认证。
若温控/配置异常导致服务失败，保持停止，不自动重试；仍可通过恢复后的USB SSH排查。

## 日常控制（手机内执行）

- 临时停止并关灯：`sudo systemctl stop picasso-screen.service`（下次开机仍启动）。
- 取消开机启动并关灯：`sudo systemctl disable --now picasso-screen.service`。
- 手动恢复：温度<40°C时`sudo systemctl start picasso-screen.service`；若失败先检查日志，不使用reset-failed掩盖问题。

证据：`out/display-persistent-20261028/result.json`及同目录新`FINAL-SHA256SUMS`。
此前pending-result、原SHA256SUMS和主机恢复失败保留；此前单键目视验收见[DISPLAY-VISUAL2.md](DISPLAY-VISUAL2.md)。
