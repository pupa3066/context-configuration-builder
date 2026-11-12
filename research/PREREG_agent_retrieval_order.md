# Pre-registration: retrieval order in a coding agent (two leaderboard submissions)

Registered 2026-11-12, before either submission was made. The commit time of this file is the
registration time.

## Question

When the dense index covers the whole repository, does the order in which an agent uses a lexical
retriever (grep over every file) and a dense retriever (the harness tool search_similar_code over the
competition-provided embeddings) change how many tasks it resolves?

## Background

Controlled retrieval experiments in this repository (benchmark/CURRENT_STATE.md, studies three to five)
found that with the dense index covering the full corpus and chunks within the embedder window, BM25 and
dense retrieval are equivalent within 0.10 on all three retrieval metrics, on six repositories (N=480).
Large lexical advantages appeared only when the dense index covered part of the corpus or when chunks
exceeded the embedder input window.

## Arms

Both arms use the same model (gemma-4-31b-it-qat-w4a16-ct), tools, sub-agent, sampling settings, budgets
and tasks. They differ only in the localization instructions in prompts/system.md and
sub_agents/analyzer.md (plus the agent name label).

- A, lexical first: benchmark/gemma_agent/submission_v6. grep over the repository first; search_similar_code
  as fallback.
- B, dense first: benchmark/gemma_agent/submission_v6dense. search_similar_code first; grep as fallback.

## Outcome and analysis

- Primary outcome: resolved tasks out of 58 on the public leaderboard, per arm.
- Analysis: difference in resolved rate (A minus B) with a 95% Newcombe interval for two independent
  proportions. The leaderboard reports no per-task results, so no paired test is possible.
- Sensitivity: with 58 tasks per arm and a resolved rate near 0.15, a two-sided test at 0.05 with 80% power
  detects a difference of about 0.19 (about 11 tasks). Smaller differences are not detectable here.

## Prediction

From the retrieval results, the retriever order should not decide the outcome at full coverage: we predict
the difference will be inside the 95% interval around zero. Because of the sensitivity limit, a result
consistent with zero is weak evidence; it is consistent with the prediction but does not establish
equivalence for task success.

## Interpretation rules, fixed in advance

- Difference inside the interval around zero: reported as consistent with the prediction and inconclusive
  for equivalence.
- Difference outside it: reported as a task-success effect of retrieval order, in whichever direction it
  falls, and as evidence against the prediction.
- Both arms 0 of 58: reported as uninformative about retrieval order (a failure common to both arms).
- No other outcomes or subsets will be analyzed.
