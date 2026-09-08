#!/usr/bin/env bash
# Deploy to Fly.io. Runs the real checks first — it does not claim
# a check passed unless that check actually ran and passed.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Running README and asset checks..."
bash scripts/check-readme.sh

if compgen -G "app/*.py" > /dev/null; then
  echo "Syntax checking app/*.py..."
  python3 -m py_compile app/*.py
else
  echo "No app/*.py — skipping syntax check."
fi

if compgen -G "tests/test_*.py" > /dev/null || compgen -G "test_*.py" > /dev/null; then
  echo "Running tests..."
  pytest -q
else
  echo "No tests — skipping pytest."
fi

if [ ! -f fly.toml ]; then
  echo "No fly.toml — nothing to deploy."
  exit 0
fi

if ! command -v fly > /dev/null 2>&1; then
  echo "fly CLI not installed — skipping deploy." >&2
  exit 0
fi

echo "Deploying to Fly.io..."
fly deploy --remote-only --yes
echo "Deploy complete."
