# Results ledger: what was registered before the data, and what was not

One page for readers who want to separate confirmatory results from exploration. "Registered" means the test, the
prediction and the analysis were committed before the result existed (commit hashes and amendment numbers in
research/PREREG_20day_agent_plan.md, research/PREREG_agent_retrieval_order.md and
research/PREREG_tiered_context_gemma_harness.md). Agent self-test rates are on published tasks; see the caution at
the end.

## What the evidence says (updated 2026-11-16)

The index decides what retrieval can find. Coverage, not the retrieval method, decided the lexical-versus-dense
comparison in two controlled sets, and chunks longer than the embedder window hid code from it; these three tests hold
after Holm correction over all 26 primary tests. The competition index contains none of the 1,014 async functions of
fastapi and httpx. On real problem statements at full coverage, dense retrieval found the changed code more often than
BM25 (125 competition tasks and 114 django tasks), so the evidence supports coverage as the deciding factor, not lexical
search as the better method; these real-query results hold only in a retrieval-only family chosen after the results.

At the agent level, retrieval is not what limits task completion. Of the 31B agent's 45 failures on scorable tasks, 3
never found the right file and 26 wrote a wrong fix in the right file; a retrieval hit on the problem statement did not
predict a solved task (Fisher p = 0.46 to 1.0). The small model, told exactly which files to fix, solved 5 of 46. None of
the 20 registered agent tests detected a difference. On 46 to 72 tasks an exact McNemar test needs about 6 net wins with
no losses to reach p < 0.05, and the largest net difference any arm showed was 3 tasks (analysis rules: plan amendment
24). The measured gap is fix-writing, not finding.

## Retrieval (the writeup, Sections 3.1 to 3.6, then registered tests on real problem statements)

| Result | Status | Outcome |
|---|---|---|
| Async functions missing from the competition code index | Measured audit | 0 of 914 fastapi and 0 of 100 httpx async functions indexed; confirmed by the organizers, who report that scored private tasks touch no async code |
| Coverage decides lexical versus dense | Controlled experiment, two sets | Gap 0.20 to 0.53 at a 1,000-chunk budget; equivalent within 0.10 at full coverage (N = 480) |
| Coverage explains the gap | Per-question decomposition | Dense finds indexed answers 0.88 to 0.92 at every budget |
| Chunk length past the embedder window | Controlled experiment plus probe | Best-segment scoring fixes 56, breaks 2 (p = 1.2e-14) |
| Same pattern on the toolkit repository | Replication, small N | Same direction, N = 34 |
| Real issue texts as queries | Exploratory, after the writeup | BM25 0.26, dense 0.37 full and 0.24 at 25 percent coverage (N = 38, no significant difference) |
| Real problem statements, 125 competition tasks | Registered, plan amendment 19 | Primary, BM25 vs dense at full coverage: 0.184 vs 0.312, p = 0.011, dense leads. Secondary, coverage: dense full 0.312 vs 25 percent 0.248, p = 0.17, not detected |
| SWE-bench Lite, django shard (114 tasks; preliminary, the registered test pools all shards) | Registered, tiered-context plan, SWE-bench Lite section | Coverage: dense full 0.342 vs 25 percent 0.210, p = 0.006. BM25 vs dense at full coverage: 0.228 vs 0.342, p = 0.035, dense leads. Chunk length (secondary): not supported, and confounded by returned text volume; an equal-text analysis is registered and not yet run. Other shards incomplete |
| Bridge: does a retrieval hit predict a solved task? | Registered, plan amendment 19 | Not supported for 31B or E4B (Fisher p = 0.46 to 1.0) |

## Agent experiments (registered tests, in order)

