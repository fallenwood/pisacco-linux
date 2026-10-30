# 长按电源关机：用户确认自行启动，暂不持久化

> 历史方案及暂停决定保留。后续用户明确接受该限制并另授权受限安装，boot已写/服务enabled但尚未重启激活；最新[POWER-PERSISTENT.md](POWER-PERSISTENT.md)。自动启动未修复，不重跑本页旧试验。

**当前结论：用户明确“自行启动的”，保持关机/手动冷开机目标未通过，不能把软件poweroff完成当硬件关机成功。
原因只读检查尚不确定，停止持久化及重复试验，见 [POWER-AUTOSTART.md](POWER-AUTOSTART.md)。以下为早期各阶段记录。**

**最新进度见 [POWER-SHUTDOWN-GUIDED2.md](POWER-SHUTDOWN-GUIDED2.md)：后续第一次armed因4.559807秒/1.682461秒均无效而超时，未请求关机。
原记录/marker保留；独立第二轮已加入2秒实时松开提示，未放宽窗口或温控、未自动启动。
先前真实1.697253秒按压未触发，2.221647秒松开被正确识别；该阶段disarmed、无关机请求。
观察机会已消耗，不重跑下方旧命令。下一步须本地明确输入POWER OFF并等待新按键，才做真正正常关机；尚未执行、未刷boot。
见 [POWER-KEY-OBSERVED.md](POWER-KEY-OBSERVED.md)。以下为早期准备/冷却步骤历史。**

**最新：候选启动成功，pm8941_pwrkey/event1已注册；第一次观察被<40°C起始保护拒绝、未消耗observer。
当前已冷却，屏幕服务恢复。请在当前启动使用`./picasso/tools/observe-power-key.sh`，不重启、不重新boot、不关机，详见 [POWER-KEY-COOLDOWN.md](POWER-KEY-COOLDOWN.md)。**

**此前fastboot曾因主机USB写权限阻塞；权限修正后已完成候选RAM boot。以下resume命令仅保留历史，当前不要执行：**

```sh
cd /home/vbox/droid
./picasso/tools/test-power-input.sh --resume-fastboot
```

**此模式不再重启手机，不重复原准备；重新核对serial/VID/PID/product及镜像hash后，仅fastboot boot临时启动。
本轮仅观察按键、不软件关机、不flash。sudo认证只在本地终端进行，不在聊天中输入。
USB权限失败、旧helper与launch记录保留；不要运行不带resume的初始流程。**

2026-10-28。用户要求“实现长按电源键开关机”。**当前已安装的#10 DTB没有注册电源键，不能声称功能已生效。**
先完成安全的真实按键观察，再做有人值守的正常关机/硬件开机试验；本阶段不刷boot、不执行关机或硬件强制复位。

## 明确语义

- 正常开机后的关机目标：**电源键按住约2秒后松开（测试限2..3秒），再请求PID1正常关机**。
  短按、repeat、无匹配release、超长/异常时间均不当成正常关机证据。
- 在release而非持续按住时触发，避免关机后按钮还按着而立即再次开机。
- 正常关机走`systemctl poweroff --no-block`，不是kill电源、raw reboot、reset或整机休眠。
- 关机后的开机由原有PMIC/引导程序处理，关机状态Linux不运行，不能用用户态代码创造此能力。
- **不修改硬件S1/S2/S3计时器、不承诺阻止过长按压的强制复位**。不要按住超过3秒做本次观察。

## 本机证据与驱动审查

本机DTB9/DTBO19：PM8150 USID0、PON0x800、IRQ<0 8 0 双边沿>、KEY_POWER116、pull-up、15625µs debounce。
厂ROM还描述了复位bark/S1/S2逻辑；这些不是Linux当前live状态证明，也不会复制/改写这些硬件计时器。

主线pm8941-pwrkey probe会配置标准debounce/pull位，读取状态并提供实际evdev。
正常shutdown/reboot notifier会配置标准PS_HOLD类型及enable位，使SoC的既有qcom,pshold路径完成电源操作。
这些是明确审核的标准驱动运行操作，不是任意PMIC/MMIO、供电/boost或NV写入。
真正poweroff是否完成、是否意外重启、关机后按键能否开机都仍需真机观察。

## 候选DTB/boot包

`dts/sm7250-xiaomi-picasso-power-trial.dts`继承**精确wifi2**，不是旧headless/screen1替代：

- 只加PM8150主PMIC/PON/pwrkey三个节点，无音量下。
- `audit-power-key.py`确认原有所有节点/属性逐字节相同，保留内存/USB/Wi-Fi默认禁用/屏幕不变。
- 复用已安装#10的Image与完整模块ABI；无内核重编译或猜测电源硬件。
- stock12-DTB blob、原DTBO不变，copydown布局/Image/内嵌DTB校验通过。
- 独立RAM boot候选`out/power-key-preparation-20261028/boot-power-key-trial.img`，**现已临时启动、未写boot分区**；设备注册已确认，长按事件/正常关机尚未验收。
- 候选DTB SHA256 `ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c`。

## 按键策略和预备部署

`power-hold-policy.py`：仅116、单次hold/release、单次关机锁存；纯离线测试不算硬件验收。
`power-key-service.py`：要求精确候选FDT、真实pm8941_pwrkey/精确116位图/phys/devt，CLOCK_MONOTONIC事件；
过期事件/SYN_DROPPED/初始已按住/温度异常均拒绝。默认**仅观察、不关机**；真正正常关机必须另行显式arm。

手机`/opt/picasso-power/`已有代码，没有启用关机服务；首个观察器在温度起始检查拒绝，尚未进入实际观察。
logind guard文件（HandlePowerKey/LongPress均ignore）已随候选这次启动读入，没有为此热重启logind；
这样候选注册电源键后不会被默认短按poweroff抢走。随后由明确armed的独立处理器实现约2秒松开关机。

## 最初的RAM启动步骤（已执行，当前不要重跑）

在正常主机本地交互终端执行：

```sh
cd /home/vbox/droid
./picasso/tools/test-power-input.sh
```

脚本只允许一次：

1. 初始模式校验RAM镜像/hash、手机正常#10 FDT、<40°C、预备guard；已进入fastboot的resume模式只验证既有launch来源，不再次重启。
2. 提示在**正常软件重启**期间按住音量下进入fastboot，不长按电源强制复位。
3. 本地sudo认证后，唯一目标serial/VID/PID/product核对后`fastboot boot`独立候选；**无flash/erase/unlock命令**，新增独占boot请求记录防重复。
4. 本地sudo仅恢复原MAC/CDC-NCM手机USB静态地址，使用严格pin的SSH主机公钥回连。
5. 观察器ready后，电源键按住约2秒并在3秒前松开；**本轮不会软件关机**。
6. 保存真实down/release和策略候选结果，回复“电源键试验完成”，再核对并安排另一次明确armed的正常关机试验。

进fastboot或SSH失败时不自动循环重启。先保留结果排查；默认boot仍#10，原#8恢复材料保留。
候选是临时启动；后续普通开机仍回默认#10，电源键持久化需要已测试后另行明确部署，不能拿打包成功当硬件通过。

当前无NV/密码读取、无屏幕供电/电压/功率提高、无新默认Wi-Fi，不做整机休眠。
已完成的控制台修正见[DISPLAY-CONSOLE.md](DISPLAY-CONSOLE.md)。
