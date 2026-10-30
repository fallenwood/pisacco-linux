# 电源键观察：候选已启动，温度保护拒绝首轮；在当前启动冷却后继续（阶段记录）

**后续真实观察已完成：1.697253秒未触发，2.221647秒松开识别为长按候选，明确未arm/未关机。
观察marker已消耗，不重跑本页旧观察命令。证据及下一轮明确确认的正常关机试验见 [POWER-KEY-OBSERVED.md](POWER-KEY-OBSERVED.md)。
本页保留温控拒绝和恢复过程，不覆盖失败，也不冒充关机/硬件开机通过。**

2026-10-28。用户从fastboot继续后，已真实运行候选DTB，并恢复USB SSH。

## 已证实

- 当前kernel仍为复用的wifi2 #10 Image/ABI，FDT SHA为已审核的`ecbfe0d99b476b21e1e50f233576bcf1ba22f84446e9367cb921403831778d3c`。
- 真实`pm8941_pwrkey`注册为event1，phys=`pm8941_pwrkey/input0`、位图仅KEY_POWER116；gpio-keys音量上为event0。
- **这是按键设备注册成功，不是实际长按事件、正常关机或硬件开机通过。**
- 首次观察器在`Start below 40C`起始检查退出，没有ready、没有observer-consumed、没有result，未发出关机请求。
- 屏幕服务在同次启动也因同一起始温度检查拒绝，模块未加载，旧failed/session记录已另存。
- 原始程序没记录拒绝瞬间的温度值；不根据之后的温度倒填“当时最高温度”。当前采样最高36.8°C。

## 这次如何继续

**不再运行任何fastboot/启动镜像/重启命令。** 在主机本地交互终端执行：

```sh
cd /home/vbox/droid
./picasso/tools/observe-power-key.sh
```

新helper仅对当前候选启动操作：

1. 严格pin的SSH主机公钥，核对候选FDT与observer/policy源文件hash，确认观察机会未消耗。
2. 最多等待120秒，所有可读传感器连续三次（0.5秒间隔）低于40°C才启动观察；>=45°C/无效传感器即拒绝。
3. **等真正观察器ready提示后**，电源键按住约2秒后松开，不超过3秒。
4. 本轮仍只观察、不软件关机。所有attempt/拒绝分别保存，不覆盖第一次失败；不得将结果缺失说成按键通过。

若温度再次上升而拒绝，程序会保存当时各传感器读数，不会先消耗observer marker；没有提高40/45°C阈值。
若已经真正开始过观察则marker保持消耗，拒绝无条件重放；先检查已有结果。
不要长按超过3秒；硬件强制复位不是软件能承诺阻止的。

## 已做的恢复与代码修正

- 捕获失败状态后，在全传感器<40°C时**手动一次**启动屏幕服务，原生tty1与15秒idle/内核租约恢复正常。
  没有reset-failed，也没有设置自动Restart循环、重启手机或重新boot候选。
- power observer新增独立startup拒绝记录，包含真实温度快照与是否消耗slot；不改写实际result或把失败变成成功。
- 新current-boot helper采用小核进程亲和性，等待冷却而非循环boot；完全不arm正常关机。
- 修改后的observer/wrapper已root-only保存并读回，**尚未执行新一轮按键观察**。
- 离线286项：285通过，1可选QEMU跳过。冷却测试是纯软件边界测试，不冒充当前硬件按键验收。

普通boot分区仍为已安装#10；本次只有fastboot RAM boot，没有flash。没有NV/凭据读取、没有DSP/WLAN启用、没有整机休眠。

证据：`out/power-key-cooldown-20261028/`；前序准备见[POWER-KEY.md](POWER-KEY.md)，USB权限阻塞在独立resume目录保留。
正常关机/冷开机必须在真实长按事件通过后，另行明确armed并有人值守地测试。
