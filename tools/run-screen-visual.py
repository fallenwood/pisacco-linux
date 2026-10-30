#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Local operator launcher for an exclusive PID1-bounded visual trial; no secrets."""
import json
import os
from pathlib import Path
import subprocess
import time

RUN=Path('/run/picasso-screen-visual1')
UNIT='picasso-display-visual1.service'


def main():
    if os.geteuid()!=0 or os.uname().release!='6.18.58-picasso-lts-wifi2':raise SystemExit('Native tested kernel/root required')
    marker=Path('/var/lib/picasso-display/visual-trial1-consumed')
    if RUN.exists() or marker.exists() or marker.is_symlink():raise SystemExit('此一次性试验已运行或启动过；请检查既有结果，不重复启动。')
    if max(int(p.read_text()) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp'))>=40000:raise SystemExit('温度>=40°C，拒绝启动；未消耗试验名额。')
    marker.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(marker,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:os.write(fd,b'Exclusive visual test launched; inspect existing unit/result before any retry.\n');os.fsync(fd)
    finally:os.close(fd)
    subprocess.run(['systemctl','start','--no-block',UNIT],check=True)
    previous=None;deadline=time.monotonic()+115
    phases={'pattern_on_first_15s':'第一段：应见低亮度灰底和红/绿/蓝横条，约15秒。',
            'off_press_only_volume_up_within_20s':'现在息屏：只短按一次【音量上】。不要按电源/音量下，不要长按。',
            'pattern_on_by_volume_up':'已记录真实音量上按下：应再次看见色条。',
            'pattern_on_scheduled_no_key_seen':'未记录到音量上，按定时再次亮屏；这不算按键唤醒通过。',
            'final_off':'试验结束：背光应关闭。'}
    final_state=''
    while time.monotonic()<deadline:
        p=RUN/'result.json'
        if p.exists():
            r=json.loads(p.read_text());phase=r.get('phase')
            if phase!=previous:
                print(phases.get(phase,phase or '正在准备'),flush=True);previous=phase
        final_state=subprocess.check_output(['systemctl','show',UNIT,'-p','ActiveState','-p','SubState','-p','Result'],text=True)
        if 'ActiveState=inactive' in final_state or 'ActiveState=failed' in final_state:break
        time.sleep(0.5)
    else:
        subprocess.run(['systemctl','stop',UNIT],check=False)
        raise SystemExit('观察等待超时；已请求关停，勿重跑，请检查清理状态。')
    if not (RUN/'result.json').exists():raise SystemExit('单元结束但结果缺失；保留失败，请检查journal。')
    r=json.loads((RUN/'result.json').read_text())
    print(json.dumps({'result':r,'unit_state':final_state},ensure_ascii=False),flush=True)
    return 0 if r['status']=='completed_bounded_sequence_visual_confirmation_required' and r['module_unloaded'] and 'Result=success' in final_state else 1


if __name__=='__main__':raise SystemExit(main())
