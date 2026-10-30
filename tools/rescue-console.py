#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Bounded serial commands on the explicitly identified Picasso rescue gadget.

Never scans storage, reboots, or writes to the phone by itself. Commands are
explicit operator input. Raw logs can contain private device data: keep them in
an out/ directory with mode 0700. No pyserial dependency or QEMU is needed.
"""
import argparse
import fcntl
import os
from pathlib import Path
import select
import subprocess
import sys
import termios
import time
import uuid


def identify(port):
    name = Path(port).name
    if not name.startswith('ttyACM'):
        raise ValueError('Only an ACM rescue serial port is accepted')
    device = (Path('/sys/class/tty') / name / 'device').resolve(strict=True)
    for parent in device.parents:
        if (parent/'idVendor').exists():
            fields = {k: (parent/k).read_text().strip()
                      for k in ('idVendor', 'idProduct', 'serial', 'product')}
            expected = {'idVendor': '1d6b', 'idProduct': '0104',
                        'serial': 'picasso-bringup', 'product': 'Picasso LTS rescue'}
            if fields != expected:
                raise ValueError('Not the expected Picasso rescue gadget: ' + str(fields))
            return parent
    raise ValueError('No USB device parent for serial port')


def extract(data, begin, end):
    normalized = data.replace(b'\r', b'')
    left, right = b'\n'+begin+b'\n', b'\n'+end+b'\n'
    if left not in normalized or right not in normalized:
        return None
    return normalized.split(left, 1)[1].split(right, 1)[0]


class Console:
    def __init__(self, port='/dev/ttyACM0', grant_acl=False):
        self.usb = identify(port)
        if grant_acl:
            subprocess.run(['sudo', '-n', 'setfacl', '-m', f'u:{os.getuid()}:rw', port],
                           check=True, timeout=10)
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            fcntl.ioctl(self.fd, termios.TIOCEXCL)
            a = termios.tcgetattr(self.fd)
            a[0] = a[1] = a[3] = 0
            a[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
            a[4] = a[5] = termios.B115200
            a[6][termios.VMIN], a[6][termios.VTIME] = 0, 1
            termios.tcsetattr(self.fd, termios.TCSANOW, a)
            # Host ModemManager may leave a partial QCDM probe in ash's input
            # buffer after enumeration. Clear the idle input line (not Ctrl-C)
            # before sending a marker, so junk cannot prefix the first printf.
            self.send(b'\x15\r')
        except BaseException:
            os.close(self.fd)
            raise

    def close(self):
        os.close(self.fd)

    def send(self, data):
        deadline = time.monotonic() + 10
        while data:
            if time.monotonic() > deadline:
                raise TimeoutError('Serial command send timed out')
            if select.select([], [self.fd], [], .2)[1]:
                try:
                    data = data[os.write(self.fd, data):]
                except BlockingIOError:
                    pass

    def command(self, command, timeout=30, log=None):
        token = uuid.uuid4().hex.encode()
        begin, end = b'__PI_BEGIN_'+token+b'__', b'__PI_END_'+token+b'__'
        wire = b"printf '\\n"+begin+b"\\n'; "+command.encode()+b"; printf '\\n"+end+b"\\n'\r"
        if len(wire) > 3500:
            raise ValueError('Command too long for conservative serial line limit')
        self.send(wire)
        deadline, raw = time.monotonic()+timeout, bytearray()
        try:
            while time.monotonic() < deadline:
                if select.select([self.fd], [], [], .2)[0]:
                    try:
                        raw.extend(os.read(self.fd, 65536))
                    except BlockingIOError:
                        pass
                if len(raw) > 8 << 20:
                    raise RuntimeError('Serial output exceeded 8 MiB capture limit')
                body = extract(bytes(raw), begin, end)
                if body is not None:
                    return body
            raise TimeoutError('Serial end marker missing; command outcome unknown. Do not blindly retry.')
        finally:
            if log:
                Path(log).write_bytes(raw)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', default='/dev/ttyACM0')
    p.add_argument('--grant-host-acl', action='store_true')
    p.add_argument('--timeout', type=float, default=30)
    p.add_argument('--log', required=True)
    p.add_argument('command')
    a = p.parse_args()
    console = Console(a.port, a.grant_host_acl)
    try:
        sys.stdout.buffer.write(console.command(a.command, a.timeout, a.log))
    finally:
        console.close()


if __name__ == '__main__':
    main()
