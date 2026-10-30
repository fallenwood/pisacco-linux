// SPDX-License-Identifier: GPL-2.0-only
/* Attended Picasso bootloader WLED5 handoff. No panel/reset/rail operations.
 * Exact native boot config was read and checked before creating this driver.
 * Only MOD_A brightness/sync and WLED module-enable can be written. Never
 * touches boost, current, voltage, string/source selection, IRQ or protection.
 */
#include <linux/module.h>
#include <linux/of.h>
#include <linux/regmap.h>
#include <linux/spmi.h>
#include <linux/backlight.h>
#include <linux/workqueue.h>
#include <linux/mutex.h>
#include <linux/jiffies.h>

#define CTRL_ENABLE 0xd846
#define MOD_BRIGHT  0xd953
#define MOD_SYNC    0xd965
#define TRIAL_MAX   256

static bool confirm_handoff;
module_param(confirm_handoff, bool, 0444);
MODULE_PARM_DESC(confirm_handoff, "Explicit attended boot-state-preserving backlight trial");
static unsigned int duration_seconds = 45;
module_param(duration_seconds, uint, 0444);
MODULE_PARM_DESC(duration_seconds, "Independent kernel fail-off deadline, 1..90 seconds");

struct expected_reg { unsigned int address, value; };
/* Entire verified runtime electrical configuration; no guessed defaults. */
static const struct expected_reg fixed_config[] = {
	{0xd804, 0x17}, {0xd805, 0x12}, {0xd904, 0x17}, {0xd905, 0x13},
	{0xd84c, 0x0b}, {0xd84d, 0x07}, {0xd84e, 0x05},
	{0xd946, 0x70}, {0xd950, 0x80}, {0xd951, 0x00}, {0xd952, 0x00},
	{0xd960, 0x00}, {0xd961, 0x00}, {0xd962, 0x00},
	{0xd972, 0x09}, {0xd973, 0x00}, {0xd982, 0x09}, {0xd983, 0x00},
	{0xd992, 0x09}, {0xd993, 0x00}, {0xd9a2, 0x0c}, {0xd9a3, 0x00},
};
static struct spmi_device *pmic;
static struct regmap *map;
static struct backlight_device *bl;
static DEFINE_MUTEX(handoff_lock);
static struct delayed_work expiry_work;
static unsigned long expires;
static bool expired;

static int config_check(void)
{
	unsigned int value;
	int i, ret;

	for (i = 0; i < ARRAY_SIZE(fixed_config); i++) {
		ret = regmap_read(map, fixed_config[i].address, &value);
		if (ret)
			return ret;
		if (value != fixed_config[i].value)
			return -EUCLEAN;
	}
	ret = regmap_read(map, 0xd808, &value);
	if (ret)
		return ret;
	if (value & 0x17) /* ILIM, OVP, short, OVP pre-alarm */
		return -EIO;
	ret = regmap_read(map, 0xd810, &value);
	if (ret)
		return ret;
	return (value & BIT(1)) ? -EIO : 0;
}

static int gate_off(void)
{
	/* Safe-off is possible even if unrelated configuration changed. */
	return regmap_update_bits(map, CTRL_ENABLE, BIT(7), 0);
}

static int actual_brightness(void)
{
	u8 bytes[2];
	unsigned int enabled;
	int ret;

	ret = regmap_read(map, CTRL_ENABLE, &enabled);
	if (ret)
		return ret;
	if (!(enabled & BIT(7)))
		return 0;
	ret = regmap_bulk_read(map, MOD_BRIGHT, bytes, 2);
	if (ret)
		return ret;
	return (bytes[0] | (bytes[1] << 8)) & 0xfff;
}

static int set_brightness(unsigned int value)
{
	u8 bytes[2] = { value & 0xff, (value >> 8) & 0x0f };
	int ret;

	if (!value)
		return gate_off();
	if (value > TRIAL_MAX || expired || time_after_eq(jiffies, expires)) {
		gate_off();
		return -ETIMEDOUT;
	}
	ret = config_check();
	if (ret)
		goto fail_off;
	ret = regmap_bulk_write(map, MOD_BRIGHT, bytes, 2);
	if (ret)
		goto fail_off;
	/* Toggle only A; preserve inactive B and all other register bits. */
	ret = regmap_update_bits(map, MOD_SYNC, BIT(0), 0);
	if (ret)
		goto fail_off;
	ret = regmap_update_bits(map, MOD_SYNC, BIT(0), BIT(0));
	if (ret)
		goto fail_off;
	ret = regmap_update_bits(map, CTRL_ENABLE, BIT(7), BIT(7));
	if (ret)
		goto fail_off;
	ret = actual_brightness();
	if (ret == value)
		return 0;
	if (ret >= 0)
		ret = -EIO;
fail_off:
	gate_off();
	return ret;
}

