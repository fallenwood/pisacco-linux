# 电源键受限持久化：boot已写入，服务已启用，待下次正常启动

用户在明确得知“关机后仍可能自行启动”以及仅写boot/XFS普通文件的范围后回复 **“接受”**。
本次完成的是已测试电源键输入DTB的安装，以及常驻长按关机服务的部署，**不是修复自动启动**。

## 当前事实

- 唯一PARTNAME=boot、PARTUUID=`4aadcdf3-3aad-3318-a158-46642b851943`、大小134217728字节，身份/挂载/swap/holder检查通过。
- 原RAM实测候选 `002147068dd9a03b467e27cf95398b3147bf5452af411f3e6a90c443e92b2c5f` 已写入boot。
- 正好写满128MiB（镜像33820672字节，其余零填充），fsync、块缓存flush、完整分区读回通过：
  `73d32de2d7e6ddd353fe76f6a513f8cf4c8a53eddc7ec8201a5fdd994ffd2d47`。
- 写后再次通过15,285个基线文件/543,194,505字节、七个保护分区、六LUN GPT检查。
- 写入窗口最高33.4°C；本阶段全部完整性检查窗口最高35.7°C，仍严格启动<40°C/运行45°C中止。
- `picasso-power-button.service` **enabled但inactive/MainPID0**，没有在旧FDT上启动，没有产生永久服务关机intent。
- **没有重启、关机、RAM boot、合成按键、再次PON采样或PMIC写入。**
- 当前boot ID仍为`2f080316-e4da-44f0-abc6-8d2319976308`，运行原#10/FDT `62ac…`，只见音量键输入。
  下次正常启动才会使用已写入的power FDT `ecbf…`，仍是相同#10 Image/config/744模块。
- **新常驻服务的开机激活和实键验收尚未进行**，不得用离线测试/文件沙箱检查替代它。

## 常驻行为与保护

代码为`tools/power-button-daemon.py`，独立目录`/opt/picasso-power-button/`；不是启用已消耗的观察/armed/guided2脚本。

仅在单一真实`pm8941_pwrkey`/`pm8941_pwrkey/input0`、精确116位图、devt匹配且启动时未按住时独占输入。
校验root0400授权、原hold policy哈希、#10 release/config与唯一候选FDT。所有可读传感器三次<40°C后启动；
额外最多等待15秒正常输入枚举，不加载/重试驱动、不产生按键；ready前再次检查<40°C。

真实KEY_POWER **按住2～3秒后松开**才接受。短按、超过3秒、repeat/重复down、无匹配release、过期/倒序或SYN_DROPPED均不作为有效触发。
请求前再读实际held位；确认已松开、温度合格并先fsync独占intent后，唯一调用为：

```text
/usr/bin/systemctl poweroff --no-block --no-ask-password
```

每boot最多一个intent，不因服务重启重复请求。PID1接受另存独立accepted记录，不覆盖原intent；接受/作业完成不证明PMIC保持断电。
记录在`/var/lib/picasso-power-button/{history,requests}/`；运行状态`/run/picasso-power-button/session.json`。
原所有试验/采样marker均未删除或重放。启动冷却最多120秒，输入等待最多15秒；8秒watchdog、Restart=no、128MiB、CPU0–3、空能力集、只允许event0/1只读；禁止内核reboot/模块/挂载/swap/raw-io/时钟系统调用。
通过UID0常规PID1总线请求正常关机，不设任何内核直接关机回退。logind忽略电源短按/长按，drop-in只在下次启动自然生效，不热重启logind。

本次文件最终修订R2增加有界输入等待和config pin；原R1及其写入时资产哈希保留。R2已在相同硬化沙箱完成**仅文件/授权/只读PID1总线检查**，未打开输入或测试关机总线授权/实键。

## 如实保留的失败与控制器修正

1. `picasso-power-install1.service`在写前PID1 executable身份检查失败：窄能力沙箱缺少读取`/proc/1/exe`所需的CAP_SYS_PTRACE。
   没有commit记录/consumed marker；独立完整读回确认原boot仍为`f091…`。失败unit和原控制器保留。
2. 新控制器2增加该能力，同时禁止`ptrace/process_vm_*`系统调用并遮蔽`/proc/1/mem`等原始内存路径。
   **只预检**随后拒绝本服务命名空间的只读根视图（ProtectSystem=strict），没有进行写入。
3. 新控制器3保留RW XFS检查，但读取**PID1的真实挂载视图**；boot占用同时检查PID1与服务两边视图。
   同等硬化沙箱只预检成功后才执行唯一实际写入。原两份失败unit仍failed，未reset-failed。
   只预检使用128MiB；实际写入为块/文件页缓存提供256MiB runtime上限，能力/目标/热限不变；RuntimeMax120秒、内部90秒、错误停止且不自动重启/回退。

原控制器、v2、v3、所有预检/失败/完整性和实写记录都在`out/power-install-20261028/`；手机控制器在`/boot/picasso/power-install-20261028/`。
`commit-consumed`已消耗，**不允许重复启动写入控制器或删除marker**。

## 回滚与不变边界

手机root私有文件保留：

- `/boot/picasso/power-install-20261028/boot-wifi2-rollback.img`：原默认#10，SHA=`61022763…`。
- 同目录`boot-lts8-rollback.img`：原#8，SHA=`81f28d44…`。
- 原`/boot/picasso/wifi-install-20261028/`回滚文件及主机canonical `out/boot-picasso.img`均未改写。

备份不等于自动回滚/启动菜单，本机非A/B。回退需重新按身份/温度/完整性与授权边界准备，不能重跑本次写入脚本。
未写DTBO、GPT、recovery、vbmeta、NV或其他固件分区；未动S1/S2/S3、CBL/USB/SMPL触发、充电设置、reboot magic、shim或CMDLINE_FORCE。
屏幕仍是原生tty1/fbcon、15秒idle/音量上亮屏/独立内核租约，无色条、无整机休眠；PID527健康。Wi-Fi disabled/inactive，凭据/NV未读写。

## 未解决项和下一步

用户此前明确“自行启动的”仍有效：**保持关机直到手动按键的目标未通过**。
CBL_POWER锁存只支持外部供电上电方向，不等于USB_CHARGER、根因或真正断电时间。USB消失、20秒无返回、PID1接受、systemd poweroff完成均不能升级为保持断电/手动冷开机验收。
本次授权只是在接受此限制后允许部分固化，不改变硬件失败结论。

当前不自动重启。待用户决定一次正常重启后，才可按新boot ID、候选FDT/config、常驻服务ready及真实输入元数据核对激活；新的破坏性关机/冷开机试验仍应另行明确安排。
不要长按超过3秒来试探硬件复位阈值。Linux服务不能实现关机状态开机，不能以黑屏/休眠/循环poweroff冒充关机。

最终离线回归：**334项，333通过，1项可选QEMU跳过**，不代表上电激活、保持断电、原生屏幕目视、电气/充电/长期稳定性通过。
