#!/usr/bin/env bash
set -euo pipefail

PATTERN='\.bak(_|\.|$)|\.BAK(\.|_|$)|\.db\.BAK\.|(^|/)\.zip$'

if git diff --cached --name-only | egrep -i "$PATTERN" >/dev/null; then
  echo "❌ Pre-commit: hay ficheros prohibidos staged:"
  git diff --cached --name-only | egrep -i "$PATTERN" | sed 's/^/   ⚠ /'
  echo "Arregla con: make clean-bak (y quita del stage)"
  exit 1
fi
