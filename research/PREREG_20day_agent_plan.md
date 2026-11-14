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

## Outcome of amendments 2 and 3 (recorded 2026-11-12 17:05 MT)

16 published tasks, same harness and budgets: L-E4B resolved 2 (patches 16), N-E4B resolved 1 (patches 13); the 31B
arms L and N resolved 4 each. L-E4B vs N-E4B: one task only L-E4B, none only N-E4B, exact McNemar p = 1.0.
L-E4B vs L: p = 0.5; N-E4B vs N: p = 0.25. Prediction 1 (E4B resolves no more than 31B) holds; prediction 2
(L-E4B at least N-E4B) holds; no difference is detected at this size. Decision rule: both E4B arms resolve at
least one task and L-E4B resolves more, so E = L-E4B and takes the day-2 slot of the amendment 3 schedule.
Files: benchmark/gemma_agent/selftest_results/selftest16_v81e4b_lexical.csv and selftest16_v81e4b_noskill.csv.

## Amendment 4 (recorded 2026-11-12 17:09 MT, before the leaderboard score of arm L)

Defect found in the BM25 skill. The traces of every BM25 arm (L, C50, A0 on 31B; L-E4B) show the skill script ranked
its own skill folder (scripts/localize.py, scores 0.00) in 15 of 16 tasks, not the repository. The script searches
/workspace if that path exists, else its working directory; skill scripts run outside the agent's sandbox, where the
repository is not at /workspace (in the self-test it is under /tmp/swegemma_sandbox_*). So no BM25 arm searched the
repository: L, C50 and A0 differ from N only by one uninformative first call, and the 16-task comparisons of L, N,
C50, A0, L-E4B and N-E4B do not test coverage. They stand as measurements of those configurations, not of BM25.
The leaderboard submission of L (ref 58287913) has the same defect and is reported as such.

Consequences: the E selection of amendment 3 is withdrawn, and no BM25 arm is submitted until a corrected
localizer is shown in the traces to rank repository files. The corrected design runs lexical search inside the
sandbox through run_command, where the repository is visible. Its arms are registered here before any result.

## Amendment 5 (recorded 2026-11-12 17:10 MT, before any result of these arms)

Corrected localizer. G = submission_v81_grep (31B) and G-E4B = submission_v81e4b_grep: identical to N and N-E4B except
the prompt, whose first step is a grep over every Python file run through run_command inside the sandbox, where the
repository is visible (full-coverage literal search), and whose step 1 no longer forbids repository-wide grep.
Gate before any leaderboard use: in the self-test traces, the first call is that grep and it prints repository paths
in most tasks. Tests: G vs N and G-E4B vs N-E4B, exact McNemar on the same 16 published tasks; a null is reported as
not detected. Small-model levers, each one change from the better E4B arm and registered before its result: a
prompt shortened for a small model, then a larger budget (the measured E4B runs used 7 to 26 of 28 tool calls and
1 to 7 of 8 minutes, so this lever is ranked last). A distillation LoRA (31B trajectories that resolved published
tasks, tested on held-out tasks) is considered only if these plateau, and registered before training.

## Outcome of amendment 5 (recorded 2026-11-12 19:10 MT)

Gate: the first call was the grep in 16 of 16 tasks for both arms, and its output listed repository .py paths in
12 of 16 (G) and 14 of 16 (G-E4B), so both pass. 16 published tasks: G resolved 5 (patches 13), N 4; G only
fastapi_5624 and rich_3777, N only rich_3480, exact McNemar p = 1.0. G-E4B resolved 1 (patches 15), N-E4B 1; each
resolved one task the other did not, p = 1.0. No difference is detected at this size.
Files: benchmark/gemma_agent/selftest_results/selftest16_v81_grep.csv and selftest16_v81e4b_grep.csv.

## Amendment 6 (recorded 2026-11-12 20:15 MT, before any result of this arm)

S-E4B = submission_v81e4b_short: identical to G-E4B except the prompt, rewritten for a small model (668 to 226
words, five numbered steps). G-E4B is the base because it tied N-E4B (1 of 16 each) and passes the trace gate. The
rewrite keeps the in-sandbox grep first step and adds one rule motivated by measured traces: edit existing files only
with edit_file, never write_file (G-E4B produced patches of 23,723 and 178,225 characters, consistent with whole-file
rewrites). Test: S-E4B vs G-E4B, exact McNemar on the same 16 published tasks; secondary, the number of patches over
10,000 characters. A null is reported as not detected.

