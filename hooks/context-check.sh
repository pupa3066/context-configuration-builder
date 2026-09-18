#!/usr/bin/env bash
# context-check.sh — fast, dependency-free context/research consistency verifier.
#
# WHY THIS EXISTS: research facts live in multiple files (study RESULTS, kit FINDINGS, steering
# cross-links). When one is updated, others silently go stale (e.g. an overturned single-model
# claim lingering in FINDINGS). This script detects that drift automatically so it never has to be
# re-checked by hand. Designed to run as a kiro-cli `agentSpawn` hook: it emits a short context
# summary on stdout (added to the agent's context) and only NON-ZERO-exits on a real problem.
#
# Runs from ANY working directory (uses absolute ~/.kiro + ~/Projects paths).
set -u
KIRO=~/.kiro
PROJ=~/Projects
warn=0
notes=""

add(){ notes="${notes}$1"$'\n'; }

# --- 1. Stale-claim detection: the specific failure mode that bit us -------------------------
# The single-model "monotonic INT4 erases memorization" claim was overturned by the 6-model run.
# If it reappears anywhere in kit FINDINGS or steering, flag it.
STALE_PATTERN='monotonic.*(0\.025|INT4 erases memorization)|0\.025 . 0\.017 . 0\.000'
for f in "$PROJ/consistent-context-kit/research/precision_context/FINDINGS.md" \
         "$KIRO/steering/cross-links.md"; do
  [ -f "$f" ] || continue
  if grep -Eiq "$STALE_PATTERN" "$f"; then
    add "STALE: overturned single-model memorization claim present in $(basename "$f") — 6-model run says scale-dominated. Fix before citing."
    warn=1
  fi
done

# --- 2. Registry ↔ reality: every active repo path should exist ------------------------------
REG="$KIRO/steering/context-registry.md"
if [ -f "$REG" ]; then
  while IFS= read -r path; do
    [ -z "$path" ] && continue
    [ -d "$PROJ/${path#Projects/}" ] || { add "REGISTRY: active project path missing on disk: $path"; warn=1; }
  done < <(grep -E '^\| \[x\]' "$REG" | awk -F'|' '{gsub(/ /,"",$6); print $6}')
fi

# --- 3. Cross-project data freshness: kit advisor should still run on real study data ---------
ADV="$PROJ/consistent-context-kit/research/precision_context/precision_advisor.py"
STUDY_JSON="${CCK_STUDY_JSON:-$PROJ/companion-study/analysis.json}"
if [ -f "$ADV" ] && [ -f "$STUDY_JSON" ]; then
  if ! python3 "$ADV" "$STUDY_JSON" >/dev/null 2>&1; then
    add "LINK: precision_advisor.py failed to run on real study data — cross-project link broken."
    warn=1
  fi
fi

# --- 4. Uncommitted data in a linked study repo (optional; set CCK_STUDY_DIR to enable) -------
if [ -n "${CCK_STUDY_DIR:-}" ] && [ -d "$CCK_STUDY_DIR/.git" ]; then
  dirty=$(git -C "$CCK_STUDY_DIR" status --porcelain 2>/dev/null | grep -cE '\.jsonl|\.json|\.md')
  [ "${dirty:-0}" -gt 0 ] && add "UNCOMMITTED: $dirty files in the linked study repo not committed/pushed."
fi

# --- Output (stdout -> added to agent context; keep terse) -----------------------------------
if [ "$warn" -eq 0 ] && [ -z "$notes" ]; then
  echo "[context-check] OK — research context consistent (no stale claims, registry matches, cross-links live)."
  exit 0
else
  echo "[context-check] issues detected:"
  printf "%s" "$notes"
  # exit 0 so it only WARNS in context, never blocks the session; real fix is prompted, not forced.
  exit 0
fi
