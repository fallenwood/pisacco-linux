import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'out/power-install-20261028/commit-power-boot.py'


@unittest.skipUnless(PATH.exists(),'Deployment-specific boot writer not staged')
class PowerInstallTests(unittest.TestCase):
 def test_new_hash_matches_authorized_tested_image_padding(self):
  a=json.loads((PATH.parent/'authorization.json').read_text());h=hashlib.sha256((ROOT/'out/power-key-preparation-20261028/boot-power-key-trial.img').read_bytes());left=a['boot_bytes']-a['image_bytes']
  while left:n=min(left,1024**2);h.update(bytes(n));left-=n
  self.assertEqual(h.hexdigest(),a['new_full_partition_sha256']);self.assertIn(h.hexdigest(),PATH.read_text())
 def test_unique_partition_identity_and_exclusions(self):
  t=PATH.read_text()
  for s in ("u.get('PARTNAME')=='boot'",'len(matches)==1','4aadcdf3-3aad-3318-a158-46642b851943','SIZE=134217728',"(p/'holders')",'/proc/self/mountinfo','/proc/swaps','st_rdev==s.st_rdev'):
   self.assertIn(s,t)
  self.assertNotIn("Path('/dev/sde55')",t)
 def test_sync_full_readback_and_failure_no_reboot(self):
  t=PATH.read_text()
  for s in ('os.O_WRONLY|os.O_EXCL|os.O_SYNC|os.O_NOFOLLOW','os.fsync(fd)','fcntl.ioctl(fd,0x1261)','readback==NEW','failed_stop_do_not_reboot','boot_may_be_partial'):
   self.assertIn(s,t)
  for s in ('systemctl reboot','fastboot flash','BLKDISCARD','reset-failed'):
   self.assertNotIn(s,t)
 def test_both_rollback_versions_and_current_baseline_required(self):
  t=PATH.read_text()
  for s in ('boot-wifi2-rollback.img','boot-lts8-rollback.img',"device_digest()==OLD",'preflight_integrity_sha256','verified_monotonic_ns','static_files_verified'):
   self.assertIn(s,t)
 def test_known_auto_start_acceptance_explicit_and_no_other_boot_hash(self):
  t=PATH.read_text()
  self.assertIn("'accepts_usb_autostart','allow_boot_only','enable_long_hold_service','no_automatic_reboot'",t)
  for s in ('old_full_partition_sha256','new_full_partition_sha256'):self.assertIn(s,t)
  self.assertNotIn('allow_any',t)
 def test_v3_root_guard_is_PID1_namespace_RW_not_relaxed(self):
  t=(PATH.parent/'commit-power-boot-v3.py').read_text();self.assertIn("Path('/proc/1/mounts').read_text()",t);self.assertIn("root[0][2]=='xfs' and 'rw'",t)
  self.assertIn("('/proc/self/mountinfo','/proc/1/mountinfo')",t);self.assertIn("Path('/proc/1/exe').resolve()==Path('/usr/lib/systemd/systemd')",t)
 def test_v3_preflight_returns_before_exclusive_write_marker(self):
  t=(PATH.parent/'commit-power-boot-v3.py').read_text();self.assertLess(t.index('if preflight_only:'),t.index("marker=os.open(BASE/'commit-consumed'"));self.assertIn("device_digest()==OLD",t)
 def test_v3_process_link_capability_but_no_ptrace_memory_syscalls(self):
  t=(PATH.parent/'picasso-power-install3.service').read_text();self.assertIn('CAP_SYS_ADMIN CAP_SYS_PTRACE',t);self.assertIn('ptrace process_vm_readv process_vm_writev',t);self.assertIn('-/proc/1/mem',t)
 def test_old_verifier_unmodified_new_verifier_exact_new_hash_only(self):
  old=(ROOT/'out/wifi-install-20261028/verify-disk.py').read_text();new=(PATH.parent/'verify-power-disk.py').read_text();h='73d32de2d7e6ddd353fe76f6a513f8cf4c8a53eddc7ec8201a5fdd994ffd2d47'
  self.assertNotIn(h,old);self.assertIn(h,new);self.assertIn("==request['expected_fdt']",new)


if __name__=='__main__':unittest.main()