| Test | Registered in | Outcome |
|---|---|---|
| BM25-first vs search-tool-first on the leaderboard | retrieval-order plan, before any result | Not run as designed: both arms failed to compile (skill name), then agent compliance made the test uninformative (amendments 3 to 6) |
| BM25 skill vs no skill, 16 tasks | retrieval-order amendment 7 | 4 vs 4, p = 1.0; later found invalid: the skill searched its own folder (plan amendment 4) |
| Grep inside the sandbox (G) vs no search step (N), 16 tasks | amendment 5 | 5 vs 4, p = 1.0; trace gate passed |
| G vs N, all 129 tasks | amendment 7 | 30 vs 28, p = 0.73; on the 21 async-fix tasks 4 vs 3 |
| G vs N, 67 fastapi tasks (replicating an exploratory lead) | amendment 9 | 14 vs 15, p = 1.0; the lead did not replicate |
| Token use, G vs N | amendment 11 (a) | No difference (p = 0.36 and 0.22, opposite directions) |
| 40-line windowed reads (W) vs G, 16 tasks | amendment 11 (b) | 31B tokens -1.2 percent (p = 0.47); E4B -19.1 percent (p = 0.07) |
| Windowed reads, E4B, 56 new tasks (replication) | amendment 12 | -3.6 percent (p = 0.74); did not replicate |
| Small-model arms (E4B): BM25 skill, grep, shorter prompt, larger reasoning budget | amendments 2, 5, 6, 8 | 1 to 2 of 16 in every arm; no difference detected |
| Test before submit (V), larger budget (B), new files (F) vs G, 16 tasks | amendments 15 to 18 | V 4, B 6, F 4, G 5 (p = 1.0 each; 9 of the 16 tasks are scorable). F created none of the new files its rule asked for |
| Larger budget (B) vs G, 72 scorable tasks | amendment 18 | 30 vs 27, p = 0.51, not detected. On the leaderboard B exceeded the 12-hour runtime limit and received no score (amendment 23 outcome) |
| E4B: ranked 8-line lexical chunk search (R-E4B) vs grep, 46 scorable tasks | amendment 20 | Resolved 3 vs 3, p = 1.0. Read or edited a gold file 38 vs 33, p = 0.18. Tokens +15.8 percent, p = 0.025, against the prediction (secondary) |
| E4B: fix check before submit (RC-E4B) vs R-E4B, same run | amendment 21 | 5 vs 4, p = 1.0; submissions after a failing own test rose from 15 to 25 |
| E4B told the gold files (D1) | amendment 22 | 5 of 46 (R-E4B 3 and 4); 39 failures were wrong fixes in the right file |
| Distillation LoRA for E4B | amendment 10 | Not completed; no result (amendment 10 outcome) |
| Tiered vs monolithic repository context | tiered-context registration and amendments 1 and 2 | Paused before any outcome; rerun after a quota reset |

## Exploratory analyses (not registered; leads only)

- Failure analysis of G's runs (amendment 14, redone on the 72 scorable tasks in amendment 17): of 45 failures, 3 never found the right file, 6 edited elsewhere, 26 were wrong fixes in the right file (23 never ran pytest), 10 produced no patch. Of the 11 tasks needing new files, 4 are scorable locally.
- Small model: on 56 tasks E4B never finds the right file in 15 (27 percent) against 3 (5 percent) for 31B.
- G's net gain on fastapi in the 129-task run (4 vs 0); tested and not replicated (amendment 9).

## Caution on agent self-test rates

Some published tasks cannot be scored in the self-test environment: tests that import packages absent from it
(dirty_equals, inline_snapshot) fail with or without a correct fix, and at least one task passes with no fix at all.
The gold-patch control (amendment 17, notebook harness-gold-patch-control-129tasks) found 72 scorable tasks of 129: the
gold fix fails on 54 and 3 pass with no fix. Over the 72, G resolves 27 and N 26 (38 vs 36 percent, p = 1.0); conclusions
are unchanged, and the 31B agent solves about 37 percent of solvable tasks. Failures of G on scorable tasks: 3 of 45
never found the right file; for E4B, 13 of 43 (30 percent).

## What we learned about our local self-test (from the gold-patch control)

- Our local self-test runs published tasks, while the leaderboard scores hidden tasks from other repositories. We now
  think the two are best compared only arm against arm on the same tasks: on the published tasks that can be scored
  locally, our 31B agent resolves about 37 percent, while its leaderboard scores are 0.15 and 0.17.
- In the writeup we set our 4 of 16 published tasks beside public leaderboard scores. We have since learned that 7 of
  those 16 tasks cannot be scored in our local environment, so we would no longer draw that comparison.
- The same 16-task set has 9 scorable tasks, which is too few to say much about the arms tested on it (including V
  and B). Our remaining self-tests use the 72 scorable tasks (benchmark/harness_audit/scorable_tasks_72.txt).
- As far as we can tell, the gold fix fails on 54 tasks because of our environment rather than the tasks: test
  packages we did not have (inline_snapshot 27, dirty_equals 7), test files whose other tests fail here (18: requests
  12, rich 4, fastapi 2), and an installed httpx that appears to shadow the repository's (1); in one task (rich_3486) the gold fix itself
  did not pass a required test. No agent run resolved a task whose gold fix fails.
- Prior reports. Other participants found these limits first, on the competition forum: gold patches failing for most
  fastapi and requests tasks because test packages are missing (topic 743973, 28 September); a gold-patch and
  empty-patch audit of all 129 tasks with 68 valid (Manohar Papasani, 2026, Kaggle forum topic 756400, 6 November); the
  missing inline_snapshot and dirty_equals packages (34 tasks) and an httpbin fixture behind 12 psf/requests failures,
  with a ceiling of 74 of 129 (larry54321zhao, 2026, Kaggle forum topic 757661, 10 November); and harness conventions
  that make rich_3486 and fastapi_14186 unresolvable (Hersh Mittelman, 2026, Kaggle forum topics 751707 and 757893).
  Several Paper Track writeups report the same ceiling (70 to 75 of 129 in the Kaggle subprocess sandbox, 3 tasks passing
  with an empty patch). Our control, run on 14 November, agrees; its 72 scorable tasks are the denominator of our
  self-tests, not a new finding. The cause of the 12 requests failures is not visible in the 6,000-character test-output
  tail we saved; it is consistent with the httpbin fixture reported in topic 757661.
