import json
import os
import re
import tomllib
from pathlib import Path

NAME = 'codex'
CLI = 'codex'

def paths(home):
    root = Path(os.environ.get('CODEX_HOME', home / '.codex'))
    return {'skills': home / '.agents/skills', 'instructions': root / 'AGENTS.md',
            'config': root / 'config.toml', 'hooks': root / 'hooks.json'}

def configure(ctx):
    p = paths(ctx.home)
    original = ctx.read(p['config'])
    parsed = tomllib.loads(original)
    if 'serena' in parsed.get('mcp_servers', {}) and not ctx.has_block(p['config'], 'serena'):
        raise RuntimeError('Existing unmanaged Serena MCP config; preserve it and resolve the name conflict before install.')
    args = [
        'start-mcp-server', '--project-from-cwd', '--context=codex',
        '--enable-web-dashboard=false', '--open-web-dashboard=false',
        '--enable-gui-log-window=false',
    ]
    body = '[mcp_servers.serena]\ncommand = ' + json.dumps(str(ctx.executable('serena'))) + '\n'
    body += 'args = ' + json.dumps(args) + '\nstartup_timeout_sec = 60\n'
    body += '\n[mcp_servers.serena.env]\nPATH = ' + json.dumps(ctx.env['PATH']) + '\n'
    ctx.block(p['config'], 'serena', body, '#')
    if not ctx.data.get('options', {}).get('serenaHooks'):
        ctx.hooks(p['hooks'], NAME, {})
        return
    # Current Codex enables hooks by default. Never override an explicit disable.
    if parsed.get('features', {}).get('hooks', parsed.get('features', {}).get('codex_hooks', True)) is False:
        ctx.warn('Codex hooks explicitly disabled; preserved. Enable features.hooks to use Serena hooks.')
    hooks = {
        'PreToolUse': ('Bash', 'remind'),
        'PostToolUse': ('^mcp__serena__.*$', 'reset'),
        'SessionStart': ('startup|resume', 'activate'),
        'SessionEnd': (None, 'cleanup'),
    }
    if not re.search(r'^\s+reset\s', ctx.run(['serena-hooks', '--help'], capture=True), re.M):
        del hooks['PostToolUse']
        ctx.warn('Released Serena lacks reset hook; omitted PostToolUse reset until supported upstream.')
    ctx.hooks(p['hooks'], NAME, hooks)
    ctx.warn('Codex: review new/changed hooks in /hooks; restart the client to load skills and MCP.')

def validate(ctx):
    p = paths(ctx.home)
    config = tomllib.loads(ctx.read(p['config']))
    server = config.get('mcp_servers', {}).get('serena', {})
    ctx.check('Codex Serena MCP configured', '--context=codex' in server.get('args', []) and Path(server.get('command', '')).is_file())
    enabled = config.get('features', {}).get('hooks', config.get('features', {}).get('codex_hooks', True))
    if ctx.data.get('options', {}).get('serenaHooks'): ctx.check('Codex hooks enabled in config (trust checked in /hooks)', enabled)
    if (p['instructions'].parent / 'AGENTS.override.md').exists():
        ctx.warn('AGENTS.override.md exists: it can shadow global AGENTS.md.')
