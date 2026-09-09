from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PortabilityTests(unittest.TestCase):
    def test_tracked_export_has_no_secrets_or_personal_home_paths(self):
        paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
        patterns = [r'gh[pousr]_[A-Za-z0-9]{30,}', r'AKIA[A-Z0-9]{16}',
                    r'sk-[A-Za-z0-9]{32,}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                    r'[A-Za-z]:[/\\]Users[/\\][A-Za-z0-9_-]+[/\\]',
                    r'/Users/[A-Za-z0-9_-]+/', r'/home/[A-Za-z0-9_-]+/']
        for name in filter(None, paths):
            path = ROOT / name
            if not path.is_file(): continue
            text = path.read_text(encoding='utf-8')
            for pattern in patterns:
                self.assertIsNone(re.search(pattern, text), f'Export hygiene failure in {name}')

    def test_single_canonical_personal_design(self):
        designs = list((ROOT / 'skills').rglob('DESIGN.md'))
        self.assertEqual(designs, [ROOT / 'skills/design/DESIGN.md'])
        self.assertFalse(list((ROOT / 'adapters').rglob('DESIGN.md')))

    def test_posix_launchers_have_executable_git_mode(self):
        records = subprocess.check_output(['git', 'ls-files', '--stage', 'scripts/*.sh'], cwd=ROOT).decode().splitlines()
        self.assertTrue(records)
        self.assertTrue(all(line.startswith('100755 ') for line in records))

if __name__ == '__main__': unittest.main()
