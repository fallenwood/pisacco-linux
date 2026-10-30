# 常驻保持真实wlan0管理状态UP：普通未连接/掉线不卸载网卡 / Persistently keep real wlan0 administratively UP: ordinary disconnection does not unload the interface

> 隐私 / Privacy: 本页中的网络、设备、密钥标识与外部本地路径已用占位符脱敏；命令和含占位符的证据路径不能原样重放。
> Network, device and key identifiers and external local paths are redacted; commands and evidence paths containing placeholders must not be replayed verbatim.

> 文档范围 / Scope: 本文保留SG常驻UP阶段及后续失败更新；旧服务、命令与“当前”均为历史快照，不应作为最新所有者操作指引。 / This preserves the SG persistent-UP stage and subsequent failure updates; old services, commands, and “current” are historical snapshots, not instructions for the latest owner.

## 中文

> 最新默认所有者已修复为`picasso-wifi-radio-cn-raw.service`，见[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)：原始CN限制核验通过并单次2.4G联网、90秒关联观察成功，当前enabled/active。本页旧SG服务disabled/failed保存为历史，不能重启它与新所有者争用。新默认开机只保持UP不自动关联，本次连接是单独请求。

> **最新国家码阶段见[WIFI-CN.md](WIFI-CN.md)**：global已确认为CN，独立CN政策/审计器已持久安装，旧SG服务disabled/failed。新CN服务唯一一次启动因5180MHz室内限制标志未能核验而failed，当前WLAN不存在/DSP offline/dirty absent，未尝试SSID，不要重启本页旧SG单元。
>
> **此前SG服务的实际状态：未保持连接，网卡已因监管检查失败安全关闭。** 用户随后指定${FALLBACK_SSID}，在相同session/既有网卡上一次`nmcli`0.672秒返回0，但控制器立即报`ValueError: Neither SG nor verified intersection candidate`。当前服务enabled/failed/MainPID0、真实WLAN absent/DSP offline/dirty absent，完整cleanup/checkpoint/CPU/core恢复经独立审计。record中上次`administrative_up=true`是失效快照，不代表接口还在。
> 此次没有第二次连接、无线重启或监管绕过；错误发生时的实际域原文没有捕获，不能推断CN/US/00或当作硬件/路由器已确诊。控制器外部NM关联与SG重请求/严格审计交接可能有竞态，须进一步确认并保持实际信道/EIRP/DFS保护；任何修正后的真机重试需另行明确。证据`out/wifi-connect-2g-20261030T072042Z/`。以下成功运行是历史空闲UP阶段，而非当前状态。

用户请求：**“不要关闭wlan 保持网卡一直在线”**。
新模式保持真实无线接口、手动MPSS和受保护后端运行，**UP不等于已关联路由器、取得IP或能访问Internet**。

## 历史空闲UP启动实测/已持久化

- `picasso-wifi-radio.service`已enabled/active，MainPID146896。
- 新控制器session `${SESSION_9}`，状态`radio_up_idle`；正常采样45秒/85次均有真实`wlan0`和`UP` flag。
- 当前没有SSID关联、没有IPv4，NM状态`30 (disconnected)`；没有发起任何SSID激活，`attempts=[]`。
- Linux `operstate=DOWN`、无`LOWER_UP`/载波，是未关联AP时正常表现。**不是管理状态被关闭**，不要用operstate冒充或否定UP flag。
- Controller、DSP、私有RMTFS/TFTP后端仍运行，dirty属于正在工作的本session，不能删除或拿上一轮cleanup宣称本轮已清理。
- 45秒运行观测峰值35.4°C，原生ready前保存三组全传感器<40°C读数；后续状态以实时检查为准，不承诺永远不触发安全退出。

新程序`tools/wifi-radio-service.py`安装于`/opt/picasso-wifi-radio/`，继承SHA256=`428495f9…`原worker的startup、guard、PID租约、私有四FD后端和完整cleanup，**原worker/config字节未改**。
只换掉“连接失败即退出整个worker”的连接驱动循环，改为检查真实网卡与安全不变量的循环。

## 普通掉线行为与安全边界

