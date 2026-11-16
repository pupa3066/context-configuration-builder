"""Holm correction over every primary test with an outcome (research/RESULTS_LEDGER.md).

p-values are the exact values recorded in the outcomes of research/PREREG_20day_agent_plan.md,
research/PREREG_agent_retrieval_order.md and research/PREREG_tiered_context_gemma_harness.md.
Family 1 (primary, conservative): all primary tests. Family 2 (labelled post hoc): retrieval tests only.
Neither family was declared before the results; family 1 is reported as primary because it is the stricter one.
Run: python3 research/holm_primary_tests.py
"""

TESTS = [
    # (domain, test, p)
    ("retrieval", "Coverage, docstrings set 1: BM25 vs dense at a 1,000-chunk budget", 1.8e-20),
    ("retrieval", "Chunk length: best-segment vs whole-chunk dense, 400-word chunks", 1.2e-14),
    ("retrieval", "Coverage, docstrings set 2: BM25 vs dense at a 1,000-chunk budget", 1.7e-13),
    ("retrieval", "Real problem statements, 125 tasks: BM25 vs dense at full coverage", 0.011),
    ("retrieval", "SWE-bench Lite django shard: dense full vs 25 percent coverage", 0.0059),
    ("retrieval", "SWE-bench Lite django shard: BM25 vs dense at full coverage", 0.035),
    ("agent", "BM25 skill vs no skill, 16 tasks (skill later found defective)", 1.0),
    ("agent", "Grep first (G) vs no search step (N), 16 tasks", 1.0),
    ("agent", "G vs N, 72 scorable tasks", 1.0),
    ("agent", "G vs N, fastapi replicate, 29 scorable tasks", 0.62),
    ("agent", "Tokens, G vs N, 129 tasks", 0.36),
    ("agent", "Tokens, G vs N, 67 fastapi tasks", 0.22),
    ("agent", "Tokens, 40-line windows (W) vs G, 31B, 16 tasks", 0.47),
    ("agent", "Tokens, 40-line windows vs grep, E4B, 16 tasks", 0.07),
    ("agent", "Tokens, 40-line windows vs grep, E4B, 56 tasks (replication)", 0.74),
    ("agent", "E4B: BM25 skill vs no skill, 16 tasks", 1.0),
    ("agent", "E4B: grep first vs no search step, 16 tasks", 1.0),
    ("agent", "E4B: shorter prompt vs grep first, 16 tasks", 1.0),
    ("agent", "E4B: double reasoning budget vs shorter prompt, 16 tasks", 1.0),
    ("agent", "Test before submit (V) vs G, 16 tasks", 1.0),
    ("agent", "Larger budget (B) vs G, 16 tasks", 1.0),
    ("agent", "New-files rule (F) vs G, 16 tasks", 1.0),
    ("agent", "Larger budget (B) vs G, 72 scorable tasks", 0.51),
    ("agent", "E4B: ranked 8-line chunk search (R-E4B) vs grep, 46 tasks", 1.0),
    ("agent", "E4B: fix check (RC-E4B) vs R-E4B, 46 tasks", 1.0),
    ("agent", "E4B told the gold files (D1) vs R-E4B run 1, 46 tasks", 0.62),
]


def holm(rows):
    rows = sorted(rows, key=lambda r: r[2])
    m, run, out = len(rows), 0.0, []
    for i, (d, name, p) in enumerate(rows):
        run = max(run, min(1.0, (m - i) * p))
        out.append((d, name, p, run))
    return out


def show(title, rows):
    print(f"\n{title} (m = {len(rows)})")
    print("| Test | p | Holm-adjusted p | Holds at 0.05 |\n|---|---|---|---|")
    for d, name, p, a in holm(rows):
        print(f"| {name} | {p:.2g} | {a:.2g} | {'yes' if a < 0.05 else 'no'} |")


if __name__ == "__main__":
    show("Family 1, primary: all primary tests", TESTS)
    show("Family 2, post hoc: retrieval tests only", [t for t in TESTS if t[0] == "retrieval"])
