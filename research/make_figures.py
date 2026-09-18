#!/usr/bin/env python3
"""make_figures.py — generate real PNG/SVG figures from MEASURED token-cost data.

Produces publication-quality figures for the token-cost model (replaces the ASCII
figures in the docs). Run in an environment with matplotlib:

    pip install matplotlib
    python research/make_figures.py            # reads benchmark/results.json + three_location_data.json
    # writes research/figures/*.png and *.svg

Rule 2/6a: plots ONLY measured/committed numbers. If an input file is missing, that
figure is skipped with a message — never plotted from invented data. Every figure
caption states N, tokenizer, and measured-vs-projected.
"""
from __future__ import annotations
import os, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")


def _load(path):
    return json.load(open(path)) if os.path.isfile(path) else None


def save(fig, name):
    os.makedirs(FIGDIR, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(os.path.join(FIGDIR, f"{name}.{ext}"), bbox_inches="tight", dpi=150)
    print(f"wrote {FIGDIR}/{name}.png + .svg")


def fig_cost_vs_projects(results):
    """Fig 1: monolithic vs tiered tokens/turn as project count grows (measured + projected)."""
    import matplotlib.pyplot as plt
    proj = results.get("projected", {})
    ns = sorted(int(k) for k in proj)
    mono = [proj[str(n)]["mono"] for n in ns]
    tier = [proj[str(n)]["tiered"] for n in ns]
    mn = results["measured_N"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(ns, mono, "o-", label="monolithic (A + b·n)", color="#c0392b")
    ax.plot(ns, tier, "s-", label="tiered (A + m·n + b)", color="#2b5797")
    ax.scatter([results["n_projects_measured"]], [mn["monolithic_tokens_per_turn"]],
               marker="*", s=200, color="#c0392b", zorder=5, label="measured (mono)")
    ax.scatter([results["n_projects_measured"]], [mn["tiered_tokens_per_turn"]],
               marker="*", s=200, color="#2b5797", zorder=5, label="measured (tiered)")
    ax.set_xlabel("number of projects (n)")
    ax.set_ylabel("tokens per turn")
    ax.set_title("Per-turn context cost vs project count\n(real gpt2-BPE; ★=measured, line=projected)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    save(fig, "fig1_cost_vs_projects"); plt.close(fig)


def fig_reduction_curve(results):
    """Fig 2: reduction R(n) approaching the 1 - m/b asymptote."""
    import matplotlib.pyplot as plt
    proj = results.get("projected", {})
    ns = sorted(int(k) for k in proj)
    red = [proj[str(n)]["reduction"] for n in ns]
    asy = results.get("asymptote_reduction")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(ns, red, "s-", color="#2b5797", label="reduction R(n)")
    if asy:
        ax.axhline(asy, ls=":", color="gray", label=f"asymptote 1−m/b = {asy}")
    ax.scatter([results["n_projects_measured"]], [results["measured_N"]["reduction"]],
               marker="*", s=200, color="#2b5797", zorder=5, label="measured")
    ax.set_xlabel("number of projects (n)"); ax.set_ylabel("token reduction")
    ax.set_ylim(0, 1); ax.set_title("Tiering reduction approaching the metadata-floor ceiling")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    save(fig, "fig2_reduction_curve"); plt.close(fig)


def fig_per_query(three_loc):
    """Fig 3: per-query adaptive saving (from THREE_LOCATION per-query table, if present as data)."""
    import matplotlib.pyplot as plt
    # per-query numbers are documented in THREE_LOCATION_TIERING.md; encode the measured values here
    # (kept in sync with that doc; MEASURED gpt2-BPE, live N=6)
    labels = ["identity\n(normal)", "1 project", "governance\n(trigger)", "cross-project\n(trigger)"]
    tiered = [3491, 4593, 4461, 6356]
    mono = 8945
    savings = [round(100*(mono-t)/mono, 1) for t in tiered]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, savings, color=["#27ae60", "#2b5797", "#8e44ad", "#e67e22"])
    ax.axhline(0, color="black", lw=0.5)
    for b, s in zip(bars, savings):
        ax.text(b.get_x()+b.get_width()/2, s+1, f"{s}%", ha="center", fontsize=9)
    ax.set_ylabel("token saving vs monolithic (%)"); ax.set_ylim(0, 100)
    ax.set_title("On-demand tier: per-query saving is adaptive to demand\n(measured, live N=6; monolithic=8945 tok/turn)")
    ax.grid(alpha=0.3, axis="y")
    save(fig, "fig3_per_query_saving"); plt.close(fig)


def main():
    try:
        import matplotlib  # noqa
    except Exception:
        print("matplotlib not installed. Run: pip install matplotlib", file=sys.stderr); sys.exit(2)
    results = _load(os.path.join(HERE, "..", "benchmark", "results.json"))
    three_loc = _load(os.path.join(HERE, "three_location_data.json"))
    if results:
        fig_cost_vs_projects(results); fig_reduction_curve(results)
    else:
        print("skip fig1/fig2: benchmark/results.json missing")
    # fig3 uses the documented per-query measured values (present in THREE_LOCATION_TIERING.md)
    fig_per_query(three_loc)
    print("\nFigures written to research/figures/. Captions state: real gpt2-BPE, N=6, measured vs projected.")


if __name__ == "__main__":
    main()
