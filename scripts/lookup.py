"""Thin entry point; database remains in the machine's shared package state."""
import json
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    runtime = json.loads(Path(__file__).with_name('runtime.json').read_text(encoding='utf-8'))
    sys.exit(subprocess.call([sys.executable, runtime['search'], *sys.argv[1:]]))