## Outcome of amendment 6 (recorded 2026-11-12 20:53 MT)

S-E4B resolved 1 of 16 (fastapi_14077), G-E4B 1 (rich_2725); each resolved one the other did not, exact McNemar
p = 1.0, no difference detected. Secondary: patches over 10,000 characters fell from 2 to 0, so the edit_file rule
removed whole-file rewrites; patches 13 vs 15. Gate passed (grep first in 16 of 16, repository paths in 12).
File: benchmark/gemma_agent/selftest_results/selftest16_v81e4b_short.csv.

## Amendment 7 (recorded 2026-11-12 20:52 MT, before any result of these runs)

Full-set paired test. G and N run with the self-test harness on all 129 published tasks (same budgets, 4 tasks in
parallel). Primary: G vs N, exact McNemar over 129 paired tasks; prediction G resolves at least as many as N.
Secondary, fixed now: (a) the 113 tasks outside the 16-task set; (b) the 21 tasks whose gold patch edits an async
function (benchmark/harness_audit/TASK_AUDIT_all129.json): fastapi_15030, fastapi_14962, fastapi_15023, fastapi_14986, fastapi_14978, fastapi_14099, fastapi_14609, fastapi_14487, fastapi_14306, fastapi_14448, fastapi_14419, fastapi_14262, fastapi_14077, httpx_3672, fastapi_15800, fastapi_14371, fastapi_15745, fastapi_14303, fastapi_13537, fastapi_13786, fastapi_11194. A null is reported as not detected.
The resolved G trajectories are kept as candidate training data for the E4B distillation LoRA; its held-out split
is registered before any training.

## Outcome of amendment 7 and the first leaderboard score (recorded 2026-11-13 08:52 MT)

All 129 published tasks, no errors: G resolved 30 (0.233), N 28 (0.217); 5 only G, 3 only N, exact McNemar
p = 0.73. Registered subsets: the 113 tasks outside the 16-task set, G 27 vs N 25, 5 vs 3, p = 0.73; the 21 tasks
whose gold patch edits an async function, G 4 vs N 3, 1 vs 0, p = 1.0. No difference is detected; G is not worse.
By repository: fastapi G 18 vs N 14 of 67, rich 11 vs 13 of 48, requests 1 vs 1 of 13, httpx 0 vs 0 of 1.
Leaderboard: arm L (ref 58287913, the BM25 skill that searched its own folder, amendment 4) scored 0.17 public,
so a corrected skill name compiles and runs on the scorer and the skill call does not break the agent.
Files: benchmark/gemma_agent/selftest_results/selftest129_v81_grep.csv and selftest129_v81_noskill.csv.

## Amendment 8 (recorded 2026-11-13 09:05 MT, before any result of this arm)

T-E4B = submission_v81e4b_think: identical to S-E4B except sampling, thinking_budget 4096 to 8192 and
max_output_tokens 8192 to 16384 (the harness default; limits are 32768). S-E4B is the base because it tied G-E4B
(1 of 16 each) and removed whole-file rewrites. Rationale: E4B finds the files (grep output listed repository paths
in 12 to 14 of 16 tasks) but writes wrong fixes, so more reasoning per turn is the cheapest relevant lever.
Test: T-E4B vs S-E4B, exact McNemar on the same 16 published tasks; a null is reported as not detected.
LoRA groundwork (no GPU): the 129-task runs give 33 unique resolved 31B trajectories (fastapi 18, rich 14,
requests 1). Any distillation LoRA, its data, held-out split and test are registered before training.

## Outcome of amendment 8 (recorded 2026-11-13 13:47 MT)

T-E4B resolved 1 of 16 (fastapi_14077, patches 14), the same task as S-E4B; no discordant tasks, p = 1.0. Doubling
the reasoning budget changed nothing detectable. E4B stays at 1 to 2 of 16 across every non-training lever.
File: benchmark/gemma_agent/selftest_results/selftest16_v81e4b_think.csv.

## Amendment 9 (recorded 2026-11-13 15:36 MT, before any result of these runs or submissions)

(a) Fastapi replicate. The 129-task outcome showed, in an analysis not registered beforehand, that all of G's net
gain was on fastapi (G only 4, N only 0, exact p = 0.125), the repository whose index omits 914 async functions;
on rich it was G only 1, N only 3. To test that lead, G and N run again with the self-test harness on the 67 fastapi
published tasks, fresh runs, same arms and budgets. Primary: G vs N on these 67 new paired runs, exact McNemar,
two-sided; prediction G resolves more. Secondary: the 20 fastapi tasks whose gold patch edits an async function.
The earlier 129-task fastapi results are not pooled into the primary test. A null is reported as not detected.

