#!/bin/sh
# ccb-parity-check.sh - SESSION-START verifier: Model and Claude Code load the SAME CCB context.
#
# Runs as a session-start hook in BOTH agents (Model agentSpawn, Claude Code SessionStart) and prints the
# same report in each, so a Model session and a Claude Code session can be compared line for line.
#
# CHECKS (PASS/FAIL each):
#   1. STEERING: fingerprint of the always-on steering both agents read (~/.kiro/steering/*.md); WARN if
#                an optional git mirror of the rules ($CCB_RULES_MIRROR) has drifted from it.
#   2. MODEL:     chat.defaultAgent=default (else the built-in kiro_default runs with NO hooks) and
#                chat.agentEngine=v1 (engines v2/v3 were measured to skip agentSpawn hooks, kiro-cli 2.24.0).
#   3. HOOKS:    both agents register the same session-start hook files (Model-only self-heal guard excluded),
#                including ccb-project-context and ccb-parity-check; every registered file exists.
#   4. CLAUDE:   ~/.claude/CLAUDE.md @imports every always-on steering file.
#   5. SKILLS:   every ~/.kiro/skills/<dir> is linked as ~/.claude/skills/<frontmatter name> (same names).
#   6. REPOS:    every active registry repo's .kiro/steering (Model workspace steering) is @imported by
#                that repo's CLAUDE.local.md (maintained by ccb-project-context.sh).
# Read-only. POSIX sh + python3. Exits 0 always (report-only), prints FAIL lines.
set -u
K="${KIRO_HOME:-$HOME/.kiro}"; C="${CLAUDE_HOME:-$HOME/.claude}"
MIRROR="${CCB_RULES_MIRROR:-$HOME/working-rules}"
fail=0

printf '[ccb-parity] Model <-> Claude Code context parity:\n'

