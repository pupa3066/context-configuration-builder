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

## Amendment 1 (before either submission)

The lexical command in both arms was `grep -rn ... | head -40`, which keeps the first 40 matches in
directory order. That cuts the lexical retriever's coverage, the confound this repository studies, and would
bias the comparison against arm A. In both arms identically it is replaced by a definition-line search
(`grep -rnE --include=*.py "(def|class) IDENTIFIER\b"`, the same pattern as retrieval metric m2) followed by
a file list (`grep -rlw`). The arms still differ only in retrieval order. Hypothesis, outcome, analysis and
interpretation rules are unchanged. The commit time of this amendment is its registration time.

## Amendment 2 (before either submission)

grep is removed from both arms. The lexical retriever is now BM25, written by the agent to /tmp/bm25.py from
text in its prompt and run with run_command. It uses the tokenizer, stopword list, 8-line chunk length and
parameters (k1=1.5, b=0.75) of benchmark/compare_algorithms.py, with one difference: chunks are formed per
file, so it can report file and line locations, instead of over the concatenated corpus. It indexes every
.py file under /workspace and prints the top 6 chunks. A Kaggle check (notebook purnimapathak15/cck-bm25-check)
on black and fastapi: exit code 0, about 0.6 s per query, 1,372 to 1,867 characters of output.

The arms are now benchmark/gemma_agent/submission_v7_lexical (A: BM25 first, search_similar_code as
fallback) and benchmark/gemma_agent/submission_v7_dense (B: search_similar_code first, BM25 as fallback).
Both are generated from one template and differ only in retrieval order and the agent name label.
Hypothesis, outcome, analysis and interpretation rules are unchanged. The commit time of this amendment is
its registration time.

## Amendment 3 (registered before any v8 result)

Arm A (v7 lexical) was submitted at 15:28:51 UTC on 12 November and resolved 0 of 58; an earlier configuration
also resolved 0 of 58. Two zero scores from different configurations indicate a failure in how our agents run,
not an effect of retrieval order, so the v7 comparison is closed as uninformative and arm B (v7 dense) will not be
submitted.

The test continues with v8 arms (benchmark/gemma_agent/submission_v8_lexical and submission_v8_dense, commit
4be0fc1). Both are built on the organizers' sample prompt, a single agent with all nine harness tools, sampling
temperature 0.2, top_p 0.95, max_output_tokens 8192, thinking budget 4096 with thoughts included, and an
eval_config.yaml budget of 8 minutes, 28 tool calls, 240 s per command and 80 turns, the settings shared by public
configurations reported to score above zero. BM25 is delivered as a skill script (skills/bm25-localize,
run with run_skill_script) instead of a shell command in the prompt; it ranks 8-line chunks of every non-test .py
file. The arms differ only in a step-0 block: v8 lexical calls the BM25 skill first and search_similar_code as
fallback; v8 dense uses the reverse order.

Both arms are first run on published tasks with the self-test harness (benchmark/gemma_agent/diag_agent_selftest.ipynb).
That run checks that the configuration executes and produces patches; it is not the registered outcome. The
registered outcome is the public leaderboard score of each v8 arm, analyzed as in the Outcome and analysis section.
Hypothesis, analysis and interpretation rules are unchanged.
