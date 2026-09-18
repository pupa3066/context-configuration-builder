"""Token-accurate benchmark — 3-LOCATION variant (this branch).

Extends the 2-location model to the live structure:
  always-on  = ~/.kiro/steering/*.md            (every turn)
  on-demand  = ~/.kiro/on-demand/*.md            (loaded ONLY when a task triggers it)
  per-project= ~/.kiro/skills/*/SKILL.md         (metadata always; body on demand)

Uses a real BPE tokenizer (GPT-2). The on-demand tier (governance appendix, cross-links)
is charged at an assumed trigger frequency `f_od` (default 0.0 = not on a typical turn),
so the every-turn baseline reflects the lean steering tier after the self-tiering split.

Run: <venv>/bin/python benchmark.py [steering_dir] [skills_dir] [ondemand_dir] [f_od]
Rule #2: real measured tokens.
"""
import os, sys, glob, json

STEER  = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.kiro/steering")
SKILLS = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/.kiro/skills")
ONDEMAND = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser("~/.kiro/on-demand")
F_OD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0  # on-demand trigger frequency per turn

from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("gpt2")  # deterministic BPE, offline-cached

def toks(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return len(tok.encode(f.read()))

# Tier 1: always-on = all steering files
steer_files = sorted(glob.glob(os.path.join(STEER, "*.md")))
always_on = sum(toks(f) for f in steer_files)

# Tier 2: on-demand = files loaded only when triggered (governance, cross-links)
ondemand_files = sorted(glob.glob(os.path.join(ONDEMAND, "*.md")))
on_demand_total = sum(toks(f) for f in ondemand_files)

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

# Per-turn cost. 3-location model:
#   monolithic = always_on + on_demand(always) + all bodies   (naive: everything resident)
#   tiered     = always_on + f_od*on_demand + all metadata + ONE active body
mono_n = always_on + on_demand_total + sum(bodies)
tier_n = always_on + round(F_OD * on_demand_total) + sum(metas) + (max(bodies) if bodies else 0)
reduction_measured = 1 - tier_n/mono_n if mono_n else 0

def project(n):
    mono = always_on + on_demand_total + mean_body*n
    tier = always_on + round(F_OD * on_demand_total) + mean_meta*n + mean_body
    return mono, tier, (1 - tier/mono if mono else 0)

result = {
    "tokenizer": "gpt2-bpe (real)",
    "structure": "3-location (steering always-on + on-demand triggered + skills per-project)",
    "always_on_tokens": always_on,
    "on_demand_tokens": on_demand_total,
    "on_demand_trigger_freq": F_OD,
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
print(json.dumps(result, indent=2))
