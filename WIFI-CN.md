# 国家码由SG切换CN：配置已写入/全局CN已确认，PHY室内限制校验未通过

> 最新已修复取证并原生通过，见[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)。R2实际raw attr14核验通过且2.4G联网/90秒观察成功，服务enabled/active；原SG/R1CN和重试失败都保留disabled。以下错误/离线信息为历史，不要按本页旧单元管理当前无线，更不能删除新session的活跃dirty。

> **后续只读排查已确认取证逻辑错误**：匹配手机的签名iw6.17源码根本不在info/list/channels文本输出原始INDOOR_ONLY，因此本页“未显示标志”的失败不能证明内核/驱动没落实限制。未删除保护或改手机政策；只准备原始nl80211 GET采集器，实际live PHY bit仍未测、无线仍关闭，见[WIFI-CN-INDOOR-DIAGNOSIS.md](WIFI-CN-INDOOR-DIAGNOSIS.md)。本页原拒绝/清理记录保留，不改写为联网成功。

> 后续用户明确“重试”，单独新runtime单元`picasso-wifi-cn-attended-20261030T083536.service`/session16556ba566ae，在相同原样CN政策下只初始化一次，仍报5180MHz室内限制标志检查失败；**未激活任何SSID**，当前WLAN absent/DSP offline/dirty absent，独立cleanup/checkpoint/assets复核通过。旧SG/CN失败单元没有restart/reset，global CN、预算22不变；该次session最高35.7°C，三组开始读数<40，证据`out/wifi-cn-retry-20261030T083536Z/`。以下是首次CN配置阶段历史，不能把新请求误计为本阶段自动重试或声称已经联网。

用户请求：**“从SG切换到CN”**。CN必须与设备实际所在地一致，仅适用于中国大陆。

## 当前真实状态

- 内核`iw reg get`全局确认为`country CN: DFS-FCC`，不是只改配置字符串。
- 手机`/opt/picasso-wifi-cn/`保存CN原生规则参考、独立审计器、窄适配控制器和root0400政策；新`picasso-wifi-radio-cn.service`已持久安装/设为enabled。
- **新CN服务真机启动未通过，当前failed/MainPID0、真实wlan0不存在、MPSS offline，不能联网，也不能宣称保持UP成功。**
- Session `e34e863ebda1`，本阶段唯一一次无线初始化；`attempts=[]`，没有连接Chaldea或Chaldea-2.4G、无SSID回退/重试。
- Exact error：`ValueError: Enabled 5180 MHz / 23 dBm exceeds observed CN20MHz rules or lacks DFS/indoor/IR restriction`。

## 为什么停止

内核签名regdb的CN规则对5150–5350MHz含`NO-OUTDOOR`，例如5150–5250/23dBm、5250–5350/20dBm+DFS。
真机抓取的global域是CN，PHY仍带板级US参考，并实际收紧了CN功率/信道：2G20dBm、5500–5720禁用、5.8G实际30dBm等。
**但5180/5200/5220/5240的PHY行未显示对应`indoor only`标志**；CN审计器要求确认该限制，不能仅因当前连接可能用2G就忽略其余启用信道。
因此在管理UP/SSID激活前安全退出，保留原始global+PHY规则和全部频点行。

这表示**无法完成现有检查要求**，不能据此宣布实际违法发射、硬件损坏、终端实际在室外，或假定具体驱动/iw映射根因。
没有为了通过删除NO-OUTDOOR/DFS/实际功率校验，没有伪造能力或修改BDF、校准、RF功率参数。
后续只能先只读核对内核/驱动/nl80211/iw对室内限制的表示与执行路径，再明确安排新的RF验收；本阶段无第二次RF初始化。

## 继承与持久化方式

- 原SG worker `wifi-auto-service.py` SHA428495…、旧radio控制器SHAa1d1…、原config-auto字节均未改，既有45s旧worker证明不是新的CN运行验收。
- CN适配器只覆盖三个方法：精确`iw reg set SG`请求映射为CN、CN严格审计、审计字段改为CN命名。startup/guard/独立cleanup继承原代码。
- 原生参考在**无WLAN/MPSS未启动**时从当前内核获取，SHA `0bb35936c13e1e16977c29d2f8c42e672075fd523c5faa9a6361fc74ed1160f7`。
- 当前内核`CONFIG_CFG80211_REQUIRE_SIGNED_REGDB=y`、`CONFIG_CFG80211_USE_KERNEL_REGDB_KEYS=y`；未替换regdb或签名。
- 旧SG `picasso-wifi-radio.service` **disabled/failed**，失败session `f4e1fdfc1f8d`原样保留。新CN服务虽enabled，但failed不等于已通过启动验收；不要直接重启旧SG服务、删除失败或反复启动新CN服务。
- Native ready样本0，没有声称CN45sUP或关联成功。下次开机实际激活也未验收；本次没有重启。

3组真实开始温度均<40°C、45°C abort、精确3秒Root PID lease/四FD backend、8秒watchdog/45秒cleanup、CPU0–3/256MiB/CPU6/7运行期1094400kHz及退出恢复保持。
正常cleanup提交working checkpoint、清空共享RAM、恢复原core/CPU、dirty absent，独立postcleanup assets/checkpoint审计通过；当前没有活动dirty，不可拿旧active快照宣称本轮仍运行。
原自动预算SHA `02213b13…`不变，未reset-failed、重放旧专用试验或刷新预算。

## 证据/下一步

`out/wifi-cn-20261030T075148Z/`保存原生CN参考、部署/签名策略、全局+PHY完整失败观察和最终独立审计。
离线384项：383通过、1可选QEMU跳过。首轮测试仅因Python增加类元数据字段而断言失败，原失败日志保留，修正为只比较可调用方法；不是RF失败重放。
最初参考采集器字符串转义SyntaxError发生在执行前，保留错误；之后独立源码采集器只写一次CN请求，无RF初始化。

当前只可经USB SSH管理。SSID/PMK保存位置、公钥/来源限定LAN22规则、SELinux实际Permissive、屏幕tty1/音量UP/15秒idle和待激活power DTB均未改。
没有boot写/重启/PMIC/原始NV或凭据/SSH私钥读取导出。CN配置已落盘不等于无线已可用、已联网或长期RF/充电安全通过。
