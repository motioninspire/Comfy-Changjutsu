#!/usr/bin/env bash
# Usage: ./install.sh /path/to/ComfyUI [--with-bernini] [--skip-models]
set -euo pipefail
COMFY="${1:?usage: install.sh /path/to/ComfyUI [--with-bernini] [--skip-models]}"; shift || true
PY="${PYTHON:-}"
# prefer the venv ComfyUI itself uses
for cand in "$COMFY/venv/bin/python" "$COMFY/.venv/bin/python" "$COMFY/../python_embeded/python"; do
  [[ -z "$PY" && -x "$cand" ]] && PY="$cand"
done
PY="${PY:-python3}"
echo "Using python: $PY"
exec "$PY" "$(dirname "$0")/install.py" --comfy "$COMFY" "$@"
