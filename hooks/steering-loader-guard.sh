#!/bin/sh
# steering-loader-guard.sh - self-healing wrapper for project-steering-loader.sh.
#
# GOAL (honest scope): make the project-steering loader DURABLE across future kiro sessions and
# resilient to kiro/config changes that might drop it. It does two things every agentSpawn:
#   1. RUN the project-steering loader (emit active-project context) - the actual feature.
#   2. SELF-HEAL: verify the loader is still installed on disk AND still registered in the agent
#      config; if either is missing (e.g. a kiro update rewrote the config, or the file was removed),
#      re-install from the CCK canonical source and re-register the hook, so the NEXT session is fixed.
#
# HONEST LIMITS (stated plainly, not overclaimed):
#   - This cannot make a file "unchangeable" against the kiro vendor. If a future kiro version removes
#     agentSpawn hooks entirely or changes the config schema, this self-heal may itself stop running.
#   - What it DOES guarantee: if the hook entry is deleted from a still-compatible config, the next
#     session detects it and restores it. So accidental/config-churn loss auto-recovers; you are not
#     silently left without it.
#   - It self-heals at MOST once per run and logs what it did, so you can see if kiro keeps fighting it.
#
# Read-only except the self-heal path (which edits ~/.kiro/agents/default.json using python json,
# never eval). Safe, POSIX sh.
set -u

CCK_SRC="${CCK_HOOK_SRC:-$HOME/Projects/consistent-context-kit/hooks/project-steering-loader.sh}"
INSTALLED="$HOME/.kiro/hooks/project-steering-loader.sh"
AGENT="$HOME/.kiro/agents/default.json"
GUARD_LOG="$HOME/.kiro/hooks/steering-loader-guard.log"

log() { printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S')" "$1" >> "$GUARD_LOG" 2>/dev/null || true; }

# --- self-heal: ensure the loader file exists on disk ---
if [ ! -f "$INSTALLED" ]; then
  if [ -f "$CCK_SRC" ]; then
    mkdir -p "$HOME/.kiro/hooks"
    cp "$CCK_SRC" "$INSTALLED" && chmod +x "$INSTALLED"
    log "SELF-HEAL: reinstalled loader from $CCK_SRC (was missing)"
  else
    log "WARN: loader missing and CCK source not found at $CCK_SRC"
  fi
fi

# --- self-heal: ensure the loader hook is registered in the agent config ---
if [ -f "$AGENT" ] && command -v python3 >/dev/null 2>&1; then
  python3 - "$AGENT" <<'PY' 2>/dev/null || true
import json, sys, os
p = sys.argv[1]
try:
    d = json.load(open(p))
except Exception:
    sys.exit(0)  # unrecognizable config (kiro schema change?) -> don't touch, don't crash
hooks = d.setdefault("hooks", {})
spawn = hooks.setdefault("agentSpawn", [])
cmd = "~/.kiro/hooks/ccb-project-context.sh"
present = any(isinstance(h, dict) and h.get("command") == cmd for h in spawn)
if not present:
    spawn.append({"command": cmd, "timeout_ms": 5000, "cache_ttl_seconds": 0})
    # backup before writing
    try:
        import shutil, time
        shutil.copy(p, p + ".guardbak")
    except Exception:
        pass
    json.dump(d, open(p, "w"), indent=2)
    with open(os.path.expanduser("~/.kiro/hooks/steering-loader-guard.log"), "a") as f:
        f.write("SELF-HEAL: re-registered loader hook in default.json\n")
PY
fi

# --- the feature itself runs as its own hook (ccb-project-context.sh, registered above), which wraps
# the loader and emits a short index; running the loader here too double-loaded and got truncated.
exit 0