- 未关联或普通连接失败：保留`wlan0`、管理UP、正常Root PID lease/后端/DSP，不再因无SSID/无carrier卸载无线。
- 此模式**不自动尝试SSID/回退/重试**；替代旧“初连＋3次后卸载”默认服务。连接SSID由新的明确请求或手机上的标准NM操作发起。
- 原`picasso-wifi-reconnect.service`从开机目标disable，但原failed状态、四次预算、所有历史和marker都保留，预算SHA仍`${PRIVATE_BUDGET_SHA256}`。
  没有reset-failed，也没有重放旧单元或刷新预算。
- `picasso-wifi.service`、`picasso-wifi-auto.service`与旧一次性单元仍是旧失败记录，不要同时启动它们；它们会拒绝现有无线或与新所有者冲突。
- 45°C/无效传感器、DSP停止或崩溃、backend/3秒精确PID租约失效、MAC/监管/CPU/防火墙不变量破坏、外部把管理UP关闭，或明确systemctl stop，仍必须安全退出。
  **不能为“永远UP”删掉这些保护**；Restart=no，故障不自动循环重新启动。

8秒watchdog、启动180秒/停止45秒、CPU0–3、Memory256MiB、CPU6/7运行期1094400kHz及退出恢复保持。
正常运行不进行系统休眠，也不更改PMIC/充电/复位设置。

## 监管域与防火墙

持续核验真实PHY/SG信道EIRP/DFS子集、永久MAC、HT20、不进入未授权SSID。
没有关联AP时SG实际表本轮为**36个20MHz信道**，仍由原审计器逐项确认是SG子集；此前关联AP国家提示后的98交集为24个，这是不同状态的实际交集，不是扩展规则/功率或伪造能力。
观察到新的已授权SSID时重新请求SG并审计；安全检查失败仍会退出，不通过保持UP绕过监管。

未关联时NM可能没有连接zone，本服务只把**未分配的wlan0**runtime绑定回原`drop`。
普通断开时NM若移除绑定，下一次检查重建这个未分配绑定；遇到其他zone不悄悄改成trusted，而是安全退出。
原LAN${LAN_SUBNET} TCP22 rich rule/用户公钥/密码禁用/root禁用保留，未改变主机网络、默认路由、DNS或NAT。

## 历史使用方式（关联交接问题尚未修复，不要重放连接命令）

最新2.4GHz尝试已在外部NM激活后触发监管保护；下列5GHz示例并未执行，不能据此再试。服务当前失败，需先诊断并另行安排修正后的运行验收。

查看管理UP/关联与服务：

```sh
ip link show wlan0
sudo iw dev wlan0 link
sudo systemctl status picasso-wifi-radio.service
```

如明确需要**只尝试${PRIMARY_SSID}**，在保持本控制器运行、使用现有受保护radio的前提下，可由root通过既有profile和native passwd-file激活：

```sh
sudo nmcli --wait 20 connection up id picasso-auto-${PRIMARY_SSID} ifname wlan0 \
  passwd-file /var/lib/picasso-wifi/credentials/${PRIMARY_SSID}.passwd
```

不要读取/复制该文件内容、用--show-secrets或把PMK放argv。此命令只发起一次指定激活，不启用旧worker或重置自动预算。
新radio循环只观察允许SSID的关联元数据和radio安全，**不把关联观察当作新的CCMP/DHCP/DNS/HTTPS验收**；连接是否真正能上网需另行实时核验。
连接失败后通常仍UP/未关联，本控制器继续持有RMTFS/MPSS，后续请求不应重新跑完整startup或cleanup。

只有明确要关闭无线，才：

```sh
sudo systemctl stop picasso-wifi-radio.service
# 取消开机保持UP（不会自动停止当前运行）：
sudo systemctl disable picasso-wifi-radio.service
```

## 证据和未验收项

证据`out/wifi-radio-up-20261030T054548Z/`；新程序/unit/readback、默认服务切换、原failed/budget备份、启动温度及45秒85次UP样本独立保存。
离线372项，371通过、1可选QEMU跳过，包括“不关联也有效”“普通失联转idle而非cleanup”“安全故障仍cleanup”“UP与operstate分离”。
真机验证了启动和未关联持续UP，**本次未再发起${PRIMARY_SSID}连接或人为断网来声称已实测全部失联路径**。
此前反复掉线/5GHz超时根因未修复；不能把保持接口存在当作修复、联网、RF/充电/长期稳定性通过。
本次未刷boot/重启，仍原#10/FDT62ac当前boot；新power镜像/下一次开机激活仍未验收。SELINUX配置disabled但实际内核仍Permissive，不在本阶段改动。

