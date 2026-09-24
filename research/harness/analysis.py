"""analysis.py  -  compute all study metrics from harness JSONL logs.

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

def repo_of(task_id):
    """Best-effort repo stratum from a SWE-bench instance_id (e.g. 'django__django-1234')."""
    return task_id.split("-")[0] if task_id else "unknown"

def cochran_mantel_haenszel(pairs):
    """CMH test (ETH's success-rate test), stratified by repo. Paired by task.
    Returns (statistic, approx_p). Strata = repos; 2x2 (condition x resolved) per stratum."""
    strata = defaultdict(lambda: [[0, 0], [0, 0]])  # [ [a_res,a_unres],[b_res,b_unres] ]
    for ra, rb in pairs:
        s = strata[repo_of(ra["task_id"])]
        s[0][0] += int(ra["resolved"]); s[0][1] += 1 - int(ra["resolved"])
        s[1][0] += int(rb["resolved"]); s[1][1] += 1 - int(rb["resolved"])
    num = 0.0; den = 0.0
    for s in strata.values():
        a = s[0][0]; b = s[0][1]; c = s[1][0]; d = s[1][1]
        n = a + b + c + d
        if n == 0: continue
        num += a - ((a + b) * (a + c)) / n
        den += ((a + b) * (c + d) * (a + c) * (b + d)) / (n * n * (n - 1)) if n > 1 else 0
    if den <= 0:
        return 0.0, 1.0
    chi2 = (abs(num) - 0.5) ** 2 / den
    return round(chi2, 4), round(math.erfc(math.sqrt(chi2 / 2)), 4)

def stratified_permutation(pairs, metric, n_perm=5000, seed=0):
    """ETH's steps/cost test: stratified permutation on a paired continuous metric.
    Within each task, randomly swap (a,b) labels; p = P(|mean diff| >= observed)."""
    rng = random.Random(seed)
    vals = [(metric(a), metric(b)) for a, b in pairs]
    if not vals: return 1.0
    obs = abs(sum(x - y for x, y in vals) / len(vals))
    ge = 0
    for _ in range(n_perm):
        d = 0.0
        for x, y in vals:
            if rng.random() < 0.5: d += x - y
            else: d += y - x
        if abs(d / len(vals)) >= obs - 1e-12: ge += 1
    return round((ge + 1) / (n_perm + 1), 4)

def _tok(r): return r.get("input_tokens", 0) + r.get("output_tokens", 0)
def _steps(r): return r.get("steps", 0)

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
                "cmh_success": dict(zip(("chi2", "p"), cochran_mantel_haenszel(pr))),
                "perm_tokens_p": stratified_permutation(pr, _tok),
                "perm_steps_p": stratified_permutation(pr, _steps),
                "rate_diff_ci": dict(zip(("diff", "ci_low", "ci_high"), bootstrap_diff_ci(pr, alpha=alpha))),
                "non_inferiority": non_inferiority(pr, delta, alpha=alpha),
                "token_reduction_vs_monolithic": round(
                    1 - cond_stats[tiered]["mean_tokens"] / cond_stats[mono]["mean_tokens"], 4)
                    if cond_stats[mono]["mean_tokens"] else None,
            }
    out["pareto_optimal_conditions"] = pareto(cond_stats)

    # Verdict logic (structural  -  applies to whatever data): "better" = non-inferior quality AND lower tokens
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
