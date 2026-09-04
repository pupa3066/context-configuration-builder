#!/bin/sh
# Kiro adapter: project the neutral context-kit core onto Kiro CLI.
#   always-on/*  -> ~/.kiro/steering/*
#   projects/<n> -> ~/.kiro/skills/<n>/SKILL.md  (adds required frontmatter)
# Usage: ./adapters/kiro.sh apply [--dry-run]
set -eu

CORE="${CONTEXT_KIT_HOME:-${HOME}/.context-kit}"
KIRO="${KIRO_HOME:-${HOME}/.kiro}"
DRY=0; CMD="${1:-}"; [ "${2:-}" = "--dry-run" ] && DRY=1

[ "$CMD" = "apply" ] || { echo "usage: kiro.sh apply [--dry-run]" >&2; exit 2; }
[ -d "$CORE" ] || { echo "error: core not found at $CORE (run install.sh)" >&2; exit 1; }

say() { printf '  %s\n' "$1"; }
run() { [ "$DRY" -eq 1 ] || eval "$1"; }

run "mkdir -p '$KIRO/steering' '$KIRO/skills'"

# Tier 1: always-on -> steering
for f in "$CORE"/always-on/*.md; do
  [ -e "$f" ] || continue
  say "steering <- $(basename "$f")"
  run "cp '$f' '$KIRO/steering/$(basename "$f")'"
done

# Tier 2: projects -> skills (wrap with frontmatter Kiro needs)
for f in "$CORE"/projects/*.md; do
  [ -e "$f" ] || continue
  name=$(basename "$f" .md)
  say "skill    <- $name"
  run "mkdir -p '$KIRO/skills/$name'"
  if [ "$DRY" -eq 0 ]; then
    {
      printf -- '---\n'
      printf 'name: %s-context\n' "$name"
      printf 'description: Deep context for %s. Load when working on %s.\n' "$name" "$name"
      printf -- '---\n\n'
      cat "$f"
    } > "$KIRO/skills/$name/SKILL.md"
  fi
done

echo "Kiro adapter: applied$( [ "$DRY" -eq 1 ] && echo ' (dry-run)')."
echo "Refresh your knowledge base on ~/.kiro/steering and ~/.kiro/skills if you use one."