## English

> The latest default owner at this update was fixed as `picasso-wifi-radio-cn-raw.service`; see [WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md): raw CN restrictions passed validation, a single 2.4G connection and 90-second association observation succeeded, and the service was enabled/active. This page's old SG service remains disabled/failed as history; do not restart it to compete with the new owner. The new default only keeps UP at boot without automatic association; this connection was separately requested.

> **See [WIFI-CN.md](WIFI-CN.md) for the latest country-code stage at that update**: global CN was confirmed, an independent CN policy/auditor was persistently installed, and the old SG service was disabled/failed. The new CN service's only startup failed because the 5180MHz indoor-restriction flag could not be verified; WLAN was absent/DSP offline/dirty absent, with no SSID attempted. Do not restart this page's old SG unit.
>
> **The earlier SG service's actual state: it did not retain connectivity; the interface was safely shut down after regulatory-check failure.** The user subsequently specified ${FALLBACK_SSID}. In the same session/on the existing interface, one `nmcli` call returned 0 in 0.672 seconds, but the controller immediately reported `ValueError: Neither SG nor verified intersection candidate`. The service was enabled/failed/MainPID0, real WLAN absent/DSP offline/dirty absent; complete cleanup/checkpoint/CPU/core restoration passed independent audit. The previous `administrative_up=true` in the record was a stale snapshot, not evidence that the interface still existed.
> No second connection, wireless restart, or regulatory bypass occurred. The actual domain text at the error was not captured; CN/US/00 cannot be inferred, nor can hardware/router diagnosis be claimed. External NM association and SG re-request/strict-audit handoff may have a race, requiring further confirmation while retaining actual channel/EIRP/DFS protection; any hardware retry after correction needs separate explicit authorization. Evidence: `out/wifi-connect-2g-20261030T072042Z/`. The successful operation below is historical idle-UP operation, not current status.

User request: **“Do not shut down wlan; keep the network interface online all the time.”**
The new mode keeps the real wireless interface, manual MPSS, and guarded backend running; **UP does not mean association with a router, an IP address, or Internet access**.

### Historical idle-UP startup measurements/persistence

- `picasso-wifi-radio.service` was enabled/active, MainPID146896.
- New controller session `${SESSION_9}`, state `radio_up_idle`; all 85 normal samples over 45 seconds had real `wlan0` and the `UP` flag.
- No SSID association or IPv4 at that time; NM state `30 (disconnected)`; no SSID activation was initiated, `attempts=[]`.
- Linux `operstate=DOWN`, no `LOWER_UP`/carrier, is normal when not associated with an AP. **Administrative state was not switched off**; operstate must not stand in for or negate the UP flag.
- Controller, DSP, and private RMTFS/TFTP backend continued running; dirty belonged to this working session. It must not be deleted, and the previous round's cleanup cannot establish this round's cleanup.
- The 45-second observation peaked at 35.4°C; three all-sensor groups <40°C were saved before native ready. Later status requires live checks; there is no promise that safety exit will never trigger.

New program `tools/wifi-radio-service.py` was installed at `/opt/picasso-wifi-radio/`, inheriting startup, guard, PID lease, private four-FD backend, and complete cleanup from the original worker SHA256=`428495f9…`; **the original worker/config bytes were unchanged**.
Only the connection-driving loop that “exits the whole worker on connection failure” was replaced with a loop checking the real interface and safety invariants.

### Ordinary link-loss behavior and safety boundaries

- Unassociated or ordinary connection failure: keep `wlan0`, administrative UP, normal Root PID lease/backend/DSP; no wireless unload merely because no SSID/carrier exists.
- This mode **does not automatically attempt SSIDs/fallback/retries**; it replaces the old default “initial connection plus 3 retries, then unload” service. SSID connections are initiated by a new explicit request or standard NM operations on the phone.
- Original `picasso-wifi-reconnect.service` was disabled from boot targets, but its failed state, four-attempt budget, all histories, and markers were retained; budget SHA remained `${PRIVATE_BUDGET_SHA256}`.
  No reset-failed, old-unit replay, or budget refresh occurred.
