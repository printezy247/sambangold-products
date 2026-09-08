#!/usr/bin/env bash
# Verify README.md renders correctly on GitHub.
# Run locally before pushing; CI runs the same script.
set -uo pipefail
cd "$(dirname "$0")/.."

fail=0
note() { printf '%s\n' "$*"; }

note "== 1. constructs GitHub strips from markdown =="
if grep -nE '<style|<script|class=|style=|<!DOCTYPE|<iframe' README.md; then
  note "FAIL: README.md contains HTML GitHub will strip."
  fail=1
else
  note "PASS: none found."
fi

note ""
note "== 2. referenced files exist =="
missing=0

# HTML src= and srcset=. srcset may hold several comma-separated candidates,
# each "<url> [descriptor]" -- take the url of every candidate.
while IFS= read -r attr; do
  value=${attr#*=\"}
  value=${value%\"}
  case $attr in
    srcset=*)
      # split candidates on comma, then take the first field of each
      printf '%s\n' "$value" | tr ',' '\n' | awk '{print $1}'
      ;;
    *)
      printf '%s\n' "$value"
      ;;
  esac
done < <(grep -oE '(src|srcset)="[^"]*"' README.md) |
  sort -u |
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    case $path in http://*|https://*|data:*|'#'*) continue ;; esac
    [ -f "$path" ] || printf 'MISSING (img): %s\n' "$path"
  done > /tmp/readme-missing-img.$$ 2>/dev/null

# Markdown image and link targets: ![alt](path) and [text](path)
grep -oE '\]\([^)#][^)]*\)' README.md |
  sed -E 's/^\]\(//; s/\)$//; s/[[:space:]]+"[^"]*"$//' |
  sort -u |
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    case $path in http://*|https://*|mailto:*|data:*|'#'*) continue ;; esac
    [ -f "$path" ] || [ -d "$path" ] || printf 'MISSING (link): %s\n' "$path"
  done > /tmp/readme-missing-link.$$ 2>/dev/null

if [ -s /tmp/readme-missing-img.$$ ] || [ -s /tmp/readme-missing-link.$$ ]; then
  cat /tmp/readme-missing-img.$$ /tmp/readme-missing-link.$$
  missing=1
  fail=1
else
  note "PASS: every referenced file resolves."
fi
rm -f /tmp/readme-missing-img.$$ /tmp/readme-missing-link.$$

note ""
note "== 3. SVG assets are well-formed XML =="
if python3 - <<'PY'
import glob, sys, xml.dom.minidom
files = sorted(glob.glob("assets/**/*.svg", recursive=True))
bad = []
for f in files:
    try:
        xml.dom.minidom.parse(f)
    except Exception as exc:
        bad.append("%s: %s" % (f, exc))
if bad:
    print("\n".join(bad))
    sys.exit(1)
print("PASS: %d SVGs valid." % len(files))
PY
then :; else fail=1; fi

note ""
note "== 4. every product spec has its required headings =="
specfail=0
for f in products/product-1[0-8].md; do
  [ -f "$f" ] || continue
  for h in "## Platform" "## Free tier" "## Problem" "## Solution" "## Monetization"; do
    grep -q "^$h" "$f" || { printf '%s missing: %s\n' "$f" "$h"; specfail=1; }
  done
done
if [ $specfail -eq 0 ]; then note "PASS: all specs complete."; else fail=1; fi

note ""
if [ $fail -eq 0 ]; then
  note "All README checks passed."
else
  note "README checks FAILED."
fi
exit $fail
