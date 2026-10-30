import ast
import importlib.util
import os
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('native_console',ROOT/'tools/screen-console.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


class ConsoleDisplayTests(unittest.TestCase):
 def test_native_blank_redraw_unblank_then_low_backlight(self):
  calls=[]
  class Blank:
   value='0'
   def write_text(self,value):self.value=value;calls.append(('blank',value))
   def read_text(self):return '1' if self.value=='4' else self.value
  with patch.object(m,'console_info',side_effect=lambda:calls.append(('console_check',))),patch.object(m,'Path',return_value=Blank()):
   m.screen_on(lambda:calls.append(('tick',)),lambda value:calls.append(('brightness',value)))
  self.assertEqual(calls,[('console_check',),('blank','4'),('tick',),('blank','0'),('tick',),('brightness',64)])

 def test_console_or_unblank_failure_never_lights(self):
  on=[]
  with patch.object(m,'console_info',side_effect=RuntimeError('graphics owner')):
   with self.assertRaises(RuntimeError):m.screen_on(lambda:None,on.append)
  class BadBlank:
   def write_text(self,value):pass
   def read_text(self):return '1'
  with patch.object(m,'console_info'),patch.object(m,'Path',return_value=BadBlank()):
   with self.assertRaises(RuntimeError):m.screen_on(lambda:None,on.append)
  self.assertEqual(on,[])

 def console_fixture(self,mode=0,active='tty1'):
  class FakePath:
   def __init__(self,value):self.value=str(value);self.name='vtcon1'
   def __truediv__(self,key):return FakePath(self.value+'/'+key)
   def read_text(self):
    if self.value.endswith('/active'):return active
    if self.value.endswith('/name'):return '(M) frame buffer device'
    if self.value.endswith('/bind'):return '1'
    raise AssertionError('No terminal/pixel reads')
   def glob(self,pattern):return [FakePath('/sys/class/vtconsole/vtcon1')]
   def lstat(self):return SimpleNamespace(st_mode=0o20600,st_rdev=os.makedev(4,1))
  def ioctl(fd,request,data,mutate):
   self.assertEqual(request,0x4b3b);struct.pack_into('@i',data,0,mode)
  return FakePath,ioctl

 def test_console_kd_text_metadata_only_readonly_fd(self):
  fake,ioctl=self.console_fixture()
  with patch.object(m,'Path',fake),patch.object(m.os,'open',return_value=77) as op,patch.object(m.os,'fstat',return_value=SimpleNamespace(st_rdev=os.makedev(4,1))),patch.object(m.os,'close') as close,patch.object(m.fcntl,'ioctl',side_effect=ioctl):
   r=m.console_info();self.assertEqual(r['mode'],'KD_TEXT');self.assertFalse(r['pixel_or_terminal_payload_read_or_written'])
   op.assert_called_once_with('/dev/tty1',os.O_RDONLY|os.O_NOCTTY|os.O_NOFOLLOW);close.assert_called_once_with(77)

 def test_graphics_owner_refused_without_mode_change(self):
  fake,ioctl=self.console_fixture(mode=1)
  with patch.object(m,'Path',fake),patch.object(m.os,'open',return_value=77),patch.object(m.os,'fstat',return_value=SimpleNamespace(st_rdev=os.makedev(4,1))),patch.object(m.os,'close'),patch.object(m.fcntl,'ioctl',side_effect=ioctl):
   with self.assertRaises(RuntimeError):m.console_info()

 def test_other_active_vt_refused_no_console_switch(self):
  fake,ioctl=self.console_fixture(active='tty2')
  with patch.object(m,'Path',fake),patch.object(m.os,'open') as op:
   with self.assertRaises(RuntimeError):m.console_info()
   op.assert_not_called()

 def test_helper_has_no_pixel_or_terminal_payload_io(self):
  text=(ROOT/'tools/screen-console.py').read_text();tree=ast.parse(text)
  for n in ast.walk(tree):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='os':
    self.assertNotIn(n.func.attr,('read','write','pread','pwrite'))
  self.assertNotIn('pattern_row',text);self.assertNotIn('mmap',text)

 def test_only_service_pwrite_is_kernel_lease_not_pixels(self):
  text=(ROOT/'tools/screen-service.py').read_text();tree=ast.parse(text);writes=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='pwrite':writes.append(n)
  self.assertEqual(len(writes),1);self.assertIsInstance(writes[0].args[0],ast.Name);self.assertEqual(writes[0].args[0].id,'leasefd')
  self.assertNotIn('visual-render.py',text);self.assertNotIn('pattern_row',text)

 def test_unit_only_readonly_framebuffer_and_tty_native_getty_dependency(self):
  text=(ROOT/'tools/picasso-screen.service').read_text()
  self.assertIn('Requires=getty@tty1.service',text);self.assertIn('DeviceAllow=/dev/fb0 r\n',text);self.assertIn('DeviceAllow=/dev/tty1 r\n',text)
  self.assertNotIn('/dev/fb0 rw',text);self.assertNotIn('/dev/tty1 rw',text)


if __name__=='__main__':unittest.main()
