#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Read-only own-ROM display/key audit. Never authorizes panel or PMIC writes."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from fdt import nodes,fixed_regions,region_covered


def cells(raw):
    if len(raw)%4:raise ValueError('Malformed cells')
    return struct.unpack('>'+str(len(raw)//4)+'I',raw)


def unique(items,what):
    items=list(items)
    if len(items)!=1:raise ValueError('Require unique '+what)
    return items[0]


def audit(vendor_blob,candidate_blob):
    v=nodes(vendor_blob);c=nodes(candidate_blob)
    if b'xiaomi,picasso' not in c['/'].get('compatible',b'').split(b'\0'):raise ValueError('Not a Picasso candidate')
    wn,wp=unique(((n,p) for n,p in v.items() if b'qcom,pm8150l-spmi-wled\0' in p.get('compatible',b'')),'factory WLED5')
    if not wn.endswith('/qcom,pm8150l@5/qcom,wled@d800') or cells(wp['reg'])!=(0xd800,0x100,0xd900,0x100):raise ValueError('Unexpected factory WLED resources')
    if (cells(wp['qcom,fs-current-limit']),cells(wp['qcom,ovp']),cells(wp['qcom,string-cfg']),cells(wp['qcom,cabc-sel']))!=((22500,),(28000,),(7,),(1,)):
        raise ValueError('Factory WLED settings differ; no guessed defaults')
    pn,pp=unique(((n,p) for n,p in v.items() if n.endswith('/qcom,pm8150@0/qcom,power-on@800')),'factory PM8150 PON')
    if cells(pp['reg'])!=(0x800,0x100) or cells(pp['interrupts'])[:8]!=(0,8,0,3,0,8,1,3):raise ValueError('Unexpected PON IRQ mapping')
    codes={cells(p['linux,code'])[0]:cells(p['qcom,pon-type'])[0] for n,p in v.items() if n.startswith(pn+'/') and 'linux,code' in p}
    if codes.get(116)!=0 or codes.get(114)!=1:raise ValueError('Unexpected factory power/volume-down mapping')
    for tree,label in ((v,'factory'),(c,'candidate')):
        up=unique((p for p in tree.values() if p.get('linux,code')==struct.pack('>I',115)),label+' volume-up')
        gp=cells(up['gpios'])
        parent=unique((n for n,p in tree.items() if p.get('phandle')==struct.pack('>I',gp[0])),label+' volume-up GPIO provider')
        if gp[1:]!=(5,1) or not any(s in parent for s in ('/qcom,pm8150l@4/','/pmic@4/')) or not ('wakeup-source' in up or 'gpio-key,wakeup' in up):raise ValueError('Volume-up must be PM8150L USID4 GPIO5 active-low/wakeup')
    primary=unique((p for p in v.values() if 'qcom,dsi-default-panel' in p),'factory default-panel property')
    ph=cells(primary['qcom,dsi-default-panel'])[0]
    default_node=unique((n for n,p in v.items() if p.get('phandle')==struct.pack('>I',ph)),'factory default-panel target')
    panel_names=[p['qcom,mdss-dsi-panel-name'].rstrip(b'\0').decode() for p in v.values() if 'qcom,mdss-dsi-panel-name' in p and p['qcom,mdss-dsi-panel-name'].startswith(b'xiaomi 3')]
    wn2,wp2=unique(((n,p) for n,p in c.items() if b'qcom,pm8150l-wled\0' in p.get('compatible',b'')),'candidate WLED')
    if not wn2.endswith('/pmic@5/backlight@d800') or cells(wp2['reg'])!=(0xd800,0xd900):raise ValueError('Candidate WLED USID/address differs')
    if wp2.get('status')!=b'disabled\0':raise ValueError('WLED setup/handoff not accepted; refuse implicit probe with unverified boost defaults')
    for key,value in [('qcom,current-limit-microamp',(22500,)),('qcom,ovp-millivolt',(28000,)),('qcom,enabled-strings',(0,1,2)),('qcom,cabc-sel',(1,)),('default-brightness',(0,))]:
        if cells(wp2[key])!=value:raise ValueError('Candidate property mismatch '+key)
    for code,irq in ((116,0),(114,1)):
        n,p=unique(((n,p) for n,p in c.items() if p.get('linux,code')==struct.pack('>I',code)),'candidate key '+str(code))
        if '/pmic@0/pon@800/' not in n or cells(p['interrupts'])!=(0,8,irq,3) or 'wakeup-source' not in p:raise ValueError('Candidate key wiring mismatch')
    for p in c.values():
        if p.get('compatible',b'').startswith((b'qcom,sm7250-mdss',b'qcom,sm7250-dpu',b'qcom,sm7250-dsi-ctrl')) and p.get('status')!=b'disabled\0':
            raise ValueError('Native display enabled without actual panel/controller validation')
    available=fixed_regions(c);uncovered=[r for r in fixed_regions(v) if not region_covered(r,available)]
    if uncovered:raise ValueError('Reserved-memory coverage regression')
    fb=unique((p for p in c.values() if p.get('compatible')==b'simple-framebuffer\0'),'splash framebuffer')
    width,height,stride=(cells(fb[x])[0] for x in ('width','height','stride'));reg=cells(fb['reg'])
    if (width,height,stride)!=(1080,2400,4320) or reg!=(0,0xa0000000,0,0x9e3400) or stride*height!=reg[3]:raise ValueError('Unexpected framebuffer span')
    return {'status':'passed_offline_handoff_key_preparation_native_display_blocked','hardware_tested':False,'vendor_dtb_sha256':hashlib.sha256(vendor_blob).hexdigest(),'candidate_dtb_sha256':hashlib.sha256(candidate_blob).hexdigest(),'wled':{'usid':5,'control':0xd800,'sink':0xd900,'strings':[0,1,2],'factory_full_scale_microamp':22500,'factory_ovp_millivolt':28000,'factory_cabc_select':1,'enabled_in_candidate':False,'boost_current_and_boot_handoff_not_verified':True},'keys':{'power':{'usid':0,'peripheral':8,'irq':0,'linux_code':116},'volume_down':{'usid':0,'peripheral':8,'irq':1,'linux_code':114},'volume_up':{'usid':4,'gpio':5,'active_low':True,'linux_code':115},'native_physical_events_verified':False},'framebuffer':{'address':0xa0000000,'bytes':0x9e3400,'width':width,'height':height,'stride':stride,'scope':'bootloader scanout handoff only'},'factory_default_panel_node':default_node,'factory_xiaomi_panel_candidates':panel_names,'actual_panel_identity_proven':False,'native_dsi_or_backlight_enable_authorized_by_this_audit':False,'reserved_memory_coverage_passed':True,'raw_partition_or_pmic_access':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vendor-dtb',type=Path,required=True);p.add_argument('--candidate-dtb',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    vendor=a.vendor_dtb.read_bytes()
    if hashlib.sha256(vendor).hexdigest()!='f75e1bf1af964147ee929b97a6b857516a4591b7bc096fe31e73d9ed8b8dc6f6':raise SystemExit('Not this phone pinned DTB9+DTBO19; no other-board substitutions')
    r=audit(vendor,a.candidate_dtb.read_bytes());a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['status'])


if __name__=='__main__':main()
