import importlib.util
from pathlib import Path
import re
import struct
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('visual_trial',ROOT/'tools/test-screen-handoff.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


class HandoffSafetyTests(unittest.TestCase):
    def test_audit_has_no_write_operations_or_arbitrary_parameters(self):
        text=(ROOT/'kernel/display/picasso-wled-audit.c').read_text()
        self.assertNotRegex(text,r'\b(?:regmap|spmi)_(?:write|update_bits|bulk_write|ext_register_write)\s*\(')
        self.assertIn('module_param(confirm_readonly, bool, 0444)',text)
        self.assertIn('pmic->usid != 5',text)
        self.assertIn('__ATTR_RO_MODE(snapshot, 0400)',text)
        self.assertIn('of_find_node_by_path("/soc@0/spmi@c440000/pmic@5/backlight@d800")',text)

    def test_handoff_only_brightness_sync_and_gate_writable(self):
        text=(ROOT/'kernel/display/picasso-wled-handoff.c').read_text()
        calls=re.findall(r'regmap_(?:bulk_write|update_bits)\(map,\s*(\w+)',text)
        self.assertTrue(calls);self.assertEqual(set(calls),{'CTRL_ENABLE','MOD_BRIGHT','MOD_SYNC'})
        for constant in ('#define CTRL_ENABLE 0xd846','#define MOD_BRIGHT  0xd953','#define MOD_SYNC    0xd965'):
            self.assertIn(constant,text)
        self.assertNotIn('regulator_enable',text);self.assertNotIn('mipi_dsi',text)
        self.assertNotIn('gpio_set',text)

    def test_kernel_deadline_cannot_be_renewed_by_brightness(self):
        text=(ROOT/'kernel/display/picasso-wled-handoff.c').read_text()
        self.assertEqual(text.count('expires = jiffies'),1)
        self.assertIn('duration_seconds > 90',text)
        self.assertIn('expired = true',text)
        self.assertIn('time_after_eq(jiffies, expires)',text)
        self.assertIn('schedule_delayed_work(&expiry_work',text)
        self.assertIn('cancel_delayed_work_sync(&expiry_work)',text)

    def test_current_voltage_boost_and_faults_checked_without_overwriting(self):
        text=(ROOT/'kernel/display/picasso-wled-handoff.c').read_text()
        for value in ('{0xd84d, 0x07}','{0xd84e, 0x05}','{0xd972, 0x09}','{0xd982, 0x09}','{0xd992, 0x09}','return -EUCLEAN','value & 0x17'):
            self.assertIn(value,text)

    def test_pattern_row_is_exact_size_subdued_and_not_pixel_capture(self):
        self.assertEqual(len(m.pattern_row(0)),4320)
        self.assertEqual(m.pattern_row(400)[:4],bytes((24,24,96,0)))
        self.assertEqual(m.pattern_row(1000)[:4],bytes((24,96,24,0)))
        self.assertEqual(m.pattern_row(1600)[:4],bytes((96,24,24,0)))
        text=(ROOT/'tools/test-screen-handoff.py').read_text()
        self.assertNotIn('os.pread',text);self.assertNotIn('/dev/mem',text);self.assertNotIn('mmap',text.replace('Never mmap physical memory.',''))

    def test_fb_shadow_geometry_accepted_physical_mapping_refused(self):
        def ioctl_factory(physical=False):
            def ioctl(fd,request,buf,mutate):
                if request==0x4602:
                    buf[:16]=b'simpledrmdrmfb'.ljust(16,b'\0')
                    struct.pack_into('@Q',buf,16,0xa0000000 if physical else 0)
                    struct.pack_into('@I',buf,24,10368000);struct.pack_into('@I',buf,48,4320)
                else:
                    struct.pack_into('@8I',buf,0,1080,2400,1080,2400,0,0,32,0)
                    for pos,value in ((32,(16,8,0)),(44,(8,8,0)),(56,(0,8,0)),(68,(0,0,0))):struct.pack_into('@3I',buf,pos,*value)
            return ioctl
        with patch.object(m.fcntl,'ioctl',side_effect=ioctl_factory()):m.framebuffer_info(1)
        with patch.object(m.fcntl,'ioctl',side_effect=ioctl_factory(True)):
            with self.assertRaises(RuntimeError):m.framebuffer_info(1)

    def test_wrapper_pins_ssh_and_requires_local_observer_not_password(self):
        text=(ROOT/'tools/test-screen-handoff.sh').read_text()
        self.assertIn('StrictHostKeyChecking=yes',text);self.assertIn('UserKnownHostsFile=',text)
        self.assertIn('read -r -p',text);self.assertIn('[[ -t 0 && -t 1 ]]',text)
        self.assertNotIn('enter-chaldea',text)

    def test_launcher_refuses_consumed_trial_and_clarifies_scheduled_wake(self):
        text=(ROOT/'tools/run-screen-visual.py').read_text()
        self.assertIn('visual-trial1-consumed',text);self.assertIn('os.O_EXCL',text)
        self.assertIn('pattern_on_scheduled_no_key_seen',text)
        self.assertIn('这不算按键唤醒通过',text)
        self.assertIn("systemctl','stop',UNIT",text)


if __name__=='__main__':unittest.main()
