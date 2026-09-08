#!/usr/bin/env bash
# Commit and push the current work.
# Usage: bash scripts/auto-commit.sh "feat: message"
#
# Opening the pull request is NOT done here — do that from the GitHub UI
# or your agent session after this script pushes the branch.
set -euo pipefail
cd "$(dirname "$0")/.."

MSG="${1:-chore: auto update}"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [ "$BRANCH" = "master" ] || [ "$BRANCH" = "main" ]; then
  echo "Refusing to auto-commit on $BRANCH. Switch to a feature branch first." >&2
  exit 1
fi

# Verify before committing — never push work that fails its own checks.
if [ -x scripts/check-readme.sh ]; then
  bash scripts/check-readme.sh
fi

git add -A
if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

git commit -m "$MSG"

for delay in 0 2 4 8 16; do
  [ "$delay" -eq 0 ] || { echo "Push failed, retrying in ${delay}s..."; sleep "$delay"; }
  if git push -u origin "$BRANCH"; then
    echo "Pushed $BRANCH."
    exit 0
  fi
done

echo "Push failed after retries." >&2
exit 1
