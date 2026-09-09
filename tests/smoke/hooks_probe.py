"""Exercise official hook commands with synthetic payloads in private temp state."""
import argparse
import json
import os
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--executable', required=True)
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='sjoerd-hook-test-') as state:
    env = dict(os.environ, SERENA_HOME=state, PYTHONUTF8='1')
    for client in ['codex', 'claude-code']:
        payload = {'session_id': 'stack-synthetic-' + client, 'cwd': state,
                   'tool_name': 'Bash', 'tool_input': {'command': 'echo check'}}
        for action in ['activate', 'remind', 'cleanup']:
            proc = subprocess.run([args.executable, action, '--client=' + client],
                input=json.dumps(payload), text=True, encoding='utf-8', capture_output=True, env=env, timeout=10)
            assert proc.returncode == 0, proc.stderr
            if proc.stdout.strip(): json.loads(proc.stdout)
            print(json.dumps({'client': client, 'hook': action, 'ok': True}))
