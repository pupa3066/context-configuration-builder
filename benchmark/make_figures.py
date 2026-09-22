#!/usr/bin/env python3
"""make_figures.py — churn empirical figures + data tables for the CCK paper.

Input: aggregate results embedded here (from compare_algorithms.py runs; NO answer values, so
publishable). Outputs into benchmark/figures/:
  - pareto_token_vs_fidelity.png  : log-x tokens/turn vs answerable retention (the frontier plot)
  - answerable_by_algorithm.png   : bar chart of answerable retention per algorithm
  - tokens_by_algorithm.png       : bar chart of tokens/turn per algorithm (log scale)
  - results_table.md / results.csv: the measured table

All numbers are aggregate metrics (avg tokens/turn, answerable fraction) over N=44 testable real
questions, real gpt2 BPE. No ground-truth answer values appear here (safe to commit).
"""
from __future__ import annotations
import os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

# MEASURED (compare_algorithms.py, N=44 testable, real gpt2, k=6 for retrieval arms)
N = 44
ROWS = [
    # algorithm, avg_tokens_per_turn, answerable
    ("monolithic",            231048, 0.9773),
    ("tiered_lossless",       234835, 0.9773),
    ("summarized_L0.33",      216887, 0.9773),
    ("summarized_L0.50",      216887, 0.9773),
    ("summarized_L0.66",      168735, 0.5909),
    ("retrieval_bm25_top6",      911, 0.9091),
    ("hybrid_bm25_top6",        4698, 0.9091),
    ("semantic_top6",            924, 0.6136),
    ("hybrid_semantic_top6",    4711, 0.6136),
]

def write_tables():
    with open(os.path.join(HERE, "results.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["algorithm", "avg_tokens_per_turn", "answerable_retention", "N"])
        for a, t, r in ROWS: w.writerow([a, t, r, N])
    with open(os.path.join(HERE, "results_table.md"), "w") as f:
        f.write(f"# Context-algorithm comparison (N={N} real questions, real gpt2 BPE)\n\n")
        f.write("| algorithm | tokens/turn | answerable | vs monolithic |\n|---|---|---|---|\n")
        mono = ROWS[0][1]
        for a, t, r in ROWS:
            red = f"{100*(1-t/mono):+.1f}%"
            f.write(f"| {a} | {t:,} | {r:.3f} | {red} |\n")
        f.write("\nPreliminary: pilot N; answerable = ground-truth fact co-located with a query keyword "
                "(a proxy for usable-in-context, NOT task success). Retrieval arms use top-k=6. "
                "Finding: on an identifier/number-dense research corpus, lexical (BM25) retrieval "
                "recalls facts better than semantic embedding retrieval (0.909 vs 0.614), because DOIs/"
                "ORCIDs/p-values/module-names carry little semantic signal; both cut tokens ~99.6% vs "
                "monolithic. Safe summarization saves little (~6%).\n")

def make_figs():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print("matplotlib unavailable:", e); return False
    names = [r[0] for r in ROWS]; toks = [r[1] for r in ROWS]; ans = [r[2] for r in ROWS]

    # 1. Pareto: tokens (log x) vs answerable
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(toks, ans, s=60)
    for n, t, a in ROWS:
        ax.annotate(n, (t, a), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_xscale("log"); ax.set_xlabel("tokens per turn (log scale)")
    ax.set_ylabel("answerable retention"); ax.set_ylim(0.5, 1.02)
    ax.axhline(0.95, ls="--", lw=0.8, color="gray"); ax.text(min(toks), 0.955, "0.95 threshold", fontsize=7)
    ax.set_title(f"Token cost vs answerable retention (N={N} real questions, gpt2 BPE)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "pareto_token_vs_fidelity.png"), dpi=150); plt.close(fig)

    # 2. answerable bars
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(range(len(names)), ans)
    ax.set_xticks(range(len(names))); ax.set_xticklabels(names, rotation=45, ha="right", fontsize=7)
    ax.axhline(0.95, ls="--", lw=0.8, color="gray"); ax.set_ylabel("answerable retention")
    ax.set_title("Answerable retention by algorithm"); fig.tight_layout()
    fig.savefig(os.path.join(FIG, "answerable_by_algorithm.png"), dpi=150); plt.close(fig)

    # 3. tokens bars (log)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(range(len(names)), toks); ax.set_yscale("log")
    ax.set_xticks(range(len(names))); ax.set_xticklabels(names, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("tokens per turn (log)"); ax.set_title("Token cost by algorithm")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "tokens_by_algorithm.png"), dpi=150); plt.close(fig)
    return True

if __name__ == "__main__":
    write_tables()
    ok = make_figs()
    print("tables written: benchmark/results.csv, benchmark/results_table.md")
    print("figures written to benchmark/figures/" if ok else "figures skipped (no matplotlib)")
