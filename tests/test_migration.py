import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_management import stack


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.ctx = stack.Context(self.home, self.home / 'state')
        self.ctx.executable = lambda _: Path(sys.executable)
        self.ctx.run = lambda *a, **kw: 'Commands:\n  activate  Start\n  remind  Guide\n  cleanup  Clean\n'
        self.skills = self.home / 'skills'
        self.source = self.home / 'source'
        self.source.mkdir()
        (self.source / 'SKILL.md').write_text('original')

    def test_migration_conflict_leaves_all_legacy_skills(self):
        for name in stack.LEGACY:
            self.ctx.skill(self.source, self.skills / name)
        (self.skills / stack.LEGACY[-1] / 'notes.txt').write_text('mine')
        with self.assertRaisesRegex(RuntimeError, 'Locally edited legacy'):
            stack.migrate(self.ctx, self.skills, stack.MODULES)
        self.assertTrue(all((self.skills / n).exists() for n in stack.LEGACY))

    def test_migration_and_reinstall_preserve_unrelated_skill(self):
        self.ctx.skill(self.source, self.skills / 'sjoerd-design')
        unrelated = self.skills / 'my-skill'
        unrelated.mkdir()
        (unrelated / 'SKILL.md').write_text('mine')
        stack.install_modules(self.ctx, self.skills)
        first = stack.tree_hash(self.skills)
        stack.install_modules(self.ctx, self.skills)
        self.assertEqual(first, stack.tree_hash(self.skills))
        self.assertFalse((self.skills / 'sjoerd-design').exists())
        self.assertEqual((unrelated / 'SKILL.md').read_text(), 'mine')
        self.assertEqual(set(p.name for p in self.skills.iterdir()), set(stack.MODULES + ['my-skill']))
        self.assertTrue(list((self.ctx.state / 'backups').rglob('SKILL.md')))

    def test_disable_hooks_preserves_unrelated_hooks(self):
        path = self.home / 'hooks.json'
        other = {'hooks': [{'type': 'command', 'command': 'keep-me'}]}
        path.write_text(json.dumps({'hooks': {'SessionStart': [other]}, 'setting': True}))
        self.ctx.hooks(path, 'codex', {'SessionStart': ('startup', 'activate')})
        self.ctx.hooks(path, 'codex', {})
        self.assertEqual(self.ctx.json_read(path), {'hooks': {'SessionStart': [other]}, 'setting': True})
        self.assertEqual(self.ctx.data['hooks'][str(path)], [])

    def test_disabled_hooks_do_not_create_configuration(self):
        path = self.home / 'hooks.json'
        self.ctx.hooks(path, 'codex', {})
        self.assertFalse(path.exists())

    def test_edited_hook_is_not_removed(self):
        path = self.home / 'hooks.json'
        self.ctx.hooks(path, 'codex', {'SessionStart': ('startup', 'activate')})
        path.write_text(path.read_text().replace('activate', 'custom'))
        with self.assertRaisesRegex(RuntimeError, 'Locally edited/missing hook'):
            self.ctx.hooks(path, 'codex', {})
        self.assertIn('custom', path.read_text())

    def test_cached_sources_do_not_run_install_or_pull(self):
        ui = self.ctx.state / 'sources/ui-ux-pro-max/scripts'
        ui.mkdir(parents=True)
        (ui / 'search.py').write_text('# database search')
        (self.ctx.state / 'sources/vercel').mkdir()
        with patch.object(self.ctx, 'run', return_value='revision') as run:
            stack.sources(self.ctx)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0], ['git', 'rev-parse', 'HEAD'])

    def test_new_name_collision_does_not_retire_old_skill(self):
        self.ctx.skill(self.source, self.skills / 'sjoerd-design')
        (self.skills / 'design').mkdir()
        with self.assertRaisesRegex(RuntimeError, 'Unmanaged skill'):
            stack.install_modules(self.ctx, self.skills)
        self.assertTrue((self.skills / 'sjoerd-design').exists())

    def test_hook_opt_in_and_opt_out_for_both_adapters(self):
        with patch.dict('os.environ', {}, clear=True):
            for name in ('codex', 'claude-code'):
                mod = stack.adapter(name)
                self.ctx.data['options'] = {'serenaHooks': True}
                mod.configure(self.ctx)
                self.assertTrue(self.ctx.data['hooks'][str(mod.paths(self.home)['hooks'])])
                self.ctx.data['options']['serenaHooks'] = False
                mod.configure(self.ctx)
                self.assertFalse(self.ctx.data['hooks'][str(mod.paths(self.home)['hooks'])])
