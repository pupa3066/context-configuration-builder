#!/usr/bin/env python3
"""make_figures.py -- churn empirical figures + data tables for the CCK paper.

Input: powered aggregate results from benchmark/POWERED_RESULTS.json (aggregate metrics only:
avg tokens/turn, answerable fraction, 95% bootstrap CIs). NO ground-truth answer values appear
here, so the outputs are publishable.

Outputs into benchmark/figures/:
  - pareto_token_vs_fidelity.png : log-x tokens/turn vs answerable retention (the frontier plot)
  - answerable_by_algorithm.png  : bar chart of answerable retention per algorithm (with 95% CI)
  - tokens_by_algorithm.png      : bar chart of tokens/turn per algorithm (log scale)
  - results_table.md / results.csv: the measured table

All numbers are aggregate metrics over N=195 testable real questions across 3 real PyPI corpora
(requests, click, black), real gpt2 BPE token counts, 1000-sample bootstrap CIs. No ground-truth
answer values appear here (safe to commit).
"""
from __future__ import annotations
import os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

# MEASURED (benchmark/POWERED_RESULTS.json; N=195 testable across requests/click/black,
# real gpt2 BPE, 1000-sample bootstrap 95% CIs; retrieval arms are BM25 at k=3/6/10)
N = 195
# algorithm, avg_tokens_per_turn, answerable, ci_low, ci_high
ROWS = [
    ("no_context",           0,      0.0000, 0.0000, 0.0000),
    ("monolithic",           471812, 1.0000, 1.0000, 1.0000),
    ("summarized_L0.5",      471551, 1.0000, 1.0000, 1.0000),
    ("retrieval_bm25_k3",    309,    0.9846, 0.9641, 1.0000),
    ("retrieval_bm25_k6",    624,    0.9897, 0.9744, 1.0000),
    ("retrieval_bm25_k10",   1061,   0.9949, 0.9846, 1.0000),
]

# monolithic is the full-context reference arm for token-reduction comparison
MONO_TOK = 471812


def write_tables():
    with open(os.path.join(HERE, "results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["algorithm", "avg_tokens_per_turn", "answerable_retention",
                    "ci95_low", "ci95_high", "N"])
        for a, t, r, lo, hi in ROWS:
            w.writerow([a, t, r, lo, hi, N])
    with open(os.path.join(HERE, "results_table.md"), "w") as f:
        f.write(f"# Context-algorithm comparison (N={N} real questions, 3 real PyPI corpora, "
                "real gpt2 BPE)\n\n")
        f.write("| algorithm | tokens/turn | answerable | 95% CI | vs monolithic tokens |\n")
        f.write("|---|---|---|---|---|\n")
        for a, t, r, lo, hi in ROWS:
            if t == 0:
                red = "n/a"
            else:
                red = f"{100*(1-t/MONO_TOK):+.2f}%"
            f.write(f"| {a} | {t:,} | {r:.4f} | [{lo:.4f}, {hi:.4f}] | {red} |\n")
        f.write("\nPreliminary: answerable = ground-truth identifier recalled in the assembled "
                "context (a proxy for usable-in-context, NOT task success); lift over no_context "
                "(0.0) is the signal. Corpora: requests, click, black (real PyPI source). "
                "Retrieval arms are BM25 at k=3/6/10. Finding: BM25 retrieval reaches 0.9846 "
                "(k=3), 0.9897 (k=6), and 0.9949 (k=10) answerable while cutting tokens versus "
                "the monolithic full-context arm (471,812 tokens/turn) by 99.93%, 99.87%, and "
                "99.78% respectively. Safe summarization at L=0.5 saves only 0.06% of tokens "
                "(471,551) because lossless-safe compression cannot drop identifier content. "
                "CIs are 1000-sample bootstrap.\n")


def make_figs():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print("matplotlib unavailable:", e)
        return False
    names = [r[0] for r in ROWS]
    toks = [r[1] for r in ROWS]
    ans = [r[2] for r in ROWS]
    # asymmetric error bars from CI
    err_lo = [r[2] - r[3] for r in ROWS]
    err_hi = [r[4] - r[2] for r in ROWS]
    yerr = [err_lo, err_hi]

    # 1. Pareto: tokens (log x) vs answerable. no_context has 0 tokens (invalid on log axis),
    #    so plot it as an annotated reference point at the left edge.
    fig, ax = plt.subplots(figsize=(8, 5))
    plotted = [(n, t, a) for n, t, a in [(r[0], r[1], r[2]) for r in ROWS] if t > 0]
    px = [t for _, t, _ in plotted]
    py = [a for _, _, a in plotted]
    ax.scatter(px, py, s=60)
    for n, t, a in plotted:
        ax.annotate(n, (t, a), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("tokens per turn (log scale)")
    ax.set_ylabel("answerable retention")
    ax.set_ylim(0.0, 1.05)
    ax.axhline(0.95, ls="--", lw=0.8, color="gray")
    ax.text(min(px), 0.955, "0.95 threshold", fontsize=7)
    ax.axhline(0.0, ls=":", lw=0.8, color="red")
    ax.text(min(px), 0.01, "no_context = 0.0 (0 tokens)", fontsize=7, color="red")
    ax.set_title(f"Token cost vs answerable retention (N={N}, 3 corpora, gpt2 BPE)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "pareto_token_vs_fidelity.png"), dpi=150)
    plt.close(fig)

    # 2. answerable bars with 95% CI error bars
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(range(len(names)), ans, yerr=yerr, capsize=4)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=7)
    ax.axhline(0.95, ls="--", lw=0.8, color="gray")
    ax.set_ylabel("answerable retention")
    ax.set_ylim(0.0, 1.05)
    ax.set_title(f"Answerable retention by algorithm (N={N}, 95% bootstrap CI)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "answerable_by_algorithm.png"), dpi=150)
    plt.close(fig)

    # 3. tokens bars (log). no_context = 0 cannot render on log axis; use a small floor for
    #    the bar and label it as 0.
    fig, ax = plt.subplots(figsize=(9, 4.5))
    floor = 1
    plot_toks = [t if t > 0 else floor for t in toks]
    ax.bar(range(len(names)), plot_toks)
    ax.set_yscale("log")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("tokens per turn (log)")
    for i, t in enumerate(toks):
        ax.text(i, plot_toks[i], f"{t:,}", ha="center", va="bottom", fontsize=6)
    ax.set_title(f"Token cost by algorithm (N={N})")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "tokens_by_algorithm.png"), dpi=150)
    plt.close(fig)
    return True


if __name__ == "__main__":
    write_tables()
    ok = make_figs()
    print("tables written: benchmark/results.csv, benchmark/results_table.md")
    print("figures written to benchmark/figures/" if ok else "figures skipped (no matplotlib)")
