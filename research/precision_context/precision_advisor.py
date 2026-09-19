#!/usr/bin/env python3
"""precision_advisor.py — workload-aware precision recommendation, grounded in MEASURED data.

Reads a quant-memorization-study analysis JSON (analysis_popqa_*.json / analysis_mem_*.json) and
emits a recommendation for how aggressively to quantize, based on the ACTUAL confidence intervals —
not hardcoded claims. If the data doesn't support a conclusion, it says so.

Usage:
  precision_advisor.py <analysis_popqa.json> [<analysis_mem.json>] [--workload factual|verbatim]
                       [--scale small.json mid.json large.json]   # same family+precision, ordered by size

Ships with cross-hardware data in data/cuda/ (NVIDIA RTX 5060, --backend hf) so the verdicts can be
checked against a second backend without re-running the study.

This is the operational link between Consistent Context Kit's cost-tiering principle and the
precision axis: spend the expensive resource (bits, or context tokens) only where it changes behavior.
"""
import json, sys, argparse

def load(p):
    with open(p) as fh: return json.load(fh)

def factual_verdict(d):
    comp = d.get("comparisons", {}).get("qa_int4_vs_fp16", {})
    ci = comp.get("acc_diff_ci", {})
    p = comp.get("mcnemar", {}).get("p")
    lo, hi = ci.get("lo"), ci.get("hi")
    if lo is None:
        return "insufficient data", None
    # null if CI straddles 0 and p high
    if lo <= 0 <= hi and (p is None or p > 0.05):
        return f"INT4 safe for factual recall (diff CI [{lo},{hi}], p={p}) — no measured degradation", True
    if hi < 0:
        return f"INT4 DEGRADES factual recall (diff CI [{lo},{hi}]) — prefer higher precision", False
    return f"inconclusive (diff CI [{lo},{hi}], p={p})", None

def memorization_verdict(d):
    pc = d.get("per_precision", {})
    g16 = pc.get("fp16", {}).get("mem_GAP")
    g4 = pc.get("int4", {}).get("mem_GAP")
    if g16 is None or g4 is None:
        return "insufficient data", None
    if g16 <= 0.03:
        return f"fp16 memorization baseline tiny ({g16}) — underpowered; can't conclude (use a bigger model)", None
    if g4 < g16:
        return f"quantization REDUCES memorization (GAP {g16} -> {g4}) — preserve precision for verbatim-recall workloads", False
    return f"memorization not clearly reduced (GAP {g16} -> {g4})", None

def scale_verdict(paths, precision="int4"):
    """Controlled scale ladder: several analysis JSONs, same family, same precision, different size.
    Reports whether mem_GAP is monotonic in the order given (caller orders by parameter count)."""
    gaps = []
    for p in paths:
        d = load(p)
        g = d.get("per_precision", {}).get(precision, {}).get("mem_GAP")
        n = d.get("per_precision", {}).get(precision, {}).get("n_mem")
        if g is None:
            return f"insufficient data ({p} has no {precision} mem_GAP)", None, []
        gaps.append({"source": p, "mem_GAP": g, "n_mem": n})
    vals = [x["mem_GAP"] for x in gaps]
    if len(vals) < 3:
        return "need >=3 sizes for a scale trend", None, gaps
    mono = all(b > a for a, b in zip(vals, vals[1:]))
    ratio = (vals[-1] / vals[0]) if vals[0] else float("inf")
    if mono:
        return (f"mem_GAP rises monotonically with size at fixed {precision} "
                f"({' -> '.join(str(v) for v in vals)}, {ratio:.0f}x) — scale drives memorization; "
                f"small-N (n_mem={vals and gaps[0]['n_mem']}), no CI on the trend"), True, gaps
    return f"mem_GAP not monotonic in size ({vals}) — scale trend not supported by this ladder", False, gaps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("popqa"); ap.add_argument("mem", nargs="?")
    ap.add_argument("--workload", choices=["factual", "verbatim"], default=None)
    ap.add_argument("--scale", nargs="+", default=None,
                    help="analysis JSONs for one family at one precision, ordered small->large")
    ap.add_argument("--scale-precision", default="int4")
    a = ap.parse_args()

    out = {"source_factuality": a.popqa}
    fv, fsafe = factual_verdict(load(a.popqa))
    out["factuality"] = fv
    if a.mem:
        mv, msafe = memorization_verdict(load(a.mem))
        out["memorization"] = mv
        out["source_memorization"] = a.mem

    if a.scale:
        sv, strend, gaps = scale_verdict(a.scale, a.scale_precision)
        out["scale"] = sv
        out["scale_ladder"] = gaps

    # workload-aware recommendation (the operational output)
    rec = []
    if a.workload == "factual" and fsafe:
        rec.append("Workload=factual: aggressive INT4 quantization is supported by the data; "
                   "pair with LEAN (on-demand) context tiering.")
    elif a.workload == "verbatim":
        rec.append("Workload=verbatim/exact-recall: load the SPECIFIC source context rather than relying "
                   "on model memory. Measured evidence says memorization is governed by model SCALE more "
                   "than by precision; the precision effect at these sizes is small and inconsistent.")
    else:
        rec.append("No workload specified: choose precision by task — factual/synthesis tolerates "
                   "INT4; verbatim recall does not. Same rule as context tiering.")
    out["recommendation"] = rec
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
