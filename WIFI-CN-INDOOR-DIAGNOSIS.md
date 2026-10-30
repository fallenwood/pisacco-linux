# CN室内限制拒绝：已定位校验器取证错误，实际PHY原始标志仍待验

> 后续明确“继续修复”已完成[WIFI-CN-RAW-FIX.md](WIFI-CN-RAW-FIX.md)：R2实际同PHY原始bit确认5180–5320的8点INDOOR_ONLY存在，41库存/24启用CN20MHz验证通过，常驻服务enabled/active，单次2.4G关联/网络及90秒观察通过。没有删室内检查。以下本页是只读诊断阶段快照，“未接入/未测live bit/无线关闭”不再代表最新状态；旧失败保留。

用户请求“继续排查”。本轮**只读诊断，没有启动无线、扫描、激活SSID、设置国家码或更改手机服务/校验政策**。

## 已确定的问题：取证路径错误，不是已经证明硬件缺少限制

**我新增的CN校验器在`iw phy … info`文本中查找`indoor only`，但手机的iw6.17根本不打印该属性。**
因此，前两次“5180MHz缺少室内标志”的结果不能证明内核/驱动没有落实NO-OUTDOOR；即便原始属性存在，这个文本检查也会拒绝。
失败单元、错误、cleanup仍是真实历史，不能改写为联网成功。

匹配手机的证据：

- Native：`iw-6.17-2.fc44.aarch64`，SourceRPM `iw-6.17-2.fc44.src.rpm`，`rpm -V iw`返回0、无差异。
- `/usr/bin/iw` SHA256 `2c8f212f7ce09350e300690350cd69bd8bc98aeb0b5bf9b36ea09d58b0311b4d`。
- Fedora44同版SourceRPM经OpenPGP/header/payload校验全部OK，签名指纹`36f612dcf27f7d1a48a835e4dbfcf71c6d9f90a6`；没有Fedora额外patch。
- SourceRPM SHA256 `e5e7738af71b61b22a15d1af11a946289a219158e1de3ccbedadbcd8a6023fe3`。

原版`iw-6.17/info.c:484–525`的频率打印分支仅输出disabled、no IR/passive/no ibss、radar及功率，**不读取`NL80211_FREQUENCY_ATTR_INDOOR_ONLY`**；整个info.c没有这个属性引用。
`iw list`使用同一printer，所以换成list也不解决；`phy.c`的channels printer同样没有该属性处理。

另一个已排除的猜测：`info.c:958–970`会查询协议特征，在支持时自动请求split dump；手机原生`iw features`回报`0x1/* split wiphy dump`。
所以不能把这次问题简单归咎于“iw phy info一定用了旧的非split请求”。当前确定的是**收到了也不打印**。

## 内核/驱动路径

精确Linux6.18.58源码中：

1. `net/wireless/reg.c:1568–1580`，`map_regdom_flags()`明确把`NL80211_RRF_NO_OUTDOOR`映射到`IEEE80211_CHAN_INDOOR_ONLY`。
2. `reg.c:1750–1820`，信道规则更新将orig/bw限制与映射后的规则flags合并；不能为绕过EEPROM/US板级限制更换regpair或BDF。
3. `net/wireless/nl80211.c:1330–1342`在large/split输出中导出`NL80211_FREQUENCY_ATTR_INDOOR_ONLY`。
4. ath/regd.c的相关notifier路径修改radar/no-IR等，已读到的这些路径没有显式清除INDOOR_ONLY；**这仍不是对已卸载PHY实际bit的测量**。

UAPI头文件还明确INDOOR_ONLY是使用条件，不能因为“手机插在电脑USB上”就推断物理室内或已验证供电来源；本轮没有发送`REG_INDOOR`环境提示、读取PMIC或改充电设置。

## 已准备的只读原始属性采集器（未接入现有服务）

新增`tools/wifi-nl80211-channels.py`，只允许：

- generic-netlink GET_FAMILY解析nl80211；
- GET_PROTOCOL_FEATURES，必须支持split；
- 带SPLIT_WIPHY_DUMP的GET_WIPHY，支持指定PHY index。

直接解析freq、原始mBm功率、disabled/no-IR/radar/INDOOR_ONLY/no20MHz等，按PHY和频点合并分片；拒绝中断/截断/重复冲突/错误序号/非内核回复，8秒/4MiB/2048消息硬限。
没有SET、scan、模块加载、设备创建、固件或NV操作，也不输出其他接口MAC/SSID/密钥。
数值常量由当前项目精确UAPI头通过小型C程序生成核对：INDOOR_ONLY=14、SPLIT_WIPHY_DUMP=174等；不是猜值。

手机上仅用临时`python -c`执行了只读GET：协议支持、完整dump、`phys=[]`，同时WLAN不存在/DSP offline。
**空PHY仅验证传输/解析路径，不证明本机运行时INDOOR_ONLY=true。** 未将采集器安装为服务或替换手机旧审计器。

## 离线复现

`out/wifi-cn-indoor-diagnosis-20261030T084546Z/reproduce-display-omission.py`：

- 合成一条明确带attr14的5180MHz/2300mBm频点（明确是合成，不是手机测量）；
- 原始TLV解析保留`indoor_only=true`；
- iw6.17当前文本格式丢弃该属性；
- **原样旧CN审计器仍报同一错误**，复现即使内核bit存在也被文本检查错误阻断。

396项离线测试：395通过、1可选QEMU跳过。新12项覆盖原始attr14、缺失标志、坏flag/TLV、disabled功率、分片一致性、GET-only限制、中断dump、空PHY不算验收等。

## 正确修复方向和当前状态

下一步应保留原CN规则/功率/DFS/NO-OUTDOOR检查，只把取证源替换成**相同PHY的完整原始nl80211属性**；真实属性缺失或dump不完整仍拒绝。
不能用全局CN字样、期望规则、no-IR或人工拼`indoor only`字符串代替真实bit，也不能删检查后称修好。
接入控制器、更新政策pin及有界原生启动/关联需下一步明确安排；本轮旧CN源SHA53aa…、auditorSHAaf60…、政策/服务与失败状态均未改。

当前仍global CN、wlan0不存在、MPSS offline、dirty absent，自动预算SHA02213b13…不变；boot不变，USB SSH可用。
此前5GHz激活超时与2.4GHz自然BEACON_MISS失联仍是独立未解决问题，显示/审计错误的定位不等于无线已稳定、已联网或RF/充电安全通过。
