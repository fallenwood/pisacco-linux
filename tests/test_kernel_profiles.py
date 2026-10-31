# SPDX-License-Identifier: GPL-2.0-only
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ParallelKernelPreparation(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in ('tools', 'downloads', 'src/linux-6.18.58', 'out',
                          'kernel/patches/7.3'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        for name in ('kernel_profile.py', 'prepare-kernel.py'):
            shutil.copyfile(ROOT / 'tools' / name, self.root / 'tools' / name)
        self.source = self.root / 'src/linux-6.18.58/verified-source'
        self.source.write_bytes(b'preserve verified LTS source\n')
        self.image = self.root / 'out/boot-picasso.img'
        self.image.write_bytes(b'preserve verified LTS image\n')
        archive = self.root / 'downloads/linux-7.3.1.tar.xz'
        with tarfile.open(archive, 'w:xz') as stream:
            data = b'VERSION = 7\nPATCHLEVEL = 3\nSUBLEVEL = 1\n'
            member = tarfile.TarInfo('linux-7.3.1/Makefile')
            member.size = len(data)
            stream.addfile(member, io.BytesIO(data))
        manifest = {
            'kernel_version': '7.3.1',
            'downloads': [{'file': archive.name,
                           'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}],
        }
        (self.root / 'sources-7.3.1.json').write_text(json.dumps(manifest))
        (self.root / 'sources.json').write_text(json.dumps({'kernel_version': '6.18.58'}))
        (self.root / 'kernel/patches/series').write_text('must-not-apply.patch\n')
        (self.root / 'kernel/patches/7.3/series').write_text('native.patch\n')
        (self.root / 'kernel/patches/7.3/native.patch').write_text(
            '--- a/Makefile\n+++ b/Makefile\n@@ -1,3 +1,4 @@\n'
            ' VERSION = 7\n PATCHLEVEL = 3\n SUBLEVEL = 1\n+PICASSO = y\n')

    def prepare(self, version=None):
        env = os.environ.copy()
        env.pop('KERNEL_VERSION', None)
        if version is not None:
            env['KERNEL_VERSION'] = version
        return subprocess.run([sys.executable, str(self.root / 'tools/prepare-kernel.py')],
                              env=env, capture_output=True, text=True)

    def assert_lts_unchanged(self):
        self.assertEqual(self.source.read_bytes(), b'preserve verified LTS source\n')
        self.assertEqual(self.image.read_bytes(), b'preserve verified LTS image\n')

    def test_new_source_uses_only_its_own_patch_series(self):
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        result = self.prepare('7.3.1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PICASSO = y', (self.root / 'src/linux-7.3.1/Makefile').read_text())
        receipt = json.loads((self.root / 'src/linux-7.3.1/.picasso-source.json').read_text())
        self.assertEqual(set(receipt['patches']), {'native.patch'})
        self.assert_lts_unchanged()

    def test_parallel_source_alias_cannot_target_lts(self):
        (self.root / 'src/linux-7.3.1').symlink_to(self.source.parent, target_is_directory=True)
        result = self.prepare('7.3.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('must not redirect through symlinks', result.stderr)
        self.assert_lts_unchanged()

    def test_parallel_output_alias_cannot_target_lts(self):
        output = self.root / 'out/linux-7.3.1'
        output.mkdir()
        (output / 'modules').symlink_to(self.image.parent, target_is_directory=True)
        result = self.prepare('7.3.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('redirects outside its profile', result.stderr)
        self.assertFalse((self.root / 'src/linux-7.3.1').exists())
        self.assert_lts_unchanged()

    def test_default_preserves_and_refuses_existing_lts_source(self):
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('will not overwrite source work', result.stderr)
        self.assertFalse((self.root / 'src/linux-7.3.1').exists())
        self.assert_lts_unchanged()

    def test_unknown_profile_never_falls_back_to_lts(self):
        for version in ('', '7.3.2', '../../out'):
            with self.subTest(version=version):
                result = self.prepare(version)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Unsupported KERNEL_VERSION', result.stderr)
                self.assertFalse((self.root / 'src/linux-7.3.1').exists())
                self.assert_lts_unchanged()

    def test_mismatched_manifest_is_rejected_before_extraction(self):
        path = self.root / 'sources-7.3.1.json'
        manifest = json.loads(path.read_text())
        manifest['kernel_version'] = '6.18.58'
        path.write_text(json.dumps(manifest))
        result = self.prepare('7.3.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('profile and source manifest versions differ', result.stderr)
        self.assertFalse((self.root / 'src/linux-7.3.1').exists())
        self.assert_lts_unchanged()


class QrtrHandshakeCompatibility(unittest.TestCase):
    @unittest.skipUnless(shutil.which('clang'), 'clang is required for the QRTR handler test')
    def test_first_peer_hello_replies_once_and_failed_send_is_retryable(self):
        patch = (ROOT / 'kernel/patches/7.3/0004-qrtr-reply-to-first-peer-hello.patch').read_text()
        # Exercise the actual patched handlers without loading a host kernel module.
        new_side = '\n'.join(line[1:] for line in patch.splitlines()
                             if line.startswith((' ', '+')) and not line.startswith('+++'))
        start = new_side.index('static int say_hello(')
        end = new_side.index('\n}', new_side.index('static int ctrl_cmd_hello(')) + 2
        handlers = new_side[start:end]
        harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <endian.h>
#include <sys/socket.h>
#include <linux/qrtr.h>
struct kvec { void *iov_base; size_t iov_len; };
struct qrtr_node { bool hello_replied; };
static struct qrtr_node peer;
static struct { void *sock; } qrtr_ns;
static int sends, announces, errors, send_result = 20;
static bool available = true;
#define cpu_to_le32 htole32
#define pr_err(...) (++errors)
static struct qrtr_node *node_get(unsigned int id) {
    assert(id == 42);
    return available ? &peer : NULL;
}
static int announce_servers(struct sockaddr_qrtr *sq) {
    assert(sq->sq_node == 42);
    assert(peer.hello_replied);
    ++announces;
    return 0;
}
static int kernel_sendmsg(void *sock, struct msghdr *msg,
                          struct kvec *iv, size_t count, size_t length) {
    (void)sock;
    assert(count == 1 && length == sizeof(struct qrtr_ctrl_pkt));
    assert(((struct sockaddr_qrtr *)msg->msg_name)->sq_node == 42);
    assert(((struct qrtr_ctrl_pkt *)iv->iov_base)->cmd == cpu_to_le32(QRTR_TYPE_HELLO));
    ++sends;
    return send_result;
}
''' + handlers + r'''
int main(void) {
    struct sockaddr_qrtr sq = { .sq_node = 42 };
    assert(ctrl_cmd_hello(&sq) == 0);
    assert(sends == 1 && announces == 1 && peer.hello_replied);
    assert(ctrl_cmd_hello(&sq) == 0);
    assert(sends == 1 && announces == 2 && errors == 0);
    peer.hello_replied = false;
    send_result = -EAGAIN;
    assert(ctrl_cmd_hello(&sq) == -EAGAIN);
    assert(sends == 2 && announces == 2 && !peer.hello_replied && errors == 1);
    send_result = 20;
    assert(ctrl_cmd_hello(&sq) == 0);
    assert(sends == 3 && announces == 3 && peer.hello_replied);
    available = false;
    assert(ctrl_cmd_hello(&sq) == -ENOMEM);
    assert(sends == 3 && announces == 3);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'hello.c'
            binary = Path(directory) / 'hello'
            source.write_text(harness)
            build = subprocess.run(
                ['clang', '-std=gnu11', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(binary)],
                capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
