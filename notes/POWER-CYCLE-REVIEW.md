# 第二轮有效按键与USB关机窗口通过；新启动核验待USB地址恢复（阶段记录） / Second-round valid key press and USB shutdown window passed; new-boot checks awaiting USB address recovery (stage record)

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 历史阶段记录，保留后续更新与当时状态；同目录链接指向配套笔记，仓库代码及证据路径以仓库根目录为基准。 / Historical stage record preserving follow-up updates and the state at the time; peer links refer to notes in this directory, and repository code/evidence paths are repository-root-relative.

## 中文

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

主机已核对同一`cdc_ncm`/`1d6b:0104`/既定USB网卡MAC，但该接口没有`${HOST_USB_IP}/24`。
固定主机密钥SSH连接在握手前超时，尚未读取新boot ID、运行FDT或持久关机记录。
完整脚本的`user-off-confirmed.json`和`after-manual-power-on.json`本地回执未生成；
聊天完成报告与已保存的USB窗口分开记录，不补造缺失回执。

**不要重跑关机、RAM boot、fastboot或刷写。** 仅在主机正常本地交互终端运行：

```sh
cd "${REPO_ROOT}"
tools/restore-screen-usb.sh
```

这只恢复独立核对的手机USB接口，不改Wi-Fi、默认路由、DNS或NAT。
Agent主机NoNewPrivs=1，不绕过权限限制；若sudo要认证，只在本地终端输入。
恢复后回复“已恢复”，并确认是否由你再次按电源后才开机。

之后继续同一启动的只读核验：新boot ID、预期原默认#10 FDT、XFS真实release/请求记录、屏幕服务/15秒idle/内核租约、温度。
正常关机与硬件手动开机的整体接受仍pending；USB消失不等于已证明PMIC各路无电。

本轮没有新增关机/重启/flash/suspend/按键注入/NV或凭据访问；只是读取和保存已发生试验的本地记录。
安装boot保持原默认wifi2#10，电源键候选及自动关机服务未持久化。

证据：`out/power-cycle-review-20261028/`；前阶段见[POWER-SHUTDOWN-GUIDED2.md](POWER-SHUTDOWN-GUIDED2.md)。

## English

**Follow-up USB recovery completed; new boot ID/original default #10/durable PID1 acceptance/old-log poweroff completion/integrity were verified.
The USB recovery or shutdown trial on this page need not run again; at that update only user confirmation of manual power-key startup remained. Latest: [POWER-CYCLE-POSTBOOT.md](POWER-CYCLE-POSTBOOT.md).
This page retains the original missing-IPv4/SSH-connection failures rather than overwriting them as success.**

The user reported “关机开机试验完成” (“power-off/on trial completed”). This is not a declaration that all acceptance is complete.

### Existing real evidence

- Real KEY_POWER116 down=`80474.983971`, release=`80477.345143`, duration **2.361172 seconds**.
- A release prompt appeared after the real key had been held for2 seconds; the release event produced `orderly_poweroff`, not a simulated/offline event.
- Armed controller SSH exit code0, consistent with the audited standard PID1 request path; final intent/acceptance record on phone XFS still awaited read-back at this stage.
- USB actually disconnected, then did not return automatically for20 consecutive seconds; original receipt `automatic_return_without_power_press=false`.
- The user later reported power cycling completed, and Linux USB with the same identity had re-enumerated.
- First-round4.559807-second/1.682461-second failures and their consumed markers remain; they are not rewritten as passed.

### Incomplete checks at that stage; do not repeat the trial

The host checked the same `cdc_ncm`/`1d6b:0104`/specified USB NIC MAC, but the interface lacked `${HOST_USB_IP}/24`.
Pinned-host-key SSH timed out before the handshake; new boot ID, running FDT, and durable shutdown records had not been read.
The full script's local `user-off-confirmed.json` and `after-manual-power-on.json` receipts were not generated.
The chat completion report and saved USB window are recorded separately; missing receipts are not fabricated.

**Do not rerun shutdown, RAM boot, fastboot, or flashing.** Only use the normal local interactive host terminal for the recovery needed at that stage:

```sh
cd "${REPO_ROOT}"
tools/restore-screen-usb.sh
```

This restores only the independently verified phone USB interface, not Wi-Fi, default route, DNS, or NAT.
Agent host NoNewPrivs=1; permission limits are not bypassed. Enter sudo authentication only in the local terminal.
After recovery, reply “已恢复” (“restored”) and confirm whether another power-key press was needed to start.

Then continue read-only checks of that same boot: new boot ID, expected original default #10 FDT, XFS real release/request record, screen service/15-second idle/kernel lease, temperature.
Overall acceptance of normal shutdown and hardware manual startup remained pending; USB disappearance does not prove all PMIC rails unpowered.

This round added no shutdown/reboot/flash/suspend/key injection/NV or credential access; it only read/saved local records of the already executed trial.
Installed boot remained original default wifi2#10; power-key candidate and automatic shutdown service were not persistent.

Evidence: `out/power-cycle-review-20261028/`; preceding stage: [POWER-SHUTDOWN-GUIDED2.md](POWER-SHUTDOWN-GUIDED2.md).
