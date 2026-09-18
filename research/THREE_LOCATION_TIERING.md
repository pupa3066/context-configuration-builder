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
