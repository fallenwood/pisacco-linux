#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Generate a private, versioned candidate runtime; no deployment or activation."""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

from kernel_profile import select_profile


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def constants(path):
    return {node.targets[0].id: node.value.value for node in ast.parse(path.read_text()).body
            if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Constant)}


def relocate(text, release):
    prefix = '/opt/picasso-kernel-7.3.1'
    text = re.sub(r'/opt/picasso-(?!wifi-trial/(?:python-jail|tftp-root|userspace)(?:/|[\'"\s]|$))',
                  prefix + '/picasso-', text)
    text = text.replace('6.18.58-picasso-lts-wifi2', release)
    for name in ('screen', 'wifi', 'power-button'):
        text = text.replace('/run/picasso-' + name, '/run/picasso-' + name + '-7.3.1')
    for name in ('screen', 'power-button'):
        text = text.replace('/var/lib/picasso-' + name, '/var/lib/picasso-' + name + '-7.3.1')
    return text.replace('auto-enable-consent-20261029.json', 'auto-enable-consent-7.3.1.json')


def bind_rmtfs_supervisor(text):
    marker = 'BindReadOnlyPaths=/usr\n'
    if text.count(marker) != 1 or 'ExecStart=/usr/bin/python3 -I /proxy/rmtfs-supervised.py ' not in text:
        raise ValueError('Unexpected supervised RMTFS jail layout')
    return text.replace(marker, marker + 'BindReadOnlyPaths='
                        '/opt/picasso-kernel-7.3.1/picasso-wifi/rmtfs-supervised.py'
                        ':/proxy/rmtfs-supervised.py\n', 1)


def bind_kernel_version(text, release):
    marker = '[Unit]\n'
    if text.count(marker) != 1 or re.search(r'^ConditionKernelVersion=', text, re.M):
        raise ValueError('Unexpected kernel condition in candidate unit template')
    return text.replace(marker, marker + 'ConditionKernelVersion=' + release + '\n', 1)


def bind_early_cooling(text):
    marker = '[Unit]\n'
    if text.count(marker) != 1 or 'Requires=picasso-thermal-policy.service\n' in text:
        raise ValueError('Unexpected early cooling dependency layout')
    return text.replace(marker, marker + 'Requires=picasso-thermal-policy.service\n'
                        'After=picasso-thermal-policy.service\n', 1)


