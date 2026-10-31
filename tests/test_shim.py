# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(all(shutil.which(x) for x in ('clang', 'ld.lld', 'llvm-objcopy', 'llvm-nm')), 'LLVM tools needed')
class ShimTests(unittest.TestCase):
    def test_assembled_layout(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            # Deliberately non-eight-byte-sized payload exercises exact incbin bounds.
            payload = bytearray(32771)
            payload[56:60] = b'ARMd'
            (tmp/'Image').write_bytes(payload)
            dtb = b'\xd0\x0d\xfe\xed' + b'DTB-test'
            (tmp/'board.dtb').write_bytes(dtb)
            subprocess.run(['clang','--target=aarch64-linux-gnu','-c','-x','assembler-with-cpp',
                            f'-DIMAGE_PATH="{tmp}/Image"', f'-DDTB_PATH="{tmp}/board.dtb"',
                            str(ROOT/'shim/copydown.S'), '-o',str(tmp/'shim.o')],check=True)
            subprocess.run(['ld.lld','--image-base=0','-Ttext=0','--entry=_start',str(tmp/'shim.o'),'-o',str(tmp/'shim.elf')],check=True)
            subprocess.run(['llvm-objcopy','-O','binary',str(tmp/'shim.elf'),str(tmp/'shim.bin')],check=True)
            syms = {}
            for line in subprocess.check_output(['llvm-nm','-n',str(tmp/'shim.elf')],text=True).splitlines():
                fields = line.split()
                if len(fields) == 3: syms[fields[2]] = int(fields[0],16)
            blob = (tmp/'shim.bin').read_bytes()
            self.assertEqual(blob[56:60], b'ARMd')
            self.assertEqual(struct.unpack_from('<Q',blob,16)[0],len(blob))
            self.assertEqual(syms['linux_image'], 0x200000)
            self.assertGreaterEqual(syms['copy_entry'],len(payload))
            self.assertEqual(blob[syms['linux_image']:syms['linux_end']], payload)
            self.assertEqual(blob[syms['runtime_dtb']:syms['runtime_dtb_end']], dtb)
            self.assertEqual(syms['runtime_dtb'] % 8, 0)
            # Both ABL entry points branch, rather than executing payload data.
            for off in (0,0x80000):
                self.assertEqual(struct.unpack_from('<I',blob,off)[0] & 0xfc000000, 0x14000000)

    def test_mkboot_pipeline_with_synthetic_inputs(self):
        # All generated images stay in a TemporaryDirectory, never out/.
        from test_bootimg import stock, image, fdt, bootimg
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            for directory in ('tools', 'shim', 'out'):
                (tmp/directory).mkdir()
            for relative in ('tools/mkboot.sh', 'tools/bootimg.py', 'tools/kernel_profile.py',
                             'shim/copydown.S', 'sources.json'):
                shutil.copy2(ROOT/relative, tmp/relative)
            (tmp/'out/Image').write_bytes(image(b'not-a-real-kernel'))
            (tmp/'out/picasso.dtb').write_bytes(fdt())
            (tmp/'out/kernel.config').write_text('CONFIG_INITRAMFS_SOURCE="/test/initramfs.list"\n# CONFIG_EFI is not set\n')
            (tmp/'stock.img').write_bytes(stock())
            subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            result = (tmp/'out/boot-picasso.img').read_bytes()
            self.assertEqual(bootimg.parse_stock(result)['dtb'], bootimg.parse_stock(stock())['dtb'])
            manifest_path = tmp/'out/boot-manifest.json'
            self.assertTrue(manifest_path.exists())
            self.assertIsNone(json.loads(manifest_path.read_text())['device'])
            # A radio trial must have a fresh, image-bound offline safety audit.
            (tmp/'out/dtb-profile.txt').write_text('wifi\n')
            failed = subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(b'Wi-Fi audit missing', failed.stderr)
            radio = {'status':'passed_offline_only','mpss_auto_boot':False,'modem_mdt_within_reserved_memory':True}
            for name,key in (('Image','image_sha256'),('picasso.dtb','candidate_dtb_sha256'),('kernel.config','kernel_config_sha256')):
                radio[key] = hashlib.sha256((tmp/'out'/name).read_bytes()).hexdigest()
            (tmp/'out/wifi-audit.json').write_text(json.dumps(radio))
            subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertEqual((tmp/'out/boot-picasso.img').read_bytes(), result)
            for key in ('image_sha256','candidate_dtb_sha256','kernel_config_sha256'):
                changed_radio = dict(radio); changed_radio[key] = '0'*64
                (tmp/'out/wifi-audit.json').write_text(json.dumps(changed_radio))
                failed = subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn(b'Stale Wi-Fi audit input', failed.stderr)
                self.assertEqual((tmp/'out/boot-picasso.img').read_bytes(), result)
            (tmp/'out/dtb-profile.txt').write_text('wifi-rmtfs\n')
            (tmp/'out/wifi-audit.json').write_text(json.dumps(radio))
            failed = subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(b'RMTFS memory audit missing', failed.stderr)
            self.assertEqual((tmp/'out/boot-picasso.img').read_bytes(), result)
            (tmp/'out/dtb-profile.txt').unlink()
            (tmp/'out/wifi-audit.json').unlink()
            # Device compatibility warnings must be explicit, independent of
            # whether the source image matches a download hash pin.
            (tmp/'device.json').write_text(json.dumps({
                'stock_boot': {'sha256': '0'*64},
                'current_rom': {'boot_test_status': 'blocked_test_fixture'},
            }))
            subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            manifest = json.loads(manifest_path.read_text())
            self.assertFalse(manifest['stock_matches_device_pin'])
            self.assertEqual(manifest['boot_test_status'], 'blocked_test_fixture')
            self.assertTrue(manifest['status'].startswith('OFFLINE ONLY'))
            self.assertEqual((tmp/'out/boot-picasso.img').read_bytes(), result)
            # A real-device result must be bound to exact image bytes/size;
            # changing a kernel must never inherit the old passing status.
            device = {
                'stock_boot': {'sha256': hashlib.sha256(stock()).hexdigest()},
                'current_rom': {'boot_test_status': 'passed_rescue_ram_boot'},
                'hardware_test': {
                    'status': 'passed_rescue_ram_boot',
                    'image_sha256': hashlib.sha256(result).hexdigest(),
                    'image_size': len(result),
                },
            }
            (tmp/'device.json').write_text(json.dumps(device))
            subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            manifest = json.loads(manifest_path.read_text())
            self.assertTrue(manifest['hardware_test_matches_image'])
            self.assertEqual(manifest['boot_test_status'], 'passed_rescue_ram_boot')
            self.assertIn('exact image rescue RAM-boot tested', manifest['status'])
            status = 'passed_fedora_ram_boot_with_known_service_failures'
            device['current_rom']['boot_test_status'] = status
            device['hardware_test']['status'] = status
            (tmp/'device.json').write_text(json.dumps(device))
            subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            manifest = json.loads(manifest_path.read_text())
            self.assertTrue(manifest['hardware_test_matches_image'])
            self.assertEqual(manifest['boot_test_status'], status)
            self.assertIn('known service failures', manifest['status'])
            # The installed OS supersedes the historical Android/RAM status.
            status = 'passed_fedora_persistent_xfs_boot_with_known_limitations'
            device['current_os'] = {'boot_test_status': status}
            device['hardware_test']['status'] = status
            (tmp/'device.json').write_text(json.dumps(device))
            subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            manifest = json.loads(manifest_path.read_text())
            self.assertTrue(manifest['hardware_test_matches_image'])
            self.assertEqual(manifest['boot_test_status'], status)
            self.assertIn('two normal reboots verified', manifest['status'])
            original = (tmp/'out/Image').read_bytes()
            changed = bytearray(original)
            changed[-1] ^= 1
            (tmp/'out/Image').write_bytes(changed)
            subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            manifest = json.loads(manifest_path.read_text())
            self.assertFalse(manifest['hardware_test_matches_image'])
            self.assertEqual(manifest['boot_test_status'], 'unverified_image_differs_from_tested_candidate')
            self.assertIn('not hardware tested', manifest['status'])
            (tmp/'out/Image').write_bytes(original)
            # Current-ROM baselines must pass a fresh audit and take precedence
            # over the historical MIUI download pin.
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            (tmp/'dtbo.img').write_bytes(b'synthetic DTBO audit fixture')
            baseline = {'boot_file': 'stock.img', 'boot_sha256': digest(tmp/'stock.img'),
                        'dtbo_file': 'dtbo.img', 'dtbo_sha256': digest(tmp/'dtbo.img'),
                        'audit_file': 'audit.json', 'dtb_index': 9, 'dtbo_index': 19}
            audit = {'offline_overlay_applied': True, 'uncovered_fixed_regions': [],
                     'archive': {'sha256': 'a'*64}, 'selected_indices': {'dtb': 9, 'dtbo': 19},
                     'inputs_sha256': {p: digest(tmp/p) for p in ('stock.img', 'dtbo.img', 'out/picasso.dtb')}}
            (tmp/'audit.json').write_text(json.dumps(audit))
            (tmp/'device.json').write_text(json.dumps({
                'stock_boot': {'sha256': '0'*64}, 'boot_baseline': baseline,
                'rom_package': {'sha256': 'a'*64},
                'current_rom': {'boot_test_status': 'blocked_test_fixture'},
            }))
            subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertTrue(json.loads(manifest_path.read_text())['stock_matches_device_pin'])
            self.assertEqual((tmp/'out/boot-picasso.img').read_bytes(), result)
            # Changed runtime DTS or a different input must fail BEFORE outputs
            # are touched, not silently reuse an earlier passing audit.
            (tmp/'out/picasso.dtb').write_bytes(fdt() + b'changed')
            failed = subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'stock.img')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(b'Stale ROM audit input', failed.stderr)
            self.assertEqual((tmp/'out/boot-picasso.img').read_bytes(), result)
            (tmp/'other-stock.img').write_bytes(stock() + b'other ROM')
            failed = subprocess.run(['bash',str(tmp/'tools/mkboot.sh'),str(tmp/'other-stock.img')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn(b'not the configured current-ROM baseline', failed.stderr)
            self.assertEqual((tmp/'out/boot-picasso.img').read_bytes(), result)
            # A selected parallel profile cannot inherit even an exact-byte
            # historical result, and must leave the default image/receipt alone.
            previous_manifest = manifest_path.read_bytes()
            candidate = tmp/'out/linux-7.3.1'
            candidate.mkdir()
            (candidate/'Image').write_bytes(original)
            (candidate/'picasso.dtb').write_bytes(fdt())
            shutil.copyfile(tmp/'out/kernel.config', candidate/'kernel.config')
            shutil.copyfile(ROOT/'sources-7.3.1.json', tmp/'sources-7.3.1.json')
            (tmp/'device.json').write_text(json.dumps(device))
            env = dict(os.environ, KERNEL_VERSION='7.3.1')
            subprocess.run(['bash', str(tmp/'tools/mkboot.sh'), str(tmp/'stock.img')],
                           env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fresh = json.loads((candidate/'boot-manifest.json').read_text())
            self.assertEqual(fresh['boot_test_status'], 'unverified_offline_candidate')
            self.assertFalse(fresh['hardware_test_matches_image'])
            self.assertEqual((tmp/'out/boot-picasso.img').read_bytes(), result)
            self.assertEqual(manifest_path.read_bytes(), previous_manifest)


@unittest.skipUnless(os.environ.get('PICASSO_RUN_QEMU_TESTS') == '1' and shutil.which('qemu-aarch64-static') and (ROOT/'downloads/busybox').exists(), 'optional QEMU test; set PICASSO_RUN_QEMU_TESTS=1, or validate applets natively on the phone')
class InitramfsTests(unittest.TestCase):
    def test_busybox_applets(self):
        available = set(subprocess.check_output(['qemu-aarch64-static',str(ROOT/'downloads/busybox'),'--list'],text=True).splitlines())
        required = {'sh','mount','mkdir','head','ls','seq','sleep','ip','ln','getty','setsid','findfs','grep','umount','switch_root','cat','uname'}
        self.assertFalse(required - available, f'missing applets: {required - available}')


if __name__ == '__main__':
    unittest.main()