# 1. steering fingerprint + optional mirror drift
fp=$(cat "$K"/steering/*.md 2>/dev/null | shasum | cut -c1-12)
printf '  STEERING fingerprint %s (both agents read ~/.kiro/steering)\n' "$fp"
if [ -d "$MIRROR" ]; then
  drift=""
  for f in "$K"/steering/*.md; do b=$(basename "$f"); [ -f "$MIRROR/$b" ] && ! cmp -s "$f" "$MIRROR/$b" && drift="$drift $b"; done
  [ -n "$drift" ] && printf '  WARN: rules mirror %s differs from ~/.kiro/steering:%s\n' "$(basename "$MIRROR")" "$drift"
fi

# 2-6 (JSON / frontmatter parsing)
python3 - "$K" "$C" <<'PY' || fail=1
import json, os, re, sys
K, C = sys.argv[1], sys.argv[2]
HOME = os.path.expanduser("~")
bad = False
def FAIL(m):
    global bad; bad = True; print("  FAIL: " + m)
def load(p):
    try: return json.load(open(p))
    except Exception: return {}

# 2. Model agent + engine
cli = load(f"{K}/settings/cli.json")
if cli.get("chat.defaultAgent") != "default":
    FAIL("Model chat.defaultAgent is not 'default' -> built-in kiro_default runs and NO CCB hooks fire")
elif cli.get("chat.agentEngine") != "v1":
    FAIL("Model chat.agentEngine is not v1 -> engines v2/v3 skip agentSpawn hooks")
else:
    print("  MODEL ok - default agent 'default' on engine v1 (hooks fire)")

# 3. same hook files in both agents
def real(cmd):
    p = os.path.expandvars(os.path.expanduser(cmd.split()[0])) if cmd else ""
    return os.path.realpath(p) if p else ""
kc = [h.get("command", "") for h in load(f"{K}/agents/default.json").get("hooks", {}).get("agentSpawn", [])]
cc = [h.get("command", "") for g in load(f"{C}/settings.json").get("hooks", {}).get("SessionStart", []) for h in g.get("hooks", [])]
kh = {real(c) for c in kc if not c.endswith("steering-loader-guard.sh")}   # Model-only config self-heal
ch = {real(c) for c in cc}
missing = sorted(os.path.basename(p) for p in kh | ch if not os.path.isfile(p))
need = {os.path.realpath(f"{K}/hooks/{n}") for n in ("ccb-project-context.sh", "ccb-parity-check.sh")}
if missing: FAIL("registered hook file(s) missing on disk: " + " ".join(missing))
if kh - ch: FAIL("hooks only in Model: " + " ".join(sorted(os.path.basename(p) for p in kh - ch)))
if ch - kh: FAIL("hooks only in Claude Code: " + " ".join(sorted(os.path.basename(p) for p in ch - kh)))
if not need <= (kh & ch): FAIL("ccb-project-context/ccb-parity-check not registered in both agents")
if not (missing or kh ^ ch) and need <= (kh & ch):
    print(f"  HOOKS ok - both agents register the same {len(kh)} session-start hooks")

# 4. CLAUDE.md imports every always-on steering file
steer = sorted(f for f in os.listdir(f"{K}/steering") if f.endswith(".md")) if os.path.isdir(f"{K}/steering") else []
try: md = open(f"{C}/CLAUDE.md").read()
except Exception: md = ""
mi = [f for f in steer if f"@~/.kiro/steering/{f}" not in md]
if mi: FAIL("~/.claude/CLAUDE.md does not import: " + " ".join(mi))
else: print(f"  CLAUDE ok - CLAUDE.md imports all {len(steer)} always-on steering files")

# 5. skills, same names
def fm_name(path):
    try:
        for ln in open(path).read().split("---")[1].splitlines():
            if ln.strip().startswith("name:"): return ln.split(":", 1)[1].strip()
    except Exception: pass
    return None
ks = sorted(d for d in os.listdir(f"{K}/skills") if os.path.isfile(f"{K}/skills/{d}/SKILL.md")) if os.path.isdir(f"{K}/skills") else []
ml = [s for s in ks if os.path.realpath(f"{C}/skills/{fm_name(f'{K}/skills/{s}/SKILL.md') or s}") != os.path.realpath(f"{K}/skills/{s}")]
if ml: FAIL("skills not linked into ~/.claude/skills under their frontmatter name: " + " ".join(ml))
else: print(f"  SKILLS ok - same {len(ks)} project skills, same names in both agents")

# 6. repo steering mirrored for Claude Code
repos, rbad = [], []
try: reg = open(f"{K}/steering/context-registry.md").read().splitlines()
except Exception: reg = []
for ln in reg:
    if not re.match(r"^\| *\[x\]", ln): continue
    cols = ln.split("|")
    if len(cols) < 6 or not cols[5].strip(): continue
    rp = cols[5].strip()
    full = rp if rp.startswith("/") else os.path.join(HOME, rp if rp.startswith("Projects/") else "Projects/" + rp)
    sd = os.path.join(full, ".kiro/steering")
    if not os.path.isdir(sd): continue
    want = sorted(f for f in os.listdir(sd) if f.endswith(".md")
                  and not re.search(r"inclusion:\s*(manual|fileMatch)", "".join(open(os.path.join(sd, f)).readlines()[:3]), re.I))
    try: have = sorted(l[len("@.kiro/steering/"):].strip() for l in open(os.path.join(full, "CLAUDE.local.md")) if l.startswith("@.kiro/steering/"))
    except Exception: have = []
    repos.append(os.path.basename(full))
    if have != want: rbad.append(os.path.basename(full))
if rbad: FAIL("repo steering not mirrored for Claude Code (CLAUDE.local.md stale/missing): " + " ".join(rbad))
else: print(f"  REPOS ok - {len(repos)} repos load the same .kiro/steering in full in both agents")
sys.exit(1 if bad else 0)
PY

if [ "$fail" -eq 0 ]; then printf '[ccb-parity] PASS - Model and Claude Code load identical CCB context (steering %s).\n' "$fp"
else printf '[ccb-parity] ISSUES ABOVE - the two agents may see different context this session.\n'; fi
exit 0