def bind_screen_cooldown(text):
    guard = "        require(below_temperature_limit(temperatures(),STARTUP_LIMIT_MC),'Start below 65C')\n"
    ready = "        data['console']=console.console_info()\n"
    if text.count(guard) != 1 or text.count(ready) != 1:
        raise ValueError('Unexpected screen pre-arming layout')
    return text.replace(guard, '', 1).replace(
        ready, ready + "        load('startup_cooling',Path("
        "'/opt/picasso-kernel-7.3.1/picasso-startup/wait-for-cool.py')).wait_for_cool()\n"
        + guard, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wifi-config', type=Path, required=True)
    parser.add_argument('--cn-policy', type=Path, required=True)
    parser.add_argument('--raw-policy', type=Path, required=True)
    parser.add_argument('--cn-reference', type=Path, required=True)
    parser.add_argument('--router-policy', type=Path)
    parser.add_argument('--router-reference', type=Path)
    args = parser.parse_args()
    profile = select_profile(ROOT)
    if profile.version != '7.3.1':
        raise SystemExit('Explicit KERNEL_VERSION=7.3.1 required')
    os.umask(0o077)
    out = profile.output
    release = (out / 'kbuild/include/config/kernel.release').read_text().strip()
    extras = json.loads((out / 'extra-modules/manifest.json').read_text())
    if extras['kernel_release'] != release or not extras['baseline_modules_unchanged']:
        raise ValueError('Matching isolated external-module receipt required')
    build = {'kernel_release': release, 'config_sha256': digest(out / 'kernel.config'),
             'fdt_sha256': digest(out / 'picasso.dtb'),
             'boot_image_sha256': digest(out / 'boot-picasso.img')}
    original_config = json.loads(args.wifi_config.read_text())
    cn_policy = json.loads(args.cn_policy.read_text())
    raw_policy = json.loads(args.raw_policy.read_text())
    reference = args.cn_reference.read_bytes()
    reference_sha = hashlib.sha256(reference).hexdigest()
    if (cn_policy['country'] != 'CN' or raw_policy['country'] != 'CN'
            or cn_policy['reference_sha256'] != reference_sha
            or raw_policy['CN_reference_sha256'] != reference_sha):
        raise ValueError('Historical CN policy/reference binding differs; review before porting')
    if (args.router_policy is None) != (args.router_reference is None):
        raise ValueError('Router policy and isolated signed-kernel reference must be supplied together')
    router_policy = None
    if args.router_policy is not None:
        router_policy = json.loads(args.router_policy.read_text())
        router_reference = args.router_reference.read_text()
        spec = importlib.util.spec_from_file_location('reviewed_router_country', ROOT / 'tools/wifi-router-country.py')
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        helper.validate_policy(router_policy, router_reference)
        if router_policy.get('reference_sha256') != hashlib.sha256(router_reference.encode()).hexdigest():
            raise ValueError('Router reference provenance binding differs')
        regdb = router_policy.get('regdb_sha256', {})
        if (not isinstance(regdb, dict)
                or set(regdb) != {'/usr/lib/firmware/regulatory.db', '/usr/lib/firmware/regulatory.db.p7s'}
                or any(not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None
                       for value in regdb.values())):
            raise ValueError('Reviewed signed regulatory database hashes required')
    bindings = (
        ('wifi-radio-service.py', 'wifi-auto-service.py', 'SOURCE_SHA'),
        ('wifi-cn-radio-service.py', 'wifi-radio-service.py', 'RADIO_SHA'),
        ('wifi-cn-raw-radio-service.py', 'wifi-cn-radio-service.py', 'R1_SHA'),
        ('wifi-autoconnect-cn-service.py', 'wifi-cn-raw-radio-service.py', 'SOURCE_SHA'),
        ('screen-service.py', 'screen-console.py', 'CONSOLE_SHA'),
        ('screen-service.py', 'screen-volume-policy.py', 'POLICY_SHA'),
        ('power-button-daemon.py', 'power-hold-policy.py', 'POLICY_SHA'),
    )
    for parent, child, key in bindings:
        if constants(ROOT / 'tools' / parent)[key] != digest(ROOT / 'tools' / child):
            raise ValueError('Pinned source changed; review before adapting: ' + parent)
    output = out / 'runtime-bundle'
    output.mkdir(mode=0o700)
    tree = output / 'rootfs'
    prefix = Path('/opt/picasso-kernel-7.3.1')
    private = tree / str(prefix).lstrip('/')
    private.mkdir(parents=True)

    def write(path, data):
        target = tree / str(path).lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.encode() if isinstance(data, str) else data)
        target.chmod(0o400)
        return target

    def write_json(path, value):
        return write(path, json.dumps(value, indent=2, ensure_ascii=True) + '\n')

    pins = {}
    screen = constants(ROOT / 'tools/screen-service.py')
    for key in ('FDT_SHA', 'POWER_TRIAL_FDT_SHA'):
        pins[screen[key]] = build['fdt_sha256']
    pins[screen['CONFIG_SHA']] = build['config_sha256']
    pins[screen['MODULE_SHA']] = extras['artifacts']['picasso-wled-service.ko']['sha256']
    for node in ast.walk(ast.parse((ROOT / 'tools/power-button-daemon.py').read_text())):
        if (isinstance(node, ast.Compare) and isinstance(node.left, ast.Subscript)
                and isinstance(node.left.slice, ast.Constant)
                and node.left.slice.value == 'image_sha256'
                and isinstance(node.comparators[0], ast.Constant)):
            pins[node.comparators[0].value] = build['boot_image_sha256']

    def port_text(text):
        text = relocate(text, release)
        return re.sub(r'\b[0-9a-f]{64}\b', lambda match: pins.get(match[0], match[0]), text)

    def script(name, component):
        source = ROOT / 'tools' / name
        text = port_text(source.read_text())
        if name == 'rmtfs-supervised.service.in':
            text = bind_rmtfs_supervisor(text)
        if name == 'screen-service.py':
            text = bind_screen_cooldown(text)
        target = write(prefix / component / name, text)
        if name == 'rmtfs-supervised.py':
            # DynamicUser reads the bind-mounted file inside the unchanged shared jail.
            target.chmod(0o444)
        pins[digest(source)] = digest(target)
        return target

    helpers = ('rmtfs-supervised.py', 'wifi-fallback-policy.py', 'fdt.py',
               'audit-wifi-regulatory.py', 'wifi-auth-evidence.py', 'wifi-bss.py',
               'provision-wlan-mac.py')
    for name in helpers + ('wifi-service.py', 'wifi-auto-service.py'):
        script(name, 'picasso-wifi')
    for name in ('rmtfs-supervised.service.in', 'tftp-supervised.service.in'):
        script(name, 'picasso-wifi')
    script('wifi-radio-service.py', 'picasso-wifi-radio')
    script('audit-wifi-regulatory-cn.py', 'picasso-wifi-cn')
    script('wifi-cn-radio-service.py', 'picasso-wifi-cn')
    for name in ('wifi-nl80211-channels.py', 'audit-wifi-regulatory-cn-raw.py',
                 'wifi-cn-raw-radio-service.py'):
        script(name, 'picasso-wifi-cn-raw')
    if router_policy is not None:
        script('wifi-router-country.py', 'picasso-wifi-cn-raw')
        write(prefix / 'picasso-wifi-cn-raw/regulatory-router-reference.txt', router_reference)
    script('wifi-autoconnect-cn-service.py', 'picasso-wifi-autoconnect-cn')
    script('wifi-kernel-probation.py', 'picasso-wifi-autoconnect-cn')
    for name in ('screen-console.py', 'screen-volume-policy.py', 'screen-service.py'):
        script(name, 'picasso-screen')
    script('power-hold-policy.py', 'picasso-power-button')
    script('power-button-daemon.py', 'picasso-power-button')
    script('wait-for-cool.py', 'picasso-startup')
    script('thermal-policy.py', 'picasso-thermal')
    write(Path('/etc/systemd/system/picasso-thermal-policy.service'),
          (ROOT / 'tools/picasso-thermal-policy.service').read_bytes())
    write(prefix / 'kernel-candidate-activation.py',
          (ROOT / 'tools/kernel-candidate-activation.py').read_bytes())
    for name, metadata in extras['artifacts'].items():
        source = ROOT / metadata['file']
        if digest(source) != metadata['sha256']:
            raise ValueError('Changed candidate module: ' + name)
        component = 'picasso-screen' if name == 'picasso-wled-service.ko' else 'modules'
        write(prefix / component / name, source.read_bytes())
    cfg = json.loads(json.dumps(original_config))
    cfg.update(config_sha256=build['config_sha256'], fdt_sha256=build['fdt_sha256'],
               observer_module=str(prefix / 'modules/ath10k_core.ko'),
               snoc_module=str(prefix / 'modules/ath10k_snoc.ko'), probation_seconds=0,
               ipv6_auto=True)
    if router_policy is not None:
        cfg['router_country'] = router_policy['country']
    else:
        cfg.pop('router_country', None)
    baseline = out / 'modules/lib/modules' / release / 'kernel/drivers/net/wireless/ath/ath10k/ath10k_core.ko'
    cfg.update(installed_core_path='/lib/modules/' + release +
               '/kernel/drivers/net/wireless/ath/ath10k/ath10k_core.ko',
               installed_core_sha256=digest(baseline))
    shared = {}
    assets = {}
    qrtr = '/lib/modules/' + release + '/kernel/net/qrtr/qrtr.ko'
    shared[qrtr] = digest(out / 'modules' / qrtr.lstrip('/'))
    for path, sha256 in original_config['file_sha256'].items():
        if path in (original_config['observer_module'], original_config['snoc_module']):
            continue
        changed = Path(relocate(path, release))
        local = tree / str(changed).lstrip('/')
        if changed.is_relative_to(prefix):
            if not local.is_file():
                raise ValueError('Candidate dependency has no staged replacement: ' + str(changed))
            assets[str(changed)] = digest(local)
        else:
            shared[str(changed)] = sha256
    for path in (cfg['observer_module'], cfg['snoc_module'],
                 str(prefix / 'picasso-wifi/wifi-auto-service.py')):
        assets[path] = digest(tree / path.lstrip('/'))
    cfg['file_sha256'] = {**shared, **assets}
    write_json(prefix / 'picasso-wifi/config-auto.json', cfg)
    write_json(prefix / 'picasso-wifi/config-probation.json', {**cfg, 'probation_seconds': 45})
    write_json(prefix / 'picasso-wifi/config.json', cfg)
    cn_policy['auditor_sha256'] = digest(private / 'picasso-wifi-cn/audit-wifi-regulatory-cn.py')
    write_json(prefix / 'picasso-wifi-cn/policy.json', cn_policy)
    write(prefix / 'picasso-wifi-cn/regulatory-CN-reference.txt', reference)
    raw_policy['file_sha256'] = {
        name: digest(private / 'picasso-wifi-cn-raw' / name)
        for name in ('wifi-nl80211-channels.py', 'audit-wifi-regulatory-cn-raw.py')
    }
    if router_policy is not None:
        raw_policy['router_country_policy'] = router_policy
        raw_policy['file_sha256'].update({
            name: digest(private / 'picasso-wifi-cn-raw' / name)
            for name in ('wifi-router-country.py', 'regulatory-router-reference.txt')
        })
        shared.update(router_policy['regdb_sha256'])
    else:
        raw_policy.pop('router_country_policy', None)
    write_json(prefix / 'picasso-wifi-cn-raw/policy.json', raw_policy)
    controller = private / 'picasso-wifi-autoconnect-cn/wifi-autoconnect-cn-service.py'
    controller_tree = ast.parse(controller.read_text())
    historical_request = next(node.comparators[0].value for node in ast.walk(controller_tree)
                              if isinstance(node, ast.Compare) and isinstance(node.left, ast.Call)
                              and isinstance(node.left.func, ast.Attribute)
                              and node.left.func.attr == 'get' and node.left.args
                              and isinstance(node.left.args[0], ast.Constant)
                              and node.left.args[0].value == 'user_request')
    names = ast.literal_eval(next(node.value for node in ast.parse(
        (ROOT / 'tools/wifi-auto-service.py').read_text()).body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == 'NAMES'))
    write_json(prefix / 'picasso-wifi-autoconnect-cn/policy.json',
               {'user_request': historical_request, 'country': 'CN', 'targets': list(names),
                'service_sha256': digest(controller),
                'historical_policy_not_candidate_activation_consent': True})
    unit_dir = Path('/etc/systemd/system')
    units = [('screen', 'picasso-screen.service', 'screen'),
             ('power-button', 'picasso-power-button.service', 'power'),
             ('wifi-autoconnect-cn', 'picasso-wifi-autoconnect-cn.service', 'wifi')]
    for name, original, feature in units:
        body = bind_kernel_version(port_text((ROOT / 'tools' / original).read_text()), release)
        body = body.replace('[Service]\n', '[Service]\nExecCondition=/usr/bin/python3 -I ' +
                            str(prefix / 'kernel-candidate-activation.py') + ' --feature ' + feature + '\n', 1)
        body = re.sub(r'^(RuntimeDirectory|StateDirectory)=(picasso-(?:screen|power-button|wifi))$',
                      r'\1=\2-7.3.1', body, flags=re.M)
        if feature in ('screen', 'wifi'):
            body = bind_early_cooling(body)
        if feature == 'screen':
            body = body.replace('TimeoutStartSec=30s', 'TimeoutStartSec=330s')
        write(unit_dir / ('picasso-' + name + '-7.3.1.service'), body)
        if feature == 'wifi':
            probation = body.replace('--feature wifi\n', '--feature wifi_probation\n')
            probation = probation.replace('wifi-autoconnect-cn-service.py', 'wifi-kernel-probation.py')
            probation = '\n'.join(line for line in probation.splitlines()
                                  if not line.startswith('ConditionPathExists=/var/lib/picasso-wifi/auto-enable-')) + '\n'
            write(unit_dir / 'picasso-wifi-probation-7.3.1.service', probation)
    example = {**build, 'runtime_manifest_sha256': '<generated-after-manifest>',
               **{'allow_' + feature: False for feature in ('screen', 'wifi', 'wifi_probation', 'power')}}
    files = {'/' + str(path.relative_to(tree)): digest(path)
             for path in sorted(tree.rglob('*')) if path.is_file()}
    shared[cfg['installed_core_path']] = cfg['installed_core_sha256']
    manifest = {'status': 'offline_only_no_hardware_acceptance_or_activation_authorization',
                'build': build, 'files': files, 'shared_files': shared,
                'baseline_modules_file': str((out / 'modules').relative_to(ROOT)),
                'private_nv_lifecycle_and_credentials_shared_unchanged': True,
                'new_native_probation_proof_required': True}
    path = write_json(prefix / 'runtime-manifest.json', manifest)
    example['runtime_manifest_sha256'] = digest(path)
    write_json(prefix / 'activation.example.json', example)
    write_json(prefix / 'picasso-power-button/authorization.example.json',
               {'accepts_usb_autostart': False, 'allow_boot_only': False,
                'enable_long_hold_service': False, 'image_sha256': build['boot_image_sha256']})
    for path in tree.rglob('*.py'):
        compile(path.read_text(), str(path), 'exec')
    print('Private versioned runtime staged; no activation/probation proof, installation or service enablement')


if __name__ == '__main__':
    main()
