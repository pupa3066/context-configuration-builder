#!/bin/sh
# ccb-integrity-check.sh - SESSION-START verifier: confirm CCB rules loaded + override active.
#
# Runs as an agentSpawn hook. Emits a short PASS/FAIL report so the agent (and Pupa) can see, every
# new session, whether the Consistent Context Kit context is actually loaded and overriding model
# defaults. This is the "integrity run after every new session" guard.
#
# CHECKS (each reported PASS/FAIL, per the Sanity/Integrity gate discipline):
#   1. OVERRIDE:  chat.disableInheritingDefaultResources == true (model defaults off)
#   2. RESOURCES: default.json declares CCB steering + skills explicitly (else override loads nothing)
#   3. RULES:     global CCB steering files present (00-rules, bootstrap, context-registry, portfolio)
#   4. LOADER:    project-steering-loader present + resolves active projects (registry paths valid)
#   5. REGISTRY:  every [x] active project path actually exists on disk (catches stale paths)
# Read-only. POSIX sh. Exits 0 always (report-only; never blocks a session), but prints FAIL lines.
set -u
MODEL="${KIRO_HOME:-$HOME/.kiro}"
AGENT="$MODEL/agents/default.json"
REG="$MODEL/steering/context-registry.md"
CLI="$MODEL/settings/cli.json"
fail=0
say(){ printf '  %s\n' "$1"; }
FAIL(){ printf '  FAIL: %s\n' "$1"; fail=1; }

printf '[ccb-integrity] session-start check:\n'

# 1. override active? prefer live kiro-cli; fall back to cli.json on disk.
ov=$(kiro-cli settings chat.disableInheritingDefaultResources 2>/dev/null | head -1)
if [ -z "$ov" ] && [ -f "$CLI" ] && command -v python3 >/dev/null 2>&1; then
  ov=$(python3 -c "import json,sys;print(str(json.load(open('$CLI')).get('chat.disableInheritingDefaultResources')).lower())" 2>/dev/null)
fi
case "$ov" in
  true*) say "OVERRIDE ok - model default inheritance OFF (CCB is source of truth)";;
  *)     FAIL "override not set (chat.disableInheritingDefaultResources != true) - model defaults may leak in";;
esac

# 2. resources declared? (required when override is on)
if command -v python3 >/dev/null 2>&1 && [ -f "$AGENT" ]; then
  res=$(python3 -c "import json;print(len(json.load(open('$AGENT')).get('resources',[])))" 2>/dev/null || echo 0)
  if [ "${res:-0}" -ge 1 ]; then say "RESOURCES ok - agent declares $res explicit CCB resource pattern(s)"
  else FAIL "agent resources[] is EMPTY while override is on -> NO context would load"; fi
fi

# 3. CCB global steering present?
missing=""
for f in 00-rules.md bootstrap.md context-registry.md portfolio.md; do
  [ -f "$MODEL/steering/$f" ] || missing="$missing $f"
done
[ -z "$missing" ] && say "RULES ok - CCB always-on steering present (00-rules/bootstrap/registry/portfolio)" \
                   || FAIL "missing CCB steering:$missing"

# 4. loader present?
[ -x "$MODEL/hooks/project-steering-loader.sh" ] && say "LOADER ok - project-steering-loader installed" \
                   || FAIL "project-steering-loader.sh missing/not executable"

# 5. registry paths valid on disk? (catches the stale-path bug that broke context loading)
if [ -f "$REG" ]; then
  bad=0
  # active rows; last pipe field = repo path
  while IFS='|' read -r _ mk nm og cx rp rest; do
    p=$(printf '%s' "$rp" | sed 's/^ *//;s/ *$//'); [ -n "$p" ] || continue
    case "$p" in /*) full="$p";; Projects/*) full="$HOME/$p";; *) full="$HOME/Projects/$p";; esac
    [ -d "$full" ] || { FAIL "registry active project path missing on disk: $p"; bad=1; }
  done <<EOF
$(grep -E '^\| *\[x\]' "$REG" 2>/dev/null)
EOF
  [ "$bad" -eq 0 ] && say "REGISTRY ok - all active project paths exist"
fi

if [ "$fail" -eq 0 ]; then printf '[ccb-integrity] PASS - CCB loaded + override active.\n'
else printf '[ccb-integrity] ISSUES ABOVE - CCB context may be incomplete this session.\n'; fi
exit 0
