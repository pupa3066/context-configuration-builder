#!/bin/sh
# rules-builder.sh — manage the editable rules/debug list as data.
# Mirrors add-project.sh but for rules. Operates on the always-on rules file.
#
# Rules file format (machine-editable, one rule per line inside sections):
#   ## <Section>
#   - [ID] rule text
# Priority rules use IDs like R0..R9; numbered rules use 1..N.
#
# Usage:
#   rules-builder.sh list [--priority-only]
#   rules-builder.sh add "<text>" [--section "<Section>"] [--priority]
#   rules-builder.sh remove <ID>
#   rules-builder.sh check          # validate: no duplicate IDs, priority rules present
#
# Env: RULES_FILE (default: $CONTEXT_KIT_HOME/always-on/rules.md, else ~/.context-kit/...)
set -eu

CORE="${CONTEXT_KIT_HOME:-${HOME}/.context-kit}"
RULES_FILE="${RULES_FILE:-$CORE/always-on/rules.md}"

die() { echo "error: $1" >&2; exit "${2:-1}"; }
[ -f "$RULES_FILE" ] || die "rules file not found: $RULES_FILE (run install-core.sh)"

CMD="${1:-}"; [ -n "$CMD" ] || die "usage: rules-builder.sh {list|add|remove|check}" 2

rule_lines() { grep -nE '^- \[[A-Za-z0-9]+\] ' "$RULES_FILE" || true; }

next_custom_id() {
  # Custom rules use stable IDs like [C1],[C2]... Compute max Cn robustly.
  max=$(grep -oE '\[C[0-9]+\]' "$RULES_FILE" | grep -oE '[0-9]+' | sort -n | tail -1)
  [ -n "$max" ] && echo $((max + 1)) || echo 1
}

case "$CMD" in
  list)
    if [ "${2:-}" = "--priority-only" ]; then
      grep -E '^- \*\*R[0-9]' "$RULES_FILE" || echo "(no priority rules)"
    else
      grep -E '^- \*\*R[0-9]|^[0-9]+\. |^- \[[A-Za-z0-9]+\] ' "$RULES_FILE" || echo "(no rules found)"
    fi
    ;;

  add)
    TEXT="${2:-}"; [ -n "$TEXT" ] || die "usage: add \"<text>\" [--section S] [--priority]" 2
    SECTION="Custom"; PRIORITY=0
    shift 2 || true
    while [ $# -gt 0 ]; do
      case "$1" in
        --section) SECTION="${2:-Custom}"; shift 2 ;;
        --priority) PRIORITY=1; shift ;;
        *) die "unknown flag: $1" 2 ;;
      esac
    done
    if [ "$PRIORITY" -eq 1 ]; then
      # next Rn
      maxr=$(grep -oE '^- \*\*R[0-9]+' "$RULES_FILE" | grep -oE '[0-9]+' | sort -n | tail -1)
      nid="R$(( ${maxr:--1} + 1 ))"
      line="- **$nid — Custom:** $TEXT"
      # insert after the PRIORITY RULES header block (after last existing R-line)
      awk -v ins="$line" '
        /^- \*\*R[0-9]/ { last=NR }
        { lines[NR]=$0 }
        END {
          for (i=1;i<=NR;i++){ print lines[i]; if (i==last) print ins }
        }' "$RULES_FILE" > "$RULES_FILE.tmp" && mv "$RULES_FILE.tmp" "$RULES_FILE"
      echo "added priority rule $nid"
    else
      nid="C$(next_custom_id)"
      ins="- [$nid] $TEXT"
      if grep -qE "^## $SECTION\$" "$RULES_FILE"; then
        awk -v sec="## $SECTION" -v ins="$ins" '
          { print }
          $0==sec && !done { print ins; done=1 }
        ' "$RULES_FILE" > "$RULES_FILE.tmp" && mv "$RULES_FILE.tmp" "$RULES_FILE"
      else
        printf '\n## %s\n%s\n' "$SECTION" "$ins" >> "$RULES_FILE"
      fi
      echo "added rule [$nid] under '$SECTION'"
    fi
    ;;

  remove)
    ID="${2:-}"; [ -n "$ID" ] || die "usage: remove <ID>" 2
    case "$ID" in
      R0) die "R0 (rule governance) is protected and cannot be removed by the builder" ;;
    esac
    before=$(wc -l < "$RULES_FILE")
    # remove priority rule (- **Rn ...) or numbered rule (n. ...)
    grep -vE "^- \*\*$ID —|^$ID\. |^- \[$ID\] " "$RULES_FILE" > "$RULES_FILE.tmp" && mv "$RULES_FILE.tmp" "$RULES_FILE"
    after=$(wc -l < "$RULES_FILE")
    [ "$before" -ne "$after" ] && echo "removed $ID" || { echo "no rule matched ID '$ID'" >&2; exit 1; }
    ;;

  check)
    # duplicate priority IDs?
    dups=$(grep -oE '^- \*\*R[0-9]+' "$RULES_FILE" | sort | uniq -d)
    [ -z "$dups" ] || die "duplicate priority rule IDs: $dups"
    # R0 present?
    grep -qE '^- \*\*R0 ' "$RULES_FILE" || die "R0 (rule governance) missing — must always be present"
    echo "check OK: R0 present, no duplicate priority IDs"
    ;;

  *) die "unknown command: $CMD (use list|add|remove|check)" 2 ;;
esac
