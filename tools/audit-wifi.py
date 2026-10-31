#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fail-closed offline Picasso radio wiring/MDT audit. Never starts hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import fdt
from kernel_profile import select_profile


def require(ok, message):
    if not ok:
        raise ValueError(message)


def cells(props, key):
    raw = props[key]
    require(len(raw) % 4 == 0, 'Unaligned cells: '+key)
    return list(struct.unpack('>'+str(len(raw)//4)+'I', raw))


def reference(tree, props, key):
    handle = cells(props, key)[0]
    matches = [(p, v) for p, v in tree.items() if v.get('phandle') == struct.pack('>I', handle)]
    require(len(matches) == 1, 'Nonunique/missing phandle: '+key)
    return matches[0]


def memory(tree, props, key):
    path, node = reference(tree, props, key)
    raw = node['reg']
    require(len(raw) == 16 and 'no-map' in node, 'Require one no-map 64-bit region: '+path)
    return struct.unpack('>QQ', raw)


def mdt_load_span(blob):
    require(len(blob) >= 52 and blob[:6] == b'\x7fELF\x01\x01', 'Expected ELF32 little-endian MDT')
    require(struct.unpack_from('<H', blob, 18)[0] == 164, 'Expected Qualcomm DSP6 ELF')
    off = struct.unpack_from('<I', blob, 28)[0]
    size, count = struct.unpack_from('<HH', blob, 42)
    require(size == 32 and 0 < count <= 4096 and off+size*count <= len(blob), 'Invalid MDT program table')
    loads = []
    for i in range(count):
        p = struct.unpack_from('<8I', blob, off+i*size)
        # Qualcomm segment type 2 contains hashes, not loadable DSP memory.
        if p[0] == 1 and p[5] and ((p[6] >> 24) & 7) != 2:
            require(p[3]+p[5] <= 2**32, 'MDT physical address overflow')
            loads.append((p[3], p[3]+p[5]))
    require(bool(loads), 'No DSP load segments')
    return min(x[0] for x in loads), max(x[1] for x in loads)


def audit(vendor, candidate, modem_mdt):
    vw = vendor['/soc/qcom,icnss@18800000']
    vm = vendor['/soc/qcom,mss@4080000']
    w = candidate['/soc@0/wifi@18800000']
    m = candidate['/soc@0/remoteproc@4080000']
    require(w['compatible'] == b'qcom,wcn3990-wifi\0', 'Wrong Wi-Fi transport')
    require(m['compatible'] == b'qcom,sm7250-mpss-pas\0', 'Wrong PAS identity')
    require(cells(vm, 'qcom,pas-id') == [4], 'Vendor does not specify PAS 4')
    require(cells(vm, 'qcom,smem-id') == [421], 'Wrong crash SMEM')
    require(cells(vm, 'qcom,ssctl-instance-id') == [18], 'Wrong sysmon instance')
    require(cells(w, 'reg') == [0, *cells(vw, 'reg')[:1], 0, cells(vw, 'reg')[1]], 'Wi-Fi MMIO differs')
    require(w['interrupts'] == vw['interrupts'], 'CE IRQ sequence differs from own vendor DT')
    irqs = cells(w, 'interrupts')
    require(len(irqs) == 36 and all(irqs[i] == 0 and irqs[i+2] == 4 for i in range(0,36,3)), 'Expected 12 level-high GIC SPIs')
    vi, ci = cells(vw, 'iommus'), cells(w, 'iommus')
    require(vi[1:] == ci[1:] == [0xc0, 1], 'Wrong Wi-Fi SMMU stream/mask')
    _, vsmmu = reference(vendor, vw, 'iommus')
    _, csmmu = reference(candidate, w, 'iommus')
    require(cells(vsmmu,'reg')[:1] == [0x15000000] and cells(csmmu,'reg')[:2] == [0,0x15000000], 'Wrong SMMU provider')
    msa = memory(candidate, w, 'memory-region')
    require(msa == memory(vendor, vw, 'qcom,wlan-msa-fixed-region') == (0x8ba00000, 0x200000), 'MSA does not match vendor')
    modem = memory(candidate, m, 'memory-region')
    require(modem == memory(vendor, vm, 'memory-region') == (0x8c000000, 0xf800000), 'MPSS carveout differs')
    start,end = mdt_load_span(modem_mdt)
    require(modem[0] <= start < end <= sum(modem), 'Modem MDT exceeds reserved region')
    require(cells(m,'reg') == [0,cells(vm,'reg')[0],0,cells(vm,'reg')[1]], 'MPSS MMIO differs')
    ext = cells(m,'interrupts-extended')
    require(ext[1:4] == cells(vm,'interrupts-extended')[1:4] == [0,266,1], 'Wrong modem watchdog IRQ')
    require(len(ext) == 19 and [ext[i+1] for i in range(4,19,3)] == [0,1,2,3,7], 'Wrong modem SMP2P event bits')
    require(all(ext[i+2] == 1 for i in range(4,19,3)), 'SMP2P must use rising edges')
    smp = candidate['/smp2p-modem']; vsmp = vendor['/soc/qcom,smp2p-mpss']
    require(smp['qcom,smem'] == vsmp['qcom,smem'] and cells(smp,'qcom,smem') == [435,428], 'Wrong modem SMEM channel')
    require(cells(smp,'mboxes')[1:] == [2,2], 'Wrong modem IPCC signal')
    edge = candidate['/soc@0/remoteproc@4080000/glink-edge']
    require(cells(edge,'mboxes')[1:] == [2,0] and cells(edge,'qcom,remote-pid') == [1], 'Wrong GLINK modem endpoint')
    _,qmp = reference(candidate,m,'qcom,qmp')
    require(b'qcom,aoss-qmp\0' in qmp['compatible'] and cells(qmp,'reg')[:2] == [0,0xc300000], 'QMP must not point at the misnamed IPCC label')
    rails = {}
    for vk, ck in (('vdd-cx-mx-supply','vdd-0.8-cx-mx-supply'),('vdd-1.8-xo-supply','vdd-1.8-xo-supply'),('vdd-1.3-rfa-supply','vdd-1.3-rfa-supply'),('vdd-3.3-ch0-supply','vdd-3.3-ch0-supply'),('vdd-3.3-ch1-supply','vdd-3.3-ch1-supply')):
        vp,vn = reference(vendor,vw,vk); cp,cn = reference(candidate,w,ck)
        parent = candidate[cp.rsplit('/',1)[0]]
        pmic = parent['qcom,pmic-id'].decode().rstrip('\0')
        resource = 'ldo'+pmic+cp.rsplit('ldo',1)[1]
        require('/rpmh-regulator-'+resource+'/' in vp, 'Wrong physical regulator for '+ck)
        low,high = cells(cn,'regulator-min-microvolt')[0], cells(cn,'regulator-max-microvolt')[0]
        require(cells(vn,'regulator-min-microvolt')[0] <= low <= high <= cells(vn,'regulator-max-microvolt')[0], 'Voltage outside own vendor window: '+ck)
        rails[ck] = {'rpmh_resource':resource,'min_uv':low,'max_uv':high}
    require('/soc@0/wifi@18800000/wifi-firmware' not in candidate, 'Do not map nonsecure DSP firmware into MSA')
    require(w.get('qcom,calibration-variant') == b'Xiaomi-Picasso\0', 'Board calibration must be scoped to Picasso')
    require(m.get('firmware-name') == b'qcom/sm7250/picasso/modem.mdt\0', 'Unscoped modem firmware name')
    uncovered = [r for r in fdt.fixed_regions(vendor) if not fdt.region_covered(r,fdt.fixed_regions(candidate))]
    require(not uncovered, 'Fixed vendor reserved regions are not covered')
    return {'status':'passed_offline_only','hardware_tested':False,'ce_gic_spis':irqs[1::3],
            'msa':{'start':msa[0],'bytes':msa[1]},'mpss_memory':{'start':modem[0],'bytes':modem[1]},
            'modem_mdt_load_span':[start,end],'modem_mdt_within_reserved_memory':True,
            'supply_windows':rails,'fixed_reserved_regions_covered':len(fdt.fixed_regions(vendor)),
            'mpss_auto_boot':False,'mpss_manual_start_required':True,
            'does_not_authorize_efs_or_firmware_partition_writes':True}


def audit_rmtfs(tree):
    matches=[(p,n) for p,n in tree.items() if n.get('compatible')==b'qcom,rmtfs-mem\0']
    require(len(matches)==1, 'Require exactly one RMTFS memory node')
    path,n=matches[0]
    require(path.startswith('/reserved-memory/') and 'reg' not in n, 'RMTFS must be dynamically reserved, not a guessed address')
    require(n.get('status',b'okay\0')==b'okay\0', 'RMTFS memory disabled')
    require('no-map' in n and 'qcom,use-guard-pages' in n, 'RMTFS must have no-map and two guard pages')
    require(cells(n,'size')==[0,0x282000] and cells(n,'alignment')==[0,0x1000], 'RMTFS usable size/guard alignment mismatch')
    require(cells(n,'alloc-ranges')==[0,0x80000000,0,0x80000000], 'RMTFS allocation must stay below 4GiB in Linux RAM')
    require(cells(n,'qcom,client-id')==[1] and cells(n,'qcom,vmid')==[15], 'Wrong RMTFS client or VMID')
    return {'checked':True,'dynamic':True,'reserved_bytes':0x282000,'usable_bytes':0x280000,'guard_bytes':8192,'alloc_range':[0x80000000,0x100000000],'client_id':1,'vmid':15}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vendor',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--modem-mdt',type=Path,required=True)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--require-rmtfs',action='store_true')
    a=p.parse_args()
    candidate=fdt.nodes(a.candidate.read_bytes())
    r=audit(fdt.nodes(a.vendor.read_bytes()),candidate,a.modem_mdt.read_bytes())
    c=a.config.read_text()
    if a.require_rmtfs:
        r['rmtfs']=audit_rmtfs(candidate)
        require('CONFIG_QCOM_RMTFS_MEM=m\n' in c, 'RMTFS must remain a manually loaded module')
    root=Path(__file__).resolve().parents[1]
    profile=select_profile(root)
    family='-picasso' if profile.version=='7.3.1' else '-picasso-lts'
    require(re.search(r'^CONFIG_LOCALVERSION="'+re.escape(family)+r'-wifi[0-9]+"$',c,re.M), 'Trial modules would collide with installed kernel')
    for name in ('ATH10K_SNOC','QCOM_Q6V5_PAS','QRTR','QRTR_SMD','QCOM_PD_MAPPER'):
        require('CONFIG_'+name+'=m\n' in c,'Missing trial module: '+name)
    pas=(profile.source/'drivers/remoteproc/qcom_q6v5_pas.c').read_text()
    require('"qcom,sm7250-mpss-pas", .data = &mpss_resource_init' in pas, 'Unknown PAS driver data')
    data=pas.split('static const struct qcom_pas_data mpss_resource_init = {',1)[1].split('};',1)[0]
    require('.auto_boot = false' in data and '.pas_id = 4' in data,'MPSS must not automatically start')
    image=a.config.parent/'Image'
    require(image.is_file(), 'Matching compiled Image is missing')
    r.update(image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
             candidate_dtb_sha256=hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
             vendor_dtb_sha256=hashlib.sha256(a.vendor.read_bytes()).hexdigest(),
             modem_mdt_sha256=hashlib.sha256(a.modem_mdt.read_bytes()).hexdigest(),
             kernel_config_sha256=hashlib.sha256(a.config.read_bytes()).hexdigest())
    a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))


if __name__=='__main__':
    main()
