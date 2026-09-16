import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from test_management import stack, ROOT

spec = importlib.util.spec_from_file_location('headroom_runner', ROOT / 'scripts/headroom_runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class HeadroomTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='headroom-test-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.ctx = stack.Context(self.home, self.home / 'state')
        self.tool = stack.headroom_executable(self.ctx)
        self.env = {'PATH': str(self.home / 'bin'), 'KEEP': 'unchanged'}
        self.url = 'http://127.0.0.1:8788'
        self.which = patch.object(runner.shutil, 'which', return_value='/client')
        self.which.start()
        self.addCleanup(self.which.stop)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def plan(self, client, extra=()):
        return runner.client_plan(client, list(extra), self.tool, self.url,
                                  self.env, self.home, self.home / 'project')

    def test_opt_in_private_pin_and_disabled_no_install(self):
        self.ctx.run = Mock(return_value='headroom, version 0.37.0')
        stack.install_headroom(self.ctx)
        self.ctx.run.assert_not_called()
        self.ctx.data['options'] = {'headroom': True}
        self.write(self.tool, 'placeholder')
        stack.install_headroom(self.ctx)
        command = self.ctx.run.call_args_list[0]
        self.assertIn('headroom-ai[proxy]==0.37.0', command.args[0])
        self.assertEqual(command.kwargs['env']['UV_TOOL_DIR'], str(self.ctx.state / 'headroom/tools'))
        self.assertEqual(self.ctx.json_read(self.ctx.manifest)['options']['headroom'], True)
        self.ctx.run.reset_mock()
        stack.install_headroom(self.ctx)
        self.assertEqual(self.ctx.run.call_count, 1)  # version check only
        self.ctx.data['options']['headroom'] = False
        stack.uninstall(self.ctx)
        self.assertTrue(self.tool.exists())
        self.assertFalse(self.ctx.json_read(self.ctx.manifest)['options']['headroom'])

    def test_missing_and_wrong_runtime_fail(self):
        self.ctx.data['options'] = {'headroom': True}
        with self.assertRaisesRegex(RuntimeError, 'runtime missing'):
            stack.install_headroom(self.ctx, skip_dependencies=True)
        self.write(self.tool, '')
        self.ctx.run = Mock(return_value='headroom, version 0.38.0')
        with self.assertRaisesRegex(RuntimeError, 'Unexpected Headroom version'):
            stack.install_headroom(self.ctx, skip_dependencies=True)

    def test_claude_session_is_additive_and_preserves_settings(self):
        path = self.home / '.claude/settings.json'
        original = json.dumps({'env': {'ENABLE_TOOL_SEARCH': 'false'},
                               'model': 'existing', 'permissions': {'allow': ['Read']},
                               'hooks': {'Stop': [{'hooks': [{'command': 'serena hook cleanup'}]}]}})
        self.write(path, original)
        self.write(self.home / '.claude.json', '{"mcpServers":{"serena":{"command":"keep"}}}')
        command, env, provider = self.plan('claude', ['-p', 'Review the design'])
        settings = json.loads(command[command.index('--settings') + 1])
        self.assertEqual(settings['env']['ANTHROPIC_BASE_URL'], self.url)
        self.assertEqual(settings['env']['ENABLE_TOOL_SEARCH'], 'false')
        servers = json.loads(command[command.index('--mcp-config') + 1])['mcpServers']
        self.assertEqual(servers[runner.SERVER]['env']['HEADROOM_PROXY_URL'], self.url)
        self.assertEqual(servers[runner.SERVER]['args'], ['mcp', 'serve'])
        self.assertNotIn('--strict-mcp-config', command)
        self.assertEqual(env['KEEP'], 'unchanged')
        self.assertIsNone(provider)
        self.assertEqual(path.read_text(), original)
        self.assertNotIn('ANTHROPIC_BASE_URL', self.env)

    def test_codex_preserves_provider_model_and_existing_mcp(self):
        path = self.home / '.codex/config.toml'
        original = 'model="existing"\n[mcp_servers.serena]\ncommand="keep"\n'
        self.write(path, original)
        command, env, provider = self.plan('codex')
        self.assertIn('openai_base_url="' + self.url + '/v1"', command)
        self.assertFalse(any('model_provider=' in arg for arg in command))
        self.assertFalse(any(arg.startswith('model=') for arg in command))
        self.assertEqual(env['OPENAI_BASE_URL'], self.url + '/v1')
        self.assertEqual(path.read_text(), original)
        self.assertIsNone(provider)

    def test_custom_routing_and_profiles_rejected(self):
        for key, client in [('ANTHROPIC_BASE_URL', 'claude'), ('OPENAI_BASE_URL', 'codex')]:
            with self.subTest(key=key):
                self.env[key] = 'http://127.0.0.1:9999'
                with self.assertRaisesRegex(RuntimeError, 'another endpoint'):
                    self.plan(client)
                del self.env[key]
        path = self.home / 'project/.codex/config.toml'
        for text in ['profile="work"', 'model_provider="azure"']:
            self.write(path, text)
            with self.assertRaisesRegex(RuntimeError, 'without a profile'):
                self.plan('codex')
        self.write(self.home / 'project/.claude/settings.local.json',
                   '{"env":{"CLAUDE_CODE_USE_BEDROCK":"1", "AWS_REGION":"eu-west-1", "AWS_PROFILE":"team"}}')
        command, env, provider = self.plan('claude')
        session = json.loads(command[command.index('--settings') + 1])['env']
        self.assertEqual(session['CLAUDE_CODE_USE_BEDROCK'], '0')
        self.assertEqual(session['ANTHROPIC_API_KEY'], 'headroom')
        self.assertEqual(provider, ('bedrock', 'eu-west-1', 'team'))

    def test_conflicting_hooks_and_reserved_mcp_rejected(self):
        path = self.home / '.claude/settings.json'
        self.write(path, '{"hooks":{"PreToolUse":[{"hooks":[{"command":"/tools/rtk-rewrite.sh"}]}]}}')
        with self.assertRaisesRegex(RuntimeError, 'compression setup'):
            self.plan('claude')
        path.unlink()
        self.write(self.home / '.claude.json', json.dumps({'mcpServers': {runner.SERVER: {}}}))
        with self.assertRaisesRegex(RuntimeError, 'already in use'):
            self.plan('claude')

    def test_routing_flags_rejected_but_prompt_remains_opaque(self):
        for client, args in [('claude', ['--settings={}']), ('codex', ['-cfoo=bar']),
                             ('codex', ['--profile', 'work'])]:
            with self.subTest(client=client, args=args):
                with self.assertRaisesRegex(RuntimeError, 'not supported'):
                    self.plan(client, args)
        command, _, _ = self.plan('codex', ['--', '--profile is a topic'])
        self.assertEqual(command[-1], '--profile is a topic')

    def test_dry_run_writes_nothing_and_disabled_fails(self):
        self.write(self.tool, '')
        self.ctx.data['options'] = {'headroom': True}
        self.ctx.save()
        before = stack.tree_hash(self.ctx.state)
        with contextlib.redirect_stdout(io.StringIO()), patch.object(runner, 'run_session') as launch, \
             patch.dict(os.environ, self.env, clear=True), \
             patch.object(runner.Path, 'home', return_value=self.home), \
             patch.object(runner.Path, 'cwd', return_value=self.home):
            self.assertEqual(runner.main(['--dry-run', 'claude'], self.ctx.state), 0)
            launch.assert_not_called()
        self.assertEqual(before, stack.tree_hash(self.ctx.state))
        self.ctx.data['options']['headroom'] = False
        self.ctx.save()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(['--dry-run', 'claude'], self.ctx.state), 1)

    def test_helper_ownership_update_and_uninstall(self):
        helper = self.ctx.state / 'bin/headroom_runner.py'
        self.write(helper, 'unmanaged')
        with self.assertRaisesRegex(RuntimeError, 'Unmanaged helper'):
            stack.install_reference_cli(self.ctx)
        helper.unlink()
        stack.install_reference_cli(self.ctx)
        stack.install_reference_cli(self.ctx)
        stack.uninstall(self.ctx)
        self.assertFalse(helper.exists())

    def test_proxy_cleanup_on_startup_failure(self):
        workspace = self.home / 'session'
        proxy = Mock()
        proxy.poll.return_value = None
        with patch.object(runner.socket, 'socket'), patch.object(runner.subprocess, 'Popen', return_value=proxy), \
             patch.object(runner, 'wait_ready', side_effect=RuntimeError('failed')):
            with self.assertRaisesRegex(RuntimeError, 'failed'):
                runner.run_session(['proxy'], ['client'], {'CLIENT': '1'}, {'PROXY': '1'}, workspace, self.url, 8788)
        proxy.terminate.assert_called_once()
        self.assertFalse((workspace / 'session.lock').exists())

    def test_client_exit_code_cleanup_and_separate_proxy_environment(self):
        workspace = self.home / 'session'
        proxy, client = Mock(), Mock()
        proxy.poll.return_value = None
        client.poll.return_value = 7
        client.returncode = 7
        with patch.object(runner.socket, 'socket'), patch.object(runner, 'wait_ready'), \
             patch.object(runner.subprocess, 'Popen', side_effect=[proxy, client]) as spawn:
            self.assertEqual(runner.run_session(['proxy'], ['client'], {'ROUTING': 'local'},
                                              {'PROXY': 'upstream'}, workspace, self.url, 8788), 7)
        self.assertEqual(spawn.call_args_list[0].kwargs['env'], {'PROXY': 'upstream'})
        proxy.terminate.assert_called_once()
        self.assertFalse((workspace / 'session.lock').exists())

    def test_occupied_port_and_existing_lock_do_not_launch_or_remove_foreign_lock(self):
        workspace = self.home / 'session'
        with patch.object(runner.socket, 'socket') as socket_mock, patch.object(runner.subprocess, 'Popen') as spawn:
            socket_mock.return_value.__enter__.return_value.bind.side_effect = OSError('in use')
            with self.assertRaisesRegex(RuntimeError, 'occupied'):
                runner.run_session([], [], {}, {}, workspace, self.url, 8788)
            spawn.assert_not_called()
        self.assertFalse((workspace / 'session.lock').exists())
        self.write(workspace / 'session.lock', '123')
        with self.assertRaisesRegex(RuntimeError, 'Session lock exists'):
            runner.run_session([], [], {}, {}, workspace, self.url, 8788)
        self.assertEqual((workspace / 'session.lock').read_text(), '123')

    def test_stop_kills_only_owned_process_on_timeout(self):
        process = Mock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired('proxy', 10), 0]
        runner.stop(process)
        process.kill.assert_called_once()


if __name__ == '__main__':
    unittest.main()
