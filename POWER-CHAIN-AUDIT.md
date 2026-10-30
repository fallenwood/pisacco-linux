# 自动启动后续：精确#10二进制审计与只读PON采样器离线准备（阶段记录）

**后续用户明确允许，已完成同boot一次只读采样并卸载：PON=0x40 CBL_POWER、POFF=0x02 PS_HOLD、warm=0。
独占marker已消耗，不重复加载；只是方向性证据，不宣称完整根因或电源循环通过。最新见 [POWER-PON-REASON.md](POWER-PON-REASON.md)。
下文“未加载”为当时的准备快照。**

保持[POWER-AUTOSTART.md](POWER-AUTOSTART.md)的失败结论：用户确认自行启动，未能保持关机，power持久化继续阻断。
本阶段没有重做关机、RAM boot、flash、休眠或PMIC操作。

## 1. 不只看源码：核对实际编译产物

按arm64原Makefile参数从`out/kbuild/vmlinux`重新提取Image，与既有精确#10 Image一致：
`235d54cf5194555a7017e3aa9197ea71e4d6d57602598e0e4f5d56b1d558b91a`。
config仍`f60bc2723f34cd08da927b4a3a79673bddc7bcd9052114cdd055cf958106dfbc`。

只反汇编四个关机相关函数，不读取/输出镜像中其他载荷：
- 编译后的`pm8941_reboot_notify`确有shutdown type4及regmap更新路径。
- 编译后的`do_msm_poweroff`是直接PS_HOLD写0，返回时延迟10秒。
- `psci_sys_poweroff`具有标准SYSTEM_OFF调用。按源码同优先级插入规则，legacy PSCI是在最终关机时加入，预期位于已注册msm回调之后；不等于已证明实际执行。
- 默认优先级允许多个handler，不把它们误判为必然注册冲突。
- 标准sysfs元数据确认当前msm-restart设备绑定；未对MMIO做读写。

## 2. 与固定版本参考源码的具体差异

已提取并保留MiCode `236f9eb092623c2bc69fa2e88eb647ad30562049`的PON、msm-poweroff源码与binding。
它是本机公开参考，不是已证明与当前crDroid ROM逐字相同的源码。

参考关机路径包含：PMIC PON shutdown配置、能力探测后SCM停SPMI arbiter、通过SCM释放PS_HOLD及直接写fallback。
目前#10最终msm回调没有这些SCM协调步骤。这是明确的比较差异，**不是已证实根因**。
参考PON关机配置等待500us，而#10使用100..1000us；只记录差异，不据此直接修改时序。
本机实际ROM合并DT没有secondary-pon/resin-shutdown/自定义shutdown-type等属性，不盲加其他机型配置。
不移植参考源码中的DLOAD/EDL magic、SDI/debug模式、ship-mode、复位计时器或充电控制。

## 3. 看门狗与时间证据的限度

- 只读manager查询：RuntimeWatchdog=0、RebootWatchdog=10min；没有证明该看门狗实际触发。
- 没有打开`/dev/watchdog`，没有关闭或修改它来掩盖问题。
- CONFIG_WATCHDOG_SYSFS未启用，解释了此前标准属性缺失，不能据此排除看门狗。
- 手机跨boot的journal墙钟发生倒退，不能相减推断自动启动延迟；持续NTP/RTC未验收。
- 另用当前phone CLOCK_BOOTTIME与host接收时间对齐，估计新Linux boot时基在host USB20秒回执之后约0.09..0.41秒。
  这依赖host历史墙钟连续性、且boot时基不是PMIC上电时刻，仅作线索，不据此判根因或排除复位。

## 4. 已构建只读采样器，但未上传/加载

文件：`kernel/power/picasso-pon-reason-audit.c/.ko`。
ABI：`6.18.58-picasso-lts-wifi2`，模块SHA256：
`416e1e03d65d8bb27bcc1ea322229a682f451018626bc1f9ee97bf31e5a9990e`。

范围审计：
- 要求明确`confirm_readonly`、精确内核、Picasso兼容及完整OF控制器/PM8150L锚点；当前标准拓扑元数据符合这些条件。
- 只向既有SPMI controller分配一个未注册命令描述对象，固定USID0；绝不device_add、不触发新PMIC/MFD/PON probe。
- 先读固定PMIC身份，必须type0x51/subtype0x1e与PON Gen2 primary subtype4；不符即停止。
- 固定白名单：身份0104/0105/0805；Gen2状态08c0/08c2/08c7；只按OFF_REASON位读取08c5、08c8/08c9或08ca。
- 不使用旧Gen1地址0808/080a/080c，不读PS_HOLD控制、S1/S2/S3计时/控制、SMPL/触发使能或NV区域；原因银行按上述条件白名单区分，S3_RESET_REASON不是S3控制寄存器。
- 只用标准`spmi_ext_register_readl`，每字节固定单次，不写PMIC寄存器；模块未解析符号检查无write/probe注册接口。
- 不启用/禁用IRQ、无reboot notifier、无电源动作、无地址参数；0400 snapshot是一次缓存，再读不再访问总线。
- 当前原DT没有primary节点；若存在则拒绝，避免与新probe竞争。控制器/设备引用已审核。

这是内核硬件读取代码，仍需单独明确允许后才可在手机执行，不把编译/静态检查当硬件安全保证。
**当前未上传/加载模块，尚未读取任何PON原因字节。** 旧原因也可能已被固件清除/改变，不保证取得即能定因。

## 5. 离线解码与接受门

`tools/power-pon-reasons.py`只解码输入JSON，不接触设备。
严格拒绝错SID/PMIC、Gen1/额外地址、非字节、缺失或多读的未选银行；保留全部PON/FAULT/S3位与多序列歧义，不仿照ffs()只取首位。
输出永不自动把位图升格为根因或关机开机通过；OFFLINE-FIXTURE文件显式标为假设输入，不是手机测量。
311项离线测试：310通过、1可选QEMU跳过。原Image/config/旧控制器与hold-policy未变。

下一步若获明确允许：在**当前启动**只读采样，起始全传感器<40°C、45°C中止、有限时长、读取后卸载；不重启、不关机、不刷写、不写PMIC寄存器。
本阶段仅准备，未执行该采样。任何再一次实际电源循环仍需另行明确范围，不重用已消耗标记。

证据：`out/power-chain-audit-20261028/`。首次发现指令时目录搜索范围过宽的告警也已保留；仅列目录名，未读外部文件，后续均限制为项目/固定参考仓库。
