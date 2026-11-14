# Results ledger: what was registered before the data, and what was not

One page for readers who want to separate confirmatory results from exploration. "Registered" means the test, the
prediction and the analysis were committed before the result existed (commit hashes and amendment numbers in
research/PREREG_20day_agent_plan.md, research/PREREG_agent_retrieval_order.md and
research/PREREG_tiered_context_gemma_harness.md). Agent self-test rates are on published tasks; see the caution at
the end.

## Retrieval (the writeup, Sections 3.1 to 3.6)

| Result | Status | Outcome |
|---|---|---|
| Async functions missing from the competition code index | Measured audit | 0 of 914 fastapi and 0 of 100 httpx async functions indexed; confirmed by the organizers, who report that scored private tasks touch no async code |
| Coverage decides lexical versus dense | Controlled experiment, two sets | Gap 0.20 to 0.53 at a 1,000-chunk budget; equivalent within 0.10 at full coverage (N = 480) |
| Coverage explains the gap | Per-question decomposition | Dense finds indexed answers 0.88 to 0.92 at every budget |
| Chunk length past the embedder window | Controlled experiment plus probe | Best-segment scoring fixes 56, breaks 2 (p = 1.2e-14) |
| Same pattern on the toolkit repository | Replication, small N | Same direction, N = 34 |
| Real issue texts as queries | Exploratory, after the writeup | BM25 0.26, dense 0.37 full and 0.24 at 25 percent coverage (N = 38, no significant difference) |

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
| Test before submit (V), larger budget (B), new files (F) vs G, 16 tasks | amendments 15 to 18 | V 4, B 6, F 4, G 5 (p = 1.0 each; 9 of the 16 tasks are scorable). F created none of the new files its rule asked for. B, the only arm above G, is being confirmed on the 72 scorable tasks |
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
  packages we did not have (inline_snapshot 27, dirty_equals 7), requests test files whose unrelated tests fail here
  (18), and an installed httpx that appears to shadow the repository's (1); in one task (rich_3486) the gold fix itself
  did not pass a required test. No agent run resolved a task whose gold fix fails.
