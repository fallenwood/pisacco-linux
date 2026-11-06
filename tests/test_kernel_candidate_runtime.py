# SPDX-License-Identifier: GPL-2.0-only
import importlib.util
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.object(sys, 'path', [str(ROOT / 'tools'), *sys.path]):
        spec.loader.exec_module(module)
    return module


activation = load('kernel-candidate-activation')
runtime = load('prepare-kernel-runtime')


class CandidateActivationTests(unittest.TestCase):
    def setUp(self):
        self.build = {'kernel_release': 'candidate', 'config_sha256': 'config',
                      'fdt_sha256': 'tree', 'boot_image_sha256': 'image'}
        self.authorization = {**self.build, 'allow_screen': True}

    def check(self, authorization=None, **changes):
        actual = {'release': 'candidate', 'config_sha256': 'config', 'fdt_sha256': 'tree', **changes}
        activation.validate_identity(self.authorization if authorization is None else authorization,
                                     self.build, 'screen', **actual)

    def test_exact_consent_does_not_authorize_another_kernel_or_tree(self):
        self.check()
        for field in ('release', 'config_sha256', 'fdt_sha256'):
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                self.check(**{field: 'previous-kernel'})

    def test_historical_or_truthy_consent_cannot_activate_candidate(self):
        for consent in ({}, {**self.authorization, 'allow_screen': 1},
                        {**self.authorization, 'boot_image_sha256': 'old-image'}):
            with self.subTest(consent=consent), self.assertRaises(RuntimeError):
                self.check(consent)

    def test_leased_screen_accepts_only_the_exact_backlight_instance_mask(self):
        with tempfile.TemporaryDirectory() as directory:
            mask = Path(directory) / 'systemd-backlight@backlight:picasso-screen.service'
            mask.symlink_to('/dev/null')
            activation.validate_screen_backlight_ownership(mask)

    def test_unmasked_or_redirected_backlight_loader_cannot_race_the_screen_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            mask = Path(directory) / 'systemd-backlight@backlight:picasso-screen.service'
            with self.assertRaises(RuntimeError):
                activation.validate_screen_backlight_ownership(mask)
            mask.write_text('[Service]\nExecStart=/usr/lib/systemd/systemd-backlight load %i\n')
            with self.assertRaises(RuntimeError):
                activation.validate_screen_backlight_ownership(mask)
            mask.unlink()
            mask.symlink_to('/usr/lib/systemd/system/systemd-backlight@.service')
            with self.assertRaises(RuntimeError):
                activation.validate_screen_backlight_ownership(mask)


