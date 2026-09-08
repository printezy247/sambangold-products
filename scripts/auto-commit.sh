#!/bin/bash
# Auto-commit script for printezy-9-products
# Usage: bash scripts/auto-commit.sh "message"
MSG="${1:-auto: updates}"
cd "$(dirname "$0")/.."
git add -A
git commit -m "$MSG" || echo "No changes to commit."
