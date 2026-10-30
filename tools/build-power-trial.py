#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Pack an isolated power-key trial using exact installed #10 Image/modules ABI.

Offline only. Does not touch canonical #8, boot partitions or connected phone.
No alternate-board match, new kernel build, firmware or initramfs substitution.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
from bootimg import pack,parse_stock

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/power-key-preparation-20261028'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(mode=0o700,parents=True,exist_ok=True)
    image=ROOT/'out/wifi-rmtfs-20261027/Image';config=ROOT/'out/wifi-rmtfs-20261027/kernel.config';base=ROOT/'out/wifi-rmtfs-20261027/picasso.dtb';vendor=ROOT/'out/rom-audit/merged-09-19.dtb';stock=ROOT/'downloads/crdroid-9.12/boot.img';tested=ROOT/'out/wifi-rmtfs-20261027/boot-wifi2-trial.img'
    for path,pinned in ((image,'235d54cf5194555a7017e3aa9197ea71e4d6d57602598e0e4f5d56b1d558b91a'),(config,'f60bc2723f34cd08da927b4a3a79673bddc7bcd9052114cdd055cf958106dfbc'),(stock,'8d29b7ebfdc1c5dd8f58b59f95218e6df43197181259dc7a490e1c32d9650070'),(tested,'61022763880509ece9c87f1815b36c841bff4a0f08a4545f6c5f4f639a148304')):
        if sha(path)!=pinned:raise SystemExit('Unpinned input: '+str(path))
    target=OUT/'boot-power-key-trial.img'
    if target.exists():raise SystemExit('Exclusive trial image already packed; inspect existing receipts')
    src=ROOT/'src/linux-6.18.58';dtb=OUT/'power-trial.dtb'
    with (OUT/'build.log').open('w') as log:
        def run(args):subprocess.run(list(map(str,args)),check=True,stdout=log,stderr=log)
        run(['clang','-E','-P','-nostdinc','-undef','-D__DTS__','-x','assembler-with-cpp','-I',src/'arch/arm64/boot/dts/qcom','-I',src/'include',ROOT/'dts/sm7250-xiaomi-picasso-power-trial.dts','-o',OUT/'power-trial.dts.pp'])
        run([ROOT/'out/kbuild/scripts/dtc/dtc','-I','dts','-O','dtb','-o',dtb,OUT/'power-trial.dts.pp'])
        spec=importlib.util.spec_from_file_location('power_audit',ROOT/'tools/audit-power-key.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);audit=m.audit(base.read_bytes(),dtb.read_bytes(),vendor.read_bytes())
        (OUT/'power-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
        run(['clang','--target=aarch64-linux-gnu','-c','-x','assembler-with-cpp','-DIMAGE_PATH="'+str(image)+'"','-DDTB_PATH="'+str(dtb)+'"',ROOT/'shim/copydown.S','-o',OUT/'shim.o'])
        run(['ld.lld','--image-base=0','-Ttext=0','--entry=_start',OUT/'shim.o','-o',OUT/'shim.elf'])
        run(['llvm-objcopy','-O','binary',OUT/'shim.elf',OUT/'shim.bin'])
    symbols=subprocess.check_output(['llvm-nm','-n',str(OUT/'shim.elf')],text=True);(OUT/'shim.symbols').write_text(symbols)
    syms={x[2]:int(x[0],16) for line in symbols.splitlines() if len(x:=line.split())==3};blob=(OUT/'shim.bin').read_bytes()
    assert blob[56:60]==b'ARMd' and struct.unpack_from('<Q',blob,16)[0]==len(blob)
    assert syms['linux_image']==0x200000 and syms['copy_entry']>=image.stat().st_size
    assert blob[syms['linux_image']:syms['linux_end']]==image.read_bytes()
    assert blob[syms['runtime_dtb']:syms['runtime_dtb_end']]==dtb.read_bytes() and syms['runtime_dtb']%8==0
    packed=pack(stock.read_bytes(),blob);assert parse_stock(packed)['dtb']==parse_stock(tested.read_bytes())['dtb'];target.write_bytes(packed)
    result={'status':'offline_only_power_key_trial_packed_not_booted','image_reused_exact_installed_wifi2':True,'config_and_matching_modules_release_unchanged':'6.18.58-picasso-lts-wifi2','mainline_dt_only_adds_own_PM8150_PON_power_key':True,'stock_12_dtb_blob_preserved':True,'no_phone_io_flash_or_protected_data_access':True,'poweroff_poweron_and_native_power_events_not_accepted':True,'audit':audit,'artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in (target,dtb,OUT/'shim.bin')},'sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'dts/sm7250-xiaomi-picasso-power-trial.dts',ROOT/'tools/audit-power-key.py',ROOT/'tools/build-power-trial.py',ROOT/'shim/copydown.S')}}
    (OUT/'build-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['artifacts'][target.name]['sha256'])


if __name__=='__main__':main()
