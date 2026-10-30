// SPDX-License-Identifier: GPL-2.0-only
/* One-shot read-only PM8150 Gen2 PON reason snapshot. NOT a power driver.
 * Addresses/conditional reads: MiCode picasso-q-oss 236f9eb, qpnp-power-on.c.
 * No PMIC writes, driver binding, IRQs, notifier, timers or arbitrary API.
 */
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/kobject.h>
#include <linux/ktime.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/spmi.h>
#include <linux/string.h>
#include <linux/sysfs.h>
#include <linux/utsname.h>

#define SPMI_PATH "/soc@0/spmi@c440000"
#define ANCHOR_PATH SPMI_PATH "/pmic@5"
#define PRIMARY_PATH SPMI_PATH "/pmic@0"

static bool confirm_readonly;
module_param(confirm_readonly, bool, 0400);
MODULE_PARM_DESC(confirm_readonly, "Explicitly permit this fixed read-only snapshot");

/* Identity, common status, then only the banks selected by OFF_REASON. */
static const u16 addresses[] = {
	0x0104, 0x0105, 0x0805, 0x08c0, 0x08c2, 0x08c7,
	0x08c5, 0x08c8, 0x08c9, 0x08ca,
};
static u8 values[ARRAY_SIZE(addresses)];
static bool valid[ARRAY_SIZE(addresses)];
static u64 captured_ns;
static struct kobject *audit_kobj;

static int read_slot(struct spmi_device *target, unsigned int slot)
{
	int ret;

	if (slot >= ARRAY_SIZE(addresses))
		return -EINVAL;
	ret = spmi_ext_register_readl(target, addresses[slot], &values[slot], 1);
	if (!ret)
		valid[slot] = true;
	return ret;
}

static int capture(void)
{
	struct device_node *node, *primary;
	struct spmi_device *anchor, *target;
	struct spmi_controller *ctrl;
	int ret, i;

	if (!confirm_readonly || !of_machine_is_compatible("xiaomi,picasso") ||
	    strcmp(utsname()->release, "6.18.58-picasso-lts-wifi2"))
		return -EPERM;
	/* Current default DT has no primary PMIC driver: do not race a probe. */
	primary = of_find_node_by_path(PRIMARY_PATH);
	if (primary) {
		of_node_put(primary);
		return -EBUSY;
	}
	node = of_find_node_by_path(ANCHOR_PATH);
	if (!node)
		return -ENODEV;
	if (!of_device_is_compatible(node, "qcom,pm8150l")) {
		of_node_put(node);
		return -ENODEV;
	}
	anchor = spmi_find_device_by_of_node(node);
	of_node_put(node);
	if (!anchor)
		return -ENODEV;
	ctrl = anchor->ctrl;
	node = of_find_node_by_path(SPMI_PATH);
	if (anchor->usid != 5 || !node || ctrl->dev.of_node != node) {
		of_node_put(node);
		ret = -ENODEV;
		goto put_anchor;
	}
	of_node_put(node);
	get_device(&ctrl->dev);
	/* Allocate an initialized command descriptor, but NEVER device_add().
	 * readl() uses ctrl+usid only; no new Linux device or PMIC probe occurs.
	 */
	target = spmi_device_alloc(ctrl);
	if (!target) {
		ret = -ENOMEM;
		goto put_ctrl;
	}
	target->usid = 0;
	for (i = 0; i < 3; i++) {
		ret = read_slot(target, i);
		if (ret)
			goto put_target;
	}
	if (values[0] != 0x51 || values[1] != 0x1e || values[2] != 0x04) {
		ret = -ENODEV;
		goto put_target;
	}
	for (i = 3; i < 6; i++) {
		ret = read_slot(target, i);
		if (ret)
			goto put_target;
	}
	if (values[5] & BIT(7)) {
		ret = read_slot(target, 6);
		if (ret)
			goto put_target;
	}
	if (values[5] & BIT(6)) {
		ret = read_slot(target, 7);
		if (ret)
			goto put_target;
		ret = read_slot(target, 8);
		if (ret)
			goto put_target;
	}
	if (values[5] & BIT(5)) {
		ret = read_slot(target, 9);
		if (ret)
			goto put_target;
	}
	captured_ns = ktime_get_boottime_ns();
	ret = 0;
put_target:
	spmi_device_put(target);
put_ctrl:
	put_device(&ctrl->dev);
put_anchor:
	spmi_device_put(anchor);
	return ret;
}

static ssize_t snapshot_show(struct kobject *kobj, struct kobj_attribute *attr,
			     char *buf)
{
	ssize_t n;
	unsigned int i;

	n = sysfs_emit(buf, "{\"scope\":\"picasso-pm8150-gen2-readonly\","
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
	audit_kobj = kobject_create_and_add("picasso_pon_reason_audit", kernel_kobj);
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
MODULE_DESCRIPTION("Picasso fixed one-shot PM8150 Gen2 PON read-only reason audit");
