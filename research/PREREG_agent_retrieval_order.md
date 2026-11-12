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

## Amendment 4 (before any v8 result): description of arm B's retriever

The harness documentation (HARNESS_README.md, section 6.3) states that search_similar_code runs offline without
a neural text encoder: it resolves the query against graph node names, then ranks nodes by cosine similarity of
the pre-computed node embeddings, with a lexical token-overlap fallback for multi-word queries. Arm B therefore
does not test dense retrieval of the issue text; it tests the harness's node index first, an index that
contains no async functions (benchmark/harness_audit/). The registered comparison is accordingly read as a
coverage comparison: BM25 over every non-test Python file first, against the harness node index first. The arms,
outcome, analysis and interpretation rules are unchanged.

## Amendment 5 (before any leaderboard result for v8 or v8.1)

A self-test of v8 on three published tasks (purnimapathak15/cck-diag-v8) showed both arms compile, make 16 to 28
tool calls and produce a patch on every run, but the step-0 instruction was followed in 1 of 3 runs of the lexical
arm and 0 of 3 of the other, so the arms barely differed in practice. The registered arms are replaced by v8.1
(benchmark/gemma_agent/submission_v81_lexical and submission_v81_dense, commit c83184b): the first tool call is made
mandatory, and search_similar_code is called with a function, class or module name in both arms, as the harness
documentation advises. Nothing else changes. v8.1 is self-tested before submission. Hypothesis, outcome,
analysis and interpretation rules are unchanged.

## Amendment 6 (before any leaderboard result for v8.1): measured compliance

The v8.1 self-test (purnimapathak15/cck-diag-v81, three published tasks per arm; benchmark/gemma_agent/selftest_results/)
produced a patch on all six runs and resolved one of three tasks in each arm. The lexical arm called the BM25 skill
first in two of three runs. The search-first arm called search_similar_code in none of three runs, despite the
instruction to make it the first call. A leaderboard comparison of the two arms therefore would not isolate retrieval
order: in practice arm B does not use the harness index. Arm A (v8.1 lexical) is submitted as registered, as a
measurement of a working full-coverage configuration; arm B is held until a version that actually calls the harness
search tool is confirmed in a self-test. Hypothesis, outcome and analysis rules are unchanged.

## Amendment 7: paired self-test of a full-coverage localizer (registered before it runs)

Because the search-first arm does not call the harness search tool, retrieval order cannot be tested with it. We
register a different paired comparison, run with the self-test harness on published tasks before the paper deadline:

- Arm L: v8.1 lexical (benchmark/gemma_agent/submission_v81_lexical).
- Arm N: v8.1 without the BM25 skill (benchmark/gemma_agent/submission_v81_noskill): the same files with the step-0
  block and the skills entry removed. The agent keeps all harness tools, including grep through run_command.
- Tasks: 16 published tasks, the same for both arms, drawn with random.Random(0).sample from tasks 4 to 129 of
  tasks.jsonl: fastapi_13713, fastapi_14077, fastapi_14360, fastapi_14361, fastapi_14372, fastapi_14485, fastapi_14986, fastapi_5624, rich_2725, rich_3064, rich_3469, rich_3480, rich_3521, rich_3772, rich_3777, rich_3953.
- Budget: each arm's eval_config.yaml (8 minutes, 28 tool calls); same model, harness and machine type.
- Outcome: tasks resolved per arm; exact two-sided McNemar test on the discordant tasks. With 16 tasks only large
  differences are detectable; a small or null difference is reported as inconclusive.
- Prediction: arm L resolves at least as many tasks as arm N. This is a directional expectation from the coverage
  results, not a claim the test is powered to confirm.
