# Three-Location Tiering — Why the Structure Changed

> **Branch:** `feature/token-cost-three-location-tiering`. Documents a structural change to the live
> deployment that the original repo model did NOT describe, why it happened, and its measured effect.
> Rule 6a/6b: numbers below are MEASURED (real gpt2-BPE) on the author's live `~/.kiro/`, N=6 projects.

## Why this branched off
The original CCK model (see `benchmark/benchmark.py`, `research/TOKEN_COST_MODEL.md`) describes a
**2-location** structure:
- `~/.kiro/steering/*.md`  → always-on tier (loaded every turn)
- `~/.kiro/skills/*/SKILL.md` → per-project tier (metadata always; body on demand)

While self-testing CCK on the hardware-constrained (8GB) live machine, the **always-on steering tier
itself grew** (governance rules 6a/6b/20–23 added), pushing the every-turn cost up. Applying CCK's own
thesis to its own rules, the steering was split: safety/priority rules stay always-on; verbose
governance detail + the cross-project fact graph move to a NEW **on-demand** location that loads only
when a task triggers it. This produced a structure the original 2-location model did not account for.

## The change: 2-location → 3-location
| | OLD (repo model) | NEW (live) |
|---|---|---|
| always-on | all `steering/*.md` (~4293 tok) | lean `steering/*.md` (**3071 tok**) |
| on-demand tier | — (did not exist) | **`~/.kiro/on-demand/`**: governance appendix (970) + cross-links (666), loaded on trigger |
| per-project | `skills/*/SKILL.md` | `skills/*/SKILL.md` (unchanged) |

The always-on tier shrank because ~1.6k tokens of governance/cross-links detail moved to on-demand,
kept live-bindable via one-line stubs in `00-rules.md` (the rule still fires; the detail loads on
publish/merge/cross-project tasks via `bootstrap.md` step 2a).

## Measured supporting data (real gpt2-BPE, N=6 live)
```
always-on steering total .............. 3071 tok  (00-rules 1276, bootstrap 923, registry 564, portfolio 308)
on-demand (triggered, NOT every turn) . cross-links 666 + governance-appendix 970 = 1636 tok
project skills ........................ N=6, mean_body 706, mean_meta 70, max_body 1102 (animevlog)
per-turn: monolithic 7309  |  tiered 4593  |  reduction 0.372 (37.2%)
```

## Differences vs the other branches (scope boundaries)
- **`feature/token-cost-tiered-context-lossless`** — models tiering of PROJECT context (skills); grounding
  null-control. Does NOT cover steering-tier self-tiering. *This* branch is about the STEERING/rules tier.
- **`feature/token-cost-tiered-context-summarization`** — LOSSY compression of a tier (fidelity-vs-token).
  *This* branch is LOSSLESS relocation (stub + defer full detail), no summarization; grounding preserved.
- **`main` (`benchmark.py` / `TOKEN_COST_MODEL.md`)** — the 2-location model. *This* branch is the
  3-location correction: it adds the `on-demand` tier the 2-location model omits.

## The bug this fixes (rule 6b sanity)
Placing the governance appendix under `skills/` made `benchmark.py` miscount it as a 7th "project"
(body 970, meta 0), corrupting mean_body/mean_meta and N. Fix: governance moved to `~/.kiro/on-demand/`
so `skills/` = 6 real projects only. `benchmark.py` must be extended to measure the `on-demand` tier
(currently it only knows steering + skills) before its numbers describe the live 3-location reality.

## Status
MEASURED, live, N=6. This is a STRUCTURE/COST result (37.2% per-turn reduction with all rules still
firing via stubs), NOT a task-quality claim. Reproduce: re-run the measurement in this branch's commit.

## Bottom-line comparison — what each change did (measured, real gpt2-BPE)
| Change | Effect on a typical turn |
|---|---|
| Add on-demand tier (move detailed rules/cross-links off always-on) | **−1222 tokens (−28%)** ← the real win |
| Fewer projects (7→6) | ~−70 tokens (a project you're not using already costs only its ~70-tok metadata under tiering, not its ~706-tok body — so the count barely matters) |

Interpretation: the saving comes from **not loading detail you aren't using** (on-demand tier), NOT
from having fewer projects. Tiering already makes idle projects nearly free (metadata only).

## Per-query cost — the on-demand tier is ADAPTIVE (measured, N=6 live)
Saving scales with what a turn actually needs; every query type still beats monolithic (8945 tok/turn):
| Prompt (what it touches) | tiered/turn | monolithic | saving |
|---|---|---|---|
| "my 10-yr experience" (identity, normal turn) | 3491 | 8945 | 61.0% |
| "AnimeVlog img2anime fault" (1 project) | 4593 | 8945 | 48.7% |
| "publish to Figshare" (governance TRIGGER → loads appendix) | 4461 | 8945 | 50.1% |
| cross-project reasoning (TRIGGER → loads cross-links) | 6356 | 8945 | 28.9% |

The governance appendix (970 tok) and cross-links (666 tok) are charged ONLY on the turns that trigger
them; a normal turn never pays for them. Constants: always_on=3071, sum_metadata=420, all_bodies=4238.
