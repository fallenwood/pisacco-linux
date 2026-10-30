# USB已恢复：有序关机路径与新启动核验通过；手动冷开机待确认（阶段记录）

**后续用户明确回复“自行启动的”：不是手动冷开机通过，保持关机目标未达成，电源候选持久化已阻断。
20秒USB静默不证明硬件一直关机；PID1作业完成不证明最终kernel/PMIC shutdown成功。
最新见 [POWER-AUTOSTART.md](POWER-AUTOSTART.md)。下文保留当时待确认的原事实与校验，勿再询问或重跑该试验。**

用户回复“已恢复”后，用原固定主机密钥SSH完成以下核验。没有再次关机、重启或刷写。

## 原生证据链

- guided2真实KEY_POWER116按下/松开持续 **2.361172秒**，松开时产生`orderly_poweroff`。
- 手机XFS持久记录`shutdown_requested=true`、`poweroff_request_stage=pid1_accepted_not_physical_poweroff_proof`。
- 旧boot ID：`279ae843-fcc4-4cfe-a49b-4ff754fd91ef`。
- 正确使用无连字符的journal boot descriptor后，旧日志确认：屏幕`stopped_cleanly`、module已卸载；`Finished systemd-poweroff.service - System Power Off`。
- 最初带连字符journal查询的parse失败原样保留，纠正查询另存；不把查询错误当作日志缺失。
- USB实际断开，连续20秒无自动返回；用户随后报告完成开机，USB与原SSH身份恢复。
- 新boot ID：`2f080316-e4da-44f0-abc6-8d2319976308`，与旧boot不同。
- 正常启动返回原默认wifi2#10，原FDT `62ac1218f2f169055c7c00528a9d0ecb36ad15bbb548dd969a96bb445f93d388`，config匹配。

## 开机后完整性与屏幕

- 15,285个基线文件 / 543,194,505字节：通过。
- 完整128MiB boot仍为已安装#10的`f091833a8d4844d14d055de8e9b3cfce523c3a6889ade6c422b3bd0d9b853ce9`。
- 七个保护分区、六组原GPT片段：原字节hash通过。
- 独立小核温控父进程：全部可读传感器起始<40°C、45°C中止，校验采样峰值35.1°C，无阈值放宽。
- 原生tty1/fbcon服务enabled/active，固定3秒内核PID租约健康；15秒idle与真实音量UP路径保留。
- 本次开机记录startup actual64→15秒off0，真实音量UP actual64→15秒off0；它不替代用户对实际屏幕内容的视觉反馈。
- 无合成像素/终端payload，无整机休眠；Wi-Fi仍disabled/inactive，没有读取NV或凭据。

## 唯一尚待用户确认

**20秒等待结束后，是否由你再次按电源，手机才开机？还是它自行启动？**

用户原报告“关机开机试验完成”保留，但未单独回答上述问题，完整脚本人工OFF/开机回执也未生成。
因此接受的是实际按键→PID1有序关机→旧boot日志完成→新的默认启动及完整性；
**硬件手动冷开机的整体接受仍pending**，不补造人工确认，也不把USB消失当PMIC所有电源无电的证明。

原默认#10 DTB没有电源输入，临时power候选没有刷入boot，电源键自动关机服务未启用。
目前不要重跑旧观察/关机试验。后续持久化需完成上述确认，并单独获得boot范围授权，保持#10/#8恢复边界。

证据：`out/power-cycle-postboot-20261028/`。此前USB缺地址与连接失败见[POWER-CYCLE-REVIEW.md](POWER-CYCLE-REVIEW.md)，第一次armed超时和guided2准备记录保留不改。
