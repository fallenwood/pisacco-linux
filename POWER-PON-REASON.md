# 用户允许的一次只读PON采样：CBL供电上电、PS_HOLD关机来源

> 后续用户明确“接受”自动启动限制，已另获授权完成boot＋常驻服务的受限安装，未重启；见[POWER-PERSISTENT.md](POWER-PERSISTENT.md)。本页是采样阶段历史，marker仍已消耗，CBL/PS_HOLD原始事实与根因未证实结论不变；该次只读许可未被扩展或重用。

用户在明确询问固定只读采样器后回复“允许”。只执行该范围，不包含再次关机/重启、刷写或PMIC写入。

## 原生实测（不是离线fixture）

同一boot ID：`2f080316-e4da-44f0-abc6-8d2319976308`，原默认#10/FDT/config匹配。
固定USID0身份通过：PMIC type=0x51、subtype=0x1e（PM8150），PON subtype=0x04（Gen2 primary）。

| 原生寄存器字段 | 值 | 按已固定参考的含义 |
|---|---:|---|
| Gen2 PON_REASON1 / 08c0 | 0x40 | CBL_POWER：外部供电/线缆上电来源 |
| WARM_RESET_REASON1 / 08c2 | 0x00 | 本次采样没有warm-reset原因位 |
| OFF_REASON / 08c7 | 0x80 | 选择POFF序列，无多序列/未知低位 |
| POFF_REASON1 / 08c5 | 0x02 | PS_HOLD：SoC控制的关机来源 |

只读了3个身份字节、3个公共状态字节及选中的1个POFF字节，共7字节。
FAULT/S3银行未选择、没有读取；原始JSON的null保留不填0。

**CBL_POWER不是USB_CHARGER（0x10）位，不把两者混写。**
这组值更符合“PS_HOLD之后由外部供电/线缆来源再次上电”，与用户“自行启动”相符；
不是用户再次按键的证据，也没有warm-reset位支持。
但固件可能保留/清除锁存状态，实际时间关联未独立证明；采样新鲜不等于状态本身来自已唯一关联的事件。
因此是方向性证据，不宣称USB充电模式、固件实现或完整根因已证实，更不据零位排除所有复位。

## 保护与清理已实际通过

- 新PID1静态单次unit，Restart=no、RuntimeMax=20秒、受限能力/设备/系统写路径、小核亲和、独立ExecStopPost清理。
- 原生预检最高33.1°C；实际采集器采样窗口峰值32.7°C，保持起始全部<40°C、45°C中止。
- insmod只执行一次；读取module缓存的root0400快照，未重复访问PMIC；保存raw后再解码。
- 模块已成功卸载，snapshot节点消失；独立StopPost再次确认无模块。unit inactive/dead、Result=success、static未启用。
- 独占consumed、load-intent、raw snapshot、解码和两份清理结果都保留，不删除或重放。
- 同一boot没有变化；原生tty1/15秒idle屏幕服务MainPID527及内核租约健康。
- 无关机/重启/flash/suspend/按键注入，无PMIC寄存器写入、驱动probe/IRQ/重启notifier；无NV/凭据访问。
- 精确Image/config未变。316项离线测试：315通过、1可选QEMU跳过；软件测试不替代硬件电源循环验收。

采集器：`tools/collect-pon-reason.py`；静态单次unit：`tools/picasso-pon-reason-read1.service`。
手机原生记录：`/var/lib/picasso-power/pon-reason-read1-20261028/`。
该unit没有[Install]，不随开机加载；marker已消耗，当前不得再次start。

## 新的调查重点：固件上电/充电引导参数，而不是盲改PS_HOLD

离线确认当前引导存在明确的观测缺口：
1. `shim/copydown.S`向Linux x0传入嵌入的静态runtime DTB，不拷贝原始ABL动态chosen bootargs。
2. CONFIG_CMDLINE_FORCE=y，命令行固定为已审计的root；静态FDT chosen bootargs为空。
3. initramfs只在显式PARTUUID/原生标记通过后进入正常Fedora systemd，没有charger-mode分支。

因此即使固件在CBL触发时指定charger-mode，当前路径也没有可靠保存/观测它。
**这不证明固件实际传过androidboot.mode=charger**；当前Linux中没有该字段不能反证或证明其存在。
后续优先设计只保留白名单启动模式的证据方案，不能直接关闭CONFIG_CMDLINE_FORCE并接纳任意ABL参数。

## 不做的事与接受门

- 不因CBL位直接屏蔽CBL/USB/SMPL上电触发、改充电设置、S1/S2/S3、reboot magic或换固件。
- 不直接移植原厂SCM/SDI/DLOAD路径；先前SCM差异仍是比较事实，不是已证明的修复。
- 不用黑屏、initramfs halt、自动反复poweroff或整机休眠冒充保持关机。
- 当前只读操作成功，但用户确认的“自行启动”失败结论保持；电源候选持久化继续阻断。
- 新的RAM引导观测或电源循环需要单独范围与明确确认；本次许可已完成，不据此继续重启。

证据：`out/pon-reason-read1-20261028/`。此前[POWER-CHAIN-AUDIT.md](POWER-CHAIN-AUDIT.md)保留为离线准备快照。