(b) Leaderboard schedule. L, C50 and A0 are withdrawn (amendment 4). From 2026-11-14 00:00 UTC the daily slots
alternate G and N (G first), giving paired replicates of a working full-coverage search against no search step on
the hidden set; E4B arms enter only if one resolves more than 2 of 16 published tasks. Final picks per amendment 3,
recorded before selection.

## Outcome of amendment 9 (recorded 2026-11-13 23:13 MT)

(a) Fastapi replicate, 67 fresh paired runs, no errors: G resolved 14, N 15; G only 2, N only 3, exact McNemar
p = 1.0. Secondary, 20 async-fix tasks: G 2, N 3, 0 vs 1, p = 1.0. The prediction (G resolves more) is not
supported: the fastapi lead from the 129-task runs (4 vs 0) did not replicate and is treated as noise. Across all
paired self-tests, a mandatory full-coverage search step does not change task success detectably for the 31B agent.
(b) Arm G submitted to the leaderboard 2026-11-14 00:00:47 UTC (ref 58324271); score pending.
Files: benchmark/gemma_agent/selftest_results/selftest67fa_v81_grep.csv and selftest67fa_v81_noskill.csv.

## Amendment 10 (recorded 2026-11-13 23:18 MT, before any training or result)

Distillation LoRA for E4B, triggered because every non-training lever plateaued at 1 to 2 of 16 (amendments 2, 5, 6, 8).
Data: resolved trajectories of the 31B arm G from the 129-task and 67-task fastapi self-tests, converted to chat
records with the harness's nine tools (benchmark/gemma_agent/lora/build_sft.py). Training split: fastapi and
requests, 33 trajectories over 19 tasks. Held out: every rich task (48); the 11 resolved rich trajectories are never
trained on. Base for training: google/gemma-4 Transformers gemma-4-e4b-it; the adapter is served on
gemma-4-e4b-it-qat-w4a16-ct. LoRA rank 16, alpha 32, attention and MLP projections of the language model, loss on
assistant turns only, 2 epochs, learning rate 1e-4, sequences truncated at 16,384 tokens.
Arm LG-E4B = G-E4B plus the adapter (same prompt as the training trajectories).
Gate: a smoke run on 4 held-out rich tasks must show tool calls in every task; otherwise the adapter is reported as a
format failure and not tested further.
Test: LG-E4B vs G-E4B on all 48 rich tasks, fresh paired runs, exact McNemar, two-sided; prediction LG-E4B resolves
more. A null is reported as not detected. Leaderboard use only if LG-E4B resolves more than G-E4B on the rich tasks.

## Leaderboard record (recorded 2026-11-14 07:57 MT)

Arm G (ref 58324271, submitted 2026-11-14 00:00:47 UTC) scored 0.15 public; arm L (ref 58287913, effectively N plus
one uninformative skill call) scored 0.17. One replicate each; the reported noise between identical submissions is
about two tasks of 58, so no difference is inferred. Arm N follows on 2026-11-15 00:00 UTC per amendment 9.

## Amendment 11 (recorded 2026-11-14 08:09 MT, before any token count of these runs was computed)

Token use as an outcome of the thesis approach (index everything the agent may need, hand it small in-window pieces).
(a) Existing runs, not yet analysed for tokens: total_prompt_tokens and total_completion_tokens from final_metrics of
every trace. Pairs: G vs N on 129 tasks and on the 67 fastapi replicate (31B); G-E4B vs N-E4B on 16 tasks (E4B).
Primary: paired Wilcoxon signed-rank on per-task total tokens, two-sided; secondary, tokens per resolved task. No
prediction is made for G vs N, since G adds a search step but may shorten exploration.
(b) New arms W (31B) and W-E4B: identical to G and G-E4B except one prompt rule, read at most 40 lines per read_file
call, centred on a grep match (start_line and end_line), the agent-level form of chunking to the window. Test on the
same 16 published tasks: W vs G and W-E4B vs G-E4B. Primary: per-task total tokens, paired Wilcoxon; prediction W
uses fewer. Co-primary: resolved tasks, exact McNemar; prediction W is not worse. Nulls are reported as not detected.

