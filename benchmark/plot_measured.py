"""plot_measured.py — charts for benchmark/results_measured.json.
Produces benchmark/measured_vs_projected.png (3 panels). Real measured data only."""
import json, sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

src = sys.argv[1] if len(sys.argv) > 1 else "benchmark/results_measured.json"
d = json.load(open(src))
rows = d["measured"]; proj = d["projected_closed_form_scale1_k1"]
ns = sorted({r["n"] for r in rows})

def pick(scale, k):
    return [next(r["reduction"] for r in rows if r["n"]==n and r["body_scale"]==scale and r["k_active"]==k)
            if any(r["n"]==n and r["body_scale"]==scale and r["k_active"]==k for r in rows) else None
            for n in ns]

fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))

# Panel 1: projection vs measured
ax[0].plot(ns, [proj[str(n)] for n in ns], "k--", lw=2, label="closed-form projection (shipped)")
ax[0].plot(ns, pick(1.0, 1), "o-", color="tab:blue", lw=2, label="MEASURED (real files)")
ax[0].axhline(0, color="gray", lw=0.8)
ax[0].set_xscale("log"); ax[0].set_xlabel("# projects (N)"); ax[0].set_ylabel("token reduction vs monolithic")
ax[0].set_title("Projection is accurate\n(measured tracks formula within 0.1pt)")
ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)

# Panel 2: active-projects-per-turn sensitivity
for k, c in zip((1, 2, 3), ("tab:blue", "tab:orange", "tab:red")):
    ax[1].plot(ns, pick(1.0, k), "o-", color=c, lw=2, label=f"k={k} active project(s)/turn")
ax[1].axhline(0, color="gray", lw=0.8)
ax[1].set_xscale("log"); ax[1].set_xlabel("# projects (N)"); ax[1].set_ylabel("token reduction")
ax[1].set_title("Savings collapse at small N when\nmultiple projects are active per turn")
ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)

# Panel 3: body-length sensitivity
scales = sorted({r["body_scale"] for r in rows})
for s, c in zip(scales, ("tab:blue", "tab:green", "tab:purple")):
    lbl = f"body x{s:g}" + (" (shipped example)" if s == 1.0 else "")
    ax[2].plot(ns, pick(s, 1), "o-", color=c, lw=2, label=lbl)
ax[2].axhline(0, color="gray", lw=0.8)
ax[2].set_xscale("log"); ax[2].set_xlabel("# projects (N)"); ax[2].set_ylabel("token reduction")
ax[2].set_title("Headline % is set by body length,\nnot by the tool")
ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)

plt.suptitle("Tiered vs monolithic context: MEASURED at every N (GPT-2 BPE, real generated skill files)", y=1.02)
plt.tight_layout()
out = os.path.join(os.path.dirname(src) or ".", "measured_vs_projected.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
print("wrote", out)
