"""benchmark_measured.py — EMPIRICAL check of the closed-form token projection.

The shipped benchmark.py measures N=4 (author's private deployment) and PROJECTS
N=10/25/50/100 with a closed-form formula. This script instead BUILDS real skill
files at each N and measures them with the same GPT-2 BPE tokenizer, so the
projection is tested rather than assumed. It also relaxes the "exactly ONE active
project per turn" assumption by measuring k = 1, 2, 3 active bodies.

Skill bodies are generated from the shipped _example/SKILL.md template with the
project name substituted, so per-project size matches what the repo actually ships
(not the author's longer private bodies). Body-length sensitivity is reported
separately by scaling the body content.

Run: python benchmark_measured.py [steering_dir] [example_skill] [--out results_measured.json]
Honesty: real measured tokens at every N. Nothing extrapolated.
"""
import os, sys, glob, json, re, tempfile, argparse

ap = argparse.ArgumentParser()
ap.add_argument("steering", nargs="?", default="templates/steering")
ap.add_argument("example_skill", nargs="?", default="templates/skills/_example/SKILL.md")
ap.add_argument("--out", default="benchmark/results_measured.json")
ap.add_argument("--ns", default="1,4,10,25,50,100")
ap.add_argument("--body-scales", default="1,2,3.5",
                help="multipliers of the shipped body length (sensitivity sweep; body-only text is scaled, frontmatter fixed)")
a = ap.parse_args()

from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("gpt2")

def ntok(text): return len(tok.encode(text))
def read(p):
    with open(p, encoding="utf-8", errors="ignore") as f: return f.read()

# ---- always-on tier (real shipped steering files) ----
steer_files = sorted(glob.glob(os.path.join(a.steering, "*.md")))
always_on = sum(ntok(read(f)) for f in steer_files)

# ---- split the shipped example skill into frontmatter + body ----
example = read(a.example_skill)
lines = example.splitlines()
assert lines and lines[0].strip() == "---", "example skill must start with YAML frontmatter"
end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
fm_lines, body_lines = lines[:end+1], lines[end+1:]
fm_text, body_text = "\n".join(fm_lines), "\n".join(body_lines)

def make_skill(i, body_scale):
    """Real skill file text for project i. Only the frontmatter `name:` line is substituted;
    the shipped `description:` is kept verbatim so metadata size matches the shipped template
    (rewriting it shortened frontmatter 46->28 tokens and made 'shipped' numbers inconsistent
    with benchmark.py). Body is repeated body_scale times to emulate longer per-project context."""
    fm = re.sub(r"(?m)^name:.*$", f"name: project-{i:03d}-context", fm_text)
    whole = int(body_scale); frac = body_scale - whole
    body = body_text * whole
    if frac > 0:
        cut = int(len(body_text) * frac)
        body += "\n" + body_text[:cut]
    return fm + "\n" + body, fm

def measure(n, body_scale, k_active):
    """Build n REAL skill files, tokenize each, compute per-turn cost."""
    bodies, metas = [], []
    for i in range(n):
        full, fm = make_skill(i, body_scale)
        bodies.append(ntok(full)); metas.append(ntok(fm))
    mono = always_on + sum(bodies)
    # tiered: always-on + ALL metadata + k active full bodies (largest k, conservative)
    top_k = sorted(bodies, reverse=True)[:k_active]
    tier = always_on + sum(metas) + sum(top_k)
    return {"n": n, "body_scale": body_scale, "k_active": k_active,
            "mean_body": sum(bodies)//n, "mean_meta": sum(metas)//n,
            "mono": mono, "tiered": tier,
            "reduction": round(1 - tier/mono, 4) if mono else 0}

ns = [int(x) for x in a.ns.split(",")]
scales = [float(x) for x in a.body_scales.split(",")]
rows = []
for s in scales:
    for n in ns:
        for k in (1, 2, 3):
            if k > n: continue
            rows.append(measure(n, s, k))

# ---- closed-form projection (the shipped formula) for direct comparison, scale=1, k=1 ----
b1 = measure(1, 1.0, 1)
mb, mm = b1["mean_body"], b1["mean_meta"]
def project(n):
    mono = always_on + mb*n; tier = always_on + mm*n + mb
    return round(1 - tier/mono, 4)
projected = {str(n): project(n) for n in ns}

out = {
    "tokenizer": "gpt2-bpe (real)",
    "always_on_tokens": always_on,
    "steering_files": [os.path.basename(f) for f in steer_files],
    "shipped_example_body_tokens": mb, "shipped_example_meta_tokens": mm,
    "note": ("Every row is MEASURED from real generated skill files. 'projected' is the shipped "
             "closed-form formula applied to the same base sizes, for comparison. body_scale=1 is the "
             "shipped example skill verbatim (only name: substituted); larger scales repeat the body text "
             "with frontmatter held fixed, as a body-length sensitivity sweep."),
    "asymptote_by_scale": {str(s): round(1 - mm / measure(1, s, 1)["mean_body"], 4) for s in scales},
    "projected_closed_form_scale1_k1": projected,
    "measured": rows,
}
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
with open(a.out, "w") as fh: json.dump(out, fh, indent=2)

# ---- console summary ----
print(f"always_on={always_on} tok | shipped skill: body={mb} meta={mm} (meta/body={mm/mb:.1%})")
print("\n== projection vs MEASURED (body_scale=1, k=1 active) ==")
print(f"{'N':>4} {'projected':>10} {'measured':>10} {'delta':>8}")
for n in ns:
    m = next(r for r in rows if r["n"]==n and r["body_scale"]==1.0 and r["k_active"]==1)
    print(f"{n:>4} {projected[str(n)]:>10.3f} {m['reduction']:>10.3f} {m['reduction']-projected[str(n)]:>+8.3f}")
print("\n== effect of #active projects per turn (body_scale=1) ==")
print(f"{'N':>4} {'k=1':>8} {'k=2':>8} {'k=3':>8}")
for n in ns:
    vals = []
    for k in (1,2,3):
        r = next((r for r in rows if r["n"]==n and r["body_scale"]==1.0 and r["k_active"]==k), None)
        vals.append(f"{r['reduction']:>8.3f}" if r else f"{'—':>8}")
    print(f"{n:>4} {''.join(vals)}")
print("\n== body-length sensitivity (k=1) ==")
print(f"{'N':>4} " + "".join(f"{'x'+str(s):>9}" for s in scales))
for n in ns:
    vals = []
    for s in scales:
        r = next(r for r in rows if r["n"]==n and r["body_scale"]==s and r["k_active"]==1)
        vals.append(f"{r['reduction']:>9.3f}")
    print(f"{n:>4} {''.join(vals)}")
print("\n== asymptote 1 - meta/body (N->inf, k=1) ==")
for s_ in scales:
    print(f"  x{s_:g}: {out['asymptote_by_scale'][str(s_)]:.3f}")
print(f"\nwrote {a.out}")
