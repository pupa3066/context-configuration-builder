#!/bin/sh
# ccb-bootstrap.sh - one-shot, idempotent, self-verifying installer for the
# Consistent Context Kit (CCB) on Kiro CLI.
#
# WHAT IT DOES (so CCB "does the default loading, override, and integrity check
# on its own for every new session"):
#   1. HOOKS     copy the agent-neutral hook scripts into $KIRO_HOME/hooks (executable)
#   2. STEERING  copy the always-on steering templates into $KIRO_HOME/steering
#                (non-destructive: never clobbers steering you already edited)
#   3. OVERRIDE  set chat.disableInheritingDefaultResources=true in settings/cli.json
#                (turns kiro's default resource inheritance OFF -> CCB is source of truth)
#   4. WIRE      in agents/default.json: declare the CCB resources[] explicitly and
#                register the agentSpawn hooks (integrity-check FIRST, then loaders).
#                A timestamped backup is written before any edit.
#   5. VERIFY    run ccb-integrity-check.sh and print its PASS/FAIL report.
#
# IDEMPOTENT: re-running makes no destructive change. Hooks are refreshed from the
# repo (they are vendored code, not user data). Steering files that already exist are
# left untouched. Config edits are applied only if the desired state is not already present.
#
# SAFE: POSIX sh, no eval, no network. Config edits use python3 json (never sed on JSON).
# Writes only under $KIRO_HOME.
#
# Usage: ./ccb-bootstrap.sh [--dry-run] [--help]
#   KIRO_HOME=/custom/path ./ccb-bootstrap.sh     # target a different kiro home (e.g. a test dir)
set -eu

KIRO_HOME="${KIRO_HOME:-${HOME}/.kiro}"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HOOK_SRC="${SCRIPT_DIR}/hooks"
STEER_SRC="${SCRIPT_DIR}/templates/steering"
DRY=0

usage() {
  cat <<EOF
ccb-bootstrap - self-installing CCB for Kiro CLI (override + resources + hooks + integrity check)

Usage: ./ccb-bootstrap.sh [--dry-run] [--help]
Environment:
  KIRO_HOME   Target kiro home (default: \$HOME/.kiro)
EOF
}

for arg in "${@:-}"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --help|-h) usage; exit 0 ;;
    "") : ;;
    *) echo "unknown option: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

command -v python3 >/dev/null 2>&1 || { echo "error: python3 required (used for safe JSON edits)" >&2; exit 1; }
[ -d "$HOOK_SRC" ]  || { echo "error: hooks dir not found at $HOOK_SRC" >&2; exit 1; }
[ -d "$STEER_SRC" ] || { echo "error: steering templates not found at $STEER_SRC" >&2; exit 1; }

AGENT="$KIRO_HOME/agents/default.json"
CLI="$KIRO_HOME/settings/cli.json"

say()  { printf '  %s\n' "$1"; }
run()  { [ "$DRY" -eq 1 ] || "$@"; }

echo "ccb-bootstrap -> $KIRO_HOME$( [ "$DRY" -eq 1 ] && echo '  (dry-run)')"

# ---------------------------------------------------------------------------
# 1. HOOKS - vendored scripts, always refreshed (they are code, not user data)
# ---------------------------------------------------------------------------
echo "[1/5] hooks"
run mkdir -p "$KIRO_HOME/hooks"
for h in ccb-integrity-check.sh project-steering-loader.sh steering-loader-guard.sh context-check.sh ccb-project-context.sh ccb-parity-check.sh; do
  if [ -f "$HOOK_SRC/$h" ]; then
    run cp "$HOOK_SRC/$h" "$KIRO_HOME/hooks/$h"
    run chmod +x "$KIRO_HOME/hooks/$h"
    say "install $h"
  fi
done

