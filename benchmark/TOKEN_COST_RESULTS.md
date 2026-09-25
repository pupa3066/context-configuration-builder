# Consistent Context Kit  -  Measured Results: Token Cost of Tiered Context

> Status: PRELIMINARY measured apparatus result (not a task-quality claim).
> Real measured data at N=4; larger N is a closed-form projection from measured per-project averages.
> Task-success/quality is NOT measured here (mock-only harness)  -  see research/STATUS.md.

## What is measured
Per-turn context tokens for a live 4-active-project deployment, comparing:
- **Monolithic**: all project context always in context every turn.
- **Tiered**: always-on tier (rules + indexes) + on-demand skills loaded only when a task touches a project.

Tokenizer: **real GPT-2 BPE** (not a bytes/token estimate). Reproduce: run the tokenizer over
`<agent-config-dir>/steering/*.md` (always-on) and `<agent-config-dir>/skills/*/SKILL.md` (per-project bodies + metadata).

Environment: agent config directory = ~/.kiro (Kiro CLI).

## Measured (N=4, real BPE)
| Metric | Tokens/turn |
|---|---|
| Monolithic | 6958 |
| Tiered | 5253 |
| **Reduction** | **24.5%** |

Always-on tier = 3859 tokens; mean per-project body = 774, metadata = 73 (n=4 projects).

## Projected (closed-form model, measured per-project averages)
| Projects | Monolithic | Tiered | Reduction |
|---|---|---|---|
| 10 | 11599 | 5363 | 53.8% |
| 25 | 23209 | 6458 | 72.2% |
| 50 | 42559 | 8283 | 80.5% |
| 100 | 81259 | 11933 | 85.3% |
| asymptote |  -  |  -  | 90.6% |

Projections are a model, not measured runs  -  labeled as such.

## Recall preservation (measured)
Tiering must not lose retrievable facts. Recall battery: **5/5 probes passed** on fresh
non-interactive sessions  -  measured Int4 compression (3.7x), mlx-vlm bug origin (PhotoBack),
zero-interference Jaccard (0.0), active-context enumeration, inactive-project (mlx-vlm) exclusion.

## Improvement over the earlier run (methodology)
An earlier measurement (docs/paper/results.json, 2026-09-04) used a **~4 bytes/token estimate**.
This run replaces the estimate with a **real BPE tokenizer** and separates *measured* (N=4) from
*projected* (N>=10). The upgrade is methodological accuracy, not a larger experiment  -  N is still 4.

## What this is NOT (honesty gate)
- NOT a task-quality/agent-success result. The SWE-bench harness runs only a RIGGED MockAgent
  (resolves by string-match, never fails; McNemar b=c=0). NO scientific claim about "better outcomes"
  follows. See research/STATUS.md.
- The empirical threshold for a publishable claim = a **real-agent SWE-bench run** (C0-C3 conditions,
  real test-execution grading, McNemar + bootstrap CIs). Until that exists, no DOI/preprint.

## Reproduce
- Token cost: `benchmark/` (real BPE over the live steering+skills files).
- Recall battery: fresh non-interactive agent sessions, 5 probes.
