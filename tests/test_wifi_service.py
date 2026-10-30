import importlib.util
import json
import os
from pathlib import Path
import socket
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

def module(name):
    s=importlib.util.spec_from_file_location(name.replace('-','_'),ROOT/'tools'/(name+'.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

svc=module('wifi-service');lease=module('rmtfs-supervised')


class ServiceSafetyTests(unittest.TestCase):
    def test_exact_native_kernel_and_fdt_gates_present(self):
        text=(ROOT/'tools/wifi-service.py').read_text()
        for value in ('6.18.58-picasso-lts-wifi2','/proc/config.gz','/sys/firmware/fdt','PICASSO_FEDORA44_DISKROOT_V2','work-checkpoint.json','dirty.json'):
            self.assertIn(value,text)

    def test_credentials_metadata_only_and_native_passwd_file(self):
        text=(ROOT/'tools/wifi-service.py').read_text()
        self.assertIn("self.rules.private_file(CREDENTIALS/(name+'.passwd')",text)
        self.assertIn("'passwd-file',str(CREDENTIALS/(ssid+'.passwd'))",text)
        self.assertNotIn('--show-secrets',text)
        self.assertNotIn("'.passwd').read",text)
        self.assertNotIn('reset-failed',text)

    def test_parent_watchdog_no_restart_and_independent_cleanup(self):
        unit=(ROOT/'tools/picasso-wifi.service').read_text()
        self.assertIn('Type=notify',unit);self.assertIn('WatchdogSec=8s',unit)
        self.assertIn('Restart=no',unit);self.assertIn('ExecStopPost=',unit)
        self.assertIn('CPUAffinity=0 1 2 3',unit)

    def test_proxy_exact_four_fds_confinement_unchanged(self):
        unit=(ROOT/'tools/rmtfs-supervised.service.in').read_text()
        self.assertEqual(sum(l.startswith('OpenFile=') for l in unit.splitlines()),4)
        for value in ('DynamicUser=yes','User=picasso-rmtfs-auto','PrivateDevices=yes','DevicePolicy=closed','CapabilityBoundingSet=','InaccessiblePaths=/proc /sys /etc/ssh /home /root','Restart=no','--controller-pid @PID@'):
            self.assertIn(value,unit)
        self.assertEqual(sum(l.startswith('DeviceAllow=') for l in unit.splitlines()),1)
        self.assertNotIn('/dev/sd',unit)

    def test_lease_parameters_refuse_invalid_pid_and_timeout(self):
        for name,pid,timeout in (('',2,1),('test',1,1),('test',2,4),('x'*81,2,1)):
            with self.assertRaises(ValueError):lease.RootLease(name,pid,timeout)

    def test_lease_expiry_without_controller(self):
        obj=lease.RootLease('picasso-host-expiry-'+str(os.getpid()),os.getpid(),0.01)
        try:
            time.sleep(0.02)
            with self.assertRaises(TimeoutError):obj.poll()
        finally:obj.close()

    def test_memory_span_and_fixed_carveout(self):
        banks={'/memory@80000000':{'device_type':b'memory\0','reg':__import__('struct').pack('>QQ',0x80000000,0x100000000)}}
        mem={'physical_address':0xffd7f000,'usable_bytes':0x280000,'major':236,'minor':1}
        with patch.object(svc,'OPT',ROOT/'tools'):
            svc.validate_memory(banks,mem)
            for key,value in (('usable_bytes',4096),('physical_address',0x70001000),('minor',2)):
                with self.assertRaises(RuntimeError):svc.validate_memory(banks,{**mem,key:value})
            tree={**banks,'/reserved-memory':{'#address-cells':b'\0\0\0\2','#size-cells':b'\0\0\0\2'},'/reserved-memory/fixed':{'reg':__import__('struct').pack('>QQ',0xffd7e000,4096)}}
            with self.assertRaises(RuntimeError):svc.validate_memory(tree,mem)

    def test_live_health_requires_actual_sg_and_mac_and_caps(self):
        text=(ROOT/'tools/wifi-service.py').read_text()
        for value in ('self.identity()','self.audit()','45000','40000','1094400','authorized:','width: 20 MHz','--interface','--noproxy','ssl_verify_result'):
            self.assertIn(value,text)

    def test_cold_boot_transport_dependency_explicit(self):
        text=(ROOT/'tools/wifi-service.py').read_text()
        self.assertIn("self.text(['modprobe','qrtr_smd'])",text)
        self.assertIn("self.text(['modprobe','qcom_pd_mapper'])",text)

    def test_tftp_retains_validated_scratch_binding(self):
        unit=(ROOT/'tools/tftp-supervised.service.in').read_text()
        self.assertIn('StateDirectory=tqftpserv',unit)
        self.assertNotIn('StateDirectory=picasso-tftp-auto',unit)

    def test_thermal_guard_stops_lease_at_exact_45c(self):
        obj=svc.Service.__new__(svc.Service)
        obj.stop_event=__import__('threading').Event();obj.record={'peak_temperature_mc':0}
        obj.failure=None;obj.last_progress=time.monotonic();obj.live=False
        with patch.object(svc,'temperatures',return_value={'sensor':45000}):obj.guard()
        self.assertIn('45C thermal abort',obj.failure)

    def test_stalled_controller_guard_stops_lease(self):
        obj=svc.Service.__new__(svc.Service)
        obj.stop_event=__import__('threading').Event();obj.record={'peak_temperature_mc':0}
        obj.failure=None;obj.last_progress=time.monotonic()-5;obj.live=False
        with patch.object(svc,'temperatures',return_value={'sensor':35000}):obj.guard()
        self.assertIn('Controller progress lease expired',obj.failure)

    def test_isolated_2g_diagnostic_cannot_run_unbounded(self):
        text=(ROOT/'tools/wifi-service.py').read_text()
        self.assertIn("require(self.cfg.get('probation_seconds',0)>0,'2G-only diagnosis must remain bounded')",text)

    def test_no_default_enable_in_credential_entry(self):
        text=(ROOT/'tools/enter-wifi-autoconnect.py').read_text()
        self.assertNotIn('systemctl',text)


if __name__=='__main__':unittest.main()
