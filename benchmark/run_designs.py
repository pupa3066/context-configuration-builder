#!/usr/bin/env python3
"""run_designs.py  -  run any/all named tiering designs against the committed sample corpus.

A contributor runs this and, for each design, sees: the NAME, the DEFINITION, the CLAIM, the MEASURED
result (real gpt2-BPE on benchmark/sample/), and whether the claim is CONFIRMED. This is what tells a
contributor exactly what they are testing and confirming, independent of git branches.

Usage:
    python benchmark/run_designs.py                 # all designs, comparison table
    python benchmark/run_designs.py --design L2_3location
Reproducible: measures the committed sample corpus, NOT anyone's private ~/.kiro.
Rule 6a: MEASURED structure/cost + rule-firing integrity; NOT task quality.
"""
from __future__ import annotations
import os, glob, json, re, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

try:
    from transformers import AutoTokenizer
except Exception:
    print("needs transformers: pip install transformers", file=sys.stderr); sys.exit(2)
tok = AutoTokenizer.from_pretrained("gpt2")
def T(text): return len(tok.encode(text))

def read(p): return open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""

def expand(patterns, base):
    out = []
    for pat in patterns:
        out += sorted(glob.glob(os.path.join(base, pat)))
    return [f for f in out if os.path.isfile(f)]

def meta_tokens(path):
    ls = read(path).splitlines()
    if ls and ls[0].strip() == "---":
        e = next((i for i in range(1, len(ls)) if ls[i].strip() == "---"), 0)
        return T("\n".join(ls[:e+1]))
    return 0

def firing_integrity(always_on_text, must_fire):
    present = [r for r in must_fire if re.search(re.escape(r), always_on_text)]
    return len(present), len(must_fire), [r for r in must_fire if r not in present]

def measure(design, sample_root, must_fire):
    base = os.path.join(ROOT, sample_root)
    ao_files = expand(design["always_on"], base)
    ao_text = "".join(read(f) for f in ao_files)
    ao = T(ao_text)
    skills = sorted(glob.glob(os.path.join(base, "skills", "*", "SKILL.md")))
    bodies = [T(read(f)) for f in skills]
    metas = [meta_tokens(f) for f in skills]
    if design.get("load_all_project_bodies"):
        per_turn = ao + sum(bodies)
    else:
        per_turn = ao + sum(metas) + (max(bodies) if bodies else 0)
    present, total, missing = firing_integrity(ao_text, must_fire)
    return {
        "always_on_tokens": ao,
        "per_turn_tokens": per_turn,
        "firing_integrity": f"{present}/{total}",
        "rules_not_firing": missing,
        "safe": present == total,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="all")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(HERE, "designs.json")))
    must = cfg["must_fire_rules"]; root = cfg["sample_root"]
    names = list(cfg["designs"]) if a.design == "all" else [a.design]

    rows = []
    for name in names:
        d = cfg["designs"][name]
        m = measure(d, root, must)
        rows.append((name, d, m))

    for name, d, m in rows:
        print(f"\n=== DESIGN: {name} ===")
        print(f"  Definition: {d['definition']}")
        print(f"  Claim:      {d['claim']}")
        print(f"  Measured:   always_on={m['always_on_tokens']} per_turn={m['per_turn_tokens']} "
              f"firing={m['firing_integrity']} safe={m['safe']}")
        if m["rules_not_firing"]:
            print(f"  Rules NOT firing: {m['rules_not_firing']}")

    if a.design == "all":
        print("\n=== COMPARISON (all designs, same sample corpus) ===")
        base = rows[0][2]["per_turn_tokens"]
        print(f"{'design':28s} {'per_turn':>9} {'reduction':>10} {'firing':>8} {'safe':>6}")
        for name, d, m in rows:
            red = round(1 - m["per_turn_tokens"]/base, 3) if base else 0
            print(f"{name:28s} {m['per_turn_tokens']:9d} {red:10.3f} {m['firing_integrity']:>8} {str(m['safe']):>6}")
        safe = [r for r in rows if r[2]["safe"]]
        best = min(safe, key=lambda r: r[2]["per_turn_tokens"]) if safe else None
        print(f"\nBEST SAFE DESIGN: {best[0] if best else 'none'} "
              f"(lowest per-turn tokens with full firing integrity)")
    print("\nScope: MEASURED structure/cost + firing integrity on the sample corpus. NOT task quality.")

if __name__ == "__main__":
    main()
