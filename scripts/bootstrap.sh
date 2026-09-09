#!/bin/sh
set -eu
UV="$(command -v uv || true)"
if [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ]; then UV="$HOME/.local/bin/uv"; fi
if [ -z "$UV" ]; then
  if [ "$READ_ONLY" = 1 ]; then echo 'uv missing; run install.sh first.' >&2; exit 1; fi
  download="$(mktemp)"
  if command -v curl >/dev/null 2>&1; then curl -LsSf https://astral.sh/uv/install.sh -o "$download";
  else wget -q https://astral.sh/uv/install.sh -O "$download"; fi
  UV_NO_MODIFY_PATH=1 sh "$download"
  rm -f "$download"
  UV="$HOME/.local/bin/uv"
fi
if [ "$READ_ONLY" = 0 ]; then "$UV" python install 3.13; fi
SJOERD_PYTHON="$("$UV" python find --no-python-downloads 3.13)"
SJOERD_UV="$UV"
export SJOERD_UV SJOERD_PYTHON
