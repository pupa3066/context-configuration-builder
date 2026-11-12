# Pre-registration: carrying the coverage results to agent task success (Agent Track, 20 days)

Registered 2026-11-12, before any of the arms below has a leaderboard result. The commit time of this file is the
registration time. Companion to research/PREREG_agent_retrieval_order.md (amendments 1 to 7).

## Question

Does the share of the repository an agent's localizer can see change how many tasks the agent resolves?
Retrieval experiments (benchmark/CURRENT_STATE.md) show that a retriever cannot find code it never indexed, and
the competition's code index contains no async functions (benchmark/harness_audit/). This plan tests whether
those blind spots change task success.

## Design rule learned from the self-tests

Arms differ in what the agent has, not in what it is told: in the v8.1 self-test the agent ignored an instruction
to call the harness search tool first (amendment 6). Every arm below shares the v8.1 lexical files
(benchmark/gemma_agent/submission_v81_lexical) and changes one thing.

| Arm | Directory | The one change |
|---|---|---|
| L | submission_v81_lexical | none: BM25 skill over every non-test .py file |
| N | submission_v81_noskill | BM25 skill and its step-0 block removed; harness tools and grep remain |
| C50 | submission_v81_cov50 | BM25 skill indexes a fixed half of the files (SHA-256 of the path, even values) |
| A0 | submission_v81_noasync | BM25 skill skips every line inside an async function, as the harness index does |

## Two instruments

1. **Self-test on published tasks (paired, per task).** Each arm runs with benchmark/gemma_agent/diag_agent_selftest.ipynb
   on the same published tasks, drawn with random.Random(0).sample from tasks.jsonl, 32 tasks if GPU quota allows and
   16 otherwise, each arm's eval_config.yaml budget. Each arm must produce patches in the self-test before it is
   submitted. Outcome: resolved per task. Test: exact two-sided McNemar of each arm against L.
   Secondary analysis: the same test restricted to tasks whose gold patch edits an async function
   (benchmark/harness_audit/ task audit), where A0 and N are predicted to lose most.
2. **Leaderboard (hidden tasks, totals only).** One submission per team per UTC day, starting 2026-11-13.

## Leaderboard schedule

| Days (UTC, from 2026-11-13) | Submission |
|---|---|
| 1 to 4 | L, N, C50, A0 |
| 5 to 8 | L, N, C50, A0 (second replicate) |
| 9 to 12 | L, N, C50, A0 (third replicate) |
| 13 to 20 | replicates of the two arms with the largest mean difference, alternating; any day may be skipped |

An arm that fails its self-test is replaced in the schedule by the next arm and repaired before its slot.

## Analysis, fixed in advance

- Report every leaderboard score with its date and the commit of the submitted zip.
- Noise: the spread of the three replicates of each arm.
- Arm comparison on the leaderboard: exact one-sided permutation test on the three replicate scores of an arm against
  the three of L (smallest attainable p = 0.05). A difference is reported only if that test gives p of at most 0.05;
  otherwise it is reported as not detected.
- Self-test comparison: as in instrument 1.

## Predictions

- L resolves at least as many tasks as N, C50 and A0.
- The C50 and A0 deficits, if any, concentrate on tasks whose fix lies in code they cannot see (files outside the
  kept half, or async functions).
- With 58 hidden tasks and reported noise of about two tasks between identical submissions, only differences of
  several tasks are detectable; null results are reported as not detected, not as equivalence.

## Final selections

Up to two final leaderboard selections: the arm with the highest mean replicate score, and L if it is not that arm.

## Contingency: if the competition data or harness changes (registered before any change)

The audit in benchmark/harness_audit/ measured the competition data released on 13 October 2026.

- If a new data or harness version is released, the audit is re-run on it with the same script, and the version and
  date are recorded with every later result.
- If the code graph gains async functions, arm N is submitted once before the change takes effect (if a slot allows)
  and once after it, with no other change; the difference is reported as the effect of the index change on task
  success. Arm A0 is kept as a deliberate recreation of the old gap.
- Scores from different data versions are never pooled or compared without stating the versions.

## Amendment 1 (recorded 2026-11-12 16:08 MT, before any leaderboard result of this plan)

The organizers state (competition discussion "Note on Code Graphs for Async Functions", 5 October 2026) that none of
the private-repository tasks used for scoring touch an async function. On the leaderboard, A0 is therefore
reclassified as a negative control: it is predicted to match L, and a difference would point to something other
than async coverage. The async effect of A0 is tested only on published tasks with the self-test harness, using the
secondary analysis above. All other arms, tests and the schedule are unchanged.

## Amendment 2 (recorded 2026-11-12 16:40 MT, before any result of these arms)

Small-model arms for the organizers' small-model prize (Gemma E2B or E4B, one of a team's two final submissions):
L-E4B = submission_v81e4b_lexical and N-E4B = submission_v81e4b_noskill, identical to L and N except the model line
(gemma-4-e4b-it-qat-w4a16-ct). One change per arm, so model size is the only difference from L and N.

Self-test first, no leaderboard slot: both arms on the same 16 published tasks as L and N, with the same harness and
budgets. Predictions: (1) each E4B arm resolves no more tasks than its 31B counterpart; (2) exploratory, L-E4B
resolves at least as many tasks as N-E4B, on the view that a smaller model gains more from retrieval that reaches
every file. Tests: exact McNemar per pair; with 16 tasks only large differences are detectable and a null is reported
as not detected. Any use of a leaderboard slot for an E4B arm, and the choice of final submissions (intended: one 31B
and one E4B), is registered here before that submission.

## Amendment 3 (recorded 2026-11-12 16:47 MT, before any result of the E4B arms)

Decision rule for the E4B arms. After the 16-task self-tests of amendment 2 finish:
- If at least one E4B arm resolves one or more of the 16 tasks, the E4B arm that resolves more tasks (L-E4B on a
  tie) is called E. Otherwise no E4B arm is submitted and the schedule below reverts to the original.
- E takes three leaderboard slots, on days 2, 6 and 10, and the original rotation moves back by one day each time:

| Days | Arms |
|---|---|
| 1 | L (submitted 2026-11-13 00:00 UTC) |
| 2 to 5 | E, N, C50, A0 |
| 6 to 9 | E, L, N, C50 |
| 10 to 13 | E, A0, L, N |
| 14 to 15 | C50, A0 (third replicates complete) |
| 16 to 20 | replicate the largest registered difference, as in the original plan |

Final submissions: the 31B arm with the highest mean public score over its replicates, and E, so the team is eligible
for both the main ranking and the small-model prize. Ties go to the arm with more replicates. The choice is recorded
here before it is made on Kaggle.
