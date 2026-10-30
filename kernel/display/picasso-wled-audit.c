// SPDX-License-Identifier: GPL-2.0-only
/* Read-only PM8150L WLED5 boot configuration. Not a display/backlight driver.
 * No arbitrary addresses, writes, OTP, NVM, calibration or panel transactions.
 */
#include <linux/module.h>
#include <linux/of.h>
#include <linux/regmap.h>
#include <linux/spmi.h>
#include <linux/kobject.h>
#include <linux/sysfs.h>

static bool confirm_readonly;
module_param(confirm_readonly, bool, 0444);
MODULE_PARM_DESC(confirm_readonly, "Explicit Picasso WLED runtime-register read-only audit");

/* Documented WLED5 runtime configuration offsets, from qcom-wled.c.
 * No interrupt-clear, SPMI commands, OTP or arbitrary user-supplied offsets.
 */
static const unsigned int offsets[] = {
	0xd800, 0xd801, 0xd802, 0xd803, 0xd804, 0xd805,
	0xd808, 0xd810, 0xd846, 0xd84c, 0xd84d, 0xd84e,
	0xd904, 0xd905, 0xd946,
	0xd950, 0xd951, 0xd952, 0xd953, 0xd954,
	0xd960, 0xd961, 0xd962, 0xd963, 0xd964, 0xd965,
	0xd972, 0xd973, 0xd982, 0xd983, 0xd992, 0xd993,
	0xd9a2, 0xd9a3,
};
static unsigned int values[ARRAY_SIZE(offsets)];
static struct spmi_device *pmic;
static struct kobject *audit_kobj;

static ssize_t snapshot_show(struct kobject *kobj, struct kobj_attribute *attr,
			     char *buf)
{
	ssize_t n = 0;
	int i;

	n += sysfs_emit_at(buf, n, "read_only=1 usid=5 runtime_registers_only=1\n");
	for (i = 0; i < ARRAY_SIZE(offsets); i++)
		n += sysfs_emit_at(buf, n, "%04x=%02x\n", offsets[i], values[i]);
	return n;
}
static struct kobj_attribute snapshot_attr = __ATTR_RO_MODE(snapshot, 0400);
static struct attribute *audit_attrs[] = { &snapshot_attr.attr, NULL };
static const struct attribute_group audit_group = { .attrs = audit_attrs };

static int __init picasso_wled_audit_init(void)
{
	struct device_node *node, *wled;
	struct regmap *map;
	u32 reg[2];
	int i, ret;

	if (!confirm_readonly || !of_machine_is_compatible("xiaomi,picasso"))
		return -EPERM;
	node = of_find_node_by_path("/soc@0/spmi@c440000/pmic@5");
	if (!node)
		return -ENODEV;
	if (!of_device_is_compatible(node, "qcom,pm8150l")) {
		of_node_put(node);
		return -ENODEV;
	}
	/* of_get_child_by_name() strips unit-addresses when comparing names. */
	wled = of_find_node_by_path("/soc@0/spmi@c440000/pmic@5/backlight@d800");
	if (!wled) {
		of_node_put(node);
		return -ENODEV;
	}
	ret = of_property_read_u32_array(wled, "reg", reg, ARRAY_SIZE(reg));
	if (ret || reg[0] != 0xd800 || reg[1] != 0xd900 ||
	    !of_device_is_compatible(wled, "qcom,pm8150l-wled")) {
		of_node_put(wled);
		of_node_put(node);
		return -EINVAL;
	}
	of_node_put(wled);
	pmic = spmi_find_device_by_of_node(node);
	of_node_put(node);
	if (!pmic)
		return -ENODEV;
	if (pmic->usid != 5) {
		ret = -ENODEV;
		goto put;
	}
	map = dev_get_regmap(&pmic->dev, NULL);
	if (!map) {
		ret = -ENODEV;
		goto put;
	}
	for (i = 0; i < ARRAY_SIZE(offsets); i++) {
		ret = regmap_read(map, offsets[i], &values[i]);
		if (ret)
			goto put;
	}
	audit_kobj = kobject_create_and_add("picasso_wled_audit", kernel_kobj);
	if (!audit_kobj) {
		ret = -ENOMEM;
		goto put;
	}
	ret = sysfs_create_group(audit_kobj, &audit_group);
	if (ret) {
		kobject_put(audit_kobj);
		audit_kobj = NULL;
		goto put;
	}
	pr_info("Picasso WLED read-only runtime snapshot available; no register writes\n");
	return 0;
put:
	spmi_device_put(pmic);
	pmic = NULL;
	return ret;
}

static void __exit picasso_wled_audit_exit(void)
{
	sysfs_remove_group(audit_kobj, &audit_group);
	kobject_put(audit_kobj);
	spmi_device_put(pmic);
}
module_init(picasso_wled_audit_init);
module_exit(picasso_wled_audit_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Picasso read-only WLED5 boot configuration snapshot");
