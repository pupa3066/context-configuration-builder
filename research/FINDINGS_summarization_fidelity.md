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

## Result 2 — Summarization fidelity-vs-token curve (N=6, measured)
| Level | mean token saving | mean grounding retention | verdict |
|---|---|---|---|
| 0.00 (lossless) | 0% | 1.0 | safe |
| **0.33** | **13.7%** | **1.0** | **safe frontier — all 6 questions keep 100% of needed facts** |
| 0.66 | 65.6% | **0.486** | UNSAFE — loses ~half the needed facts |

**Mean safe-compression frontier = 0.33 across all 6 questions.**

### Per-question (measured)
| Question (project) | C2 lossless | C4 @0.33 save/ret | C4 @0.66 save/ret | safe |
|---|---|---|---|---|
| Q1 my 10-yr experience (resume) | ident, 1.0 | 0.096 / 1.0 | 0.865 / **0.0** | 0.33 |
| Q2 AnimeVlog img2anime fault | ident, 1.0 | 0.195 / 1.0 | 0.574 / 0.6 | 0.33 |
| Q3 apple-ml what it does | ident, 1.0 | 0.079 / 1.0 | 0.291 / 0.8 | 0.33 |
| Q4 PhotoBack measured numbers | ident, 1.0 | 0.323 / 1.0 | 0.738 / 0.25 | 0.33 |
| Q5 quant study headline | ident, 1.0 | 0.038 / 1.0 | 0.786 / 0.667 | 0.33 |
| Q6 CCK token-cost result | ident, 1.0 | 0.092 / 1.0 | 0.679 / 0.6 | 0.33 |

The narrative/experience question (Q1) is the MOST fragile: at level 0.66 it drops to 0.0 retention
(all employer names gone) — narrative content compresses worst because the operator preserves
code/identifier lines over prose, and Q1's facts live in prose.

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