- `picasso-wifi.service`, `picasso-wifi-auto.service`, and old one-shot units remain old failure records; do not start them simultaneously. They reject existing wireless or conflict with the new owner.
- 45°C/invalid sensors, DSP stop/crash, backend/3-second exact-PID lease failure, violated MAC/regulatory/CPU/firewall invariants, externally switched-off administrative UP, or explicit systemctl stop still require safe exit.
  **These protections cannot be removed to achieve “UP forever”**; Restart=no, without automatic restart loops on failure.

The 8-second watchdog, startup180/stop45 seconds, CPU0–3, Memory256MiB, CPU6/7 runtime1094400kHz, and exit restoration remain.
Normal operation does not suspend the system or change PMIC/charging/reset settings.

### Regulatory domain and firewall

Continuously verify real PHY/SG channel EIRP/DFS subset, permanent MAC, HT20, and no entry into unauthorized SSIDs.
Without AP association, the actual SG table this round had **36 20MHz channels**, each still audited as an SG subset by the original auditor; the earlier 98 intersection after an associated AP's country hint had 24. These are actual intersections in different states, not expanded rules/power or fabricated capabilities.
On observing a new authorized SSID, SG is requested again and audited; failed safety checks still exit, without using UP to bypass regulation.

While unassociated, NM may have no connection zone; this service runtime-binds only **unassigned wlan0** back to the original `drop`.
If NM removes that binding on ordinary disconnection, the next check recreates the unassigned binding; another zone causes safe exit, not silent reassignment to trusted.
The original LAN${LAN_SUBNET} TCP22 rich rule/user public key/password-disabled/root-disabled settings remain; host network/default route/DNS/NAT were unchanged.

### Historical usage (association handoff remains unfixed; do not replay connection commands)

The latest 2.4GHz attempt triggered regulatory protection after external NM activation; the 5GHz example below was not executed and does not authorize another attempt. The service was failed at this stage; diagnosis and separately arranged post-correction runtime acceptance are required first.

Check administrative UP/association/service:

```sh
ip link show wlan0
sudo iw dev wlan0 link
sudo systemctl status picasso-wifi-radio.service
```

If explicitly requesting **only a ${PRIMARY_SSID} attempt**, with this controller running and the existing guarded radio, root can activate through the existing profile and native passwd-file:

```sh
sudo nmcli --wait 20 connection up id picasso-auto-${PRIMARY_SSID} ifname wlan0 \
  passwd-file /var/lib/picasso-wifi/credentials/${PRIMARY_SSID}.passwd
```

Do not read/copy the file contents, use --show-secrets, or put the PMK in argv. This command initiates only one specified activation; it neither enables the old worker nor resets the automatic budget.
The new radio loop only observes allowed-SSID association metadata and radio safety; **association observation is not new CCMP/DHCP/DNS/HTTPS acceptance**. Actual Internet connectivity requires separate live validation.
After connection failure it normally remains UP/unassociated and this controller retains RMTFS/MPSS; subsequent requests should not rerun complete startup or cleanup.

Only when explicitly wishing to shut down wireless:

```sh
sudo systemctl stop picasso-wifi-radio.service
# Disable keeping UP at boot (does not automatically stop the current run):
sudo systemctl disable picasso-wifi-radio.service
```

### Evidence and unaccepted items

Evidence: `out/wifi-radio-up-20261030T054548Z/`; new program/unit/readback, default-service switch, original failed/budget backup, startup temperature, and 85 UP samples over 45 seconds are saved independently.
Offline: 372 cases, 371 passed, 1 optional QEMU skipped, including “valid without association,” “ordinary loss becomes idle rather than cleanup,” “safety failure still cleans up,” and “UP distinct from operstate.”
Hardware validated startup and sustained unassociated UP; **no further ${PRIMARY_SSID} attempt or deliberate disconnection was made to claim all loss paths were measured**.
Prior repeated disconnections/5GHz timeout root causes were not fixed; keeping the interface present cannot be called a fix, connectivity, or RF/charging/long-term stability acceptance.
No boot flashing/reboot occurred; this boot remained original #10/FDT62ac, and the new power image/next boot activation remained unaccepted. SELINUX configuration was disabled but the actual kernel remained Permissive, unchanged in this stage.
