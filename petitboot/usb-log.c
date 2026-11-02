// SPDX-License-Identifier: GPL-2.0-only
#define _DEFAULT_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#ifndef KMSG_PATH
#define KMSG_PATH "/dev/kmsg"
#endif
#ifndef SERIAL_PATH
#define SERIAL_PATH "/dev/ttyGS0"
#endif

static int pause_fd(int fd, short events)
{
	struct pollfd p = { .fd = fd, .events = events };
	int ret;

	do {
		ret = poll(&p, 1, 1000);
	} while (ret < 0 && errno == EINTR);
	return ret > 0 ? p.revents : ret;
}

int main(void)
{
	char buffer[16384];
	size_t length = 0, offset = 0;
	int serial = -1;
	int kmsg = open(KMSG_PATH, O_RDONLY | O_NONBLOCK | O_CLOEXEC);

	if (kmsg < 0) {
		perror("picasso-usb-log: open kernel log");
		return 1;
	}
	for (;;) {
		ssize_t n;

		if (serial < 0) {
			struct termios settings;

			serial = open(SERIAL_PATH, O_WRONLY | O_NONBLOCK |
				      O_NOCTTY | O_CLOEXEC);
			if (serial < 0) {
				if (errno != ENOENT && errno != ENODEV &&
				    errno != ENXIO && errno != EIO) {
					perror("picasso-usb-log: open serial");
					return 1;
				}
				fprintf(stderr, "picasso-usb-log: waiting for serial\n");
				sleep(1);
				continue;
			}
			if (tcgetattr(serial, &settings) < 0) {
				perror("picasso-usb-log: serial attributes");
				return 1;
			}
			cfmakeraw(&settings);
			settings.c_cflag |= CLOCAL;
			if (tcsetattr(serial, TCSAFLUSH, &settings) < 0) {
				perror("picasso-usb-log: raw output-only serial");
				return 1;
			}
		}
		if (offset == length) {
			n = read(kmsg, buffer, sizeof(buffer));
			if (n < 0) {
				if (errno == EINTR)
					continue;
				if (errno == EAGAIN) {
					if (pause_fd(kmsg, POLLIN) >= 0)
						continue;
				} else if (errno == EPIPE) {
					const char lost[] = "picasso-usb-log: kernel log overrun; records lost\n";
					memcpy(buffer, lost, sizeof(lost) - 1);
					n = sizeof(lost) - 1;
				}
				if (n < 0) {
					perror("picasso-usb-log: read kernel log");
					return 1;
				}
			}
			if (!n) {
				fprintf(stderr, "picasso-usb-log: unexpected kernel log EOF\n");
				return 1;
			}
			length = (size_t)n;
			offset = 0;
		}
		n = write(serial, buffer + offset, length - offset);
		if (n > 0) {
			offset += (size_t)n;
			continue;
		}
		if (n < 0 && errno == EINTR)
			continue;
		if (n < 0 && errno == EAGAIN) {
			int events = pause_fd(serial, POLLOUT);
			if (events < 0) {
				perror("picasso-usb-log: poll serial");
				return 1;
			}
			if (!(events & (POLLERR | POLLHUP | POLLNVAL)))
				continue;
		} else if (n != 0 && !(n < 0 &&
			   (errno == EIO || errno == ENODEV || errno == ENXIO))) {
			perror("picasso-usb-log: serial write");
			return 1;
		}
		fprintf(stderr, "picasso-usb-log: serial disconnected; queued output may be lost\n");
		close(serial);
		serial = -1;
		sleep(1);
	}
}
