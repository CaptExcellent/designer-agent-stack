#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
READ_ONLY=0
for arg in "$@"; do if [ "$arg" = --dry-run ]; then READ_ONLY=1; fi; done
. "$SCRIPT_DIR/bootstrap.sh"
exec "$SJOERD_PYTHON" "$SCRIPT_DIR/stack.py" install "$@"
