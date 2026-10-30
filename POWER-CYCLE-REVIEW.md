# 第二轮有效按键与USB关机窗口通过；新启动核验待USB地址恢复（阶段记录）

**后续USB已恢复，新boot ID/原默认#10/持久PID1接受/旧日志poweroff完成/完整性均已核验。
不需再执行本页USB恢复或关机试验；只差用户确认是否手动按电源才开机。最新见 [POWER-CYCLE-POSTBOOT.md](POWER-CYCLE-POSTBOOT.md)。
本页保存缺IPv4与SSH连接失败的原事实，不覆盖为成功。**

用户报告“关机开机试验完成”。这不是全部验收已完成的声明。

## 已有真实证据

- 真实KEY_POWER116 down=`80474.983971`、release=`80477.345143`，持续 **2.361172秒**。
- 真实按下满2秒后出现松开提示；release事件产生`orderly_poweroff`，不是模拟/离线事件。
- armed控制器SSH退出码0，符合已审计的标准PID1请求路径；尚待读回手机XFS上的最终意图/接受记录。
- USB实际断开，随后连续20秒无自动返回，原回执`automatic_return_without_power_press=false`。
- 用户随后报告完成开关机，当前同身份Linux USB已经重新枚举。
- 第一轮4.559807秒/1.682461秒失败及其消费标记继续保留，不把它们改为通过。

## 当前未完成项，不重做试验

主机已核对同一`cdc_ncm`/`1d6b:0104`/既定USB网卡MAC，但该接口没有`192.168.7.1/24`。
固定主机密钥SSH连接在握手前超时，尚未读取新boot ID、运行FDT或持久关机记录。
完整脚本的`user-off-confirmed.json`和`after-manual-power-on.json`本地回执未生成；
聊天完成报告与已保存的USB窗口分开记录，不补造缺失回执。

**不要重跑关机、RAM boot、fastboot或刷写。** 仅在主机正常本地交互终端运行：

```sh
cd /home/vbox/droid
./picasso/tools/restore-screen-usb.sh
```

这只恢复独立核对的手机USB接口，不改Wi-Fi、默认路由、DNS或NAT。
Agent主机NoNewPrivs=1，不绕过权限限制；若sudo要认证，只在本地终端输入。
恢复后回复“已恢复”，并确认是否由你再次按电源后才开机。

之后继续同一启动的只读核验：新boot ID、预期原默认#10 FDT、XFS真实release/请求记录、屏幕服务/15秒idle/内核租约、温度。
正常关机与硬件手动开机的整体接受仍pending；USB消失不等于已证明PMIC各路无电。

本轮没有新增关机/重启/flash/suspend/按键注入/NV或凭据访问；只是读取和保存已发生试验的本地记录。
安装boot保持原默认wifi2#10，电源键候选及自动关机服务未持久化。

证据：`out/power-cycle-review-20261028/`；前阶段见[POWER-SHUTDOWN-GUIDED2.md](POWER-SHUTDOWN-GUIDED2.md)。
