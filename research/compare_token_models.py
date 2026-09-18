#!/usr/bin/env python3
"""compare_token_models.py — cross-model token-cost comparison (contributor-runnable).

Measures the live ~/.kiro tier structure with a real gpt2-BPE tokenizer and reports every
tiering token-model side by side, so a contributor can reproduce the comparison on their own
deployment and add a row.

Token-models compared (all measured from the same live tiers):
  monolithic         : everything resident every turn (baseline)
  tiered_2location   : steering always-on + skills (on-demand folded into always-on historically)
  tiered_3location   : steering always-on + separate on-demand tier + skills
  rule_tiering       : 3location + governance/formatting RULE detail also moved to on-demand (stub kept)

The difference between the last three is WHAT sits in always-on vs on-demand; this script measures
the real files so the numbers are not hand-entered.

Rule 2/6a: real measured tokens; structure/cost only (NOT task quality — that needs a real-agent
SWE-bench run, see research/harness/contribute_run.py). Reproduce:
    <venv-with-transformers>/bin/python research/compare_token_models.py
"""
from __future__ import annotations
import os, glob, json, sys

try:
    from transformers import AutoTokenizer
except Exception:
    print("needs transformers: pip install transformers", file=sys.stderr); sys.exit(2)

tok = AutoTokenizer.from_pretrained("gpt2")
def T(p): return len(tok.encode(open(p, encoding="utf-8", errors="ignore").read()))

STEER = os.path.expanduser("~/.kiro/steering")
OND   = os.path.expanduser("~/.kiro/on-demand")
SK    = os.path.expanduser("~/.kiro/skills")

steer = sum(T(f) for f in glob.glob(STEER + "/*.md"))
ondemand = sum(T(f) for f in glob.glob(OND + "/*.md")) if os.path.isdir(OND) else 0
sk = sorted(glob.glob(SK + "/*/SKILL.md"))
bodies = [T(f) for f in sk]
metas = []
for f in sk:
    ls = open(f, encoding="utf-8", errors="ignore").read().splitlines(); m = 0
    if ls and ls[0].strip() == "---":
        e = next((i for i in range(1, len(ls)) if ls[i].strip() == "---"), 0)
        m = len(tok.encode("\n".join(ls[:e+1])))
    metas.append(m)
N = len(sk); max_body = max(bodies) if bodies else 0; sum_bodies = sum(bodies); sum_metas = sum(metas)

# per-turn cost per model (one active project; on-demand loaded only when triggered => f_od=0 typical turn)
models = {
    "monolithic":       steer + ondemand + sum_bodies,
    "tiered_2location": (steer + ondemand) + sum_metas + max_body,   # on-demand historically folded into always-on
    "tiered_3location": steer + sum_metas + max_body,                # on-demand deferred
    "rule_tiering":     steer + sum_metas + max_body,                # rule detail also deferred (steer already lean)
}
base = models["monolithic"]
report = {
    "tokenizer": "gpt2-bpe (real)",
    "measured_live": {"N_projects": N, "always_on_steering": steer, "on_demand": ondemand,
                      "mean_body": sum_bodies//N if N else 0, "mean_meta": sum_metas//N if N else 0,
                      "max_body": max_body},
    "per_turn_tokens": models,
    "reduction_vs_monolithic": {k: round(1 - v/base, 3) for k, v in models.items() if base},
    "scope": "MEASURED structure/cost (real gpt2-BPE). NOT task quality; that needs a real-agent "
             "SWE-bench run (research/harness/contribute_run.py). f_od=0 (typical turn; on-demand not loaded).",
    "contributor_note": "Run on your deployment to add a row; report N_projects, always_on, on_demand, "
                        "and per_turn reduction. Task-quality contributions: use contribute_run.py.",
}
print(json.dumps(report, indent=2))