class CandidateRelocationTests(unittest.TestCase):
    def test_new_controllers_and_cleanup_use_disjoint_paths(self):
        text = "/opt/picasso-wifi/wifi-auto-service.py /run/picasso-wifi /var/lib/picasso-screen"
        result = runtime.relocate(text, '7.3.1-picasso-wifi2')
        self.assertIn('/opt/picasso-kernel-7.3.1/picasso-wifi/wifi-auto-service.py', result)
        self.assertIn('/run/picasso-wifi-7.3.1 ', result)
        self.assertIn('/var/lib/picasso-screen-7.3.1', result)

    def test_shared_read_only_userspace_and_private_nv_are_not_relocated(self):
        for suffix in ('python-jail', 'tftp-root', 'userspace'):
            for ending in ('', '/proxy/helper.py', '"\n'):
                value = '/opt/picasso-wifi-trial/' + suffix + ending
                with self.subTest(value=value):
                    self.assertEqual(runtime.relocate(value, 'candidate'), value)
        value = '/var/lib/picasso-wifi-nv/work-wifi2 /var/lib/picasso-wifi/credentials'
        self.assertEqual(runtime.relocate(value, 'candidate'), value)

    def test_old_native_probation_cannot_be_reused_by_filename(self):
        result = runtime.relocate('/var/lib/picasso-wifi/auto-enable-consent-20261029.json',
                                  '7.3.1-picasso-wifi2')
        self.assertEqual(result, '/var/lib/picasso-wifi/auto-enable-consent-7.3.1.json')

    def test_shared_jail_executes_the_versioned_supervisor_without_rewriting_it(self):
        template = (ROOT / 'tools/rmtfs-supervised.service.in').read_text()
        rendered = runtime.bind_rmtfs_supervisor(runtime.relocate(template, '7.3.1-picasso-wifi2'))
        mounts = {}
        for line in rendered.splitlines():
            if line.startswith('BindReadOnlyPaths='):
                for binding in shlex.split(line.partition('=')[2]):
                    source, _, destination = binding.partition(':')
                    mounts[destination or source] = source
        command = next(line.partition('=')[2] for line in rendered.splitlines()
                       if line.startswith('ExecStart='))
        self.assertEqual(mounts[shlex.split(command)[2]],
                         '/opt/picasso-kernel-7.3.1/picasso-wifi/rmtfs-supervised.py')
        self.assertIn('RootDirectory=/opt/picasso-wifi-trial/python-jail\n', rendered)

    def test_changed_jail_layout_cannot_silently_run_the_old_supervisor(self):
        template = (ROOT / 'tools/rmtfs-supervised.service.in').read_text()
        with self.assertRaises(ValueError):
            runtime.bind_rmtfs_supervisor(template.replace('BindReadOnlyPaths=/usr\n', ''))

    def test_candidate_service_conditions_select_the_exact_kernel_before_exec(self):
        for name in ('screen', 'power-button', 'wifi-autoconnect-cn'):
            template = (ROOT / 'tools' / ('picasso-' + name + '.service')).read_text()
            rendered = runtime.bind_kernel_version(template, '7.3.1-picasso-wifi2')
            with self.subTest(service=name):
                self.assertIn('[Unit]\nConditionKernelVersion=7.3.1-picasso-wifi2\n', rendered)
                self.assertLess(rendered.index('ConditionKernelVersion='), rendered.index('[Service]'))

    def test_early_cooling_is_required_before_screen_and_wifi_activation(self):
        for name in ('screen', 'wifi-autoconnect-cn'):
            template = (ROOT / 'tools' / ('picasso-' + name + '.service')).read_text()
            rendered = runtime.bind_early_cooling(runtime.bind_kernel_version(template, '7.3.1-picasso-wifi2'))
            self.assertIn('Requires=picasso-thermal-policy.service\n', rendered)
            self.assertIn('After=picasso-thermal-policy.service\n', rendered)
            self.assertLess(rendered.index('Requires=picasso-thermal-policy.service'), rendered.index('[Service]'))
            with self.assertRaises(ValueError):
                runtime.bind_early_cooling(rendered)
        with self.assertRaises(ValueError):
            runtime.bind_early_cooling('[Service]\n')

    def test_existing_or_missing_kernel_condition_layout_requires_explicit_review(self):
        for template in ('[Service]\n', '[Unit]\nConditionKernelVersion=6.18.*\n[Service]\n'):
            with self.subTest(template=template), self.assertRaises(ValueError):
                runtime.bind_kernel_version(template, '7.3.1-picasso-wifi2')

    def test_screen_cooling_occurs_inside_the_owner_after_validation_before_input_arming(self):
        source = (ROOT / 'tools/screen-service.py').read_text()
        rendered = runtime.bind_screen_cooldown(runtime.relocate(source, '7.3.1-picasso-wifi2'))
        self.assertLess(rendered.index("data['console']=console.console_info()"),
                        rendered.index("load('startup_cooling'"))
        self.assertLess(rendered.index("load('startup_cooling'"),
                        rendered.index('below_temperature_limit(temperatures(),STARTUP_LIMIT_MC)'))
        self.assertLess(rendered.index('below_temperature_limit(temperatures(),STARTUP_LIMIT_MC)'),
                        rendered.index('keyfd=os.open'))
        self.assertIn('below_temperature_limit(values,RUNTIME_ABORT_MC)', rendered)
        self.assertIn('STARTUP_LIMIT_MC = 65000', rendered)
        self.assertIn('RUNTIME_ABORT_MC = 65000', rendered)
        compile(rendered, '<candidate-screen>', 'exec')

    def test_changed_screen_arming_layout_cannot_silently_drop_the_start_guard(self):
        source = (ROOT / 'tools/screen-service.py').read_text()
        with self.assertRaises(ValueError):
            runtime.bind_screen_cooldown(
                source.replace("        data['console']=console.console_info()\n", ''))


if __name__ == '__main__':
    unittest.main()
