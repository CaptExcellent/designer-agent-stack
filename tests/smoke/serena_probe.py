"""Run with Serena's uv tool Python (it already contains the MCP SDK)."""
import argparse
import asyncio
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--executable', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--context', choices=['codex', 'claude-code'], default='codex')
    args = parser.parse_args()
    params = StdioServerParameters(command=args.executable, args=[
        'start-mcp-server', '--context=' + args.context, '--project-from-cwd',
        '--open-web-dashboard', 'false', '--enable-gui-log-window', 'false'],
        cwd=args.project, env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listing = await session.list_tools()
            names = {tool.name for tool in listing.tools}
            assert 'get_symbols_overview' in names
            calls = [('initial_instructions', {}),
                     ('get_symbols_overview', {'relative_path': 'scripts/stack.py', 'depth': 0})]
            if 'activate_project' in names: calls.insert(0, ('activate_project', {'project': args.project}))
            else: print(json.dumps({'context': args.context, 'activation': 'single-project startup from cwd'}))
            for name, arguments in calls:
                result = await session.call_tool(name, arguments)
                assert not result.isError, str(result)
                payload = ' '.join(c.text for c in result.content if hasattr(c, 'text'))
                if name == 'get_symbols_overview':
                    assert 'Context' in payload and 'main' in payload, payload
                print(json.dumps({'context': args.context, 'tool': name, 'ok': True}))

asyncio.run(main())
