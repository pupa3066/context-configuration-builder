#!/bin/sh
# context-config-builder installer  -  POSIX sh, non-destructive, idempotent.
# Copies templates into $KIRO_HOME (default ~/.kiro) without overwriting.
#
# Usage: ./install.sh [--dry-run] [--help]
#   KIRO_HOME=/custom/path ./install.sh
set -eu

KIRO_HOME="${KIRO_HOME:-${HOME}/.kiro}"
DRY_RUN=0

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SRC="${SCRIPT_DIR}/templates"

usage() {
  cat <<EOF
context-config-builder installer

Usage: ./install.sh [options]
  --dry-run    Show what would be installed without writing
  --help       Show this help

Environment:
  KIRO_HOME    Target dir (default: \$HOME/.kiro)
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "unknown option: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

# Preflight
if [ ! -d "$SRC" ]; then
  echo "error: templates dir not found at $SRC" >&2
  exit 1
fi
command -v cp >/dev/null 2>&1 || { echo "error: cp not found" >&2; exit 1; }

echo "context-config-builder -> $KIRO_HOME (non-destructive$([ "$DRY_RUN" -eq 1 ] && echo ', dry-run'))"

do_mkdir() { [ "$DRY_RUN" -eq 1 ] || mkdir -p "$1"; }

copy_if_absent() {
  src="$1"; dst="$2"
  if [ -e "$dst" ]; then
    printf '  skip (exists): %s\n' "${dst#"$HOME"/}"
  else
    do_mkdir "$(dirname "$dst")"
    [ "$DRY_RUN" -eq 1 ] || cp "$src" "$dst"
    printf '  add:           %s\n' "${dst#"$HOME"/}"
  fi
}

do_mkdir "$KIRO_HOME/steering"
do_mkdir "$KIRO_HOME/skills"

# steering templates
for f in "$SRC"/steering/*.md; do
  [ -e "$f" ] || continue
  copy_if_absent "$f" "$KIRO_HOME/steering/$(basename "$f")"
done

# example skill
copy_if_absent "$SRC/skills/_example/SKILL.md" "$KIRO_HOME/skills/_example/SKILL.md"

[ "$DRY_RUN" -eq 1 ] && { echo; echo "(dry-run: no files written)"; exit 0; }

cat <<'EOF'

Installed. Next steps:
  1. Edit ~/.kiro/steering/00-rules.md          (your rules + visibility policy)
  2. Edit ~/.kiro/steering/context-registry.md  (add your projects; flip check/uncheck)
  3. Scaffold a project:  ./scripts/add-project.sh <name>
  4. (Optional) Index ~/.kiro/steering and ~/.kiro/skills into your agent's knowledge base.

Start a new session; steering auto-loads. Verify with: /context show
EOF
