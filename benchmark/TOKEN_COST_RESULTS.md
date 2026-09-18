# Consistent Context Kit — Measured Results: Token Cost of Tiered Context

> Status: PRELIMINARY measured apparatus result (not a task-quality claim).
> Real measured data at N=6; larger N is a closed-form projection from measured per-project averages.
> Task-success/quality is NOT measured here (mock-only harness) — see research/STATUS.md.

## What is measured
Per-turn context tokens for a live 6-active-project deployment, comparing:
- **Monolithic**: all project context always in context every turn.
- **Tiered**: always-on tier (rules + indexes) + on-demand skills loaded only when a task touches a project.

Tokenizer: **real GPT-2 BPE** (not a bytes/token estimate). Reproduce: run the tokenizer over
`~/.kiro/steering/*.md` (always-on) and `~/.kiro/skills/*/SKILL.md` (per-project bodies + metadata).

## Measured (N=6, real BPE)
| Metric | Tokens/turn |
|---|---|
| Monolithic | 8531 |
| Tiered | 5815 |
| **Reduction** | **31.8%** |

Always-on tier = 4293 tokens; mean per-project body = 706, metadata = 70 (n=6 projects). The tiered
figure charges the single largest active body (animevlog, 1102 tok), so the measured reduction is
conservative relative to the mean-based projection — see research/TOKEN_COST_MODEL.md §6.

## Projected (closed-form model, measured per-project averages)
| Projects | Monolithic | Tiered | Reduction |
|---|---|---|---|
| 10 | 11353 | 5699 | 49.8% |
| 25 | 21943 | 6749 | 69.2% |
| 50 | 39593 | 8499 | 78.5% |
| 100 | 74893 | 11999 | 84.0% |
| asymptote | — | — | 90.1% |

Projections are a model, not measured runs — labeled as such.

## Recall preservation (measured)
Tiering must not lose retrievable facts. Recall battery: **5/5 probes passed** on fresh
non-interactive sessions — measured Int4 compression (3.7x), mlx-vlm bug origin (PhotoBack),
zero-interference Jaccard (0.0), active-context enumeration, inactive-project (mlx-vlm) exclusion.

## Improvement over the earlier run (methodology)
An earlier measurement (docs/paper/results.json, 2026-09-04) used a **~4 bytes/token estimate**.
This run replaces the estimate with a **real BPE tokenizer** and separates *measured* from *projected*.
The upgrade is methodological accuracy; N grew from 4 to 6 as active projects were added.

## What this is NOT (honesty gate)
- NOT a task-quality/agent-success result. The SWE-bench harness runs only a RIGGED MockAgent
  (resolves by string-match, never fails; McNemar b=c=0). NO scientific claim about "better outcomes"
  follows. See research/STATUS.md.
- The empirical threshold for a publishable claim = a **real-agent SWE-bench run** (C0-C3 conditions,
  real test-execution grading, McNemar + bootstrap CIs). Until that exists, no DOI/preprint.

## Reproduce
- Token cost: `benchmark/` (real BPE over the live steering+skills files).
- Recall battery: fresh `kiro-cli --no-interactive` sessions, 5 probes.
