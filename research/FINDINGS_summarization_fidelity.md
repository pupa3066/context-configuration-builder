# FINDINGS — Summarized-Tier Fidelity (C4) vs Lossless (C2)

> **Status: MEASURED but PRELIMINARY (rule 6a/6b).** Real compression operator run on real
> project sources. N=6 questions, keyword-based fact detection, single compression operator,
> **no agent/task-success run**. This measures whether needed facts are still PRESENT in the
> context, NOT whether an agent ANSWERS better. Reproduce: `python research/eval_n6.py`.

## Headline (the corrected, honest finding)
**Summarization loses the needed facts FIRST at aggressive compression** — contradicting the naive
intuition that "summarizing keeps the facts, just shortens prose." A by-hand simulation predicted
summarization would preserve employer names/dates; running the real operator **falsified that**: at
compression level 0.66 the experience question lost every employer name. Measuring corrected the guess.

## Result 1 — Lossless (C2) = Monolithic (C1): confirmed free
Measured across all N=6 questions: `C2_lossless_all_identical_to_C1 = True`, mean grounding
retention = **1.0**. Lossless tiering is byte-identical to monolithic — zero fidelity loss. The token
win comes from *deferral* (load full body on demand), not from shrinking content.

## Result 2 — Summarization fidelity-vs-token curve (N=6, real gpt2-BPE, finer grid)
| Level | token saving | retention mean | retention stdev | retention min | verdict |
|---|---|---|---|---|---|
| 0.00 | 0% | 1.000 | 0 | 1.0 | safe (lossless) |
| 0.20 | 11.3% | 1.000 | 0 | 1.0 | safe |
| 0.33 | 11.3% | 1.000 | 0 | 1.0 | safe |
| **0.50** | **11.3%** | **1.000** | **0** | **1.0** | **safe frontier (measured)** |
| 0.66 | 66.9% | 0.486 | 0.274 | 0.0 | UNSAFE — cliff |
| 0.80 | 66.9% | 0.486 | 0.274 | 0.0 | UNSAFE |
| 1.00 | 66.9% | 0.486 | 0.274 | 0.0 | UNSAFE |

**Three measured properties:**
1. **Safe frontier = level 0.50** (finer grid; retention 1.0, stdev 0, min 1.0 up to 0.50). A coarser
   grid earlier reported 0.33 — measuring more finely moved the safe frontier up to 0.50.
2. **Sharp cliff between 0.50 and 0.66** — retention drops 1.0 → 0.486 with high variance (stdev 0.274,
   min 0.0). Not gradual: a discontinuity where the operator stops dropping prose and starts dropping
   structure/facts.
3. **Bimodal token saving** — 11.3% in the safe zone, jumps to 66.9% only AFTER the cliff. No
   intermediate free lunch: you cannot get large savings without crossing into fact loss.

### Per-question at the cliff (level 0.66, measured)
| Question (project) | retention @0.66 |
|---|---|
| Q1 my 10-yr experience (resume) | 0.0 (all employer names lost — narrative worst) |
| Q4 PhotoBack numbers | 0.25 |
| Q2 AnimeVlog / Q6 CCK | 0.60 |
| Q5 quant headline | 0.667 |
| Q3 apple-ml | 0.80 |
Narrative/prose-heavy questions collapse hardest; code/identifier-heavy ones survive longer, because
the operator preserves code lines over prose.

## Interpretation (for the 6-project deployment)
- Use **lossless tiering** freely — it costs nothing in fidelity (confirmed N=6).
- Use **summarization only at level ≤0.33** — safe (100% grounding) but modest saving (~14%).
- Do NOT summarize aggressively (≥0.66) for fact/narrative recall — grounding collapses to ~49%.
- This mirrors the quant study's precision axis: aggressive compression is safe until it crosses the
  point where it changes the behavior you care about — here, ~level 0.33.

## What would make this EMPIRICAL (rule 6a — not yet met)
- N is 6 questions on 6 sources; adequate for a directional signal, not for a statistical claim.
- Fact detection is keyword-overlap (a proxy); a stronger measure is real answer grading.
- No task-success: this measures fact PRESENCE, not agent ANSWER quality. The empirical threshold is
  the real-agent SWE-bench run (C1/C2/C4 conditions, McNemar + CIs), which needs API budget + Docker.

## Reproduce
```sh
python research/eval_n6.py                      # N=6 fidelity table (this doc's numbers)
python research/harness/summarized_tier.py       # operator + curve self-test
python research/harness/grounding.py             # lossless null-control self-test (on the lossless branch)
```
