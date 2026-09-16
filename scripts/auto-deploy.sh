#!/usr/bin/env bash
# Verify, then deploy to Railway if the CLI is linked. Runs the real checks
# first — it does not claim a check passed unless that check actually ran
# and passed.
#
# Railway normally deploys itself: once this repo is connected to a Railway
# project, every push to `master` redeploys automatically from the
# Dockerfile (see railway.json). This script exists for a manual/local
# redeploy — e.g. to push a change without waiting on git, or to redeploy
# after only an env var changed.
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

if ! command -v railway > /dev/null 2>&1; then
  echo "railway CLI not installed — skipping manual deploy. Railway's own" \
       "GitHub integration will still redeploy master automatically."
  exit 0
fi

echo "Deploying to Railway..."
railway up --detach
echo "Deploy complete."
