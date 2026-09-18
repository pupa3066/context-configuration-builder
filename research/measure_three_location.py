#!/usr/bin/env python3
"""measure_three_location.py — reproduce the 3-location tiering measurement.

Measures the live ~/.kiro token structure across THREE tiers (steering always-on,
on-demand triggered, per-project skills) with a real gpt2-BPE tokenizer, and writes
three_location_data.json. This is the supporting data generator for
research/THREE_LOCATION_TIERING.md.

Requires a transformers env (gpt2 tokenizer). Rule 2: real tokens, no estimate.
Run: <venv-with-transformers>/bin/python research/measure_three_location.py
"""
import glob, os, json
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("gpt2")
def t(p): return len(tok.encode(open(p, encoding="utf-8", errors="ignore").read()))

S  = os.path.expanduser("~/.kiro/steering")
OD = os.path.expanduser("~/.kiro/on-demand")
SK = os.path.expanduser("~/.kiro/skills")

steer = {os.path.basename(f): t(f) for f in sorted(glob.glob(S + "/*.md"))}
od    = {os.path.basename(f): t(f) for f in sorted(glob.glob(OD + "/*.md"))}
sk = sorted(glob.glob(SK + "/*/SKILL.md"))
bodies, metas = [], []
for f in sk:
    b = t(f); ls = open(f).read().splitlines(); m = 0
    if ls and ls[0].strip() == "---":
        e = next((i for i in range(1, len(ls)) if ls[i].strip() == "---"), 0)
        m = len(tok.encode("\n".join(ls[:e + 1])))
    bodies.append(b); metas.append(m)
N = len(sk); ao = sum(steer.values())
mono = ao + sum(bodies); tier = ao + sum(metas) + (max(bodies) if bodies else 0)

out = {
    "tokenizer": "gpt2-bpe (real)",
    "structure": "3-LOCATION: steering (always-on) + on-demand (triggered) + skills (per-project)",
    "measured_live_N": N,
    "tiers": {
        "always_on_steering": {"files": steer, "total": ao},
        "on_demand": {"files": od, "total": sum(od.values()),
                      "note": "loaded only on trigger (governance on publish/merge; cross-links on cross-project)"},
        "project_skills": {"N": N, "mean_body": sum(bodies)//N if N else 0,
                           "mean_meta": sum(metas)//N if N else 0, "max_body": max(bodies) if bodies else 0},
    },
    "per_turn_tokens": {"monolithic": mono, "tiered": tier,
                        "reduction": round(1 - tier/mono, 3) if mono else 0},
}
path = os.path.join(os.path.dirname(__file__), "three_location_data.json")
open(path, "w").write(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
print(f"\nwrote {path}")