static int handoff_update(struct backlight_device *device)
{
	int ret;

	mutex_lock(&handoff_lock);
	ret = set_brightness(backlight_get_brightness(device));
	mutex_unlock(&handoff_lock);
	return ret;
}

static int handoff_get(struct backlight_device *device)
{
	int ret;

	mutex_lock(&handoff_lock);
	ret = actual_brightness();
	mutex_unlock(&handoff_lock);
	return ret;
}

static const struct backlight_ops handoff_ops = {
	.options = BL_CORE_SUSPENDRESUME,
	.update_status = handoff_update,
	.get_brightness = handoff_get,
};

static void expire_trial(struct work_struct *work)
{
	int ret;

	mutex_lock(&handoff_lock);
	expired = true;
	ret = gate_off();
	if (bl)
		bl->props.brightness = 0;
	mutex_unlock(&handoff_lock);
	pr_info("Picasso WLED handoff deadline: fail-off result %d\n", ret);
}

static ssize_t boot_config_verified_show(struct device *device,
					 struct device_attribute *attr, char *buf)
{
	int ret;

	mutex_lock(&handoff_lock);
	ret = config_check();
	mutex_unlock(&handoff_lock);
	if (ret)
		return ret;
	return sysfs_emit(buf,
		"usid=5 ctrl=d800 sink=d900 strings=7 current_ua=22500 ovp_mv=28000 boost_ma=1400 hardware_max=4095 trial_max=256\n");
}
static DEVICE_ATTR_RO(boot_config_verified);

static int __init picasso_wled_handoff_init(void)
{
	struct device_node *node, *wled;
	struct backlight_properties props = {0};
	u32 reg[2];
	int ret;

	if (!confirm_handoff || duration_seconds < 1 || duration_seconds > 90 ||
	    !of_machine_is_compatible("xiaomi,picasso"))
		return -EPERM;
	node = of_find_node_by_path("/soc@0/spmi@c440000/pmic@5");
	if (!node)
		return -ENODEV;
	if (!of_device_is_compatible(node, "qcom,pm8150l")) {
		of_node_put(node);
		return -ENODEV;
	}
	wled = of_find_node_by_path("/soc@0/spmi@c440000/pmic@5/backlight@d800");
	if (!wled) {
		of_node_put(node);
		return -ENODEV;
	}
	ret = of_property_read_u32_array(wled, "reg", reg, 2);
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
	ret = config_check();
	if (ret)
		goto put; /* zero writes on an unaudited configuration */
	expires = jiffies + msecs_to_jiffies(duration_seconds * 1000);
	INIT_DELAYED_WORK(&expiry_work, expire_trial);
	ret = set_brightness(64); /* reduce boot 1023/4095 to a bounded low duty */
	if (ret)
		goto put;
	props.type = BACKLIGHT_RAW;
	props.max_brightness = TRIAL_MAX;
	props.brightness = 64;
	bl = backlight_device_register("picasso-handoff", &pmic->dev, NULL,
				       &handoff_ops, &props);
	if (IS_ERR(bl)) {
		ret = PTR_ERR(bl);
		bl = NULL;
		goto off;
	}
	ret = device_create_file(&bl->dev, &dev_attr_boot_config_verified);
	if (ret)
		goto unregister;
	schedule_delayed_work(&expiry_work,
			      time_after_eq(jiffies, expires) ? 0 : expires - jiffies);
	pr_info("Picasso bounded WLED handoff: electrical configuration preserved; low brightness only\n");
	return 0;
unregister:
	backlight_device_unregister(bl);
	bl = NULL;
off:
	gate_off();
put:
	spmi_device_put(pmic);
	pmic = NULL;
	return ret;
}

static void __exit picasso_wled_handoff_exit(void)
{
	cancel_delayed_work_sync(&expiry_work);
	mutex_lock(&handoff_lock);
	expired = true;
	gate_off();
	mutex_unlock(&handoff_lock);
	device_remove_file(&bl->dev, &dev_attr_boot_config_verified);
	backlight_device_unregister(bl);
	spmi_device_put(pmic);
}
module_init(picasso_wled_handoff_init);
module_exit(picasso_wled_handoff_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Bounded Picasso verified-boot WLED handoff, no electrical reconfiguration");
