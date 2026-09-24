"""analyze_metrics.py  -  multi-axis summary for the extended CCK evaluation.

Consumes JSONL run rows (from harness.py / swebench_run.py, instrumented with metrics.py)
and reports, grouped by the requested factors:

  factors : condition x model x os x project_count
  metrics : task success (behavior/resolved), token cost (memory-of-context),
            peak RSS + RSS delta (process memory), wall latency, TTFT,
            output determinism (behavioral stability), scaling (metric vs project_count)

Statistics stay honest: means with n; if a run set is from the MockAgent (detectable:
every resolved value trivially tracks context-substring, no variance), it is FLAGGED as
NON-EMPIRICAL and no scientific claim is attached (rule 6a + research/STATUS.md).

Factuality is intentionally NOT a column here  -  see metrics.py header.

Run: python research/harness/analyze_metrics.py research/harness/runs.jsonl
"""
from __future__ import annotations
import json, sys, argparse, statistics
from collections import defaultdict


def load(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(statistics.mean(xs), 4) if xs else None


def _looks_mock(rows) -> bool:
    """Heuristic honesty gate: MockAgent output is 'PASS'/'FAIL' by substring and has
    no model/os variance beyond context. If every row carries no real model label
    (or the config agent starts with 'mock'), treat as non-empirical."""
    agents = set()
    for r in rows:
        cfg = r.get("config", {})
        agents.add(cfg.get("agent", r.get("model", "")))
    return (not agents) or all((a or "").lower().startswith(("mock", "", "selftest")) for a in agents)


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        key = (
            r.get("condition", "?"),
            r.get("model", r.get("config", {}).get("agent", "?")),
            r.get("os", "?"),
            r.get("project_count", "?"),
        )
        groups[key].append(r)

    out = []
    for (cond, model, os_, pc), rs in sorted(groups.items(), key=lambda x: str(x[0])):
        shas = [r.get("output_sha") for r in rs if r.get("output_sha")]
        from_metrics = None
        try:
            sys.path.insert(0, __file__.rsplit("/", 1)[0])
            from metrics import determinism
            from_metrics = determinism(shas)
        except Exception:
            from_metrics = None
        out.append({
            "condition": cond, "model": model, "os": os_, "project_count": pc,
            "n": len(rs),
            "resolved_rate": _mean([1.0 if r.get("resolved") else 0.0 for r in rs]),
            "input_tokens_mean": _mean([r.get("input_tokens") for r in rs]),
            "output_tokens_mean": _mean([r.get("output_tokens") for r in rs]),
            "wall_seconds_mean": _mean([r.get("wall_seconds", r.get("seconds")) for r in rs]),
            "ttft_seconds_mean": _mean([r.get("ttft_seconds") for r in rs]),
            "peak_rss_mib_mean": _mean([r.get("peak_rss_mib_after") for r in rs]),
            "rss_delta_mib_mean": _mean([r.get("rss_delta_mib") for r in rs]),
            "determinism": from_metrics,
        })
    return out


def scaling_view(summary):
    """Pull the scaling axis: token cost + resolved rate vs project_count, per condition."""
    by_cond = defaultdict(list)
    for s in summary:
        if s["project_count"] != "?":
            by_cond[s["condition"]].append(
                (s["project_count"], s["input_tokens_mean"], s["resolved_rate"]))
    return {c: sorted(v, key=lambda x: (x[0] is None, x[0])) for c, v in by_cond.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    rows = load(a.runs)
    summary = summarize(rows)
    report = {
        "n_rows": len(rows),
        "EMPIRICAL": not _looks_mock(rows),
        "note": ("Real-agent run  -  metrics are empirical."
                 if not _looks_mock(rows)
                 else "MOCK/self-test data  -  NO scientific claim (rule 6a). "
                      "Proves the measurement pipeline only; run swebench_run.py "
                      "with a real --agent for empirical metrics."),
        "by_group": summary,
        "scaling": scaling_view(summary),
        "excluded": {"factuality": "precision-axis of quant-memorization-study, not a coding metric"},
    }
    js = json.dumps(report, indent=2)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(js)
    print(js)


if __name__ == "__main__":
    main()
