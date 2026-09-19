"""plot_quality.py — charts for results_quality_*.json. Headline panels exclude latency/VRAM."""
import json, glob, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

files = sorted(glob.glob("benchmark/results_quality_*.json"))
data = {json.load(open(f))["model"]: json.load(open(f)) for f in files}
models = list(data)
fig, ax = plt.subplots(1, 3, figsize=(17, 5))
colors = {"Qwen2.5-1.5B-Instruct": "tab:blue", "Qwen2.5-3B-Instruct": "tab:purple"}

def cells(m, k): return [c for c in data[m]["cells"] if c["k_active"] == k]

# Panel 1: recall on in-ACTIVE questions — tiered vs monolithic
for m in models:
    cs = cells(m, 1); ns = [c["n"] for c in cs]
    ax[0].plot(ns, [c["recall"]["mono"]["in-active"] for c in cs], "s--", color=colors[m], alpha=.6, lw=2,
               label=f"{m.split('-')[1]} monolithic")
    ax[0].plot(ns, [c["recall"]["tiered"]["in-active"] for c in cs], "o-", color=colors[m], lw=2.5,
               label=f"{m.split('-')[1]} tiered")
ax[0].set_ylim(0, 1.08); ax[0].set_xscale("log"); ax[0].set_xticks([4, 10, 25]); ax[0].set_xticklabels([4, 10, 25])
ax[0].set_xlabel("# projects (N), k=1 active"); ax[0].set_ylabel("recall on facts in the ACTIVE project")
ax[0].set_title("Fact in the loaded project:\ntiered ≥ monolithic (less context = less distraction)")
ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)

# Panel 2: recall on in-INACTIVE questions
for m in models:
    cs = cells(m, 1); ns = [c["n"] for c in cs]
    ax[1].plot(ns, [c["recall"]["mono"]["in-inactive"] for c in cs], "s--", color=colors[m], alpha=.6, lw=2,
               label=f"{m.split('-')[1]} monolithic")
    ax[1].plot(ns, [c["recall"]["tiered"]["in-inactive"] for c in cs], "o-", color=colors[m], lw=2.5,
               label=f"{m.split('-')[1]} tiered")
ax[1].set_ylim(-0.05, 1.08); ax[1].set_xscale("log"); ax[1].set_xticks([4, 10, 25]); ax[1].set_xticklabels([4, 10, 25])
ax[1].set_xlabel("# projects (N), k=1 active"); ax[1].set_ylabel("recall on facts in an INACTIVE project")
ax[1].set_title("Fact in an unloaded project:\ntiered = 0% recall (the cost token benchmarks hide)")
ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)

# Panel 3: what tiered does when the fact is missing — UNKNOWN vs hallucinated
w = 0.38
for i, m in enumerate(models):
    cs = cells(m, 1); xs = [j + (i - 0.5) * w for j in range(len(cs))]
    unk = [c["tiered"]["unknown_on_inactive"] / c["tiered"]["in-inactive"][1] for c in cs]
    hal = [1 - u for u in unk]
    ax[2].bar(xs, hal, w, color=colors[m], alpha=.85, label=f"{m.split('-')[1]}: hallucinated a value")
    ax[2].bar(xs, unk, w, bottom=hal, color=colors[m], alpha=.3, hatch="//", label=f"{m.split('-')[1]}: said UNKNOWN")
ax[2].set_xticks(range(3)); ax[2].set_xticklabels([f"N={c['n']}" for c in cells(models[0], 1)])
ax[2].set_ylim(0, 1.05); ax[2].set_ylabel("share of inactive-project questions (tiered)")
ax[2].set_title("When the fact is NOT loaded:\nsmall models confidently invent one")
ax[2].legend(fontsize=7.5, loc="lower right"); ax[2].grid(axis="y", alpha=.3)

plt.suptitle("Tiered vs monolithic context — answer QUALITY with a real local model (RTX 5060, fp16, planted un-guessable facts, 20 Q/cell)", y=1.02)
plt.tight_layout()
plt.savefig("benchmark/quality_recall.png", dpi=150, bbox_inches="tight")
print("wrote benchmark/quality_recall.png")