# ---------------------------------------------------------------------------
# 2. STEERING - non-destructive (never clobber edited steering)
# ---------------------------------------------------------------------------
echo "[2/5] steering (non-destructive)"
run mkdir -p "$KIRO_HOME/steering"
for f in "$STEER_SRC"/*.md; do
  [ -e "$f" ] || continue
  dst="$KIRO_HOME/steering/$(basename "$f")"
  if [ -e "$dst" ]; then say "skip (exists) $(basename "$f")"
  else run cp "$f" "$dst"; say "add $(basename "$f")"; fi
done

# ---------------------------------------------------------------------------
# 3. OVERRIDE - chat.disableInheritingDefaultResources = true
# ---------------------------------------------------------------------------
echo "[3/5] override (cli.json)"
run mkdir -p "$KIRO_HOME/settings"
CLI="$CLI" DRY="$DRY" python3 - <<'PY'
import json, os
p = os.environ["CLI"]; dry = os.environ["DRY"] == "1"
try:
    d = json.load(open(p))
except Exception:
    d = {}
# disableInheritingDefaultResources: CCB is the source of truth.
# defaultAgent/agentEngine: measured 2026-09-25 (kiro-cli 2.24.0): without defaultAgent=default a plain
# session runs the built-in kiro_default and NO agentSpawn hooks fire; engines v2 (default) and v3 skip
# agentSpawn hooks even with the right agent. Only v1 ran them. ccb-parity-check.sh verifies both.
want = {"chat.disableInheritingDefaultResources": True, "chat.defaultAgent": "default", "chat.agentEngine": "v1"}
todo = {k: v for k, v in want.items() if d.get(k) != v}
if not todo:
    print("  already set: " + ", ".join("%s=%s" % kv for kv in want.items()))
else:
    d.update(todo)
    if not dry:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(d, open(p, "w"), indent=2)
    print("  set: " + ", ".join("%s=%s" % kv for kv in todo.items()))
PY

# ---------------------------------------------------------------------------
# 4. WIRE - resources[] + agentSpawn hooks in default.json (backup first)
# ---------------------------------------------------------------------------
echo "[4/5] agent config (default.json)"
AGENT="$AGENT" DRY="$DRY" python3 - <<'PY'
import json, os, shutil, time
p = os.environ["AGENT"]; dry = os.environ["DRY"] == "1"

DESIRED_RES = [
    "file://~/.kiro/steering/**/*.md",
    "skill://~/.kiro/skills/**/SKILL.md",
]
# integrity check MUST run first; loaders after. context-check optional.
DESIRED_HOOKS = [
    "~/.kiro/hooks/ccb-integrity-check.sh",
    "~/.kiro/hooks/steering-loader-guard.sh",   # Kiro-only config self-heal, prints nothing
    "~/.kiro/hooks/ccb-project-context.sh",     # wraps project-steering-loader: index + repo steering
    "~/.kiro/hooks/ccb-parity-check.sh",        # Kiro <-> Claude Code parity report
]
# migration: the loader used to run as its own hook; its full dump was truncated and double-loaded.
LEGACY_HOOKS = ["~/.kiro/hooks/project-steering-loader.sh"]

if os.path.exists(p):
    try:
        d = json.load(open(p))
    except Exception:
        print("  WARN: %s unparseable -> leaving untouched" % p); raise SystemExit(0)
else:
    d = {"name": "default",
         "description": "Default agent with CCB session-start context + integrity check.",
         "mcpServers": {}, "tools": [], "allowedTools": [],
         "toolsSettings": {}, "includeMcpJson": True, "model": None}

changed = False

# resources: ensure both CCB patterns present (preserve any extras the user added)
res = d.get("resources") or []
for r in DESIRED_RES:
    if r not in res:
        res.append(r); changed = True
d["resources"] = res

# hooks.agentSpawn: ensure each desired hook present; integrity check ordered first
hooks = d.setdefault("hooks", {})
spawn = hooks.setdefault("agentSpawn", [])
def has(cmd): return any(isinstance(h, dict) and h.get("command") == cmd for h in spawn)
for old in LEGACY_HOOKS:
    if has(old):
        spawn[:] = [h for h in spawn if not (isinstance(h, dict) and h.get("command") == old)]
        changed = True
for cmd in DESIRED_HOOKS:
    if not has(cmd):
        entry = {"command": cmd, "timeout_ms": 8000, "cache_ttl_seconds": 0}
        if cmd.endswith("ccb-integrity-check.sh"):
            spawn.insert(0, entry)      # integrity check runs FIRST
        else:
            spawn.append(entry)
        changed = True

# guarantee integrity-check is position 0 even if it already existed later
ic = "~/.kiro/hooks/ccb-integrity-check.sh"
idx = next((i for i,h in enumerate(spawn) if isinstance(h,dict) and h.get("command")==ic), None)
if idx not in (None, 0):
    spawn.insert(0, spawn.pop(idx)); changed = True

if not changed:
    print("  already wired: resources[] + agentSpawn hooks present, integrity-check first")
else:
    if not dry:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if os.path.exists(p):
            bak = "%s.bak.%s" % (p, time.strftime("%Y%m%d_%H%M%S"))
            shutil.copy(p, bak)
            print("  backup: %s" % os.path.basename(bak))
        json.dump(d, open(p, "w"), indent=2)
    print("  wired: %d resource pattern(s), %d agentSpawn hook(s)" % (len(res), len(spawn)))
PY

# ---------------------------------------------------------------------------
# 5. VERIFY - run the integrity check the same way the session hook does
# ---------------------------------------------------------------------------
echo "[5/5] self-verify (integrity check)"
if [ "$DRY" -eq 1 ]; then
  echo "  (dry-run: skipping verification)"
else
  KIRO_HOME="$KIRO_HOME" HOME_OVERRIDE="$KIRO_HOME" \
    sh "$KIRO_HOME/hooks/ccb-integrity-check.sh" || true
fi

echo
echo "Done. Start a new Kiro session; CCB loads + self-checks automatically."
echo "Manual re-check any time:  sh $KIRO_HOME/hooks/ccb-integrity-check.sh"
