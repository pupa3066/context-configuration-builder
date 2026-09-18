# Cross-Model Token-Cost Comparison

> Measured comparison of every tiering token-model on the same live deployment (real gpt2-BPE, N=6).
> Structure/cost only, not task quality (that needs a real-agent SWE-bench run). Reproduce:
> `python research/compare_token_models.py`

## Measured (N=6, live ~/.kiro; always_on=4006, on_demand=3520, mean_body=706, mean_meta=70, max_body=1102)
| Token-model | what sits always-on | per-turn tokens | reduction vs monolithic |
|---|---|---|---|
| monolithic | everything resident | 11764 | 0% |
| tiered_2location | steering + on-demand folded in + skill metadata | 9048 | 23.1% |
| tiered_3location | lean steering + skill metadata (on-demand deferred) | 5528 | 53.0% |
| rule_tiering | 3location + rule detail also deferred (stub kept) | 5528 | 53.0% |

## Interpretation
- The dominant win is the ON-DEMAND SEPARATION: 2location (23.1%) to 3location (53.0%) nearly doubles
  the saving, because ~3520 tokens of governance/formatting/cross-links detail move off the every-turn
  path and load only when a task triggers them.
- 3location and rule_tiering measure EQUAL on a typical turn (f_od = 0): both defer the same content.
  rule_tiering's separate value is that governance/formatting RULE detail is also deferred while a
  one-line stub keeps each rule firing every turn; the difference appears on publish/merge turns that
  would otherwise load the full rule text.
- monolithic scales worst: each project adds a full ~706-token body every turn; tiered adds only the
  ~70-token metadata for inactive projects.

## What is NOT measured here
Task quality (does tiering resolve as many tasks). That requires a real-agent SWE-bench run on
Docker + a code model; see research/harness/contribute_run.py and research/harness/compare_all.py
(Family B). This doc is Family A (structure/cost) only.

## For contributors
Run `python research/compare_token_models.py` on your own deployment and report a row: N_projects,
always_on, on_demand, and per-turn reduction. For the task-quality axis, use `contribute_run.py`
(needs Docker + a code model) and submit the bundle per CONTRIBUTING (attribution + provenance gate).
