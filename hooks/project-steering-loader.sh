#!/bin/sh
# project-steering-loader.sh - CCK feature (AGENT-NEUTRAL): load the ACTIVE project's per-project
# context/rules regardless of the directory the agent was launched from.
#
# PROBLEM: most agents only auto-load per-project rules from the CURRENT launch dir. If you start
# the agent from ~ (home) but work on a project elsewhere, that project's debug/research rules never
# load. This hook detects the active project and emits its per-project context on demand.
#
# AGENT-NEUTRAL: the per-project rule locations are configurable, so this works for Kiro, Claude
# Code, Cursor, or any agent. Defaults cover the common conventions; override via env.
#
# CONFIG (env):
#   CCK_ACTIVE_PROJECT   explicit path to the active repo (highest priority)
#   CCK_STEER_DIRS       colon-separated per-project rule DIRECTORIES to emit (all *.md inside)
#                        default: ".kiro/steering:.cursor/rules:.claude/steering"
#   CCK_STEER_FILES      colon-separated per-project rule FILES to emit if present
#                        default: "context.md:AGENTS.md:CLAUDE.md:.cursorrules"
#
# DETECTION (priority): 1) CCK_ACTIVE_PROJECT  2) git rev-parse --show-toplevel from $PWD
# If none resolves -> no-op (safe). Read-only; no writes; no eval; no network. POSIX sh.
set -eu

STEER_DIRS="${CCK_STEER_DIRS:-.kiro/steering:.cursor/rules:.claude/steering}"
STEER_FILES="${CCK_STEER_FILES:-context.md:AGENTS.md:CLAUDE.md:.cursorrules}"

# split a colon-separated list into positional args safely (no eval)
_emit_md_dir() {
  dir="$1"
  [ -d "$dir" ] || return 0
  for f in "$dir"/*.md "$dir"/*.mdc; do
    [ -e "$f" ] || continue
    head -3 "$f" 2>/dev/null | grep -qiE 'inclusion:[[:space:]]*(manual|fileMatch)' && continue
    printf '\n--- %s ---\n' "${f#"$PROJ"/}"
    cat "$f"
  done
}

emit_project() {
  PROJ="$1"
  # does this project actually have ANY of the configured rule dirs/files?
  have=0
  OLDIFS=$IFS; IFS=:
  for rel in $STEER_DIRS; do [ -d "$PROJ/$rel" ] && have=1; done
  for rel in $STEER_FILES; do [ -f "$PROJ/$rel" ] && have=1; done
  IFS=$OLDIFS
  [ "$have" -eq 1 ] || return 0

  # DOUBLE-LOAD GUARD (agent-neutral): if the agent was launched from INSIDE this project, it likely
  # already auto-inherits the project's rule dirs/files from cwd. Re-emitting would double-count.
  # Resolve BOTH paths to physical form first (handles symlinks, e.g. /var -> /private/var on macOS).
  phys_pwd=$(cd "$PWD" 2>/dev/null && pwd -P || printf '%s' "$PWD")
  phys_proj=$(cd "$PROJ" 2>/dev/null && pwd -P || printf '%s' "$PROJ")
  case "$phys_pwd/" in
    "$phys_proj/"*) printf '(project-steering-loader: %s already auto-loaded from cwd; skipping to avoid double-count)\n' "$PROJ"; return 0 ;;
  esac

  printf '=== PROJECT CONTEXT: %s ===\n' "$PROJ"
  OLDIFS=$IFS; IFS=:
  for rel in $STEER_DIRS; do _emit_md_dir "$PROJ/$rel"; done
  for rel in $STEER_FILES; do
    f="$PROJ/$rel"
    [ -f "$f" ] || continue
    printf '\n--- %s ---\n' "$rel"
    cat "$f"
  done
  IFS=$OLDIFS
}

# 1. explicit override
if [ -n "${CCK_ACTIVE_PROJECT:-}" ] && [ -d "${CCK_ACTIVE_PROJECT}" ]; then
  emit_project "${CCK_ACTIVE_PROJECT}"
  exit 0
fi

# 2. git root from current dir
if root=$(git rev-parse --show-toplevel 2>/dev/null); then
  emit_project "$root"
  exit 0
fi

# 3. REGISTRY FALLBACK (the fix for launched-from-home sessions): if no explicit project and not
# inside a repo (e.g. kiro started from ~), load the ACTIVE projects listed in the context-registry
# so per-project debug/research rules are NEVER silently missing regardless of launch dir. This is
# the enforcement that closes the "launched from home => no project context" gap.
REG="${CCK_REGISTRY:-$HOME/.kiro/steering/context-registry.md}"
if [ -f "$REG" ]; then
  emitted=0
  # parse active rows: lines like "| [x] | name | origin | context file | Repo path |"
  # extract the LAST pipe-field (repo path, relative to ~/Projects) for [x] rows.
  grep -E '^\| *\[x\]' "$REG" 2>/dev/null | while IFS='|' read -r _ mark name origin ctx repopath rest; do
    rp=$(printf '%s' "$repopath" | sed 's/^ *//; s/ *$//')
    [ -n "$rp" ] || continue
    case "$rp" in
      /*) full="$rp" ;;                          # absolute
      Projects/*) full="$HOME/$rp" ;;            # ~/Projects/... form
      *) full="$HOME/Projects/$rp" ;;            # bare name
    esac
    [ -d "$full" ] && emit_project "$full"
  done
  exit 0
fi

# 4. nothing resolved -> no-op
exit 0
