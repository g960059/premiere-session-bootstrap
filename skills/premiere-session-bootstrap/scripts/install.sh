#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -L "$SKILL_DIR" ]]; then
  SKILL_DIR="$(readlink "$SKILL_DIR")"
fi
REPO_ROOT="$(cd "$SKILL_DIR/../.." && pwd -P)"
exec "$REPO_ROOT/scripts/install.sh"
