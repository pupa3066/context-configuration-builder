#!/bin/sh
# context-config-builder core installer (agent-neutral).
# Scaffolds $CCB_HOME (default ~/.context-config-builder) from templates. Non-destructive.
# Then run an adapter (adapters/<agent>.sh) to project onto your agent.
# Usage: ./install-core.sh [--dry-run]
set -eu

CORE="${CCB_HOME:-${HOME}/.context-config-builder}"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SRC="${SCRIPT_DIR}/core/templates"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

[ -d "$SRC" ] || { echo "error: core templates not found at $SRC" >&2; exit 1; }
echo "context-config-builder core -> $CORE (non-destructive$([ "$DRY" -eq 1 ] && echo ', dry-run'))"

copy_if_absent() {
  src="$1"; dst="$2"
  if [ -e "$dst" ]; then printf '  skip: %s\n' "${dst#"$HOME"/}"
  else [ "$DRY" -eq 1 ] || { mkdir -p "$(dirname "$dst")"; cp "$src" "$dst"; }
       printf '  add:  %s\n' "${dst#"$HOME"/}"; fi
}

for f in "$SRC"/always-on/*.md; do
  [ -e "$f" ] || continue
  copy_if_absent "$f" "$CORE/always-on/$(basename "$f")"
done
for f in "$SRC"/projects/*.md; do
  [ -e "$f" ] || continue
  copy_if_absent "$f" "$CORE/projects/$(basename "$f")"
done
[ "$DRY" -eq 1 ] || mkdir -p "$CORE/index"

cat <<EOF

Core installed at $CORE. Next: project it onto your agent:
  ./adapters/kiro.sh apply             # Model CLI
  ./adapters/claude-code.sh apply      # Claude Code (writes ./CLAUDE.md)
  ./adapters/cursor.sh apply           # Cursor (.cursor/rules)
  ./adapters/generic.sh build          # any LLM (single preamble.md)
EOF
