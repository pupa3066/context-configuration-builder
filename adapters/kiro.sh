#!/bin/sh
# Model adapter: project the Consistent Context Kit core onto Model CLI.
#   always-on/*  -> ~/.kiro/steering/*
#   projects/<n> -> ~/.kiro/skills/<n>/SKILL.md  (adds required frontmatter)
# Usage: ./adapters/kiro.sh apply [--dry-run]
# Security: no eval, no network; writes only under $MODEL.
set -eu

CORE="${CCB_HOME:-${HOME}/.context-config-builder}"
MODEL="${KIRO_HOME:-${HOME}/.kiro}"
DRY=0; CMD="${1:-}"; [ "${2:-}" = "--dry-run" ] && DRY=1

[ "$CMD" = "apply" ] || { echo "usage: kiro.sh apply [--dry-run]" >&2; exit 2; }
[ -d "$CORE" ] || { echo "error: core not found at $CORE (run install-core.sh)" >&2; exit 1; }

say() { printf '  %s\n' "$1"; }

[ "$DRY" -eq 1 ] || mkdir -p "$MODEL/steering" "$MODEL/skills"

# Tier 1: always-on -> steering (direct, quoted commands; no eval)
for f in "$CORE"/always-on/*.md; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  say "steering <- $base"
  [ "$DRY" -eq 1 ] || cp "$f" "$MODEL/steering/$base"
done

# Tier 2: projects -> skills (wrap with frontmatter Model needs)
for f in "$CORE"/projects/*.md; do
  [ -e "$f" ] || continue
  name=$(basename "$f" .md)
  say "skill    <- $name"
  if [ "$DRY" -eq 0 ]; then
    mkdir -p "$MODEL/skills/$name"
    {
      printf -- '---\n'
      printf 'name: %s-context\n' "$name"
      printf 'description: Deep context for %s. Load when working on %s.\n' "$name" "$name"
      printf -- '---\n\n'
      cat "$f"
    } > "$MODEL/skills/$name/SKILL.md"
  fi
done

echo "Model adapter: applied$( [ "$DRY" -eq 1 ] && echo ' (dry-run)')."
echo "Refresh your knowledge base on ~/.kiro/steering and ~/.kiro/skills if you use one."
