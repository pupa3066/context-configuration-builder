"""Token-accurate benchmark: monolithic (all context always-on) vs tiered
(always-on + on-demand skill bodies loaded only when invoked).

Uses a real BPE tokenizer (GPT-2 via transformers) for exact token counts,
not byte estimates.

AGENT-INDEPENDENT: pass --context-root (or CCK_CONTEXT_ROOT env) to point at ANY agent's
context directory (must contain steering/ and skills/ subdirs). Defaults to ~/.kiro (Kiro),
but a Claude Code / Cursor / generic user points it at their own root. So the measurement,
like the core+adapters, is not tied to one agent.

--agent-baseline TOKENS: fixed per-turn overhead the agent always loads (e.g. a system
  prompt that cannot be disabled). Added to both monolithic and tiered totals.
  Without it: output is CCB-marginal only (correct for Kiro with override on; understates
  total context cost for agents like Claude Code that have no disable knob).
  With it: output adds ccb_marginal_reduction (CCB-controlled savings, comparable across
  agents) and total_reduction (honest total including the fixed overhead).

Run:
  python benchmark.py                                         # default ~/.kiro
  python benchmark.py --context-root /path/to/context         # any agent's deployment
  python benchmark.py --agent-baseline 4096                   # with fixed agent overhead
  python benchmark.py <steering_dir> <skills_dir>             # explicit dirs (back-compat)
Rule #2: real measured tokens.
"""
import os, sys, glob, json, argparse

def _parse_args():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--context-root", default=os.environ.get("CCK_CONTEXT_ROOT", os.path.expanduser("~/.kiro")))
    ap.add_argument("--agent-baseline", type=int, default=0, metavar="TOKENS",
                    help="Fixed per-turn token overhead added to both mono and tiered totals.")
    ap.add_argument("pos", nargs="*")
    return ap.parse_known_args()[0]

_args = _parse_args()
if len(_args.pos) >= 2:                        # explicit steering + skills dirs (back-compat)
    STEER, SKILLS = _args.pos[0], _args.pos[1]
else:
    root = _args.context_root
    STEER = os.path.join(root, "steering")
    SKILLS = os.path.join(root, "skills")
BASELINE = _args.agent_baseline

from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("gpt2")  # deterministic BPE, offline-cached

def toks(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return len(tok.encode(f.read()))

# Always-on tier = all steering files
steer_files = sorted(glob.glob(os.path.join(STEER, "*.md")))
always_on = sum(toks(f) for f in steer_files)

# Per-project skills: body (full file) and metadata (frontmatter block only)
def meta_tokens(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
        return len(tok.encode("\n".join(lines[:end+1])))
    return 0

skill_files = sorted(glob.glob(os.path.join(SKILLS, "*/SKILL.md")))
bodies = [toks(f) for f in skill_files]
metas = [meta_tokens(f) for f in skill_files]
N = len(skill_files)
mean_body = sum(bodies)//N if N else 0
mean_meta = sum(metas)//N if N else 0

# Per-turn cost (avg over a session where any ONE project is active):
# monolithic = always_on + all bodies (everything always loaded)
# tiered     = always_on + all metadata + ONE body (the active project)
mono_n = always_on + sum(bodies)
tier_n = always_on + sum(metas) + (max(bodies) if bodies else 0)
reduction_measured = 1 - tier_n/mono_n if mono_n else 0

def project(n):
    mono = always_on + mean_body*n
    tier = always_on + mean_meta*n + mean_body  # one active body
    return mono, tier, (1 - tier/mono if mono else 0)

result = {
    "tokenizer": "gpt2-bpe (real)",
    "always_on_tokens": always_on,
    "n_projects_measured": N,
    "mean_body_tokens": mean_body,
    "mean_meta_tokens": mean_meta,
    "measured_N": {
        "monolithic_tokens_per_turn": mono_n,
        "tiered_tokens_per_turn": tier_n,
        "reduction": round(reduction_measured, 3),
    },
    "projected": {str(n): {"mono": project(n)[0], "tiered": project(n)[1],
                            "reduction": round(project(n)[2], 3)} for n in (10, 25, 50, 100)},
    "asymptote_reduction": round(1 - mean_meta/mean_body, 3) if mean_body else 0,
}

if BASELINE > 0:
    # ccb_marginal: savings on the CCB-controlled portion only (comparable across agents).
    # total: savings on total context including the fixed agent overhead (honest for agents
    # that cannot disable their system prompt, e.g. Claude Code).
    result["agent_baseline_tokens"] = BASELINE
    result["note_baseline"] = (
        "[MEASURED] ccb_marginal excludes agent baseline (comparable to Kiro with override on). "
        "total includes it (honest total-context figure for agents with no disable knob)."
    )
    mn = result["measured_N"]
    mn["ccb_marginal_reduction"] = mn.pop("reduction")
    mn["monolithic_tokens_per_turn_total"] = mono_n + BASELINE
    mn["tiered_tokens_per_turn_total"] = tier_n + BASELINE
    mn["total_reduction"] = round(1 - (tier_n + BASELINE) / (mono_n + BASELINE), 3)

    for k, v in result["projected"].items():
        m, t, _ = project(int(k))
        v["ccb_marginal_reduction"] = v.pop("reduction")
        v["mono_total"] = m + BASELINE
        v["tiered_total"] = t + BASELINE
        v["total_reduction"] = round(1 - (t + BASELINE) / (m + BASELINE), 3)

    result["asymptote_ccb_marginal"] = result.pop("asymptote_reduction")
    # Asymptote with baseline: as N->inf, mono->inf, tiered->baseline+always_on+mean_body
    # reduction approaches 1 - mean_meta/mean_body still on CCB portion, but total asymptote
    # is bounded by how large baseline is relative to the growing mono cost.
    result["asymptote_total_note"] = (
        "total asymptote converges to ccb_marginal asymptote as N grows "
        "(baseline becomes negligible vs N*mean_body); honest only at measured N."
    )

print(json.dumps(result, indent=2))
