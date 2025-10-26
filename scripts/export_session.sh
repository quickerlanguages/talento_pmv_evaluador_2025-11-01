#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
ZIP="$ROOT/data/exports/sessions_$TS.zip"
cd "$ROOT"
zip -r "$ZIP" data/sessions >/dev/null
echo "→ $ZIP"
