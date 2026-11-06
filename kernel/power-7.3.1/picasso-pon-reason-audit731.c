// SPDX-License-Identifier: GPL-2.0-only
/* One-shot read-only PM8150 Gen2 reason sampler for the native 7.3.1 tree.
 * NOT a power driver. The existing pmic-spmi driver owns the primary regmap.
 * Register plan: pinned MiCode picasso-q-oss 236f9eb, qpnp-power-on.c.
 * No PMIC writes, new device/probe, IRQs, notifier, timers or address API.
 */
#include <linux/device.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/kobject.h>
#include <linux/ktime.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/regmap.h>
#include <linux/spmi.h>
#include <linux/string.h>
#include <linux/sysfs.h>
#include <linux/utsname.h>

#define AUDIT_RELEASE "7.3.1-picasso-wifi2"
#define SPMI_PATH "/soc@0/spmi@c440000"
#define PRIMARY_PATH SPMI_PATH "/pmic@0"
#define ANCHOR_PATH SPMI_PATH "/pmic@5"

static bool confirm_readonly;
module_param(confirm_readonly, bool, 0400);
MODULE_PARM_DESC(confirm_readonly, "Explicitly permit one fixed read-only snapshot");

/* Identity, common status, then only banks selected by OFF_REASON. */
static const u16 addresses[] = {
	0x0104, 0x0105, 0x0805, 0x08c0, 0x08c2, 0x08c7,
	0x08c5, 0x08c8, 0x08c9, 0x08ca,
};
static u8 values[ARRAY_SIZE(addresses)];
static bool valid[ARRAY_SIZE(addresses)];
static u64 captured_ns;
static struct kobject *audit_kobj;

static int read_slot(struct regmap *map, unsigned int slot)
{
	unsigned int value;
	int ret;

	if (slot >= ARRAY_SIZE(addresses) || valid[slot])
		return -EINVAL;
	ret = regmap_read(map, addresses[slot], &value);
	if (ret)
		return ret;
	if (value > 0xff)
		return -ERANGE;
	values[slot] = value;
	valid[slot] = true;
	return 0;
}

static int capture_from_regmap(struct regmap *map)
{
	int ret, i;

	for (i = 0; i < 3; i++) {
		ret = read_slot(map, i);
		if (ret)
			return ret;
	}
	if (values[0] != 0x51 || values[1] != 0x1e || values[2] != 0x04)
		return -ENODEV;
	for (i = 3; i < 6; i++) {
		ret = read_slot(map, i);
		if (ret)
			return ret;
	}
	if (values[5] & BIT(7)) {
		ret = read_slot(map, 6);
		if (ret)
			return ret;
	}
	if (values[5] & BIT(6)) {
		ret = read_slot(map, 7);
		if (ret)
			return ret;
		ret = read_slot(map, 8);
		if (ret)
			return ret;
	}
	if (values[5] & BIT(5)) {
		ret = read_slot(map, 9);
		if (ret)
			return ret;
	}
	return 0;
}

static int capture(void)
{
	struct device_node *node;
	struct spmi_device *primary, *anchor;
	struct regmap *map;
	int ret;

	if (!confirm_readonly || !of_machine_is_compatible("xiaomi,picasso") ||
	    strcmp(utsname()->release, AUDIT_RELEASE))
		return -EPERM;
	node = of_find_node_by_path(PRIMARY_PATH);
	if (!node)
		return -ENODEV;
	if (!of_device_is_available(node) ||
	    !of_device_is_compatible(node, "qcom,pm8150") ||
	    !of_device_is_compatible(node, "qcom,spmi-pmic")) {
		of_node_put(node);
		return -ENODEV;
	}
	primary = spmi_find_device_by_of_node(node);
	of_node_put(node);
	if (!primary)
		return -ENODEV;

	ret = -ENODEV;
	node = of_find_node_by_path(ANCHOR_PATH);
	if (!node)
		goto put_primary;
	if (!of_device_is_available(node) ||
	    !of_device_is_compatible(node, "qcom,pm8150l")) {
		of_node_put(node);
		goto put_primary;
	}
	anchor = spmi_find_device_by_of_node(node);
	of_node_put(node);
	if (!anchor)
		goto put_primary;
	node = of_find_node_by_path(SPMI_PATH);
	if (primary->usid != 0 || anchor->usid != 5 ||
	    primary->ctrl != anchor->ctrl || !node ||
	    primary->ctrl->dev.of_node != node) {
		of_node_put(node);
		goto put_anchor;
	}
	of_node_put(node);

	/* No wait/probe: fail closed if binding is busy or incomplete. Holding
	 * the existing device lock prevents its devm regmap being removed.
	 * Its unmodified qcom-spmi-pmic regmap uses REGCACHE_NONE; regmap_read
	 * serializes each byte using that existing map's lock. Never reconfigure it.
	 */
	ret = -EBUSY;
	if (!device_trylock(&primary->dev))
		goto put_anchor;
	if (!device_is_bound(&primary->dev) || !primary->dev.driver ||
	    strcmp(primary->dev.driver->name, "pmic-spmi"))
		goto unlock_primary;
	map = dev_get_regmap(&primary->dev, NULL);
	if (!map) {
		ret = -ENODEV;
		goto unlock_primary;
	}
	ret = capture_from_regmap(map);
	if (!ret)
		captured_ns = ktime_get_boottime_ns();
unlock_primary:
	device_unlock(&primary->dev);
put_anchor:
	spmi_device_put(anchor);
put_primary:
	spmi_device_put(primary);
	return ret;
}

static ssize_t snapshot_show(struct kobject *kobj, struct kobj_attribute *attr,
			     char *buf)
{
	ssize_t n;
	unsigned int i;

	n = sysfs_emit(buf, "{\"scope\":\"picasso-pm8150-gen2-readonly\","
		       "\"access\":\"existing-primary-regmap\","
		       "\"kernel_release\":\"" AUDIT_RELEASE "\","
		       "\"usid\":0,\"base\":2048,\"capture_boottime_ns\":%llu,"
		       "\"registers\":{", (unsigned long long)captured_ns);
	for (i = 0; i < ARRAY_SIZE(addresses); i++) {
		n += sysfs_emit_at(buf, n, "%s\"%04x\":", i ? "," : "",
				   addresses[i]);
		if (valid[i])
			n += sysfs_emit_at(buf, n, "%u", values[i]);
		else
			n += sysfs_emit_at(buf, n, "null");
	}
	n += sysfs_emit_at(buf, n, "}}\n");
	return n;
}
static struct kobj_attribute snapshot_attr = __ATTR(snapshot, 0400, snapshot_show, NULL);

static int __init audit_init(void)
{
	int ret = capture();

	if (ret)
		return ret;
	audit_kobj = kobject_create_and_add("picasso_pon_reason_audit731", kernel_kobj);
	if (!audit_kobj)
		return -ENOMEM;
	ret = sysfs_create_file(audit_kobj, &snapshot_attr.attr);
	if (ret)
		kobject_put(audit_kobj);
	return ret;
}

static void __exit audit_exit(void)
{
	sysfs_remove_file(audit_kobj, &snapshot_attr.attr);
	kobject_put(audit_kobj);
}
module_init(audit_init);
module_exit(audit_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Picasso 7.3.1 fixed read-only PON audit via existing PM8150 regmap");