- The async gap in the code index was first reported by Jason Wold (2026, Kaggle forum topic 742911, 24 September:
  0 of 305 async definitions present) before the organizers' note (topic 745998); our writeup credits only the note.

## Correction for multiple comparisons (Holm, recomputed 2026-11-16)

Exact p-values from the recorded outcomes, Holm-corrected. Script: research/holm_primary_tests.py. Neither family below
was declared before the results. Family 1, every primary test with an outcome (26), is reported as primary because it
is the stricter choice; family 2, the six retrieval tests, is labelled post hoc. Secondary outcomes (for example the
token increase of R-E4B, p = 0.025) are not corrected and are not used as confirmatory. From 2026-11-16, families are
declared in advance (plan amendment 24). The previous 13-test table (2026-11-14) is superseded; it reached the same
conclusion for family 1.


Family 1, primary: every primary test with an outcome (m = 26). Three hold.
| Test | p | Holm-adjusted p | Holds at 0.05 |
|---|---|---|---|
| Coverage, docstrings set 1: BM25 vs dense at a 1,000-chunk budget | 1.8e-20 | 4.7e-19 | yes |
| Chunk length: best-segment vs whole-chunk dense, 400-word chunks | 1.2e-14 | 3e-13 | yes |
| Coverage, docstrings set 2: BM25 vs dense at a 1,000-chunk budget | 1.7e-13 | 4.1e-12 | yes |
| SWE-bench Lite django shard: dense full vs 25 percent coverage | 0.0059 | 0.14 | no |
| Real problem statements, 125 tasks: BM25 vs dense at full coverage | 0.011 | 0.24 | no |
| SWE-bench Lite django shard: BM25 vs dense at full coverage | 0.035 | 0.74 | no |
| Tokens, 40-line windows vs grep, E4B, 16 tasks | 0.07 | 1 | no |
| Tokens, G vs N, 67 fastapi tasks | 0.22 | 1 | no |
| Tokens, G vs N, 129 tasks | 0.36 | 1 | no |
| Tokens, 40-line windows (W) vs G, 31B, 16 tasks | 0.47 | 1 | no |
| Larger budget (B) vs G, 72 scorable tasks | 0.51 | 1 | no |
| G vs N, fastapi replicate, 29 scorable tasks | 0.62 | 1 | no |
| E4B told the gold files (D1) vs R-E4B run 1, 46 tasks | 0.62 | 1 | no |
| Tokens, 40-line windows vs grep, E4B, 56 tasks (replication) | 0.74 | 1 | no |
| BM25 skill vs no skill, 16 tasks (skill later found defective) | 1 | 1 | no |
| Grep first (G) vs no search step (N), 16 tasks | 1 | 1 | no |
| G vs N, 72 scorable tasks | 1 | 1 | no |
| E4B: BM25 skill vs no skill, 16 tasks | 1 | 1 | no |
| E4B: grep first vs no search step, 16 tasks | 1 | 1 | no |
| E4B: shorter prompt vs grep first, 16 tasks | 1 | 1 | no |
| E4B: double reasoning budget vs shorter prompt, 16 tasks | 1 | 1 | no |
| Test before submit (V) vs G, 16 tasks | 1 | 1 | no |
| Larger budget (B) vs G, 16 tasks | 1 | 1 | no |
| New-files rule (F) vs G, 16 tasks | 1 | 1 | no |
| E4B: ranked 8-line chunk search (R-E4B) vs grep, 46 tasks | 1 | 1 | no |
| E4B: fix check (RC-E4B) vs R-E4B, 46 tasks | 1 | 1 | no |

Family 2, post hoc: retrieval tests only (m = 6). All six hold, including the two real-query tests in which dense leads; the django results are one shard of a pooled test.
| Test | p | Holm-adjusted p | Holds at 0.05 |
|---|---|---|---|
| Coverage, docstrings set 1: BM25 vs dense at a 1,000-chunk budget | 1.8e-20 | 1.1e-19 | yes |
| Chunk length: best-segment vs whole-chunk dense, 400-word chunks | 1.2e-14 | 6e-14 | yes |
| Coverage, docstrings set 2: BM25 vs dense at a 1,000-chunk budget | 1.7e-13 | 6.8e-13 | yes |
| SWE-bench Lite django shard: dense full vs 25 percent coverage | 0.0059 | 0.018 | yes |
| Real problem statements, 125 tasks: BM25 vs dense at full coverage | 0.011 | 0.022 | yes |
| SWE-bench Lite django shard: BM25 vs dense at full coverage | 0.035 | 0.035 | yes |
