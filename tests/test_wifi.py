# SPDX-License-Identifier: GPL-2.0-only
import copy
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('audit_wifi',ROOT/'tools/audit-wifi.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def u(*v): return struct.pack('>'+str(len(v))+'I',*v)
def reg64(start,size): return struct.pack('>QQ',start,size)


def fixture():
    v={'/reserved-memory':{'#address-cells':u(2),'#size-cells':u(2)}}
    c=copy.deepcopy(v)
    vw={'reg':u(0x18800000,0x800000,0xb0000000,0x10000),'iommus':u(10,0xc0,1),'qcom,wlan-msa-fixed-region':u(11)}
    cw={'compatible':b'qcom,wcn3990-wifi\0','reg':u(0,0x18800000,0,0x800000),'iommus':u(10,0xc0,1),'memory-region':u(11),'qcom,calibration-variant':b'Xiaomi-Picasso\0'}
    irqs=u(*[x for irq in (132,81,415,416,417,86,94,96,82,119,120,87) for x in (0,irq,4)])
    vw['interrupts']=cw['interrupts']=irqs
    v['/soc/qcom,icnss@18800000']=vw; c['/soc@0/wifi@18800000']=cw
    for tree in (v,c):
        tree['/reserved-memory/msa']={'phandle':u(11),'reg':reg64(0x8ba00000,0x200000),'no-map':b''}
        tree['/reserved-memory/modem']={'phandle':u(12),'reg':reg64(0x8c000000,0xf800000),'no-map':b''}
    v['/soc/smmu']={'phandle':u(10),'reg':u(0x15000000,0x100000)}
    c['/soc@0/smmu']={'phandle':u(10),'reg':u(0,0x15000000,0,0x100000)}
    vm={'reg':u(0x4080000,0x100),'memory-region':u(12),'qcom,pas-id':u(4),'qcom,smem-id':u(421),'qcom,ssctl-instance-id':u(18),'interrupts-extended':u(1,0,266,1)}
    cm={'compatible':b'qcom,sm7250-mpss-pas\0','reg':u(0,0x4080000,0,0x100),'memory-region':u(12),
        'interrupts-extended':u(1,0,266,1,*[x for bit in (0,1,2,3,7) for x in (4,bit,1)]),
        'qcom,qmp':u(13),'firmware-name':b'qcom/sm7250/picasso/modem.mdt\0'}
    v['/soc/qcom,mss@4080000']=vm; c['/soc@0/remoteproc@4080000']=cm
    v['/soc/qcom,smp2p-mpss']={'qcom,smem':u(435,428)}
    c['/smp2p-modem']={'qcom,smem':u(435,428),'mboxes':u(14,2,2)}
    c['/soc@0/remoteproc@4080000/glink-edge']={'mboxes':u(14,2,0),'qcom,remote-pid':u(1)}
    c['/soc@0/qmp']={'phandle':u(13),'compatible':b'qcom,aoss-qmp\0','reg':u(0,0xc300000,0,0x400)}
    for i,(old,new,pmic,num,lo,hi,clo,chi) in enumerate((
        ('vdd-cx-mx-supply','vdd-0.8-cx-mx-supply','a',1,352000,952000,752000,752000),
        ('vdd-1.8-xo-supply','vdd-1.8-xo-supply','a',14,1616000,1984000,1800000,1800000),
        ('vdd-1.3-rfa-supply','vdd-1.3-rfa-supply','c',2,1144000,1328000,1144000,1328000),
        ('vdd-3.3-ch0-supply','vdd-3.3-ch0-supply','c',10,3000000,3312000,3000000,3312000),
        ('vdd-3.3-ch1-supply','vdd-3.3-ch1-supply','c',11,3000000,3312000,3000000,3312000))):
        h=20+i; vw[old]=cw[new]=u(h)
        v[f'/soc/rpmh-regulator-ldo{pmic}{num}/regulator']={'phandle':u(h),'regulator-min-microvolt':u(lo),'regulator-max-microvolt':u(hi)}
        c[f'/soc@0/regulators-{pmic}']={'qcom,pmic-id':pmic.encode()+b'\0'}
        c[f'/soc@0/regulators-{pmic}/ldo{num}']={'phandle':u(h),'regulator-min-microvolt':u(clo),'regulator-max-microvolt':u(chi)}
    elf=bytearray(84); elf[:6]=b'\x7fELF\x01\x01'; struct.pack_into('<H',elf,18,164)
    struct.pack_into('<I',elf,28,52); struct.pack_into('<HH',elf,42,32,1)
    struct.pack_into('<8I',elf,52,1,0x1000,0x8c000000,0x8c000000,0x1000,0x2000,0x8000005,0x1000)
    return v,c,elf


class WifiAudit(unittest.TestCase):
    def setUp(self): self.v,self.c,self.elf=fixture()
    def check(self): return mod.audit(self.v,self.c,self.elf)
    def test_scoped_radio_passes_offline_only(self):
        r=self.check(); self.assertEqual(r['status'],'passed_offline_only'); self.assertFalse(r['hardware_tested'])
    def test_foreign_soc_irq_sequence_rejected(self):
        self.c['/soc@0/wifi@18800000']['interrupts']=u(*[x for i in range(414,426) for x in (0,i,4)])
        with self.assertRaises(ValueError): self.check()
    def test_wrong_smmu_stream_rejected(self):
        self.c['/soc@0/wifi@18800000']['iommus']=u(10,0x20,1)
        with self.assertRaises(ValueError): self.check()
    def test_undersized_mpss_region_rejected(self):
        self.c['/reserved-memory/modem']['reg']=reg64(0x8c000000,0x1000)
        with self.assertRaises(ValueError): self.check()
    def test_out_of_carveout_firmware_rejected(self):
        struct.pack_into('<I',self.elf,52+12,0xb0000000)
        with self.assertRaises(ValueError): self.check()
    def test_wrong_machine_rejected(self):
        struct.pack_into('<H',self.elf,18,183)
        with self.assertRaises(ValueError): self.check()
    def test_below_vendor_voltage_rejected(self):
        self.c['/soc@0/regulators-c/ldo2']['regulator-min-microvolt']=u(1104000)
        with self.assertRaises(ValueError): self.check()
    def test_swapped_antenna_supplies_rejected(self):
        self.c['/soc@0/wifi@18800000']['vdd-3.3-ch0-supply']=u(24)
        with self.assertRaises(ValueError): self.check()
    def test_wrong_qmp_provider_rejected(self):
        self.c['/soc@0/qmp']['compatible']=b'qcom,ipcc\0'
        with self.assertRaises(ValueError): self.check()
    def test_missing_no_map_rejected(self):
        del self.c['/reserved-memory/msa']['no-map']
        with self.assertRaises(ValueError): self.check()
    def test_nonsecure_firmware_mapping_rejected(self):
        self.c['/soc@0/wifi@18800000/wifi-firmware']={}
        with self.assertRaises(ValueError): self.check()
    def test_generic_calibration_rejected(self):
        self.c['/soc@0/wifi@18800000']['qcom,calibration-variant']=b'generic\0'
        with self.assertRaises(ValueError): self.check()


if __name__=='__main__': unittest.main()
