import os
from pathlib import Path

NAME = 'claude-code'
CLI = 'claude'

def paths(home):
    root = Path(os.environ.get('CLAUDE_CONFIG_DIR', home / '.claude'))
    # Claude uses .claude.json by default, or .claude.json inside an override dir.
    config = root / '.claude.json' if os.environ.get('CLAUDE_CONFIG_DIR') else home / '.claude.json'
    return {'skills': root / 'skills', 'instructions': root / 'CLAUDE.md',
            'config': config, 'hooks': root / 'settings.json'}

def configure(ctx):
    p = paths(ctx.home)
    ctx.json_value(p['config'], ['mcpServers', 'serena'], {
        'type': 'stdio', 'command': str(ctx.executable('serena')),
        'args': [
            'start-mcp-server', '--context=claude-code', '--project-from-cwd',
            '--enable-web-dashboard=false', '--open-web-dashboard=false',
            '--enable-gui-log-window=false',
        ],
        'env': {'PATH': ctx.env['PATH']}})
    if not ctx.data.get('options', {}).get('serenaHooks'):
        ctx.hooks(p['hooks'], NAME, {})
        return
    ctx.hooks(p['hooks'], NAME, {'PreToolUse': ('', 'remind'),
              'SessionStart': ('', 'activate'), 'SessionEnd': ('', 'cleanup')})

def validate(ctx):
    p = paths(ctx.home)
    server = ctx.json_read(p['config']).get('mcpServers', {}).get('serena', {})
    ctx.check('Claude Code Serena MCP configured', '--context=claude-code' in server.get('args', []) and Path(server.get('command', '')).is_file())
    if ctx.json_read(p['hooks']).get('disableAllHooks'):
        ctx.warn('Claude Code disableAllHooks is enabled; preserved.')
