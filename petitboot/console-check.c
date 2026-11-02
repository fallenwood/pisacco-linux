/* SPDX-License-Identifier: GPL-2.0-only */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/fb.h>
#include <linux/kd.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>

static int device_open(const char *path, unsigned int major_id, unsigned int minor_id)
{
	struct stat st;
	int fd = open(path, O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NOCTTY);

	if (fd < 0)
		return -1;
	if (fstat(fd, &st) || !S_ISCHR(st.st_mode) ||
			st.st_rdev != makedev(major_id, minor_id)) {
		close(fd);
		errno = ENODEV;
		return -1;
	}
	return fd;
}

int main(void)
{
	struct fb_fix_screeninfo fixed;
	struct fb_var_screeninfo var;
	const char expected_id[16] = "simpledrmdrmfb";
	int fd, mode;

	fd = device_open("/dev/tty1", 4, 1);
	if (fd < 0 || ioctl(fd, KDGETMODE, &mode))
		goto fail;
	if (mode != KD_TEXT) {
		errno = ENODEV;
		goto fail;
	}
	close(fd);
	fd = device_open("/dev/fb0", 29, 0);
	if (fd < 0 || ioctl(fd, FBIOGET_FSCREENINFO, &fixed) ||
			ioctl(fd, FBIOGET_VSCREENINFO, &var))
		goto fail;
	close(fd);
	if (memcmp(fixed.id, expected_id, sizeof(fixed.id)) ||
			fixed.smem_start != 0 || fixed.smem_len != 10368000 ||
			fixed.line_length != 4320 ||
			var.xres != 1080 || var.yres != 2400 ||
			var.xres_virtual != 1080 || var.yres_virtual != 2400 ||
			var.xoffset || var.yoffset || var.bits_per_pixel != 32 || var.grayscale ||
			var.red.offset != 16 || var.red.length != 8 || var.red.msb_right ||
			var.green.offset != 8 || var.green.length != 8 || var.green.msb_right ||
			var.blue.offset != 0 || var.blue.length != 8 || var.blue.msb_right ||
			var.transp.offset || var.transp.length || var.transp.msb_right) {
		fprintf(stderr, "Loader console: framebuffer layout is not the audited mode\n");
		return 1;
	}
	return 0;
fail:
	fprintf(stderr, "Loader console: expected native tty1/KD_TEXT and framebuffer: %s\n",
		strerror(errno));
	return 1;
}
