#!/bin/sh
# research-neutrality-check.sh - research rule: research text names tools by role, not by product.
# Scans research artifacts for agent/tool product names. Allowed only on the one line starting with
# "Environment:" (reproducibility, exact versions), inside fenced code (functional names), or on a
# line marked <!-- cited-setup --> (a cited paper's own setup). Exit 1 on any hit, 0 when clean.
#
# Usage: sh scripts/research-neutrality-check.sh [file ...]   (default: the research artifact set)
set -u
cd "$(dirname "$0")/.." || exit 2
PAT='kiro|claude[ -]code|claude\.md|cursor|copilot|windsurf'
if [ "$#" -gt 0 ]; then files="$*"; else
  files=$(ls research/*.md docs/PROVENANCE.md marketing/story.md benchmark/*.md docs/paper/*.md 2>/dev/null)
fi
# skip: fenced code blocks (functional names), the Environment line, and lines marked <!-- cited-setup -->
# (a cited paper's own setup, reported verbatim).
hits=$(awk -v pat="$PAT" '
  FNR==1 { fence=0 }
  /^[[:space:]]*```/ { fence=!fence; next }
  fence { next }
  /^[[:space:]>*-]*Environment:/ || /cited-setup/ { next }
  tolower($0) ~ pat { print FILENAME ":" FNR ": " $0 }
' $files 2>/dev/null)
if [ -n "$hits" ]; then
  echo "[research-neutrality] FAIL - product names in research text (use: agent, coding agent, agent A/B, agent config directory, session-start hook):"
  echo "$hits" | sed 's/^/  /'
  exit 1
fi
echo "[research-neutrality] PASS - $(echo $files | wc -w | tr -d ' ') research files, no product names outside the Environment line."
