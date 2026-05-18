#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

uv sync

echo "Installed premiere-session-bootstrap dependencies in:"
echo "  $DIR/.venv"
