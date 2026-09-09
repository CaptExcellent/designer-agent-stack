#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
READ_ONLY=1
. "$SCRIPT_DIR/bootstrap.sh"
exec "$SJOERD_PYTHON" "$SCRIPT_DIR/stack.py" doctor "$@"
