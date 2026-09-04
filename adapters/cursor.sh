#!/bin/sh
# Cursor adapter: project the neutral core onto Cursor rules.
#   always-on/* -> ./.cursor/rules/<name>.mdc  (alwaysApply: true)
#   projects/*  -> ./.cursor/rules/project-<name>.mdc (alwaysApply: false, agent loads on demand)
# Usage: ./adapters/cursor.sh apply [target-dir]
set -eu

CORE="${CONTEXT_KIT_HOME:-${HOME}/.context-kit}"
CMD="${1:-}"; DEST="${2:-$PWD}"

[ "$CMD" = "apply" ] || { echo "usage: cursor.sh apply [target-dir]" >&2; exit 2; }
[ -d "$CORE" ] || { echo "error: core not found at $CORE" >&2; exit 1; }

mkdir -p "$DEST/.cursor/rules"

for f in "$CORE"/always-on/*.md; do
  [ -e "$f" ] || continue
  name=$(basename "$f" .md)
  { printf -- '---\nalwaysApply: true\n---\n\n'; cat "$f"; } > "$DEST/.cursor/rules/$name.mdc"
done

for f in "$CORE"/projects/*.md; do
  [ -e "$f" ] || continue
  name=$(basename "$f" .md)
  { printf -- '---\nalwaysApply: false\ndescription: Deep context for %s\n---\n\n' "$name"; cat "$f"; } \
    > "$DEST/.cursor/rules/project-$name.mdc"
done

echo "Cursor adapter: wrote $DEST/.cursor/rules/*.mdc (always-on + on-demand project rules)"
