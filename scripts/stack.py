#!/usr/bin/env python3
"""Portable stack manager. Standard library only; adapters own client syntax."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
import urllib.request
import zipfile

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
TOOLS = json.loads((ROOT / 'config/tools.json').read_text(encoding='utf-8'))
WIN = os.name == 'nt'
MODULES = ['design', 'motion', 'frontend-quality', 'engineering-quality', 'task-planning', 'browser-qa']
LEGACY = ['sjoerd-design', 'ui-ux-pro-max', 'agent-browser', 'vercel-react-best-practices', 'vercel-composition-patterns', 'vercel-optimize']

def digest(data):
    return hashlib.sha256(data).hexdigest()

def block_digest(text):
    return digest(text.replace('\r\n', '\n').encode())

def tree_hash(path):
    return {str(p.relative_to(path)).replace('\\', '/'): digest(p.read_bytes())
            for p in sorted(path.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}

def adapter(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'adapters' / name / 'adapter.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class Context:
    def __init__(self, home=None, state=None):
        self.home = Path(home or Path.home()).resolve()
        self.state = Path(state or os.environ.get('SJOERD_STACK_HOME', self.home / '.local/share/sjoerd-agent-stack')).resolve()
        self.manifest = self.state / 'manifest.json'
        self.data = self.json_read(self.manifest) or {'schema': 1, 'blocks': {}, 'json': {}, 'hooks': {}, 'skills': {}, 'agents': [], 'versions': {}}
        self.warnings = []
        self.failures = []
        self.stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        self.bins = [self.state / 'bin', self.state / 'npm' / ('' if WIN else 'bin'),
                     self.state / 'node' / ('' if WIN else 'bin'), Path(sys.executable).parent, self.home / '.local/bin']
        self.env = dict(os.environ)
        entries = [*map(str, self.bins), *os.environ.get('PATH', '').split(os.pathsep)]
        seen = set()
        unique = []
        for entry in entries:
            key = os.path.normcase(os.path.normpath(entry))
            if entry and key not in seen:
                unique.append(entry); seen.add(key)
        self.env['PATH'] = os.pathsep.join(unique)
        self.env['UV_TOOL_DIR'] = str(self.state / 'uv-tools')
        self.env['UV_TOOL_BIN_DIR'] = str(self.state / 'bin')
        self.env['PYTHONUTF8'] = '1'
        self.env['PYTHONDONTWRITEBYTECODE'] = '1'

    def read(self, path):
        return path.read_bytes().decode('utf-8-sig') if path.exists() else ''

    def json_read(self, path):
        return json.loads(self.read(path)) if path.exists() and path.stat().st_size else {}

    def save(self):
        self.state.mkdir(parents=True, exist_ok=True)
        self.data['version'] = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        tmp = self.manifest.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.data, indent=2) + '\n', encoding='utf-8')
        tmp.replace(self.manifest)

    def backup(self, path):
        if path.exists() or path.is_symlink():
            dest = self.state / 'backups' / self.stamp / (datetime.now(timezone.utc).strftime('%H%M%S%f') + '-' + digest(str(path).encode())[:12] + '-' + path.name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path.is_symlink(): dest.with_suffix('.link.json').write_text(json.dumps({'target': str(path.readlink())}), encoding='utf-8')
            elif path.is_dir(): shutil.copytree(path, dest, symlinks=True)
            else: shutil.copy2(path, dest)
            print('Backup:', path, '->', dest)

    def write(self, path, text):
        data = text.encode('utf-8')
        if path.exists() and path.read_bytes() == data: return
        self.backup(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + '.sjoerd-tmp')
        if tmp.exists(): raise RuntimeError(f'Pending write exists: {tmp}')
        tmp.write_bytes(data)
        tmp.replace(path)

    def warn(self, text):
        self.warnings.append(text)
        print('WARN:', text)

    def check(self, text, ok):
        print(('OK: ' if ok else 'FAIL: ') + text)
        if not ok: self.failures.append(text)

    def executable(self, name):
        special = os.environ.get('SJOERD_' + name.upper())
        value = special or shutil.which(name, path=self.env['PATH'])
        if not value: raise RuntimeError(f'Missing executable: {name}')
        return Path(value)

    def run(self, args, cwd=None, capture=False, timeout=600, env=None):
        args = list(map(str, args))
        args[0] = str(self.executable(args[0])) if not Path(args[0]).is_absolute() else args[0]
        # npm .cmd is invoked through its JS entrypoint, avoiding cmd shell quoting.
        if WIN and Path(args[0]).name.lower() in ('npm.cmd', 'npx.cmd', 'uipro.cmd', 'vercel.cmd', 'agent-browser.cmd'):
            names = {'npm.cmd': 'node_modules/npm/bin/npm-cli.js', 'npx.cmd': 'node_modules/npm/bin/npx-cli.js',
                     'uipro.cmd': 'node_modules/ui-ux-pro-max-cli/dist/index.js',
                     'vercel.cmd': 'node_modules/vercel/dist/vc.js',
                     'agent-browser.cmd': 'node_modules/agent-browser/bin/agent-browser.js'}
            script = Path(args[0]).parent / names[Path(args[0]).name.lower()]
            if script.is_file(): args = [str(self.executable('node')), str(script), *args[1:]]
        result = subprocess.run(args, cwd=cwd, env=self.env if env is None else env, text=True, encoding='utf-8', errors='replace',
                                capture_output=capture, timeout=timeout)
        if result.returncode:
            raise RuntimeError(f'Command failed ({result.returncode}): {Path(args[0]).name} ' + ' '.join(args[1:3]) +
                               ('\n' + (result.stderr or result.stdout)[-4000:] if capture else ''))
        return result.stdout.strip() if capture else ''

    def markers(self, key, prefix):
        if prefix == '#': return f'# BEGIN sjoerd-agent-stack:{key}', f'# END sjoerd-agent-stack:{key}'
        return f'<!-- BEGIN sjoerd-agent-stack:{key} -->', f'<!-- END sjoerd-agent-stack:{key} -->'

    def block_span(self, text, key, prefix):
        begin, end = self.markers(key, prefix)
        if text.count(begin) != text.count(end) or text.count(begin) > 1:
            raise RuntimeError(f'Malformed/duplicate managed markers: {key}')
        if begin not in text: return None
        start = text.index(begin)
        stop = text.index(end, start) + len(end)
        if text[stop:stop+2] == '\r\n': stop += 2
        elif text[stop:stop+1] == '\n': stop += 1
        return start, stop

    def has_block(self, path, key):
        return self.block_span(self.read(path), key, '#') is not None

    def block(self, path, key, body, prefix='<!--'):
        text = self.read(path)
        span = self.block_span(text, key, prefix)
        record_key = str(path) + '::' + key
        previous = self.data['blocks'].get(record_key)
        begin, end = self.markers(key, prefix)
        new = begin + '\n' + body.rstrip() + '\n' + end + '\n'
        if span:
            existing = text[span[0]:span[1]]
            if existing != new and (not previous or block_digest(existing) != previous['hash']):
                raise RuntimeError(f'Conflict: locally edited managed block in {path}')
            result = text[:span[0]] + new + text[span[1]:]
        else:
            result = text + ('\n' if text and not text.endswith('\n') else '') + new
        self.write(path, result)
        self.data['blocks'][record_key] = {'path': str(path), 'key': key, 'prefix': prefix, 'hash': block_digest(new)}
        self.save()

    def json_value(self, path, keys, value):
        data = self.json_read(path)
        current = data
        for key in keys[:-1]: current = current.setdefault(key, {})
        ident = str(path) + '::' + '.'.join(keys)
        old = self.data['json'].get(ident)
        if keys[-1] in current and (not old or current[keys[-1]] != old['value']):
            raise RuntimeError(f'Unmanaged or locally edited JSON value: {path} {keys}')
        current[keys[-1]] = value
        self.write(path, json.dumps(data, indent=2) + '\n')
        self.data['json'][ident] = {'path': str(path), 'keys': keys, 'value': value}
        self.save()

    def hooks(self, path, client, specs):
        if not specs and not self.data['hooks'].get(str(path)): return
        data = self.json_read(path)
        hookset = data.setdefault('hooks', {})
        ident = str(path)
        old = self.data['hooks'].get(ident, [])
        for record in old:
            if record['group'] not in hookset.get(record['event'], []):
                raise RuntimeError(f'Locally edited/missing hook: {path} {record["event"]}')
        for record in old: hookset[record['event']].remove(record['group'])
        records = []
        executable = str(self.executable('serena-hooks')).replace('\\', '/') if specs else ''
        for event, (matcher, action) in specs.items():
            command = '"' + executable + '" ' + action + ' --client=' + client
            group = {'hooks': [{'type': 'command', 'command': command, 'timeout': 3 if event == 'SessionEnd' else 10}]}
            if matcher is not None: group['matcher'] = matcher
            # Preserve pre-existing equivalent hooks without claiming ownership.
            existing = hookset.setdefault(event, [])
            if any(any(f'serena-hooks' in h.get('command', '') and f' {action} ' in h.get('command', '')
                       for h in g.get('hooks', [])) for g in existing):
                self.warn(f'Existing {event} Serena hook preserved in {path}')
                continue
            existing.append(group)
            records.append({'event': event, 'group': group})
        self.write(path, json.dumps(data, indent=2) + '\n')
        self.data['hooks'][ident] = records
        self.save()

    def skill(self, source, dest, personal=False):
        ident = str(dest)
        old = self.data['skills'].get(ident)
        if dest.exists() or dest.is_symlink():
            if not old: raise RuntimeError(f'Unmanaged skill exists: {dest}')
            if dest.is_symlink():
                if str(dest.readlink()) != old.get('link'): raise RuntimeError(f'Changed symlink: {dest}')
                if dest.resolve() == source.resolve(): return
            elif tree_hash(dest) != old['hashes']:
                raise RuntimeError(f'Locally edited skill: {dest}. Move edits to source or resolve before updating.')
            elif tree_hash(dest) == tree_hash(source): return
            self.backup(dest)
            if dest.is_symlink(): dest.unlink()
            else:
                # Only exact manifest-owned trees reach this branch.
                shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        link = None
        if personal:
            try:
                dest.symlink_to(source.resolve(), target_is_directory=True)
                link = str(source.resolve())
            except OSError: pass
        if not link: shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        self.data['skills'][ident] = {'hashes': tree_hash(source), 'link': link, 'personal': personal}
        self.save()

def download(url, dest):
    with urllib.request.urlopen(url, timeout=90) as response, dest.open('wb') as out:
        shutil.copyfileobj(response, out)

def install_node(ctx, update):
    try:
        version = ctx.run(['node', '--version'], capture=True)
        ctx.run(['npm', '--version'], capture=True)
        if int(version.lstrip('v').split('.')[0]) >= TOOLS['nodeMinimum'] and not (update and (ctx.state / 'node').exists()): return
    except RuntimeError: pass
    system = {'Windows': 'win', 'Darwin': 'darwin', 'Linux': 'linux'}[platform.system()]
    arch = {'amd64': 'x64', 'x86_64': 'x64', 'arm64': 'arm64', 'aarch64': 'arm64'}.get(platform.machine().lower())
    if not arch: raise RuntimeError('Unsupported Node CPU architecture: ' + platform.machine())
    releases = json.load(urllib.request.urlopen('https://nodejs.org/dist/index.json', timeout=60))
    artifact = f'{system}-{arch}' + ('-zip' if WIN else '')
    release = next(r for r in releases if r['lts'] and artifact in r['files'])
    version = release['version']
    filename = f'node-{version}-{system}-{arch}' + ('.zip' if WIN else '.tar.gz')
    base = f'https://nodejs.org/dist/{version}/'
    checksums = urllib.request.urlopen(base + 'SHASUMS256.txt', timeout=60).read().decode()
    checksum = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1] == filename)
    with tempfile.TemporaryDirectory(prefix='sjoerd-node-') as temp:
        temp = Path(temp)
        archive = temp / filename
        download(base + filename, archive)
        if digest(archive.read_bytes()) != checksum: raise RuntimeError('Node download checksum mismatch')
        if WIN:
            with zipfile.ZipFile(archive) as z: z.extractall(temp / 'unpacked')
        else:
            with tarfile.open(archive) as t: t.extractall(temp / 'unpacked', filter='data')
        source = next((temp / 'unpacked').iterdir())
        dest = ctx.state / 'node'
        if dest.exists():
            ctx.backup(dest)
            shutil.rmtree(dest) # fixed package-private runtime directory
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, dest)
    print('Installed private Node LTS', version)

def dependencies(ctx, update):
    ctx.executable('git') # no system package-manager escalation; prerequisite for git clone.
    install_node(ctx, update)
    for package in TOOLS['npm']:
        if package == 'vercel' and not ctx.data.get('options', {}).get('vercel'): continue
        installed = ctx.state / 'npm' / ('' if WIN else 'lib') / 'node_modules' / package / 'package.json'
        if update or not installed.exists():
            ctx.run(['npm', 'install', '--global', '--prefix', ctx.state / 'npm', package + '@latest', '--no-fund', '--no-audit'])
        ctx.data['versions'][package] = json.loads(installed.read_text(encoding='utf-8'))['version']
    try: ctx.executable('serena')
    except RuntimeError:
        ctx.run(['uv', 'tool', 'install', '-p', TOOLS['python'], TOOLS['serena']])
    else:
        if update and (ctx.state / 'uv-tools/serena-agent').exists():
            ctx.run(['uv', 'tool', 'upgrade', 'serena-agent'])
    ctx.run(['serena', '--help'], capture=True)
    # Browser download is idempotent; no Linux root package installation.
    ctx.run(['agent-browser', 'install'])
    ctx.data['versions']['node'] = ctx.run(['node', '--version'], capture=True)
    ctx.data['versions']['npm'] = ctx.run(['npm', '--version'], capture=True)
    ctx.data['versions']['python'] = platform.python_version()
    ctx.data['versions']['uv'] = ctx.run(['uv', '--version'], capture=True)
    ctx.data['versions']['serena'] = ctx.run(['uv', 'tool', 'list'], capture=True).splitlines()[0]
    ctx.save()

def headroom_executable(ctx):
    return ctx.state / 'headroom/bin' / ('headroom.exe' if WIN else 'headroom')


def install_headroom(ctx, update=False, skip_dependencies=False):
    if not ctx.data.get('options', {}).get('headroom'):
        return
    tool = headroom_executable(ctx)
    version = TOOLS['headroom']['version']
    env = {**ctx.env, 'UV_TOOL_DIR': str(ctx.state / 'headroom/tools'),
           'UV_TOOL_BIN_DIR': str(tool.parent)}
    if not skip_dependencies and (update or not tool.is_file() or
                                  ctx.data['versions'].get('headroom') != version):
        requirement = TOOLS['headroom']['package'] + '==' + version
        # Separate tool environment and bin directory: never replace a user's Headroom.
        command = ['uv', 'tool', 'install', '--python', TOOLS['python'], requirement]
        if update: command.append('--upgrade')
        ctx.run(command, env=env)
    if not tool.is_file():
        raise RuntimeError('Headroom runtime missing; reinstall with --with-headroom without --skip-dependencies.')
    actual = ctx.run([tool, '--version'], capture=True, env=env)
    if not re.search(r'\b' + re.escape(version) + r'\s*$', actual):
        raise RuntimeError('Unexpected Headroom version: ' + actual)
    ctx.data['versions']['headroom'] = version
    ctx.save()

def sources(ctx, update=False):
    store = ctx.state / 'sources'
    store.mkdir(parents=True, exist_ok=True)
    dest = store / 'ui-ux-pro-max'
    if update or not dest.exists():
        previous = ctx.data.get('sourceHashes', {}).get('ui-ux-pro-max')
        if previous and tree_hash(dest) != previous:
            raise RuntimeError('Edited UI knowledge source; resolve before updating')
        with tempfile.TemporaryDirectory(prefix='sjoerd-uipro-') as temp:
            ctx.run(['uipro', 'init', '--ai', 'universal'], cwd=temp)
            src = Path(temp) / '.agents/skills/ui-ux-pro-max'
            if not (src / 'scripts/search.py').exists(): raise RuntimeError('UI Pro output format changed')
            if dest.exists():
                ctx.backup(dest)
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
    ctx.data.setdefault('sourceHashes', {})['ui-ux-pro-max'] = tree_hash(dest)
    dest = store / 'vercel'
    if not dest.exists(): ctx.run(['git', 'clone', '--depth', '1', TOOLS['skillSources']['vercel'], dest])
    elif update:
        if ctx.run(['git', 'status', '--porcelain'], cwd=dest, capture=True):
            raise RuntimeError(f'Edited upstream source checkout: {dest}')
        ctx.run(['git', 'pull', '--ff-only'], cwd=dest)
    ctx.data['versions']['vercel-skills-commit'] = ctx.run(['git', 'rev-parse', 'HEAD'], cwd=dest, capture=True)
    ctx.save()


def migrate(ctx, skills, desired):
    # Preflight every retirement before removing any directory.
    retiring = []
    for name in LEGACY:
        path = skills / name
        if name in desired or not (path.exists() or path.is_symlink()): continue
        old = ctx.data['skills'].get(str(path))
        if not old: raise RuntimeError(f'Unmanaged legacy skill: {path}')
        valid = str(path.readlink()) == old.get('link') if path.is_symlink() else tree_hash(path) == old['hashes']
        if not valid: raise RuntimeError(f'Locally edited legacy skill: {path}')
        retiring.append(path)
    for path in retiring:
        ctx.backup(path)
        if path.is_symlink(): path.unlink()
        else: shutil.rmtree(path)
        del ctx.data['skills'][str(path)]
        ctx.save()


def install_modules(ctx, destination):
    desired = MODULES + (['vercel-optimize'] if ctx.data.get('options', {}).get('vercel') else [])
    # Check new destinations before migration so name collisions cannot retire v1.
    for name in desired:
        path = destination / name
        if (path.exists() or path.is_symlink()) and str(path) not in ctx.data['skills']:
            raise RuntimeError(f'Unmanaged skill exists: {path}')
    migrate(ctx, destination, desired)
    with tempfile.TemporaryDirectory(prefix='stack-modules-') as temp:
        for name in MODULES:
            source = Path(temp) / name
            shutil.copytree(ROOT / 'skills' / name, source)
            if name == 'design':
                shutil.copy2(ROOT / 'scripts/lookup.py', source / 'lookup.py')
                (source / 'runtime.json').write_text(json.dumps({'search': str(ctx.state / 'sources/ui-ux-pro-max/scripts/search.py')}), encoding='utf-8')
            ctx.skill(source, destination / name)
    if 'vercel-optimize' in desired:
        ctx.skill(ctx.state / 'sources/vercel/skills/vercel-optimize', destination / 'vercel-optimize')


def install_reference_cli(ctx):
    runner = ctx.state / 'bin/stack-reference.py'
    headroom_runner = ctx.state / 'bin/headroom_runner.py'
    if headroom_runner.exists() and str(headroom_runner) not in ctx.data.get('files', {}):
        raise RuntimeError(f'Unmanaged helper already exists: {headroom_runner}')
    for ident, expected in ctx.data.get('files', {}).items():
        path = Path(ident)
        if path.exists() and digest(path.read_bytes()) != expected:
            raise RuntimeError(f'Edited managed helper: {path}')
    ctx.write(runner, (ROOT / 'scripts/reference.py').read_text(encoding='utf-8'))
    if WIN:
        launcher = ctx.state / 'bin/agent-stack.cmd'
        body = '@echo off\n"' + sys.executable + '" "' + str(runner) + '" %*\n'
    else:
        launcher = ctx.state / 'bin/agent-stack'
        body = '#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' ' + shlex.quote(str(runner)) + ' "$@"\n'
    ctx.write(launcher, body)
    if not WIN: launcher.chmod(0o755)
    ctx.write(headroom_runner, (ROOT / 'scripts/headroom_runner.py').read_text(encoding='utf-8'))
    ctx.data.setdefault('files', {}).update({str(p): digest(p.read_bytes()) for p in (runner, launcher, headroom_runner)})
    ctx.save()


def expose_path(ctx):
    if WIN:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try: old, kind = winreg.QueryValueEx(key, 'Path')
            except FileNotFoundError: old, kind = '', winreg.REG_EXPAND_SZ
            entries = old.split(';') if old else []
            added = [str(p) for p in ctx.bins if str(p).lower() not in [e.lower().rstrip('\\') for e in entries]]
            if added:
                backup = ctx.state / 'backups' / ctx.stamp / 'user-path.json'
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_text(json.dumps({'value': old, 'kind': kind}), encoding='utf-8')
                winreg.SetValueEx(key, 'Path', 0, kind, ';'.join(entries + added))
                ctx.data.setdefault('pathEntries', []).extend(added)
                broadcast_environment()
    else:
        value = ':'.join(shlex.quote(str(p)) for p in ctx.bins)
        body = 'export PATH=' + value + ':"$PATH"'
        # Login + interactive shells (idempotent PATH duplication is avoided by env.sh).
        envfile = ctx.state / 'env.sh'
        envbody = '\n'.join('case ":$PATH:" in *:' + shlex.quote(str(p)) + ':*) ;; *) PATH=' + shlex.quote(str(p)) + ':"$PATH" ;; esac' for p in ctx.bins) + '\nexport PATH\n'
        ctx.block(envfile, 'path', envbody, '#')
        shell = Path(os.environ.get('SHELL', '/bin/sh')).name
        profiles = [ctx.home / '.profile']
        if shell == 'zsh': profiles.append(ctx.home / '.zshrc')
        elif shell == 'bash':
            profiles.append(ctx.home / '.bashrc')
            if (ctx.home / '.bash_profile').exists(): profiles.append(ctx.home / '.bash_profile')
        for profile in profiles: ctx.block(profile, 'path', '. ' + shlex.quote(str(envfile)), '#')
    ctx.save()

def broadcast_environment():
    if WIN:
        import ctypes
        # Let Explorer pick up the updated user PATH; no visible helper process.
        result = ctypes.c_size_t()
        ctypes.windll.user32.SendMessageTimeoutW(65535, 26, 0, 'Environment', 2, 5000, ctypes.byref(result))

def doctor(ctx):
    print('Agent stack', (ROOT / 'VERSION').read_text(encoding='utf-8').strip(), platform.system(), platform.machine())
    if not ctx.data['agents']: ctx.check('At least one installed adapter', False)
    for name in ctx.data['agents']:
        mod = adapter(name)
        ctx.check(name + ' detected', shutil.which(mod.CLI, path=ctx.env['PATH']) is not None)
        paths = mod.paths(ctx.home)
        for skill in MODULES + (['vercel-optimize'] if ctx.data.get('options', {}).get('vercel') else []):
            path = paths['skills'] / skill
            ctx.check(name + ': ' + skill + ' available', (path / 'SKILL.md').is_file())
            record = ctx.data['skills'].get(str(path))
            if record and not path.is_symlink() and tree_hash(path) != record['hashes']:
                ctx.warn('Locally modified skill: ' + str(path))
        ctx.check(name + ': orchestration active', 'BEGIN sjoerd-agent-stack:workflow' in ctx.read(paths['instructions']))
        mod.validate(ctx)
        hooks = ctx.json_read(paths['hooks']).get('hooks', {})
        records = ctx.data['hooks'].get(str(paths['hooks']), [])
        ctx.check(name + ': optional Serena hooks', (bool(records) if ctx.data.get('options', {}).get('serenaHooks') else not records) and all(r['group'] in hooks.get(r['event'], []) for r in records))
    for name in ['node', 'npm', 'uv', 'serena', 'serena-hooks', 'agent-browser', 'uipro']:
        try: ctx.check(name + ' executable available', ctx.executable(name).is_file())
        except RuntimeError: ctx.check(name + ' executable available', False)
    ctx.check('Shared design search available', (ctx.state / 'sources/ui-ux-pro-max/scripts/search.py').is_file())
    ctx.check('React reference library available', (ctx.state / 'sources/vercel/skills/react-best-practices/rules').is_dir())
    ctx.check('Composition reference library available', (ctx.state / 'sources/vercel/skills/composition-patterns/rules').is_dir())
    for ident, expected in ctx.data.get('files', {}).items():
        path = Path(ident)
        ctx.check('Managed helper intact: ' + path.name, path.is_file() and digest(path.read_bytes()) == expected)
    if ctx.data.get('options', {}).get('vercel'):
        try: ctx.check('Optional Vercel CLI available', ctx.executable('vercel').is_file())
        except RuntimeError: ctx.check('Optional Vercel CLI available', False)
    for key, record in ctx.data['blocks'].items():
        text = ctx.read(Path(record['path']))
        span = ctx.block_span(text, record['key'], record['prefix'])
        ctx.check('Managed block intact: ' + record['key'], span is not None and block_digest(text[span[0]:span[1]]) == record['hash'])
    if ctx.data.get('options', {}).get('headroom'):
        tool = headroom_executable(ctx)
        ctx.check('Optional Headroom private runtime available', tool.is_file())
        if tool.is_file():
            try:
                version = ctx.run([tool, '--version'], capture=True)
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                version = ''
            ctx.check('Headroom matches reviewed version', bool(re.search(
                r'\b' + re.escape(TOOLS['headroom']['version']) + r'\s*$', version)))
        print('Headroom is session-only: agent-stack headroom claude or agent-stack headroom codex.')
        print('Authenticated routing and savings require a live session; doctor does not start one.')
    print('Recorded versions:', json.dumps(ctx.data['versions'], indent=2))
    print('Restart clients after changes. Optional hook trust and authenticated behavior require a fresh session.')
    return 1 if ctx.failures else 0

def uninstall(ctx):
    for ident, expected in list(ctx.data.get('files', {}).items()):
        path = Path(ident)
        if path.exists() and digest(path.read_bytes()) == expected:
            ctx.backup(path); path.unlink(); del ctx.data['files'][ident]
        elif path.exists(): ctx.warn('Preserved edited helper: ' + ident)
    for ident, record in list(ctx.data['skills'].items()):
        path = Path(ident)
        if not path.exists() and not path.is_symlink(): del ctx.data['skills'][ident]; continue
        if path.is_symlink() and str(path.readlink()) == record['link']:
            ctx.backup(path); path.unlink()
        elif not path.is_symlink() and tree_hash(path) == record['hashes']:
            ctx.backup(path); shutil.rmtree(path)
        else: ctx.warn('Preserved changed skill: ' + str(path)); continue
        del ctx.data['skills'][ident]
        ctx.save()
    for ident, record in list(ctx.data['blocks'].items()):
        path = Path(record['path']); text = ctx.read(path)
        span = ctx.block_span(text, record['key'], record['prefix'])
        if span and block_digest(text[span[0]:span[1]]) == record['hash']:
            ctx.write(path, text[:span[0]] + text[span[1]:])
            del ctx.data['blocks'][ident]
        elif span: ctx.warn('Preserved edited block: ' + str(path))
        else: del ctx.data['blocks'][ident]
        ctx.save()
    for ident, records in list(ctx.data['hooks'].items()):
        path = Path(ident); data = ctx.json_read(path); remaining = []
        for record in records:
            groups = data.get('hooks', {}).get(record['event'], [])
            if record['group'] in groups: groups.remove(record['group'])
            else: remaining.append(record); ctx.warn('Preserved changed hook: ' + ident)
        if path.exists(): ctx.write(path, json.dumps(data, indent=2) + '\n')
        if remaining: ctx.data['hooks'][ident] = remaining
        else: del ctx.data['hooks'][ident]
        ctx.save()
    for ident, record in list(ctx.data['json'].items()):
        path = Path(record['path']); data = ctx.json_read(path); current = data
        for key in record['keys'][:-1]: current = current.get(key, {})
        if current.get(record['keys'][-1]) == record['value']:
            del current[record['keys'][-1]]
            ctx.write(path, json.dumps(data, indent=2) + '\n')
            del ctx.data['json'][ident]
        else: ctx.warn('Preserved changed config value: ' + ident)
        ctx.save()
    if WIN and ctx.data.get('pathEntries'):
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            value, kind = winreg.QueryValueEx(key, 'Path')
            backup = ctx.state / 'backups' / ctx.stamp / 'user-path-uninstall.json'
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(json.dumps({'value': value, 'kind': kind}))
            winreg.SetValueEx(key, 'Path', 0, kind, ';'.join(v for v in value.split(';') if v not in ctx.data['pathEntries']))
            broadcast_environment()
        ctx.data['pathEntries'] = []
    ctx.data['agents'] = []
    ctx.data.setdefault('options', {})['headroom'] = False
    ctx.save()
    print('Removed unchanged owned integrations. Retained runtimes, caches, backups and edited files. No backups restored.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['install', 'doctor', 'uninstall'])
    parser.add_argument('--agent', choices=['auto', 'codex', 'claude-code'], default='auto')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--skip-dependencies', action='store_true')
    parser.add_argument('--serena-hooks', action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument('--with-vercel', action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument('--with-headroom', action=argparse.BooleanOptionalAction, default=None)
    args = parser.parse_args()
    ctx = Context()
    if args.command == 'doctor': return doctor(ctx)
    if args.command == 'uninstall': uninstall(ctx); return 0
    agents = ['codex', 'claude-code'] if args.all else ([args.agent] if args.agent != 'auto' else
              [a for a in ['codex', 'claude-code'] if shutil.which(adapter(a).CLI, path=ctx.env['PATH'])])
    if not agents: raise RuntimeError('No supported agent detected. Install a client, or select --agent explicitly to prepare its config.')
    print('Target:', platform.system(), platform.machine(), 'agents:', ', '.join(agents))
    for name in agents: print(name, {k: str(v) for k, v in adapter(name).paths(ctx.home).items()})
    if args.dry_run:
        enabled = args.with_headroom if args.with_headroom is not None else ctx.data.get('options', {}).get('headroom', False)
        print('Headroom:', ('opt-in, pinned ' + TOOLS['headroom']['version']) if enabled else 'disabled',
              '(session launcher only; no persistent agent configuration)')
        print('Read-only plan: bootstrap missing tools, stage upstream skills, merge owned config, validate. State:', ctx.state)
        for name in agents:
            mod = adapter(name); p = mod.paths(ctx.home)
            print('Existing configuration:', p['config'].exists(), 'instructions:', p['instructions'].exists())
        return 0
    ctx.state.mkdir(parents=True, exist_ok=True)
    lock = ctx.state / 'install.lock'
    try: handle = lock.open('x')
    except FileExistsError: raise RuntimeError(f'Another install may be running. Inspect before removing stale lock: {lock}')
    try:
        handle.write(str(os.getpid())); handle.close()
        options = ctx.data.setdefault('options', {'serenaHooks': False, 'vercel': False})
        if args.serena_hooks is not None: options['serenaHooks'] = args.serena_hooks
        if args.with_vercel is not None: options['vercel'] = args.with_vercel
        if args.with_headroom is not None: options['headroom'] = args.with_headroom
        if not args.skip_dependencies: dependencies(ctx, args.update)
        install_headroom(ctx, args.update, args.skip_dependencies)
        sources(ctx, args.update)
        install_reference_cli(ctx)
        for name in agents:
            mod = adapter(name)
            p = mod.paths(ctx.home)
            mod.configure(ctx)
            ctx.block(p['instructions'], 'workflow', (ROOT / 'instructions/GLOBAL.md').read_text(encoding='utf-8') + '\n' +
                      (ROOT / 'adapters' / name / 'orchestration.md').read_text(encoding='utf-8'))
            install_modules(ctx, p['skills'])
            if name not in ctx.data['agents']: ctx.data['agents'].append(name)
            ctx.save()
        expose_path(ctx)
        history = ctx.state / 'history' / (ctx.stamp + '.json')
        history.parent.mkdir(parents=True, exist_ok=True)
        history.write_text(json.dumps({'version': ctx.data['version'], 'agents': agents,
                                      'versions': ctx.data['versions']}, indent=2), encoding='utf-8')
        return doctor(ctx)
    finally:
        lock.unlink(missing_ok=True)

if __name__ == '__main__':
    try: sys.exit(main())
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