### Outcome of amendment 11 (a) (recorded 2026-11-14 08:12 MT)

Total tokens per task (prompt plus completion), paired Wilcoxon signed-rank, normal approximation:
G vs N, 129 tasks: median 214,792 vs 243,611, total -2.7 percent, z = -0.92, p = 0.36.
G vs N, 67 fastapi: median 253,677 vs 235,088, total +7.0 percent, z = +1.22, p = 0.22.
G-E4B vs N-E4B, 16 tasks: median 126,561 vs 132,583, total +1.5 percent, z = +0.26, p = 0.80.
A full-coverage search step does not change token use detectably; the two 31B samples point in opposite directions.

### Outcome of amendment 11 (b) (recorded 2026-11-14 08:53 MT)

Total tokens per task, paired Wilcoxon (normal approximation), same 16 published tasks:
W vs G (31B): median 238,452 vs 248,902, total -1.2 percent, z = -0.72, p = 0.47. Resolved 4 vs 5 (only G rich_3777),
McNemar p = 1.0. Compliance: whole-file reads fell from 56 to 22 of about 160 read_file calls; median ranged read 22
vs 28.5 lines.
W-E4B vs G-E4B: median 91,284 vs 126,561, total -19.1 percent, z = -1.81, p = 0.07. Resolved 2 vs 1 (only W
fastapi_14077), McNemar p = 1.0. Compliance partial: whole-file reads fell from 33 to 18; median ranged read 100.5
vs 91 lines, so the 40-line rule was mostly not followed.
Neither token prediction reaches p < 0.05; W is not worse on resolution in either model. The E4B saving is the
largest token effect measured in this plan and is treated as a lead for a registered replication, not a result.
Files: benchmark/gemma_agent/selftest_results/selftest16_v81_window.csv and selftest16_v81e4b_window.csv.

## Amendment 12 (recorded 2026-11-14 08:54 MT, before any result of these runs)

(a) Replication of the windowed-read lead. Fresh paired runs of W-E4B and G-E4B (unchanged arms) on 56 published
tasks: all 48 rich tasks plus the 8 fastapi tasks of the 16-task set. Primary: total tokens per task, paired
Wilcoxon signed-rank, two-sided; prediction W-E4B uses fewer. Co-primary: resolved tasks, exact McNemar; prediction
W-E4B is not worse. The 16-task results of amendment 11 are not pooled. Nulls are reported as not detected.
(b) Budget. GPU: about 2 hours of the 20.6 left before the 2026-11-21 reset. Leaderboard: one submission per day
and one pending at a time; 18 slots remain (2026-11-15 to 2026-12-02).
(c) Slot schedule, replacing amendment 9 (b) from 2026-11-16: 15 Nov N (already armed), 16 Nov G, 17 Nov N. If (a)
supports both predictions (token p < 0.05, W-E4B not worse), 18 to 23 Nov alternate W-E4B and G-E4B (three each,
W-E4B first) as hidden-set replicates of the small-model pair; otherwise G and N keep alternating. 24 Nov to 2 Dec:
further replicates of the pair with the largest difference in mean public score. Final picks: the 31B arm and the
E4B arm with the highest mean public score, recorded here before selection.

### Outcome of amendment 12 (a) (recorded 2026-11-14 09:40 MT)

56 fresh paired tasks, no errors. Tokens: median 117,678 vs 119,676, total -3.6 percent, W-E4B lower on 31 of 56,
Wilcoxon z = -0.33, p = 0.74. Resolved: W-E4B 3, G-E4B 4 (only W rich_3006; only G rich_3518, rich_3894), McNemar
p = 1.0. The token prediction is not supported and the 19.1 percent saving seen on 16 tasks did not replicate; the
co-primary (not worse) is not contradicted. Per (c), 18 to 23 Nov keep the G/N alternation; W-E4B and G-E4B are
not submitted. Not registered and not a result: on the 8 fastapi tasks the saving was -18.9 percent (on rich -0.8).
Files: benchmark/gemma_agent/selftest_results/selftest56_v81e4b_window.csv and selftest56_v81e4b_grep.csv.

## Amendment 13 (recorded 2026-11-14 11:56 MT, before any result of the runs named here)

