"""Token-accurate benchmark: monolithic (all context always-on) vs tiered
(always-on + on-demand skill bodies loaded only when invoked).

Uses a real BPE tokenizer (GPT-2 via transformers) for exact token counts,
not byte estimates. Measures the author's LIVE deployment for N=4, then
projects with the closed-form model using measured per-project averages.

Run: <venv>/bin/python benchmark.py [steering_dir] [skills_dir]
Rule #2: real measured tokens.
"""
import os, sys, glob, json

STEER = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.kiro/steering")
SKILLS = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/.kiro/skills")

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
print(json.dumps(result, indent=2))
