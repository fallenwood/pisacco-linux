# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
import fcntl
import gzip
import hashlib
import json
import os
import select
from pathlib import Path
import shlex
import subprocess
import struct
import sys
import tempfile
import termios
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
SPEC = importlib.util.spec_from_file_location('petitboot_loader',
                                             ROOT / 'tools/build-petitboot-loader.py')
LOADER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOADER)


class PetitbootLoader(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_outputs_cannot_reuse_baselines_or_follow_redirects(self):
        namespace = self.root / 'out/petitboot-1.15'
        namespace.mkdir(parents=True)
        (namespace / 'old-build').mkdir()
        (namespace / 'redirect').symlink_to(self.root, target_is_directory=True)
        with patch.object(LOADER, 'ROOT', self.root):
            self.assertEqual(LOADER.new_output(namespace / 'fresh'), namespace / 'fresh')
            for path in (namespace, namespace / 'old-build', namespace / 'redirect/new',
                         self.root / 'out/linux-7.3.1/new', self.root / 'outside'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    LOADER.new_output(path)
        self.assertFalse((namespace / 'fresh').exists())

    def test_initramfs_rejects_escape_symlinks(self):
        (self.root / 'bin').mkdir()
        (self.root / 'bin/sh').symlink_to('../outside')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            LOADER.initramfs_list(self.root, self.root / 'list')
        self.assertFalse((self.root / 'list').exists())

    def run_tick(self, temperature='39000', brightness='64', broken_lease=False):
        thermal = self.root / 'thermal/thermal_zone0'
        thermal.mkdir(parents=True)
        (thermal / 'temp').write_text(temperature + '\n')
        backlight = self.root / 'backlight'
        backlight.mkdir()
        (backlight / 'actual_brightness').write_text(brightness + '\n')
        (backlight / 'boot_config_verified').write_text(
            'usid=5 ctrl=d800 sink=d900 strings=7 current_ua=22500 ovp_mv=28000 '
            'boost_ma=1400 hardware_max=4095 trial_max=256\n')
        if broken_lease:
            (backlight / 'lease').mkdir()
        else:
            (backlight / 'lease').write_text('')
        init = (ROOT / 'petitboot/init').read_text()

        def function(name):
            start = init.index(name + '() {')
            return init[start:init.index('\n}\n', start) + 3]

        code = ("fail() { printf '%s\\n' \"$*\" >&2; exit 77; }\n" +
                function('temperatures').replace('/sys/class/thermal',
                                                  str(self.root / 'thermal')) +
                function('tick') +
                f'\nBL={shlex.quote(str(backlight))}\nexpected=64\ntick\n')
        return subprocess.run(['sh', '-c', code], text=True, capture_output=True), backlight

    def test_guard_renews_from_supervisor_and_checks_actual_brightness(self):
        result, backlight = self.run_tick()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((backlight / 'lease').read_text(), 'LIVE\n')

    def test_hot_or_invalid_temperature_never_renews_lease(self):
        for value in ('45000', 'broken', '150001'):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                self.root = Path(temporary)
                result, backlight = self.run_tick(temperature=value)
                self.assertEqual(result.returncode, 77, result.stderr)
                self.assertEqual((backlight / 'lease').read_text(), '')

    def test_lease_failure_and_external_brightness_are_fatal(self):
        for options, message in (({'broken_lease': True}, 'lease renewal failed'),
                                 ({'brightness': '65'}, 'Unexpected actual backlight')):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as temporary:
                self.root = Path(temporary)
                result, _ = self.run_tick(**options)
                self.assertEqual(result.returncode, 77, result.stderr)
                self.assertIn(message, result.stderr)

    def test_console_checker_uses_audited_geometry_and_character_devices(self):
        obj = self.root / 'console.o'
        subprocess.run(
            ['cc', '-Wall', '-Wextra', '-Werror', '-Dmain=console_check_main',
             '-Dopen=mock_open', '-Dfstat=mock_fstat', '-Dioctl=mock_ioctl',
             '-Dclose=mock_close', '-c', str(ROOT / 'petitboot/console-check.c'),
             '-o', str(obj)], check=True, capture_output=True)
        harness = self.root / 'console-test.c'
        harness.write_text(r'''
#include <assert.h>
#include <linux/fb.h>
#include <linux/kd.h>
#include <stdarg.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
static int corrupt;
int console_check_main(void);
int mock_open(const char *path, int flags, ...) {
    (void)flags;
    return strcmp(path, "/dev/tty1") == 0 ? 10 : 11;
}
int mock_close(int fd) { (void)fd; return 0; }
int mock_fstat(int fd, struct stat *st) {
    memset(st, 0, sizeof(*st));
    st->st_mode = corrupt == 2 ? S_IFREG : S_IFCHR;
    st->st_rdev = fd == 10 ? makedev(4, 1) : makedev(29, 0);
    return 0;
}
int mock_ioctl(int fd, unsigned long op, ...) {
    va_list ap; void *value; (void)fd;
    va_start(ap, op); value = va_arg(ap, void *); va_end(ap);
    if (op == KDGETMODE) { *(int *)value = KD_TEXT; return 0; }
    if (op == FBIOGET_FSCREENINFO) {
        struct fb_fix_screeninfo *f = value;
        memset(f, 0, sizeof(*f)); strcpy(f->id, "simpledrmdrmfb");
        f->smem_len = 10368000; f->line_length = 4320;
    } else {
        struct fb_var_screeninfo *v = value;
        memset(v, 0, sizeof(*v));
        v->xres = v->xres_virtual = 1080; v->yres = v->yres_virtual = 2400;
        v->bits_per_pixel = 32; v->red.offset = 16; v->green.offset = 8;
        v->red.length = v->green.length = v->blue.length = 8;
        if (corrupt == 1) v->xoffset = 1;
    }
    return 0;
}
int main(void) {
    assert(console_check_main() == 0);
    corrupt = 1; assert(console_check_main() != 0);
    corrupt = 2; assert(console_check_main() != 0);
    return 0;
}
''')
        executable = self.root / 'console-test'
        subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', str(harness), str(obj),
                        '-o', str(executable)], check=True, capture_output=True)
        subprocess.run([str(executable)], check=True, capture_output=True)

    def start_usb_log(self, actual_arm64=False):
        (self.root / 'dev').mkdir()
        fifo = self.root / 'dev/kmsg'
        os.mkfifo(fifo)
        writer = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
        self.addCleanup(os.close, writer)
        master, slave = os.openpty()
        self.addCleanup(os.close, master)
        self.addCleanup(os.close, slave)
        serial = self.root / 'dev/ttyGS0'
        serial.symlink_to(os.ttyname(slave))
        executable = self.root / 'usb-log'
        if actual_arm64:
            rootfs = ROOT / os.environ['PETITBOOT_LOADER_BUILD'] / 'rootfs'
            for path in rootfs.iterdir():
                if path.name != 'dev':
                    (self.root / path.name).symlink_to(path)
            command = ['qemu-aarch64', '-strace', '-L', str(self.root),
                       str(rootfs / 'usr/libexec/picasso-petitboot/usb-log')]
        else:
            subprocess.run(
                ['cc', '-Wall', '-Wextra', '-Werror',
                 f'-DKMSG_PATH="{fifo}"', f'-DSERIAL_PATH="{serial}"',
                 str(ROOT / 'petitboot/usb-log.c'), '-o', str(executable)],
                check=True, capture_output=True)
            command = [str(executable)]
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        def finish():
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=5)

        self.addCleanup(finish)
        deadline = time.monotonic() + 5
        while termios.tcgetattr(slave)[3] & (termios.ECHO | termios.ISIG):
            if process.poll() is not None:
                error = process.stderr.read().decode()
                if (actual_arm64 and '0x802c542a' in error and
                        'serial attributes: Inappropriate ioctl for device' in error and
                        subprocess.check_output(['qemu-aarch64', '--version'],
                                                text=True).startswith(
                                                    'qemu-aarch64 version 9.1.1')):
                    # This emulator lacks TCGETS2; do not alter production termios for it.
                    fcntl.ioctl(slave, 0x802c542a, bytearray(44))
                    self.skipTest('QEMU 9.1.1 lacks TCGETS2 translation; '
                                  'full ARM64 serial replay remains unverified')
                self.fail('USB relay exited: ' + error)
            self.assertLess(time.monotonic(), deadline, 'USB relay never configured tty')
            time.sleep(0.01)
        return process, writer, master, serial

    def relay_exchange(self, writer, master, data):
        sent = 0
        received = bytearray()
        deadline = time.monotonic() + 10
        while len(received) < len(data):
            self.assertLess(time.monotonic(), deadline, 'USB output stalled')
            readable, writable, _ = select.select(
                [master], [writer] if sent < len(data) else [], [], 0.1)
            if writable:
                sent += os.write(writer, data[sent:sent + 4096])
            if readable:
                received.extend(os.read(master, 16384))
        self.assertEqual(bytes(received), data)

    def test_usb_log_replays_backlog_under_backpressure_without_host_input_echo(self):
        process, writer, master, _ = self.start_usb_log()
        os.write(master, b'reboot\n\x03\x13')
        data = b'6,1,1,-;picasso-petitboot: STAGE isolation\n' * 4096
        self.relay_exchange(writer, master, data)
        self.assertIsNone(process.poll())
        self.assertEqual(select.select([master], [], [], 0.1)[0], [])

    def test_usb_log_reopens_after_serial_disconnect(self):
        process, writer, master, serial = self.start_usb_log()
        self.relay_exchange(writer, master, b'before disconnect\n')
        serial.unlink()
        second_master, second_slave = os.openpty()
        self.addCleanup(os.close, second_master)
        self.addCleanup(os.close, second_slave)
        serial.symlink_to(os.ttyname(second_slave))
        # Closing the peer causes the relay's old slave to return EIO.
        os.dup2(second_master, master)
        self.relay_exchange(writer, second_master, b'after disconnect\n')
        self.assertIsNone(process.poll())

    @unittest.skipUnless(os.environ.get('PETITBOOT_LOADER_BUILD'),
                         'requires the actual ARM64 diagnostic executable')
    def test_actual_arm64_relay_forwards_only_fixture_logs_under_qemu(self):
        process, writer, master, _ = self.start_usb_log(actual_arm64=True)
        os.write(master, b'reboot\n\x03\x13')
        self.relay_exchange(writer, master, b'6,1,1,-;STAGE pid1-entry\n' * 4096)
        self.assertIsNone(process.poll())
        self.assertEqual(select.select([master], [], [], 0.1)[0], [])

    def test_failure_retains_relay_and_exports_recent_ui_logs_after_stopping_children(self):
        (self.root / 'ui.log').write_text(''.join(f'ui-{i}\n' for i in range(120)))
        (self.root / 'discover.log').write_text('discovery error\n')
        init = (ROOT / 'petitboot/init').read_text()
        start = init.index('fail() {')
        failure = init[start:init.index('\n}\n', start) + 3]
        failure = failure.replace('/run/petitboot', str(self.root))
        failure = failure.replace('while :; do sleep 60; done', 'return 77')
        code = ('log() { printf "%s\\n" "$*"; }\n'
                'stop_child() { printf "stopped:%s\\n" "$1"; }\n'
                'MODULE_OWNED=0; UI_PID=ui; DISCOVER_PID=discover; LOG_PID=relay\n' +
                failure + '\nfail "Menu exited"\n')
        result = subprocess.run(['sh', '-c', code], text=True, capture_output=True)
        self.assertEqual(result.returncode, 77, result.stderr)
        self.assertIn('FAILED: Menu exited', result.stdout)
        self.assertIn('discovery error', result.stdout)
        self.assertIn('ui-40\n', result.stdout)
        self.assertIn('ui-119\n', result.stdout)
        self.assertNotIn('ui-39\n', result.stdout)
        self.assertLess(result.stdout.index('stopped:discover'),
                        result.stdout.index('discovery error'))
        self.assertNotIn('stopped:relay', result.stdout)

    @unittest.skipUnless(os.environ.get('PETITBOOT_LOADER_BUILD'),
                         'requires an explicitly selected loader build')
    def test_real_config_and_dtb_refuse_scope_expansion(self):
        build = ROOT / os.environ['PETITBOOT_LOADER_BUILD']
        config = (build / 'kernel.config').read_text()
        LOADER.check_config(config)
        for symbol in ('BLOCK', 'INET', 'REMOTEPROC', 'RPMSG', 'USB_CONFIGFS',
                       'USB_F_NCM', 'USB_F_MASS_STORAGE', 'MAGIC_SYSRQ'):
            with self.subTest(symbol=symbol), self.assertRaises(ValueError):
                LOADER.check_config(config + f'\nCONFIG_{symbol}=y\n')
        with self.assertRaises(ValueError):
            LOADER.check_config(config.replace('rdinit=/init', 'root=/dev/example'))
        with self.assertRaises(ValueError):
            LOADER.check_config(config.replace('CONFIG_LOG_BUF_SHIFT=20',
                                               'CONFIG_LOG_BUF_SHIFT=19'))
        for option in ('console=ttyGS0', 'g_serial.use_acm=1', 'g_serial.n_ports=1'):
            with self.subTest(option=option), self.assertRaises(ValueError):
                LOADER.check_config(config.replace(option, ''))
        baseline = (ROOT / 'out/linux-7.3.1/picasso.dtb').read_bytes()
        dtb = (build / 'picasso.dtb').read_bytes()
        LOADER.check_dtb(baseline, dtb)
        with self.assertRaises(ValueError):
            LOADER.check_dtb(baseline, baseline)

    @unittest.skipUnless(os.environ.get('PETITBOOT_LOADER_BUILD'),
                         'requires the actual packed loader Image')
    def test_image_embeds_exact_supervisor_programs_targets_and_matching_module(self):
        build = ROOT / os.environ['PETITBOOT_LOADER_BUILD']
        record = json.loads((build / 'build.json').read_text())
        compressed = (build / 'kbuild/usr/initramfs_inc_data').read_bytes()
        self.assertNotEqual((build / 'Image').read_bytes().find(compressed), -1,
                            'Image does not embed the generated initramfs')
        archive = gzip.decompress(compressed)
        position = 0
        files = {}
        while True:
            self.assertEqual(archive[position:position + 6], b'070701')
            fields = [int(archive[position + 6 + i * 8:position + 14 + i * 8], 16)
                      for i in range(13)]
            self.assertEqual(fields[2:4], [0, 0], 'Non-root initramfs ownership')
            start = position + 110
            name = archive[start:start + fields[11] - 1].decode().lstrip('/')
            start = (start + fields[11] + 3) & ~3
            if name == 'TRAILER!!!':
                break
            files[name] = archive[start:start + fields[6]]
            if name == 'dev/kmsg':
                self.assertEqual(fields[1] & 0o170000, 0o020000)
                self.assertEqual(fields[9:11], [1, 11])
            position = (start + fields[6] + 3) & ~3
        self.assertTrue(files['init'] == (ROOT / 'petitboot/init').read_bytes(),
                        'Embedded /init differs from reviewed source')
        self.assertIn('dev/kmsg', files, 'Missing early PID1 diagnostic device')
        userspace = Path(record['userspace_receipt'])
        self.assertEqual(LOADER.digest(userspace), record['userspace_receipt_sha256'])
        programs = json.loads(userspace.read_text())['programs']
        for name, expected in programs.items():
            if name.endswith('kexec.unvalidated'):
                self.assertNotIn(name, files)
            else:
                self.assertEqual(hashlib.sha256(files[name]).hexdigest(), expected, name)
        module = files['usr/libexec/picasso-petitboot/picasso-wled-service.ko']
        self.assertEqual(struct.unpack_from('<H', module, 18)[0], 183)
        self.assertIn(b'vermagic=' + LOADER.RELEASE.encode() + b' ', module)
        relay = files['usr/libexec/picasso-petitboot/usb-log']
        self.assertEqual(struct.unpack_from('<H', relay, 18)[0], 183)
        self.assertEqual(hashlib.sha256(relay).hexdigest(),
                         record['usb_diagnostics']['relay_sha256'])
        for target in record['retained_targets']:
            directory = Path(target['directory'])
            for name in ('Image', 'picasso.dtb'):
                self.assertTrue(files[f"kernels/{target['release']}/{name}"] ==
                                (directory / name).read_bytes(), 'Target payload changed')

    @unittest.skipUnless(os.environ.get('PETITBOOT_LOADER_BUILD'),
                         'requires the actual separately patched kernel source')
    def test_actual_input_only_irq_never_synthesizes_orphan_presses(self):
        source = (ROOT / os.environ['PETITBOOT_LOADER_BUILD'] /
                  'linux-7.3.1/drivers/input/misc/pm8941-pwrkey.c').read_text()
        irq = source[source.index('static irqreturn_t pm8941_pwrkey_irq('):
                     source.index('static int pm8941_pwrkey_sw_debounce_init(')]
        harness = self.root / 'irq-test.c'
        harness.write_text(r'''
#include <assert.h>
#include <stdbool.h>
typedef int irqreturn_t;
typedef long long ktime_t;
#define IRQ_HANDLED 1
#define PON_RT_STS 0x10
#define dev_dbg(...) ((void)0)
#define dev_err_ratelimited(...) (++errors)
struct pm8941_data { bool input_only; unsigned int status_bit; };
struct pm8941_pwrkey {
    unsigned int sw_debounce_time_us, baseaddr, code;
    ktime_t sw_debounce_end_time;
    void *dev, *regmap, *input;
    bool last_status;
    const struct pm8941_data *data;
};
static int errors, failed_read, count, values[4];
static unsigned int status;
static ktime_t ktime_get(void) { return 10000000; }
static bool ktime_before(ktime_t a, ktime_t b) { return a < b; }
static ktime_t ktime_add_us(ktime_t a, unsigned int b) { return a + b; }
static int regmap_read(void *map, unsigned int addr, unsigned int *value) {
    (void)map; (void)addr; *value = status; return failed_read;
}
static void input_report_key(void *input, unsigned int code, unsigned int value) {
    (void)input; (void)code; values[count++] = value;
}
static void input_sync(void *input) { (void)input; }
''' + irq + r'''
int main(void) {
    struct pm8941_data data = { .input_only = true, .status_bit = 1 };
    struct pm8941_pwrkey key = { .data = &data };
    pm8941_pwrkey_irq(0, &key);
    assert(count == 1 && values[0] == 0);
    count = 0; key.last_status = true;
    pm8941_pwrkey_irq(0, &key);
    assert(count == 1 && values[0] == 0);
    count = 0; data.input_only = false;
    pm8941_pwrkey_irq(0, &key);
    assert(count == 2 && values[0] == 1 && values[1] == 0);
    count = 0; data.input_only = true; failed_read = -1;
    pm8941_pwrkey_irq(0, &key);
    assert(count == 0 && errors == 1);
    return 0;
}
''')
        executable = self.root / 'irq-test'
        subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
                        str(harness), '-o', str(executable)], check=True,
                       capture_output=True)
        subprocess.run([str(executable)], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