On Pupa's instruction, no leaderboard submission and no new Kaggle notebook until the running self-tests are complete:
the tiered-context study runs (research/PREREG_tiered_context_gemma_harness.md, cck-ctx-monolithic-129 and
cck-ctx-tiered-129) and then the new-files test below. The N upload armed for 2026-11-15 00:00 UTC was disarmed at
11:55 MT; that slot is skipped, leaving at most 17. The amendment 12 schedule resumes, in order, from the first slot
after these self-tests finish.
New-files arm, registered now, launched only after the current runs: F = submission_v81_grep plus one prompt rule,
"if the fix needs a new module, example or documentation file, create it with write_file, following the naming of
existing files in that folder". Motivation (CPU analysis of existing traces): 11 of 129 published tasks need new
files (8 under fastapi docs_src); G and N created none of them and resolved none, 9 with test-collection errors.
Test: F vs G on those 11 tasks (primary, exact McNemar, prediction F resolves more) and on the 16-task set (not worse).

## Amendment 14 (recorded 2026-11-14 12:19 MT, before any result of this arm; launched only after the running self-tests, per amendment 13)

CPU analysis of G's 129-task traces (no new runs). Among the 67 fixes in the right file that failed: 57 never ran
pytest; the agent's patch was a median 2.75 times the gold patch's added lines; 21 skipped other files the gold fix
changes (89 source files and 24 docs_src examples across those tasks). Observationally, runs that ran pytest resolved
11 of 21 (0.52) and runs that did not resolved 18 of 89 (0.20); this is not causal, since easier tasks may invite testing.
Arm V = G plus one rule: "Before submit_patch, run the existing test file for the code you changed
(pytest <file> -q -x) and fix any failure your change caused; if no test file exists, import the changed module with
python -c." Test: V vs G on the same 16 published tasks; primary resolved tasks, exact McNemar, prediction V resolves
more; secondary, share of runs that ran a test. A null is reported as not detected.

## Amendment 15 (recorded 2026-11-14 12:34 MT, before any result of these arms)

Score priority, on Pupa's instruction. The tiered-context runs (cck-ctx-monolithic-129, cck-ctx-tiered-129) were
stopped at 12:34 MT, unanalysed; they rerun after a quota reset as registered (recommendation R36). This supersedes
amendment 13's order. Three one-change arms from G, each aimed at a measured failure cause of G's 129-task run:
- V = submission_v81_verify (amendment 14): test the changed code before submit_patch.
- F = submission_v81_newfiles (amendment 13): create new files the fix needs.
- B = submission_v81_budget: eval budget 28 to 50 tool calls, 8 to 15 minutes, 80 to 140 turns (scorer defaults are
  100 calls and 60 minutes). 42 of G's 99 failures used all 28 calls.
Self-tests: V and B on the 16-task set; F on the 11 tasks whose gold fix creates files (fastapi_15661, 15030, 15280,
14978, 14099, 14262, 14186, 15800, 14953, 13786, rich_3930) plus the 16-task set. Each vs G's runs on the same tasks
(G's 16-task run; G's 129-task results for the 11). Primary: resolved, exact McNemar, prediction arm resolves more.
Combination rule, fixed now: every arm whose resolved count exceeds G's on its primary set joins one combined arm,
confirmed on as many tasks as quota allows before any submission. Risk noted: B raises per-task time on the scorer.

## Amendment 16 (recorded 2026-11-14 12:42 MT, before any result of the amendment 15 arms)

From the harness source (swegemma 0.2.11, harness/verification.py), read to explain failures:
- A task is resolved only if pytest exits 0 on every test file the hidden test patch touches (whole files, not only
  the new tests), with no failures or errors in the JUnit report and every required test passing. A change that
  breaks any other test in those files fails the task. Exit code 2 is a collection error, typically a failed import.
- Before verification the harness drops every agent edit to protected paths: any test_*.py or *_test.py, any .py
  under a tests, test or testing directory, conftest.py, pyproject.toml, setup.cfg, tox.ini, pytest.ini and .pth
  files. In G's 129-task run, 28 runs edited protected files (19 unresolved), almost all scratch test files; no gold
  patch touches a protected path.
- Our self-test notebooks recorded only the exit code. From now on each run also saves the harness's test output,
  its error reason and the agent's patch (test_output/ in the notebook output). The V and B self-tests were
  restarted at 12:45 MT to capture this (about 16 GPU minutes lost); no outcome had been recorded.
Candidate rule for the combined arm, decided by the amendment 15 rule only if it is tested first: "Edits to test
files, conftest.py, pyproject.toml, setup.cfg and tox.ini are discarded by the grader; put the whole fix in source
files, and keep every existing test in the module's test file passing."
