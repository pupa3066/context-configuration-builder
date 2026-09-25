#!/bin/sh
# agent-notes.sh - per-project advisor recommendations + tasks (rules 6c, 18c). Agent-neutral.
#
# Files live IN the project: <repo>/.agent/recommendations.md and <repo>/.agent/tasks.md.
#   - private GitHub repo  -> tracked; committed on the current branch (reaches GitHub with the next push)
#   - public or unknown    -> git-excluded (.git/info/exclude); stays local only
# Every recommendation is ALSO recorded in the negatives ledger (negatives-add.sh), cross-referenced by N-id.
# Append-only: nothing is ever deleted; status changes are appended lines (latest line per id wins).
#
# Usage:
#   agent-notes.sh rec     <repo> <P1|P2|P3> "<title>" "<why>" "<action>" "<done-when>"
#   agent-notes.sh task    <repo> "<task>"
#   agent-notes.sh resolve <repo> <R#|T#> "<how it was resolved / evidence>"
#   agent-notes.sh show    <repo>          # open items (used by the session-start hook)
# Env: AGENT_NOTES_VISIBILITY=private|public overrides the GitHub lookup (tests).
set -u
cmd="${1:-}"; repo="${2:-}"
[ -n "$cmd" ] && [ -n "$repo" ] && [ -d "$repo" ] || { sed -n 2,16p "$0"; exit 2; }
repo=$(cd "$repo" && pwd -P)
D="$repo/.agent"; REC="$D/recommendations.md"; TSK="$D/tasks.md"
NEG="$HOME/.kiro/negatives/negatives-add.sh"
today=$(date +%Y-%m-%d)

visibility() {
  [ -n "${AGENT_NOTES_VISIBILITY:-}" ] && { echo "$AGENT_NOTES_VISIBILITY"; return; }
  url=$(git -C "$repo" remote get-url origin 2>/dev/null) || { echo public; return; }
  slug=$(printf '%s' "$url" | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')
  v=$(gh repo view "$slug" --json visibility -q .visibility 2>/dev/null)
  [ "$v" = "PRIVATE" ] && echo private || echo public    # unknown -> treat as public (stays local)
}
setup() {
  mkdir -p "$D"
  [ -f "$REC" ] || printf '# Advisor recommendations (append-only; latest line per id wins)\n\n' > "$REC"
  [ -f "$TSK" ] || printf '# Project tasks (append-only; read when opening this project)\n\n' > "$TSK"
  if [ "$(visibility)" = public ]; then
    ex="$repo/.git/info/exclude"
    [ -f "$ex" ] && ! grep -qx '.agent/' "$ex" && echo '.agent/' >> "$ex"
    MODE=local
  else MODE=github; fi
}
save() {   # $1 = commit message
  if [ "$MODE" = github ]; then
    git -C "$repo" add .agent && git -C "$repo" commit -q -m "$1" -- .agent && echo "  committed in $(basename "$repo") (private repo; pushes with the branch)"
  else echo "  saved locally (public repo: .agent/ is git-excluded)"; fi
}
next_id() { n=$(grep -oE "^- \[[A-Z-]+\] $1[0-9]+" "$2" 2>/dev/null | grep -oE "$1[0-9]+" | tr -d "$1" | sort -n | tail -1); echo "$1$(( ${n:-0} + 1 ))"; }

case "$cmd" in
  rec)
    pr="${3:?priority}"; title="${4:?title}"; why="${5:-}"; act="${6:-}"; done_when="${7:-}"
    setup; id=$(next_id R "$REC")
    nid=""; [ -x "$NEG" ] && nid=$("$NEG" new "[$(basename "$repo")] $pr $title" "$why" "advisor recommendation $id" "$act" "$done_when" | grep -oE "N[0-9]+")
    { echo "- [OPEN] $id $pr $today - $title (ledger $nid)"
      [ -n "$why" ] && echo "  why: $why"
      [ -n "$act" ] && echo "  action: $act"
      [ -n "$done_when" ] && echo "  done-when: $done_when"; } >> "$REC"
    echo "added $id ($pr)${nid:+ + ledger $nid}"; save "Add advisor recommendation $id: $title" ;;
  task)
    t="${3:?task}"; setup; id=$(next_id T "$TSK")
    echo "- [OPEN] $id $today - $t" >> "$TSK"; echo "added $id"; save "Add project task $id" ;;
  resolve)
    id="${3:?id}"; ev="${4:?resolution/evidence required}"; setup
    case "$id" in R*) f="$REC";; T*) f="$TSK";; *) echo "id must be R# or T#" >&2; exit 2;; esac
    grep -qE "^- \[[A-Z-]+\] $id " "$f" || { echo "$id not found in $f" >&2; exit 1; }
    echo "- [RESOLVED] $id $today - $ev" >> "$f"
    nid=$(grep -m1 -E "^- \[OPEN\] $id " "$f" | grep -oE "ledger N[0-9]+" | grep -oE "N[0-9]+")
    [ -n "$nid" ] && [ -x "$NEG" ] && "$NEG" flip "$nid" "$ev" >/dev/null && echo "  ledger $nid flipped"
    echo "resolved $id (history kept)"; save "Resolve $id" ;;
  show)
    for f in "$TSK" "$REC"; do
      [ -f "$f" ] || continue
      python3 - "$f" <<'PY'
import re, sys
last, first = {}, {}
for ln in open(sys.argv[1]):
    m = re.match(r"- \[([A-Z-]+)\] ([RT]\d+) (.*)", ln.rstrip())
    if m:
        last[m.group(2)] = m.group(1); first.setdefault(m.group(2), m.group(3))
for i, st in last.items():
    if st != "RESOLVED": print(f"  {i} [{st}] {first[i]}")
PY
    done ;;
  *) sed -n 2,16p "$0"; exit 2 ;;
esac
