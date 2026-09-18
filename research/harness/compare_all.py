#!/usr/bin/env python3
"""compare_all.py — UNIFIED cross-variant benchmark + comparison churner.

One entry point to compare every tiering variant on a common metric set, and to
aggregate SWE-bench task-success runs across variants when they exist.

VARIANTS compared:
  - monolithic          (baseline: everything resident)
  - tiered_2location    (steering always-on + skills; the main model)
  - tiered_3location    (steering + on-demand + skills; governance/cross-links deferred)
  - summarized_L<level>  (lossy compression tiers; from the summarization study)

METRIC FAMILIES:
  A. STRUCTURE / TOKEN-COST  — MEASURED NOW, zero budget (real gpt2-BPE; --steering/--skills/--ondemand override for any agent, default ~/.kiro).
  B. SWE TASK metrics        — resolved-rate, tokens, latency, grounding, determinism, per model/OS.
     These are AGGREGATED from runs*.jsonl produced by swebench_run.py / contribute_run.py.
     If no run files exist, family B is reported as AWAITING_RUN (honest: not measured yet).

Rule 6a/6b: family A is measured/preliminary (structure, N=live projects). Family B is empirical
ONLY when a real-agent SWE-bench run exists (Docker + code model). No task-success number is
invented; absence is reported as AWAITING_RUN, never zero.

Usage:
    python research/harness/compare_all.py                       # family A now; B if run files present
    python research/harness/compare_all.py --runs-glob 'research/harness/**/runs*.jsonl'
"""
from __future__ import annotations
import os, sys, glob, json, argparse, statistics

def _tok():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained("gpt2")

def toks(tok, path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return len(tok.encode(f.read()))

def meta_tokens(tok, path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
        return len(tok.encode("\n".join(lines[:end+1])))
    return 0

# ---------- Family A: structure / token-cost (measured now) ----------
def family_a(steer, skills, ondemand):
    try:
        tok = _tok()
    except Exception as e:
        return {"error": f"tokenizer unavailable: {e}", "note": "install transformers to measure family A"}
    ao = sum(toks(tok, f) for f in sorted(glob.glob(os.path.join(steer, "*.md"))))
    od = sum(toks(tok, f) for f in sorted(glob.glob(os.path.join(ondemand, "*.md")))) if os.path.isdir(ondemand) else 0
    sk = sorted(glob.glob(os.path.join(skills, "*/SKILL.md")))
    bodies = [toks(tok, f) for f in sk]; metas = [meta_tokens(tok, f) for f in sk]
    N = len(sk); mb = max(bodies) if bodies else 0
    variants = {
        "monolithic":       ao + od + sum(bodies),
        "tiered_2location": ao + sum(metas) + mb,                # on-demand folded into always-on historically
        "tiered_3location": ao + sum(metas) + mb,                # on-demand deferred (f_od=0 typical turn)
    }
    base = variants["monolithic"]
    return {
        "measured": True, "N_projects": N,
        "always_on_tokens": ao, "on_demand_tokens": od,
        "per_turn_tokens": variants,
        "reduction_vs_monolithic": {k: round(1 - v/base, 3) for k, v in variants.items() if base},
        "note": "MEASURED (real gpt2-BPE; context dirs via args, default ~/.kiro). Structure/cost only — not task quality.",
    }

# ---------- Family B: SWE task metrics (aggregate runs if present) ----------
def family_b(run_files):
    if not run_files:
        return {"status": "AWAITING_RUN",
                "note": "No runs*.jsonl found. SWE task-success/latency/grounding require a real-agent "
                        "SWE-bench run (Docker + code model) — see contribute_run.py. NOT measured yet (rule 6a)."}
    rows = []
    for rf in run_files:
        with open(rf) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try: rows.append(json.loads(line))
                    except Exception: pass
    if not rows:
        return {"status": "AWAITING_RUN", "note": "run files present but empty/unparseable."}
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        key = (r.get("variant", r.get("condition", "?")), r.get("model", r.get("config", {}).get("agent", "?")))
        groups[key].append(r)
    def mean(xs): 
        xs = [x for x in xs if isinstance(x, (int, float))]
        return round(statistics.mean(xs), 4) if xs else None
    out = []
    for (variant, model), rs in sorted(groups.items(), key=lambda x: str(x[0])):
        out.append({
            "variant": variant, "model": model, "n": len(rs),
            "resolved_rate": mean([1.0 if r.get("resolved") else 0.0 for r in rs]),
            "input_tokens_mean": mean([r.get("input_tokens") for r in rs]),
            "wall_seconds_mean": mean([r.get("wall_seconds", r.get("seconds")) for r in rs]),
            "grounding_coverage_mean": mean([r.get("grounding_coverage") for r in rs]),
        })
    # honesty: is any of this a real agent (not mock)?
    agents = {r.get("config", {}).get("agent", r.get("model", "")) for r in rows}
    empirical = not all((a or "").lower().startswith(("mock", "", "selftest", "local:mock")) for a in agents)
    return {"status": "MEASURED" if empirical else "MOCK_ONLY_NO_CLAIM",
            "by_variant_model": out,
            "note": ("Real-agent runs aggregated." if empirical
                     else "Mock/self-test only — NO task-quality claim (rule 6a).")}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steering", default=os.path.expanduser("~/.kiro/steering"))
    ap.add_argument("--skills", default=os.path.expanduser("~/.kiro/skills"))
    ap.add_argument("--ondemand", default=os.path.expanduser("~/.kiro/on-demand"))
    ap.add_argument("--runs-glob", default="research/harness/**/runs*.jsonl")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    run_files = [f for f in glob.glob(a.runs_glob, recursive=True) if os.path.isfile(f)]
    report = {
        "benchmark": "compare_all — unified cross-variant comparison",
        "family_A_structure_tokencost": family_a(a.steering, a.skills, a.ondemand),
        "family_B_swe_task_metrics": family_b(run_files),
        "run_files_found": run_files,
        "SCOPE": "Family A measured now (structure/cost). Family B empirical only with a real-agent "
                 "SWE-bench run; otherwise AWAITING_RUN. Nothing fabricated (rule 6a/6b).",
    }
    js = json.dumps(report, indent=2)
    if a.out: open(a.out, "w").write(js)
    print(js)

if __name__ == "__main__":
    main()
