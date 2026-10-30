#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Best-effort disarm of this one known shutdown waiter, never scan processes.

Cannot undo a PID1 poweroff request already accepted. Does not reboot or reset.
"""
import json
import os
from pathlib import Path
import signal


def main():
    if os.geteuid()!=0:raise SystemExit('Root required')
    p=Path('/run/picasso-power-shutdown-control.json')
    if not p.exists():print(json.dumps({'status':'no_control_record_nothing_killed'}));return
    r=json.loads(p.read_text());boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if r['boot_id']!=boot:raise SystemExit('Wrong boot, refuse PID signal')
    pid=r['pid'];assert isinstance(pid,int) and pid>1
    root=Path('/proc')/str(pid)
    if not root.exists():print(json.dumps({'status':'waiter_already_exited','cannot_cancel_already_accepted_pid1_request':True}));return
    start=(root/'stat').read_text().rpartition(')')[2].split()[19];assert start==r['process_start_ticks'],'PID reused'
    argv=(root/'cmdline').read_bytes().split(b'\0')
    wrapper=b'/opt/picasso-power/power-shutdown-current.py' in argv and b'--confirmed-local-shutdown-test' in argv
    core=b'/opt/picasso-power/power-key-service.py' in argv and b'--arm-orderly-poweroff' in argv
    assert wrapper or core,'Unrecognized process; do not signal'
    os.kill(pid,signal.SIGTERM)
    print(json.dumps({'status':'term_sent_to_verified_single_waiter','pid':pid,'cannot_cancel_already_accepted_pid1_request':True}))


if __name__=='__main__':main()
