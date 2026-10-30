import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))

def module(name):
    s=importlib.util.spec_from_file_location(name.replace('-','_'),ROOT/'tools'/(name+'.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

p=module('screen-idle-policy');io=module('screen-idle');audit=module('audit-display')


class ScreenPolicyTests(unittest.TestCase):
    def test_idle_deadline_screen_off(self):
        x=p.ScreenPolicy(60,100)
        self.assertIsNone(x.tick(159.9));self.assertEqual(x.tick(160),'off');self.assertFalse(x.on)
        self.assertIsNone(x.tick(200))

    def test_each_of_three_keys_wakes_and_rearms_timeout(self):
        for key in (114,115,116):
            x=p.ScreenPolicy(60);x.tick(60)
            self.assertEqual(x.key(key,1,80),'on');self.assertEqual(x.deadline,140)

    def test_short_power_toggles_but_repeat_or_held_duplicate_does_not(self):
        x=p.ScreenPolicy(60)
        self.assertEqual(x.key(116,1,1),'off')
        self.assertIsNone(x.key(116,2,2));self.assertIsNone(x.key(116,1,3))
        x.key(116,0,4);self.assertEqual(x.key(116,1,5),'on')

    def test_volume_on_resets_idle_without_blank(self):
        x=p.ScreenPolicy(60)
        self.assertIsNone(x.key(115,1,50));self.assertEqual(x.deadline,110);self.assertTrue(x.on)

    def test_unknown_keys_are_not_activity_or_wake(self):
        x=p.ScreenPolicy(60);x.tick(60)
        self.assertIsNone(x.key(30,1,70));self.assertFalse(x.on)

    def test_invalid_timeouts_refused(self):
        for n in (0,4,3601):
            with self.assertRaises(ValueError):p.ScreenPolicy(n)

    def test_native_key_bitmap_preserves_word_width(self):
        self.assertEqual(io.key_bits('8000000000000 0'),{115})
        self.assertEqual(io.key_bits('10000000000000 0'),{116})
        self.assertEqual(io.key_bits('4000000000000 0'),{114})
        with self.assertRaises(ValueError):io.key_bits('1'+'0'*16)

    def test_off_physically_disables_backlight_before_virtual_blank(self):
        calls=[]
        with patch.object(io,'write_verified',side_effect=lambda path,v,accepted=None:calls.append((str(path),v,accepted))):
            io.apply({'backlight':'/audited/bl','framebuffer':'/audited/fb'},False,64)
        self.assertEqual(calls,[('/audited/bl/brightness',0,None),('/audited/fb/blank',4,(1,4))])

    def test_wake_orders_framebuffer_before_backlight(self):
        calls=[]
        with patch.object(io,'temps',return_value={'sensor':35000}),patch.object(io,'write_verified',side_effect=lambda path,v:calls.append((str(path),v))):
            io.apply({'backlight':'/audited/bl','framebuffer':'/audited/fb'},True,64)
        self.assertEqual(calls,[('/audited/fb/blank',0),('/audited/bl/brightness',64)])

    def test_hot_wake_refused_before_any_brightness_write(self):
        with patch.object(io,'temps',return_value={'sensor':45000}),patch.object(io,'write_verified') as write:
            with self.assertRaises(RuntimeError):io.apply({'backlight':'/audited/bl','framebuffer':'/audited/fb'},True,64)
            write.assert_not_called()

    def test_service_bounded_independent_off_and_no_default_enable(self):
        text=(ROOT/'tools/picasso-screen-trial.service.in').read_text()
        for value in ('RuntimeMaxSec=135s','WatchdogSec=8s','Restart=no','ExecStopPost=','--off','DevicePolicy=closed','@EXACT_INPUT_DEVICE_ALLOW@','CapabilityBoundingSet='):
            self.assertIn(value,text)
        self.assertNotIn('[Install]',text)

    def test_daemon_never_suspends_reboots_or_opens_raw_memory(self):
        text=(ROOT/'tools/screen-idle.py').read_text()
        self.assertNotIn('/dev/mem',text);self.assertNotIn('/sys/power/state',text)
        self.assertNotIn('systemctl',text)
        self.assertIn('hardware=discover(require_keys=not args.off)',text)
        self.assertIn("coverage=={114,115,116}",text)
        self.assertIn('EVIOCGRAB',text)

    def test_pmic_prep_defaults_remain_disabled_and_brightness_zero(self):
        text=(ROOT/'dts/sm7250-xiaomi-picasso-screen-handoff.dts').read_text()
        self.assertIn('default-brightness = <0>',text)
        self.assertIn('status = "disabled"',text)
        self.assertIn('qcom,current-limit-microamp = <22500>',text)
        self.assertIn('qcom,ovp-millivolt = <28000>',text)
        self.assertIn('IRQ_TYPE_EDGE_BOTH',text)
        self.assertEqual(text.count('wakeup-source;'),2)

    def test_auditor_cells_and_ambiguity_rejected(self):
        self.assertEqual(audit.cells(b'\0\0\0\5'),(5,))
        with self.assertRaises(ValueError):audit.cells(b'bad')
        with self.assertRaises(ValueError):audit.unique([], 'panel')
        with self.assertRaises(ValueError):audit.unique([1,2], 'panel')


if __name__=='__main__':unittest.main()
