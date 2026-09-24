#!/usr/bin/env python3
"""run_fidelity.py  -  run FIDELITY-AXIS designs against the committed sample corpus.

DIFFERENT AXIS from run_designs.py. This measures GROUNDING RETENTION (fraction of task-needed facts
still present after deferral/compression) vs TOKEN SAVING. It answers "does the design lose the facts a
task needs?", not "how many always-on tokens" (that is run_designs.py, token-cost axis).

Per design: NAME, DEFINITION, CLAIM, MEASURED (token_saving, grounding_retention), and CONFIRMED /
SAFE (retention == 1.0). Uses the summarize() operator (research/harness/summarized_tier.py); level 0.0
= lossless (F1). Reproducible on benchmark/sample/skills content.

Rule 6a: MEASURED fidelity (grounding retention) via keyword fact-detection; NOT task quality.
LABEL DISCIPLINE: fidelity numbers (fraction retained) are NOT comparable to token-cost numbers
(tokens). Report each on its own axis; never put them in one column.
"""
from __future__ import annotations
import os, glob, json, re, sys, argparse, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "research", "harness"))
from summarized_tier import summarize, token_estimate  # noqa: E402

_T = re.compile(r"[A-Za-z_][A-Za-z0-9_\.]{3,}")

def read(p): return open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""

def retention(text, needed):
    if not needed: return None
    syms = set(_T.findall(text))
    return round(len([f for f in needed if f in syms]) / len(needed), 4)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="all")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(HERE, "designs_fidelity.json")))
    base = os.path.join(ROOT, cfg["sample_root"])
    skills = sorted(glob.glob(os.path.join(base, "skills", "*", "SKILL.md")))
    # needed facts per skill = its identifier-like tokens (what a task on that project would need)
    corpus = {os.path.basename(os.path.dirname(f)): read(f) for f in skills}
    needed = {k: set(list(set(_T.findall(v)))[:10]) for k, v in corpus.items()}  # sample fact set/project

    names = list(cfg["designs"]) if a.design == "all" else [a.design]
    rows = []
    for name in names:
        d = cfg["designs"][name]; lv = d["compression_level"]
        rets, saves = [], []
        for k, body in corpus.items():
            summ = summarize(body, lv)
            rets.append(retention(summ, needed[k]))
            saves.append(1 - token_estimate(summ) / max(1, token_estimate(body)))
        mret = round(statistics.mean([r for r in rets if r is not None]), 4)
        msave = round(statistics.mean(saves), 4)
        rows.append((name, d, mret, msave, mret >= 1.0))

    print(f"AXIS: {cfg['axis']}")
    print(f"(token-cost axis is separate: {cfg['compare_to_axes']['token_cost']})")
    for name, d, mret, msave, safe in rows:
        print(f"\n=== DESIGN: {name}  [FIDELITY AXIS] ===")
        print(f"  Definition: {d['definition']}")
        print(f"  Claim:      {d['claim']}")
        print(f"  Measured:   grounding_retention={mret}  token_saving={msave}  safe(retention==1.0)={safe}")

    if a.design == "all":
        print("\n=== FIDELITY COMPARISON (retention vs saving; NOT comparable to token-cost tokens) ===")
        print(f"{'design':24s} {'level':>6} {'retention':>10} {'token_saving':>13} {'safe':>6}")
        for name, d, mret, msave, safe in rows:
            print(f"{name:24s} {d['compression_level']:6.2f} {mret:10.4f} {msave:13.4f} {str(safe):>6}")
        safe = [r for r in rows if r[4]]
        best = max(safe, key=lambda r: r[3]) if safe else None  # most token saving among retention==1.0
        print(f"\nBEST SAFE FIDELITY DESIGN: {best[0] if best else 'none'} "
              f"(max token saving while retention == 1.0). Past the safe frontier, retention drops (the cliff).")
    print("\nScope: MEASURED grounding retention (keyword fact-detection) vs token saving. NOT task quality. "
          "Fidelity units (fraction retained) are NOT comparable to token-cost units (tokens).")

if __name__ == "__main__":
    main()
