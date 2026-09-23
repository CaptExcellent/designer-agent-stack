import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stack', ROOT / 'scripts/stack.py')
stack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stack)

class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stack-test-')
        self.home = Path(self.temp.name)
        self.ctx = stack.Context(self.home, self.home / 'state')
        self.ctx.executable = lambda _: Path(sys.executable)
        self.ctx.run = lambda *args, **kwargs: 'Commands:\n  activate  Start\n  remind  Guide\n  reset  Reset\n  cleanup  Clean\n'
        self.env = patch.dict(os.environ, {}, clear=False)
        self.env.start()
        for key in ('CODEX_HOME', 'CLAUDE_CONFIG_DIR'): os.environ.pop(key, None)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_codex_preservation_idempotence_and_uninstall(self):
        mod = stack.adapter('codex')
        paths = mod.paths(self.home)
        original = '# Keep comment\nmodel = "existing-model"\n[features]\njs_repl = false\n[mcp_servers.other]\ncommand = "keep"\n'
        paths['config'].parent.mkdir()
        paths['config'].write_text(original)
        unrelated = {'hooks': {'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'other-hook'}]}]}}
        paths['hooks'].write_text(json.dumps(unrelated))
        mod.configure(self.ctx)
        server = tomllib.loads(paths['config'].read_text())['mcp_servers']['serena']
        self.assertIn('--open-web-dashboard=false', server['args'])
        self.assertIn('--enable-web-dashboard=false', server['args'])
        self.assertIn('--enable-gui-log-window=false', server['args'])
        first = paths['config'].read_bytes(), paths['hooks'].read_bytes()
        mod.configure(self.ctx)
        self.assertEqual(first, (paths['config'].read_bytes(), paths['hooks'].read_bytes()))
        self.assertTrue(paths['config'].read_text().startswith(original))
        # A later unrelated user edit survives uninstall.
        paths['config'].write_text(paths['config'].read_text() + '\n# added by user\n')
        stack.uninstall(self.ctx)
        self.assertEqual(paths['config'].read_text(), original + '\n# added by user\n')
        self.assertEqual(self.ctx.json_read(paths['hooks'])['hooks']['PreToolUse'], unrelated['hooks']['PreToolUse'])

    def test_claude_preserves_account_settings_hooks_and_mcp(self):
        mod = stack.adapter('claude-code'); paths = mod.paths(self.home)
        original = {'preferences': {'theme': 'dark'}, 'mcpServers': {'other': {'command': 'keep'}}}
        paths['config'].write_text(json.dumps(original))
        paths['hooks'].parent.mkdir()
        paths['hooks'].write_text(json.dumps({'permissions': {'allow': ['Read']}, 'hooks': {'Stop': []}}))
        mod.configure(self.ctx)
        server = self.ctx.json_read(paths['config'])['mcpServers']['serena']
        self.assertIn('--open-web-dashboard=false', server['args'])
        self.assertIn('--enable-web-dashboard=false', server['args'])
        self.assertIn('--enable-gui-log-window=false', server['args'])
        first = paths['config'].read_bytes(), paths['hooks'].read_bytes()
        mod.configure(self.ctx)
        self.assertEqual(first, (paths['config'].read_bytes(), paths['hooks'].read_bytes()))
        stack.uninstall(self.ctx)
        self.assertEqual(self.ctx.json_read(paths['config']), original)
        self.assertEqual(self.ctx.json_read(paths['hooks'])['permissions'], {'allow': ['Read']})

    def test_conflict_blocks_are_preserved(self):
        path = self.home / 'INSTRUCTIONS.md'
        self.ctx.block(path, 'workflow', 'original')
        path.write_text(path.read_text().replace('original', 'user edit'))
        with self.assertRaisesRegex(RuntimeError, 'Conflict'):
            self.ctx.block(path, 'workflow', 'update')
        stack.uninstall(self.ctx)
        self.assertIn('user edit', path.read_text())

    def test_skill_user_changes_and_extra_files_survive(self):
        source = self.home / 'source'; source.mkdir()
        (source / 'SKILL.md').write_text('skill')
        target = self.home / 'skills/test'
        self.ctx.skill(source, target)
        self.ctx.skill(source, target)
        (target / 'my-notes.txt').write_text('keep')
        with self.assertRaisesRegex(RuntimeError, 'Locally edited skill'):
            self.ctx.skill(source, target)
        stack.uninstall(self.ctx)
        self.assertEqual((target / 'my-notes.txt').read_text(), 'keep')

    def test_skill_updates_backed_up_and_uninstall(self):
        source = self.home / 'source'; source.mkdir()
        (source / 'SKILL.md').write_text('one')
        target = self.home / 'skills/test'
        self.ctx.skill(source, target)
        (source / 'SKILL.md').write_text('two')
        self.ctx.skill(source, target)
        self.assertEqual((target / 'SKILL.md').read_text(), 'two')
        stack.uninstall(self.ctx)
        self.assertFalse(target.exists())
        self.assertTrue(list((self.ctx.state / 'backups').rglob('SKILL.md')))

    def test_uninstall_preview_is_read_only_and_identifies_changed_items(self):
        instructions = self.home / 'INSTRUCTIONS.md'
        self.ctx.block(instructions, 'workflow', 'owned')
        source = self.home / 'source'; source.mkdir()
        (source / 'SKILL.md').write_text('skill')
        target = self.home / 'skills/test'
        self.ctx.skill(source, target)
        (target / 'notes.txt').write_text('user edit')
        config = self.home / 'settings.json'
        self.ctx.json_value(config, ['mcpServers', 'serena'], {'command': 'owned'})
        before = stack.tree_hash(self.home)
        actions = stack.uninstall_plan(self.ctx)
        self.assertEqual(before, stack.tree_hash(self.home))
        self.assertIn(('remove', 'instruction block', instructions), actions)
        self.assertIn(('preserve (changed)', 'skill', target), actions)
        self.assertIn(('remove', 'JSON setting', config), actions)

    def test_uninstall_preview_flags_malformed_markers_for_review(self):
        path = self.home / 'INSTRUCTIONS.md'
        self.ctx.block(path, 'workflow', 'owned')
        source = self.home / 'source'; source.mkdir()
        (source / 'SKILL.md').write_text('skill')
        target = self.home / 'skills/test'
        self.ctx.skill(source, target)
        path.write_text(path.read_text().replace('<!-- END sjoerd-agent-stack:workflow -->', ''))
        self.assertIn(('blocked (review needed)', 'instruction block', path), stack.uninstall_plan(self.ctx))
        before = stack.tree_hash(self.home)
        with self.assertRaisesRegex(RuntimeError, 'stopped before changes'):
            stack.uninstall(self.ctx)
        self.assertEqual(before, stack.tree_hash(self.home))
        self.assertTrue(target.exists())

    def test_unmanaged_mcp_refused(self):
        mod = stack.adapter('codex'); paths = mod.paths(self.home)
        paths['config'].parent.mkdir()
        paths['config'].write_text('[mcp_servers.serena]\ncommand="mine"\n')
        with self.assertRaisesRegex(RuntimeError, 'unmanaged Serena'):
            mod.configure(self.ctx)

    def test_backups_do_not_overwrite_each_other(self):
        path = self.home / 'test.md'; path.write_text('one')
        self.ctx.write(path, 'two'); self.ctx.write(path, 'three')
        copies = list((self.ctx.state / 'backups').rglob('*-test.md'))
        self.assertEqual({p.read_text() for p in copies}, {'one', 'two'})

    def test_claude_override_is_independent_of_codex(self):
        with patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': str(self.home / 'custom')}):
            p = stack.adapter('claude-code').paths(self.home)
            self.assertEqual(p['config'], self.home / 'custom/.claude.json')
            self.assertEqual(p['skills'], self.home / 'custom/skills')

if __name__ == '__main__': unittest.main()
