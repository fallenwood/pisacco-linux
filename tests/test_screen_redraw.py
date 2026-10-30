import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('visual2',ROOT/'tools/test-screen-handoff2.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


class ScreenRedrawTests(unittest.TestCase):
    def test_unblank_then_redraw_then_backlight_order(self):
        events=[]
        class FakePath:
            def write_text(self,value):events.append(('blank',value))
        with patch.object(m,'Path',return_value=FakePath()),patch.object(m,'draw_pattern',side_effect=lambda *args:events.append(('redraw',))):
            m.screen_on(4,b'fixture',lambda:None,lambda value:events.append(('brightness',value)))
        self.assertEqual(events,[('blank','0'),('redraw',),('brightness',64)])

    def test_failed_redraw_never_turns_on_backlight(self):
        on=[]
        class FakePath:
            def write_text(self,value):pass
        with patch.object(m,'Path',return_value=FakePath()),patch.object(m,'draw_pattern',side_effect=RuntimeError('test failure')):
            with self.assertRaises(RuntimeError):m.screen_on(4,b'fixture',lambda:None,on.append)
        self.assertEqual(on,[])

    def test_full_frame_partial_write_offsets_and_guard(self):
        data=bytes(10368000);offsets=[];ticks=[]
        def write(fd,view,offset):
            offsets.append(offset);return 8 if offset==0 else len(view)
        with patch.object(m.os,'pwrite',side_effect=write):m.draw_pattern(4,data,lambda:ticks.append(True))
        self.assertEqual(offsets,[0,8]);self.assertEqual(len(ticks),2)

    def test_no_progress_or_wrong_size_fails(self):
        with patch.object(m.os,'pwrite',return_value=0):
            with self.assertRaises(RuntimeError):m.draw_pattern(4,b'fixture',lambda:None)
        with patch.object(m.os,'pwrite',side_effect=lambda fd,data,offset:len(data)):
            with self.assertRaises(RuntimeError):m.draw_pattern(4,b'fixture',lambda:None)

    def test_all_on_phases_share_redraw_no_one_time_initial_paint(self):
        text=(ROOT/'tools/test-screen-handoff2.py').read_text()
        self.assertEqual(text.count('screen_on(fb,frame,tick,brightness)'),1)
        self.assertEqual(text.count('frame=b\'\'.join(pattern_row(y)'),1)
        self.assertIn("RUN=Path('/run/picasso-screen-visual2')",text)
        self.assertIn("'full_redraw_after_unblank':on",text)
        self.assertNotIn('os.pread',text)
        self.assertNotIn('KDSETMODE',text)

    def test_new_exclusive_profile_keeps_old_trial_intact(self):
        text=(ROOT/'tools/run-screen-visual2.py').read_text()
        self.assertIn('visual-trial2-consumed',text);self.assertIn('os.O_EXCL',text)
        self.assertIn('picasso-display-visual2.service',text)
        wrapper=(ROOT/'tools/test-screen-handoff2.sh').read_text()
        self.assertIn('StrictHostKeyChecking=yes',wrapper)
        self.assertIn('run-screen-visual2.py',wrapper)
        self.assertIn('display-visual2-20261028',wrapper)
        self.assertNotIn('reset-failed',text+wrapper)


if __name__=='__main__':unittest.main()
