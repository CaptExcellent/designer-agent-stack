"""Session-only Headroom routing. No upstream wrap/init or persistent client edits."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request

# Upstream compression markers refer to mcp__headroom__headroom_retrieve.
SERVER = 'headroom'


def read_config(path, toml=False):
    if not path.exists():
        return {}
    text = path.read_text(encoding='utf-8-sig')
    return tomllib.loads(text) if toml else json.loads(text)


def check_endpoint(env, key, allowed):
    if env.get(key, '').rstrip('/') not in ('', allowed):
        raise RuntimeError(f'{key} already selects another endpoint. Use that setup separately.')


def check_hooks(config):
    for groups in config.get('hooks', {}).values():
        for group in groups:
            for hook in group.get('hooks', []):
                if re.search(r'(?i)(?<![\w])(?:rtk|headroom)(?![\w])', hook.get('command', '')):
                    raise RuntimeError('An RTK or Headroom hook is configured. Use one compression setup per session.')


def enabled(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def configured_value(environments, key):
    for source in reversed(environments):
        value = source.get(key)
        if value not in (None, ''):
            return str(value)
    return None


def client_plan(client, extra, tool, url, env, home, cwd):
    """Merge session settings only; reject routing we cannot safely preserve."""
    env = dict(env)
    # Configuration flags can silently undo routing or replace existing MCP servers.
    blocked = ('--config', '--profile', '--oss', '--local-provider',
               '--settings', '--setting-sources', '--mcp-config', '--strict-mcp-config',
               '--remote', '--remote-control')
    for arg in extra:
        if arg == '--':
            break
        if arg.split('=', 1)[0] in blocked or (client == 'codex' and arg.startswith(('-c', '-p'))):
            raise RuntimeError(f'{arg.split("=", 1)[0]} is not supported by this session launcher.')
    command = shutil.which(client, path=env.get('PATH'))
    if not command:
        raise RuntimeError(f'{client} is not installed or not on PATH.')
    mcp_env = {key: value for key, value in env.items() if key.startswith('HEADROOM_')}
    mcp_env['HEADROOM_PROXY_URL'] = url
    server = {'command': str(tool), 'args': ['mcp', 'serve'], 'env': mcp_env}
    ancestors = [*reversed(cwd.parents), cwd]
    if client == 'claude':
        config_dir = Path(env.get('CLAUDE_CONFIG_DIR', home / '.claude'))
        configs = [read_config(config_dir / 'settings.json')]
        configs += [read_config(p / '.claude' / name) for p in ancestors
                    for name in ('settings.json', 'settings.local.json')]
        for config in configs:
            check_hooks(config)
        environments = [env, *(c.get('env', {}) for c in configs)]
        for config_env in environments:
            check_endpoint(config_env, 'ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
        if any(enabled(config_env.get(key)) for config_env in environments
               for key in ('CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY')):
            raise RuntimeError('This launcher does not support the configured Claude cloud provider.')
        bedrock = any(enabled(config_env.get('CLAUDE_CODE_USE_BEDROCK')) for config_env in environments)
        mcp_configs = [read_config(home / '.claude.json'), read_config(config_dir / '.claude.json')]
        mcp_configs += [read_config(p / '.mcp.json') for p in ancestors]
        for config in mcp_configs:
            scopes = [config, *config.get('projects', {}).values()]
            if any(SERVER in c.get('mcpServers', {}) for c in scopes):
                raise RuntimeError(f'MCP name {SERVER} is already in use.')
        session_env = {'ANTHROPIC_BASE_URL': url}
        proxy = None
        if bedrock:
            region = configured_value(environments, 'AWS_REGION')
            if not region:
                raise RuntimeError('Bedrock requires AWS_REGION in the existing Claude settings.')
            # Claude's Bedrock SDK bypasses ANTHROPIC_BASE_URL. Let Headroom use
            # the existing AWS credentials/profile and re-sign its Bedrock calls.
            session_env.update({'CLAUDE_CODE_USE_BEDROCK': '0', 'ANTHROPIC_API_KEY': 'headroom'})
            proxy = ('bedrock', region, configured_value(environments, 'AWS_PROFILE'))
        # Custom endpoints otherwise disable Claude's deferred tool loading.
        search = env.get('ENABLE_TOOL_SEARCH')
        for config in configs:
            search = config.get('env', {}).get('ENABLE_TOOL_SEARCH', search)
        session_env['ENABLE_TOOL_SEARCH'] = search or 'auto'
        env.update(session_env)
        return [command, '--settings', json.dumps({'env': session_env}),
                '--mcp-config', json.dumps({'mcpServers': {SERVER: server}}), *extra], env, proxy

    check_endpoint(env, 'OPENAI_BASE_URL', 'https://api.openai.com/v1')
    config_dir = Path(env.get('CODEX_HOME', home / '.codex'))
    configs = [read_config(config_dir / 'config.toml', toml=True)]
    configs += [read_config(p / '.codex/config.toml', toml=True) for p in ancestors]
    for path in [config_dir / 'hooks.json', *(p / '.codex/hooks.json' for p in ancestors)]:
        check_hooks(read_config(path))
    for config in configs:
        if config.get('model_provider', 'openai') != 'openai' or config.get('profile'):
            raise RuntimeError('This launcher supports Codex built-in OpenAI without a profile only.')
        check_endpoint(config, 'openai_base_url', 'https://api.openai.com/v1')
        if config.get('model_providers', {}).get('openai'):
            raise RuntimeError('Custom overrides of the OpenAI provider require a separate setup.')
        if SERVER in config.get('mcp_servers', {}):
            raise RuntimeError(f'MCP name {SERVER} is already in use.')
    env['OPENAI_BASE_URL'] = url + '/v1'
    overrides = ['openai_base_url=' + json.dumps(env['OPENAI_BASE_URL']),
                 f'mcp_servers.{SERVER}.command=' + json.dumps(str(tool)),
                 f'mcp_servers.{SERVER}.args=["mcp", "serve"]']
    overrides += [f'mcp_servers.{SERVER}.env.{key}=' + json.dumps(value)
                  for key, value in mcp_env.items()]
    args = [item for override in overrides for item in ('-c', override)]
    return [command, *args, *extra], env, None


def wait_ready(process, url, timeout=120):
    # Local health checks must never use an inherited HTTP proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('Headroom exited before becoming ready; inspect proxy.log.')
        try:
            with opener.open(url + '/health', timeout=1) as response:
                if response.status == 200 and process.poll() is None:
                    health = json.load(response)
                    if health.get('service') == 'headroom-proxy' and health.get('ready') is True:
                        return health
        except (OSError, urllib.error.URLError, ValueError):
            pass
        time.sleep(0.25)
    raise RuntimeError('Headroom startup timed out; inspect proxy.log and retry after model downloads finish.')


def stop(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def run_session(proxy_args, command, env, proxy_env, workspace, url, port):
    workspace.mkdir(parents=True, exist_ok=True)
    lock = workspace / 'session.lock'
    try:
        handle = lock.open('x')
    except FileExistsError:
        raise RuntimeError(f'Session lock exists: {lock}. Check the recorded process before removing a stale lock.')
    proxy = None
    try:
        with handle:
            handle.write(str(os.getpid()))
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', port))
            except OSError:
                raise RuntimeError(f'Port {port} is occupied. Existing services are never reused or stopped.')
        log_path = workspace / 'proxy.log'
        with log_path.open('w', encoding='utf-8') as log:
            print('Starting Headroom; first use may download compression models. Log:', log_path, flush=True)
            proxy = subprocess.Popen(proxy_args, env=proxy_env, stdout=log, stderr=subprocess.STDOUT)
            health = wait_ready(proxy, url)
            if health.get('checks', {}).get('kompress', {}).get('ready') is False:
                print('Headroom reports its optional Kompress model is not ready; compression may be limited.', flush=True)
            print('Headroom ready at', url, '— cache mode, retrieval enabled.', flush=True)
            client = subprocess.Popen(command, env=env)
            try:
                while client.poll() is None:
                    if proxy.poll() is not None:
                        raise RuntimeError('Headroom stopped unexpectedly; the client session has been stopped.')
                    time.sleep(0.25)
                return client.returncode
            finally:
                stop(client)
    finally:
        stop(proxy)
        lock.unlink(missing_ok=True)


def main(argv=None, state=None):
    parser = argparse.ArgumentParser(prog='agent-stack headroom')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--port', type=int, default=8788)
    parser.add_argument('client', choices=['claude', 'codex'])
    parser.add_argument('client_args', nargs=argparse.REMAINDER, help='Client arguments after --')
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be between 1024 and 65535.')
    state = Path(state) if state else Path(__file__).resolve().parents[1]
    try:
        manifest = read_config(state / 'manifest.json')
        if not manifest.get('options', {}).get('headroom'):
            raise RuntimeError('Headroom is disabled. Install the stack with --with-headroom first.')
        tool = state / 'headroom/bin' / ('headroom.exe' if os.name == 'nt' else 'headroom')
        if not tool.is_file():
            raise RuntimeError('Headroom runtime missing. Reinstall with --with-headroom.')
        workspace = state / 'headroom' / f'session-{args.port}'
        # Do not inherit another installation's optimization, routing, or memory settings.
        env = {k: v for k, v in os.environ.items() if not k.startswith('HEADROOM_')}
        env.update(HEADROOM_WORKSPACE_DIR=str(workspace), HEADROOM_CONFIG_DIR=str(workspace / 'config'),
                   HEADROOM_OUTPUT_SHAPER='0')
        url = f'http://127.0.0.1:{args.port}'
        extra = args.client_args[1:] if args.client_args[:1] == ['--'] else args.client_args
        command, client_env, provider = client_plan(args.client, extra, tool, url, env, Path.home(), Path.cwd())
        proxy_args = [str(tool), 'proxy', '--host', '127.0.0.1', '--port', str(args.port),
                      '--mode', 'cache', '--no-cache', '--no-rate-limit']
        if provider:
            _, region, profile = provider
            proxy_args += ['--backend', 'bedrock', '--region', region]
            if profile:
                proxy_args += ['--bedrock-profile', profile]
        if args.dry_run:
            print(f'Headroom {manifest.get("versions", {}).get("headroom", "unknown")} -> {args.client} at {url}')
            mode = 'Bedrock via your existing AWS profile' if provider else 'direct provider routing'
            print(f'Cache-preserving compression; semantic response cache off; retrieval MCP enabled; {mode}.')
            print('Session arguments only. No client files, hooks, provider identity, or account settings changed.')
            return 0
        return run_session(proxy_args, command, client_env, env, workspace, url, args.port)
    except KeyboardInterrupt:
        return 130
    except (RuntimeError, OSError, ValueError) as exc:
        print('Headroom:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
