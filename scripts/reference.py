"""List bounded reference pointers, without loading whole skills into context."""
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['reference'])
    parser.add_argument('topic', choices=['react', 'composition', 'optimize'])
    parser.add_argument('terms', nargs='*')
    args = parser.parse_args()
    state = Path(__file__).resolve().parents[1]
    if args.topic == 'optimize':
        config = json.loads((state / 'manifest.json').read_text(encoding='utf-8'))
        if not config.get('options', {}).get('vercel'):
            parser.error('Vercel Optimize is optional: install with --with-vercel.')
    folder = {'react': 'react-best-practices', 'composition': 'composition-patterns', 'optimize': 'vercel-optimize'}[args.topic]
    base = state / 'sources/vercel/skills' / folder
    candidates = sorted((base / 'rules').glob('*.md')) if args.topic != 'optimize' else [base / 'SKILL.md']
    terms = [term.lower() for term in args.terms]
    matches = [p for p in candidates if all(term in p.name.lower() or term in p.read_text(encoding='utf-8').lower() for term in terms)]
    for path in matches[:8]: print(path)
    if not matches: print('No matching references; broaden one search term.')
    elif len(matches) > 8: print('More matches available; narrow the query.')

if __name__ == '__main__': main()
