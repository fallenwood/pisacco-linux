#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Explicit persistent-secret consent, only in a local native interactive TTY.

Does not start RF or silently enable a half-installed service. The operator must
complete guarded activation/normal-reboot validation before enabling default-on.
Never collect this directory as evidence. Controller checks metadata only;
native nmcli reads each SSID-specific PMK via passwd-file.
"""
import getpass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

ROOT=Path('/var/lib/picasso-wifi')
DEST=ROOT/'credentials'


def policy():
    p=Path(__file__).with_name('wifi-fallback-policy.py')
    spec=importlib.util.spec_from_file_location('wifi_policy',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def save(passphrase,parent=ROOT):
    rules=policy();values=rules.derive_both(passphrase)
    parent=Path(parent);parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    s=parent.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid or stat.S_IMODE(s.st_mode)!=0o700:
        raise ValueError('Unsafe private parent directory')
    dest=parent/'credentials'
    if dest.exists() or dest.is_symlink():raise ValueError('Existing credentials refused; no overwrite/readback of stored secrets')
    stage=Path(tempfile.mkdtemp(prefix='.credential-entry-',dir=parent));os.chmod(stage,0o700)
    try:
        entries={ssid+'.passwd':('802-11-wireless-security.psk:'+value+'\n').encode('ascii') for ssid,value in values.items()}
        consent={'scope':'persistent SSID-specific PMKs; guarded boot Wi-Fi; primary then fallback; CPU6/7 active-only max cap 1094400 kHz restored on stop; 45C fail-off; no retries after fatal errors',
                 'targets':[x[0] for x in rules.TARGETS], 'physical_encryption_claim':False,'automatic_cellular_enabled':False}
        entries['consent.json']=(json.dumps(consent,indent=2)+'\n').encode()
        for name,data in entries.items():
            fd=os.open(stage/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            try:
                view=memoryview(data)
                while view:
                    n=os.write(fd,view)
                    if n<=0:raise OSError('Short credential write')
                    view=view[n:]
                os.fsync(fd)
            finally:os.close(fd)
        fd=os.open(stage,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        os.rename(stage,dest)
        fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if stage.exists():shutil.rmtree(stage)


def main():
    os.umask(0o077)
    if os.geteuid()!=0 or os.uname().release!='6.18.58-picasso-lts-wifi2' or not sys.stdin.isatty() or not sys.stderr.isatty():
        raise SystemExit('Native wifi2 + interactive local TTY required; no password argv, pipes or chat')
    if len(sys.argv)!=1:raise SystemExit('No password arguments accepted')
    if DEST.exists() or DEST.is_symlink():raise SystemExit('Credentials already exist; do not overwrite or retrieve them')
    print('优先 Chaldea（5GHz），失败后仅回退 Chaldea-2.4G。')
    print('将分别派生并长期保存两个SSID的PMK，手机root0700目录/root0600文件；不是物理加密，root/离线读取存储者仍可获取。')
    print('后续受控开机Wi-Fi：开启期间CPU6/7最大1.0944GHz，关闭后恢复；45°C关停，不重启循环；不是充电/RF/长期稳定认证。')
    print('当前只保存凭据，不启动无线/启用未验收服务。旧临时凭据不会读取。')
    if input('同意上述保存和运行范围，请输入 SAVE AND ENABLE（其他输入取消）: ')!='SAVE AND ENABLE':
        raise SystemExit('Cancelled; nothing stored')
    first=getpass.getpass('两个SSID共同的WPA2密码（隐藏输入）: ')
    second=getpass.getpass('再次输入: ')
    if first!=second:raise SystemExit('Passwords differ; nothing stored')
    try:save(first)
    except (ValueError,OSError) as exc:raise SystemExit(type(exc).__name__+': credential storage refused')
    print('已保存SSID独立PMK及明确同意记录；未启动无线。不要发送密码，请回复 已保存。')


if __name__=='__main__':main()
