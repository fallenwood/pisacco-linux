# CN校验取证R2已修复并持久启用：原始INDOOR_ONLY核验通过，2.4GHz联网成功

用户请求：**“继续修复”**。新版本只更换取证路径，不删CN功率/DFS/NO-OUTDOOR/no-IR/HT20检查。

## 当前已实测

- 新`picasso-wifi-radio-cn-raw.service` **enabled/active，PID166423**，session `24ad8293b0d1`。
- 原始同PHY、完整split nl80211 dump与iw仅用于库存的频点列表交叉一致：**41个总频点，24个启用20MHz信道**。
- 实际raw attr14确认**5180/5200/5220/5240/5260/5280/5300/5320MHz**均有INDOOR_ONLY；不是预期规则或文本补字生成的标志。
- global CN，实际EIRP/DFS/NO-OUTDOOR/no-IR子集、永久MAC和HT20均通过。
- 空闲UP先观察45秒/85次样本，然后在同一无线所有者、同一DSP lifecycle上，仅一次Chaldea-2.4G激活，**0.713秒nmcli返回0**。
- 新鲜WPA2-RSN CCMP握手、授权station、DHCP、实际HT20、WLAN绑定新DNS事务、证书验证HTTPS200均通过，IPv4 **192.168.1.64/24**。
- 之后90秒/87次样本均观察到目标关联/管理UP；进一步实时检查NM100、station authorized、UP+LOWER_UP、HTTPS`200 0 577`通过。
- 这是短期原生成功和当前快照，不是连续无丢包/长期稳定保证；历史2G BEACON_MISS失联、5GHz超时根因没有因此被证明全部修好。

## 修复方式（未绕过保护）

R2目录`/opt/picasso-wifi-cn-raw/`：

- `wifi-cn-raw-radio-service.py`只覆盖R1的**audit方法**；R1精确国家码映射/字段命名以及原startup/guard/lease/cleanup继承不动。
- `wifi-nl80211-channels.py`保留诊断阶段同一5055c3…原始GET-only采集版本，现由R2明确集成调用；历史诊断时未集成的说明不代表当前调用状态。
- `audit-wifi-regulatory-cn-raw.py`使用原CN参考/规则解析器，但直接判断原始bool和其observed attribute IDs。
- `policy.json` root0400固定原生参考和采集器/审计器hash。

每次审计从`wlan0/phy80211/{index,name}`取得实际身份，要求原始回复只含该PHY；检查协议split支持、完整dump、精确内核、41点全库存一致、原始mBm、旗标/attr ID一致。
原始属性确实缺失、DFS/功率越界、错误PHY、分片中断、库存不完整、属性冲突或dump前后监管变化仍拒绝。**不是把`indoor only`拼进文本，也不是删除室内要求。**
`iw phy info`仅继续用于HT20/无VHT及频点库存，不再用其缺失的indoor文本判断bit。
原始bit存在只证明内核的限制表示，不证明物理室内地点、RF发射认证、充电/电池安全。

## 常驻与保存

- R2先文件与政策无RF检查、一次原生启动且45秒UP/raw验证通过，再设为默认开机enabled；本轮没有重启验证下次开机。
- 旧SG/R1CN和前次attended失败单元、错误、源码均保留。R1CN现disabled/failed，未reset-failed、重启旧failed或删marker。
- **新默认仍仅保持网卡UP，不自动关联SSID/回退/循环重连**。本次联网是用户修复范围内单独的一次2G连接，凭据仍在原root私有目录，没有读取/哈希/导出PMK。
- 普通未关联/掉线保留接口和受保护所有者；温控45°C、DSP/backend/精确3秒Root PID lease/监管/身份/CPU等真正安全故障仍完整关闭，Restart=no。
- 原自动预算SHA `02213b13308d69248bc68a73d3a91da926485986359b36b6e3e1a7c855bcc555`原样，不因成功联网或新服务重置。
- 活跃dirty属于session24ad8293b0d1，是正常DSP工作生命周期。**不能删除，不能用上轮cleanup或旧checkpoint宣称当前已清理。**
- Watchdog8/Stop45/Memory256MiB/CPU0–3、CPU6/7运行期1094400kHz及退出恢复、私有四FD/RAM/MPSS手动启动与恢复禁用保持。
- 本轮R2仍运行，未为了测试cleanup再停止/重启一次；cleanup继承路径及离线测试保留，不声称本轮进行了R2完整stop验收。

查看当前状态（手机内）：

```sh
sudo systemctl status picasso-wifi-radio-cn-raw.service
ip link show wlan0
sudo iw dev wlan0 link
```

明确需要关闭时仅stop新R2所有者；不要启动旧SG/R1服务或另一个完整worker去争用同一DSP/RUN目录。
LAN192.168.1.0/24 TCP22/drop、公钥均保持；可用LAN地址需以实时DHCP为准，新公钥从另一机器登录仍未单独验收。
SELinux实际仍Permissive、屏幕原生tty1/音量UP/15秒idle、待激活power DTB/自动开机限制未改变。本次无boot写/重启/PMIC/原始NV或凭据/SSH私钥读取导出。

## 证据

`out/wifi-cn-raw-fix-20261030T090245Z/`包括R2源码/政策/unit/readback、三组<40°C开始读数、原始实际bit、45秒UP、一次联网验证、90秒关联观察和实时复核。
当前session采样峰值37.4°C，45°C abort不变；不同阶段读数不混作开始温度。
离线412项：411通过、1可选QEMU跳过。新16项证明“raw bit存在、iw没有文本也应通过”，并继续拒绝真正缺bit/坏证据/错误PHY/库存缺失/越功率/缺DFS等。
