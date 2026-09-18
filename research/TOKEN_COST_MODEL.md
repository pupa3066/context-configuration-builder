# The Token-Cost Model of Tiered Context — Math, Figures, and Measured Validation

> Research note for the Consistent Context Kit (CCK) branch. Derives the closed-form token-cost model
> behind CCK's tiering thesis, states its assumptions, and validates it against the real gpt2-BPE
> measurement in `benchmark/results.json`. Rule 2/6a/6b: every number here is measured or an
> explicitly-labeled projection; the measured point and the projection are kept distinct.

## 1. Setup and notation
An AI coding agent is given project context every turn. Let there be **n** projects in the workspace.
Measured constants (real gpt2-BPE tokenizer, author's live 4-project deployment):

| symbol | meaning | measured value |
|---|---|---|
| `A` | always-on tier tokens (rules + indexes, loaded every turn) | **4293** |
| `b` | mean per-project **body** tokens (full skill file) | **706** |
| `m` | mean per-project **metadata** tokens (frontmatter only) | **70** |
| `n` | number of projects | 6 (measured); 10–100 (projected) |

Metadata is ~1/10th of a body: `m/b = 70/706 = 0.099`.

## 2. The two regimes

**Monolithic** — all project bodies are always in context (naive "load everything"):
```
    C_mono(n) = A + b·n
```

**Tiered** — always-on tier + *metadata for all projects* + *exactly one body* (the project the
current task touches; others load on demand only when needed):
```
    C_tier(n) = A + m·n + b
```

**Token reduction** from tiering:
```
    R(n) = 1 − C_tier(n)/C_mono(n) = 1 − (A + m·n + b)/(A + b·n)
```

## 3. Three analytic properties (all provable from the formulas)

**(a) Crossover — when does tiering win?**
Tiered < monolithic ⇔ `m·n + b < b·n` ⇔ `n > b/(b−m)`.
```
    n* = b/(b−m) = 706/(706−70) = 1.11
```
→ Tiering wins for **n ≥ 2 projects**. There is essentially no regime where monolithic is cheaper.

**(b) Asymptote — the ceiling on savings.**
As n→∞, both grow linearly; the ratio → `m/b`, so:
```
    lim R(n) = 1 − m/b = 1 − 70/706 = 0.901
    n→∞
```
→ Tiering can cut at most **~90.1%** of per-turn project-context tokens. You never beat the
metadata floor (you always pay `m` per project to know it *exists*).

**(c) Why savings grow with n.**
`C_mono` grows at slope `b` (706 tok/project); `C_tier` grows at slope `m` (70 tok/project) — an
**~10.1× smaller slope**. The always-on `A` and the single active body `b` are fixed overhead, so the
per-project marginal cost is what dominates at scale.

## 4. Figure 1 — Per-turn token cost vs number of projects (real numbers)
Monolithic (●) grows ~10× faster than Tiered (○). Values from `benchmark/results.json` (N=6 live).
```
tokens/turn
 74893 |                                             ● mono(100)
       |
       |
 39593 |                        ● mono(50)
       |
 21943 |            ● mono(25)
 11999 |                                             ○ tier(100)  ← tiered barely rises
 11353 |  ● mono(10) ................................
  8531 |● mono(6, MEASURED)
  5815 |○ tier(6, MEASURED)   ○(10) 5699  ○(25) 6749  ○(50) 8499
       +----|--------|----------|------------|------------|--→ n
            6        10         25           50          100

slope(mono)=b=706 tok/project      slope(tier)=m=70 tok/project
```

## 5. Figure 2 — Reduction R(n) approaching the 90.1% ceiling
```
R(n)
0.901 |········································ asymptote (1 − m/b) ·······
0.84  |                                   ○ 0.840 (n=100)
0.785 |                        ○ 0.785 (n=50)
0.692 |            ○ 0.692 (n=25)
0.498 |     ○ 0.498 (n=10)
0.318 |○ 0.318 (n=6, MEASURED)
0.00  +----|--------|----------|------------|------------|--→ n
           6        10         25           50          100
```
Diminishing returns: most of the benefit (0 → ~0.69) is captured by the first ~25 projects.

## 6. Measured vs projected — the honest caveat, made rigorous

CCK reports two DIFFERENT estimators. They are not interchangeable, and the divergence at the measured
point has an exact closed form.

### 6.1 Two estimators
Let project i have body `bᵢ` and metadata `mᵢ`. Define the mean body `b̄ = (Σᵢ bᵢ)/n` and mean
metadata `m̄ = (Σᵢ mᵢ)/n`.

**Exact (MEASURED)** — sum over the *actual* files; the tiered case loads the single *active* body,
worst-case the largest:
```
    C_mono^exact = A + Σᵢ bᵢ
    C_tier^exact = A + Σᵢ mᵢ + max_i(bᵢ)
```

**Projected (MODEL)** — assume every project equals the average, and the one active body is a
mean-sized body:
```
    C_mono^proj(n) = A + b̄·n
    C_tier^proj(n) = A + m̄·n + b̄
```

### 6.2 Why monolithic always matches but tiered does not
Monolithic divergence:
```
    C_mono^exact − C_mono^proj = Σᵢ bᵢ − b̄·n = 0        (since b̄·n ≡ Σᵢ bᵢ by definition of the mean)
```
→ The monolithic curve passes exactly through the measured point. Always.

Tiered divergence (using Σᵢ mᵢ = m̄·n):
```
    C_tier^exact − C_tier^proj = (Σᵢ mᵢ + max_i bᵢ) − (m̄·n + b̄)
                               = max_i(bᵢ) − b̄
```
→ **The entire tiered gap equals "largest body − mean body."** The exact model charges the real active
project (worst case, the biggest skill); the projection charges an average-sized one. Because real
skills are unequal, `max_i(bᵢ) > b̄`, so `C_tier^exact ≥ C_tier^proj` — the measured tiered cost sits
ABOVE the mean-based curve, and the measured reduction is therefore SMALLER (more conservative) than
the projection. That is the right direction to be off: the measured number does not over-claim.

### 6.3 Consequences
- The projection formula is EXACT for the mean-field model (reproduces projected rows to the token).
- The measured point is exact for the REAL deployment; it diverges from the mean curve by exactly
  `max_i(bᵢ) − b̄` on the tiered side, 0 on the monolithic side.
- This is precisely why `benchmark.py` emits `measured_N` and `projected` as SEPARATE objects and never
  blends them, and why the measured reduction (conservative) is the one to quote for a claim.

### 6.4 Constants refreshed to the live machine (rule 6b)
`benchmark/results.json` is now refreshed to the CURRENT live deployment via real gpt2-BPE:
**N=6, A=4293, b̄=706, m̄=70** (a prior run recorded N=4, A=3859, b̄=774, m̄=73 before skills were
added + steering grew; the MODEL is unchanged, only the constants). Always re-run `benchmark.py`
before quoting an absolute number publicly (rule 6b). Worked example at the current N=6, using §6.1:
```
    max_i(bᵢ)=1102 (animevlog),  b̄=706  →  tiered gap = 1102 − 706 = 396 tokens
    C_mono^exact = 4293 + Σbᵢ(4238)         = 8531
    C_tier^exact = 4293 + Σmᵢ(420) + 1102   = 5815     → R_measured = 1 − 5815/8531 = 0.318
    C_tier^proj  = 4293 + 70·6 + 706         = 5419     (mean-based) — differs by the 396-tok max−mean gap
```

## 7. Application to this hardware-constrained machine (steering self-tiering)
The same model applies to CCK's *own* always-on steering (`~/.kiro/steering/`), which is pure `A`
(loaded every turn). MEASURED (gpt2-BPE): `A = 4293 tok/turn`, of which `00-rules.md` = 2002 (46.6%),
`cross-links.md` = 666, `bootstrap` 753, `registry` 564, `portfolio` 308.
Hypothesis (to be measured, not claimed): splitting `00-rules.md` into an always-on **priority core**
(must-fire rules) + an **on-demand governance appendix**, and moving `cross-links.md` to on-demand,
converts part of fixed `A` into per-task-loaded cost — reducing the every-turn baseline. Constraint:
safety/governance rules that must gate every turn (R0–R3, no-fabrication, secrets) STAY always-on; a
rule that isn't loaded can't fire (the N14 lesson). The reduction will be MEASURED with the same BPE
tokenizer + a rule-recall battery before any claim (rule 6a/6b).

## 8. Reproduce
```sh
# real token counts (gpt2-BPE), author's live deployment:
<venv-with-transformers>/bin/python benchmark/benchmark.py ~/.kiro/steering ~/.kiro/skills
# closed-form check (this doc's equations) reproduces the projected rows exactly.
```
Constants and measured/projected split: `benchmark/results.json`. Tokenizer: gpt2 BPE (deterministic).
