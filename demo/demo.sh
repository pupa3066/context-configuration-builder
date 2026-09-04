#!/bin/sh
# demo.sh — clean-room walkthrough of context-config-builder.
# Installs into a throwaway KIRO_HOME, adds/removes a project, shows structure.
# Safe: never touches your real ~/.kiro. Basis for the demo GIF.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP=$(mktemp -d)
export KIRO_HOME="$TMP/.kiro"

echo "==> 1. Install (non-destructive) into a fresh home"
sh "$ROOT/install.sh" | sed 's/^/   /'

echo
echo "==> 2. Add a project 'payments-api'"
sh "$ROOT/scripts/add-project.sh" payments-api acme | sed 's/^/   /'

echo
echo "==> 3. Resulting context tree"
( cd "$TMP" && find .kiro -type f | sort | sed 's/^/   /' )

echo
echo "==> 4. Generated skill frontmatter"
sed -n '1,4p' "$KIRO_HOME/skills/payments-api/SKILL.md" | sed 's/^/   /'

echo
echo "==> 5. Remove it (lifecycle)"
sh "$ROOT/scripts/remove-project.sh" payments-api --force | sed 's/^/   /'

echo
echo "==> 6. Re-run install proves idempotency (all skipped)"
sh "$ROOT/install.sh" | grep -c 'skip (exists)' | sed 's/^/   skipped: /'

rm -rf "$TMP"
echo
echo "Demo complete. No real files were modified."
