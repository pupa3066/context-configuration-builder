"""analysis.py — compute all study metrics from harness JSONL logs.

Implements the statistics specified in RESEARCH_PLAN.md:
- per-condition resolved rate + token cost (mean, paired)
- McNemar's test for paired binary success (C2 vs C1, C3 vs C1)
- bootstrap CIs for rate differences
- non-inferiority test (is tiered NOT worse than monolithic by margin delta?)
- Pareto frontier (resolved rate vs tokens)

Pure-Python (no scipy needed). Reads runs.jsonl; writes analysis.json.
Usage: python analysis.py [runs.jsonl] [--delta 0.02] [--alpha 0.05]

NOTE: This computes REAL statistics on WHATEVER data you feed it. On mock data
the numbers are meaningless (mock agent is rigged). A scientific conclusion
requires real-agent run data (see STATUS.md).
"""
from __future__ import annotations
import json, sys, math, random
from collections import defaultdict

def load(path):
    return [json.loads(l) for l in open(path) if l.strip()]

def by_condition(rows):
    d = defaultdict(list)
    for r in rows:
        d[r["condition"]].append(r)
    return d

def paired(rows_a, rows_b):
    """Align two conditions by task_id."""
    a = {r["task_id"]: r for r in rows_a}
    b = {r["task_id"]: r for r in rows_b}
    keys = sorted(set(a) & set(b))
    return [(a[k], b[k]) for k in keys]

def mcnemar(pairs, key="resolved"):
    """Paired binary test. Returns (b, c, statistic, approx_p)."""
    b = c = 0  # b: a solved, b didn't; c: b solved, a didn't
    for ra, rb in pairs:
        xa, xb = int(ra[key]), int(rb[key])
        if xa == 1 and xb == 0: b += 1
        elif xa == 0 and xb == 1: c += 1
    n = b + c
    if n == 0:
        return b, c, 0.0, 1.0
    # continuity-corrected chi-square, 1 dof
    chi2 = (abs(b - c) - 1) ** 2 / n
    # survival of chi2 with 1 dof = erfc(sqrt(chi2/2))
    p = math.erfc(math.sqrt(chi2 / 2))
    return b, c, chi2, p

def rate(rows, key="resolved"):
    return sum(int(r[key]) for r in rows) / len(rows) if rows else 0.0

def bootstrap_diff_ci(pairs, key="resolved", n_boot=5000, alpha=0.05, seed=0):
    """Bootstrap CI for paired rate difference (a - b)."""
    rng = random.Random(seed)
    diffs = []
    m = len(pairs)
    if m == 0:
        return (0.0, 0.0, 0.0)
    base = sum(int(a[key]) - int(b[key]) for a, b in pairs) / m
    for _ in range(n_boot):
        s = [pairs[rng.randrange(m)] for _ in range(m)]
        diffs.append(sum(int(a[key]) - int(b[key]) for a, b in s) / m)
    diffs.sort()
    lo = diffs[int((alpha / 2) * n_boot)]
    hi = diffs[int((1 - alpha / 2) * n_boot)]
    return (round(base, 4), round(lo, 4), round(hi, 4))

def non_inferiority(pairs, delta, key="resolved", alpha=0.05):
    """Is (tiered - monolithic) >= -delta? Non-inferior if lower CI bound > -delta."""
    base, lo, hi = bootstrap_diff_ci(pairs, key=key, alpha=alpha)
    return {"diff": base, "ci_low": lo, "ci_high": hi, "delta": -delta,
            "non_inferior": lo > -delta}

def mean_tokens(rows):
    return sum(r["input_tokens"] + r["output_tokens"] for r in rows) / len(rows) if rows else 0.0

def pareto(cond_stats):
    """Points (tokens, rate); mark Pareto-optimal (low tokens, high rate)."""
    pts = [(c, s["mean_tokens"], s["resolved_rate"]) for c, s in cond_stats.items()]
    optimal = []
    for c, tk, rt in pts:
        dominated = any((tk2 <= tk and rt2 >= rt and (tk2 < tk or rt2 > rt))
                        for c2, tk2, rt2 in pts if c2 != c)
        if not dominated:
            optimal.append(c)
    return sorted(optimal)

def main():
    path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "research/harness/runs.jsonl"
    delta = 0.02; alpha = 0.05
    for i, a in enumerate(sys.argv):
        if a == "--delta": delta = float(sys.argv[i+1])
        if a == "--alpha": alpha = float(sys.argv[i+1])

    rows = load(path)
    bc = by_condition(rows)
    cond_stats = {c: {"n": len(rs), "resolved_rate": round(rate(rs), 4),
                      "mean_tokens": round(mean_tokens(rs), 1)} for c, rs in bc.items()}

    out = {"data_source": path, "n_rows": len(rows), "delta": delta, "alpha": alpha,
           "per_condition": cond_stats, "comparisons": {}}

    mono = "C1_monolithic"
    for tiered in ("C2_tiered_manual", "C3_tiered_auto"):
        if mono in bc and tiered in bc:
            pr = paired(bc[tiered], bc[mono])  # (tiered, monolithic)
            b, c, chi2, p = mcnemar(pr)
            out["comparisons"][f"{tiered}_vs_{mono}"] = {
                "mcnemar": {"b": b, "c": c, "chi2": round(chi2, 4), "p": round(p, 4)},
                "rate_diff_ci": dict(zip(("diff", "ci_low", "ci_high"), bootstrap_diff_ci(pr, alpha=alpha))),
                "non_inferiority": non_inferiority(pr, delta, alpha=alpha),
                "token_reduction_vs_monolithic": round(
                    1 - cond_stats[tiered]["mean_tokens"] / cond_stats[mono]["mean_tokens"], 4)
                    if cond_stats[mono]["mean_tokens"] else None,
            }
    out["pareto_optimal_conditions"] = pareto(cond_stats)

    # Verdict logic (structural — applies to whatever data): "better" = non-inferior quality AND lower tokens
    verdicts = {}
    for k, comp in out["comparisons"].items():
        ni = comp["non_inferiority"]["non_inferior"]
        cheaper = (comp["token_reduction_vs_monolithic"] or 0) > 0
        verdicts[k] = ("BETTER (non-inferior quality + fewer tokens)" if ni and cheaper
                       else "not established" )
    out["verdict"] = verdicts

    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
