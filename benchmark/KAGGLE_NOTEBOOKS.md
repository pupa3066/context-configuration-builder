# Kaggle notebooks: what each one is, why it ran, and what it showed

Kaggle notebook addresses cannot be renamed without breaking links or losing outputs, so this index gives each one a
descriptive name. All notebooks are under kaggle.com/code/purnimapathak15/. "Writeup" refers to the Paper Track
writeup; "amendment" refers to research/PREREG_20day_agent_plan.md unless noted.

## Evidence for the writeup

| Notebook | Descriptive name | Why it ran | What it showed |
|---|---|---|---|
| cck-results-public | Rebuild every table and figure of the writeup | Reproducibility for judges | All tables and figures rebuild byte for byte from tag v1.0-paper |
| cck-async-check | Async functions missing from the competition code graph | Writeup 3.1 | 914 of 914 fastapi and 100 of 100 httpx async functions absent; sync 94 to 100 percent present |
| cck-task-audit | Which published tasks need async code (all 129) | Follow-up to 3.1 | 21 of 129 gold fixes edit an async function; in 17 the edited symbol is not indexed |
| cck-confound-lines8 | Coverage sweep, 8-line chunks, set 1 | Writeup 3.2, 3.3 | BM25 beats dense by 0.40 at 1,000 chunks; equivalent within 0.10 at full coverage |
| cck-confound-lines8-newrepos | Coverage sweep, 8-line chunks, set 2 | Replication on three new repositories | Same pattern: gap 0.28 at 1,000 chunks; equivalent at full coverage |
| cck-gold-orig | Was the answer indexed? Set 1 | Mechanism behind 3.2 | Dense finds indexed answers 0.89 to 0.92 at every budget |
| cck-gold-newrepos | Was the answer indexed? Set 2 | Replication of the mechanism | 0.88 to 0.90 at every budget |
| cck-sweep-bgebase | Second embedder (bge-base) at full coverage | Writeup 3.4 robustness | Same result with a larger embedder |
| cck-sweep-thr065 | Metric m3 at threshold 0.65 | Writeup 3.4 robustness | Conclusion unchanged |
| cck-sweep-thr080 | Metric m3 at threshold 0.80 | Writeup 3.4 robustness | Conclusion unchanged |
| cck-confound-lines32 | Chunk length, 32-line chunks | Writeup 3.5 | Dense falls to 0.821 although every chunk is indexed |
| cck-confound-words400 | Chunk length, 400-word chunks | Writeup 3.5 | Dense falls to 0.663; every chunk exceeds the 512-token window |
| cck-confound-words400-maxwin | Best-segment scoring on 400-word chunks, plus window probe | Isolates truncation (3.5) | Fixes 56 questions, breaks 2 (p = 1.2e-14); text past about 600 words is ignored |
| cck-confound-words400-jina | Long-context embedder attempt | Test of a larger window | Did not fit in memory (writeup limitation) |
| cck-kb-audit | The method applied to the toolkit's own repository | Writeup 3.6 | Same coverage pattern (N = 34); a markdown-only index reaches 0 of 277 code symbols |
| cck-diag-agenta | Why arm A scored 0.00 | Writeup 5 | Skill name repo_navigation is rejected; the agent never compiles (0 tool calls) |
| cck-diag-v8 | Corrected arms, 3 tasks | Writeup 5 | Corrected arms run and resolve 0 to 1 of 3 |
| cck-diag-v81 | Corrected arms with a mandatory first call, 3 tasks | Writeup 5 | First-call compliance measured; the agent avoids the harness search tool |
| cck-st16-lexical | BM25-skill arm, 16 tasks | Writeup 5 paired test | 4 of 16 resolved (the skill later found to search its own folder, amendment 4) |
| cck-st16-noskill | No-skill arm, 16 tasks | Writeup 5 paired test | 4 of 16 resolved |

## Follow-up after the writeup (each registered before its result)

| Notebook | Descriptive name | Why it ran | What it showed |
|---|---|---|---|
| cck-st16-cov50 | BM25 skill over half the files, 16 tasks | Coverage at task level | 6 of 16; not interpretable (skill defect, amendment 4) |
| cck-st16-noasync | BM25 skill blind to async code, 16 tasks | Coverage at task level | 5 of 16; not interpretable (skill defect) |
| cck-st16-grep | Grep inside the sandbox first, 31B, 16 tasks | Fixed localizer (amendment 5) | Passes the trace check; 5 of 16 vs 4 |
| cck-all129-grep | Grep first, 31B, all 129 tasks | Full-set test (amendment 7) | 30 of 129 (23.3 percent) |
| cck-all129-noskill | No search step, 31B, all 129 tasks | Control for the above; the no-context baseline of the tiered-context study | 28 of 129 (21.7 percent); p = 0.73 vs grep |
| cck-fa67-grep | Grep first, 31B, 67 fastapi tasks | Replicate the fastapi lead (amendment 9) | 14 of 67 |
| cck-fa67-noskill | No search step, 31B, 67 fastapi tasks | Control for the above | 15 of 67; the lead did not replicate |
| cck-st16-window | Read in 40-line windows, 31B, 16 tasks | Chunked reading at agent level (amendment 11) | Tokens -1.2 percent, not significant |
| cck-st16e4b-lexical | Small model, BM25 skill, 16 tasks | Small-model prize arms (amendment 2) | 2 of 16 |
| cck-st16e4b-noskill | Small model, no skill, 16 tasks | Control | 1 of 16 |
| cck-st16e4b-grep | Small model, grep first, 16 tasks | Fixed localizer on E4B | 1 of 16; passes the trace check |
| cck-st16e4b-short | Small model, shortened prompt, 16 tasks | Prompt lever (amendment 6) | 1 of 16; whole-file rewrites 2 to 0 |
| cck-st16e4b-think | Small model, double reasoning budget, 16 tasks | Reasoning lever (amendment 8) | 1 of 16, no change |
| cck-st16e4b-window | Small model, 40-line windows, 16 tasks | Chunked reading on E4B | Tokens -19.1 percent (p = 0.07) |
| cck-r56e4b-window | Small model, 40-line windows, 56 new tasks | Replication (amendment 12) | Tokens -3.6 percent (p = 0.74); did not replicate |
| cck-r56e4b-grep | Small model, grep first, 56 new tasks | Control for the above | 4 of 56 resolved vs 3 |
| cck-ctx-monolithic-129 | Monolithic repository context (whole file in the prompt), 129 tasks | Tiered-context study (PREREG_tiered_context_gemma_harness.md) | Stopped unanalysed for score work (plan amendment 15); notebook removed; rerun registered |
| cck-ctx-tiered-129 | Tiered repository context (index in the prompt, sections loaded on demand), 129 tasks | Same study | Stopped unanalysed (plan amendment 15); notebook removed; rerun registered |
| cck-ctx-tiered-smoke | Tiered context smoke test, 4 tasks | Check before the full run | All 4 ran with tool calls; full run launched |

## Score work (amendment 15)

| Notebook | Descriptive name | Why it ran | What it showed |
|---|---|---|---|
| agent-31b-test-before-submit-16tasks | 31B agent tests its change before submitting | 57 of 67 wrong fixes were never tested | V 4 of 16 vs G 5, p = 1.0 |
| agent-31b-budget-50calls-15min-16tasks | 31B agent with a larger budget | 42 of 99 failures used all 28 calls | B 6 of 16 vs G 5, p = 1.0; confirmed on 72 scorable tasks below |
| agent-31b-create-new-files-27tasks | 31B agent allowed to create new files | 11 tasks need new files (4 scorable) | F 4 of 16 vs G 5, p = 1.0; F created none of the 49 new files the gold fixes add |

## Retrieval on real problem statements (registered before results)

| Notebook | Descriptive name | Why it ran | What it showed |
|---|---|---|---|
| harness-gold-patch-control-129tasks | Gold patch vs empty patch on all 129 published tasks | Find which tasks can be scored locally | 72 scorable; gold fails on 54 (environment), 3 pass with no fix |
| retrieval-on-task-problem-statements | Competition problem statements as queries, gold-patch code as targets | Extend the coverage finding to real task queries; bridge to agent success | Dense beats BM25 at full coverage, 0.312 vs 0.184 (p = 0.011); coverage 0.312 vs 0.248 (p = 0.17); a retrieval hit does not predict a solved task |
| retrieval-swebench-lite-coverage-and-chunk-length | SWE-bench Lite smoke run, 3 flask tasks | Check the notebook before the full run | Passed |
| retrieval-swebench-lite-django, -sympy, -scientific-libs, -dev-tools-and-web | SWE-bench Lite, four repository shards | Model-agnostic test of coverage and chunk length on a standard benchmark | django complete: coverage p = 0.006, dense beats BM25 p = 0.035. sympy stopped at 39 of 77 and scientific-libs at 40 of 61; dev-tools-and-web removed; rerun needed before the pooled test |
| agent-31b-budget-50calls-15min-72scorable | 31B agent with a larger budget, 72 scorable tasks | Confirm the only arm that beat G (amendment 18) | 30 vs 27, p = 0.51; on the leaderboard B exceeded the 12-hour runtime limit (no score) |

## Small model, after the gold-patch control (registered before results)

| Notebook | Descriptive name | Why it ran | What it showed |
|---|---|---|---|
| agent-e4b-ranked-chunk-search-smoke3 | Ranked 8-line chunk search for E4B, 3-task smoke run | Gate before the full run (amendment 20) | First run had 0 tool calls (a template variable in the prompt); repeated after the fix before the full run |
| agent-e4b-ranked-chunk-search-46scorable | Ranked 8-line lexical chunk search vs grep, E4B, 46 scorable tasks | The writeup's method at agent level (amendment 20) | Solved 3 vs 3; never found the right file 13 to 5; tokens +15.8 percent (p = 0.025) |
| agent-e4b-fix-check-vs-ranked-search-46tasks | Fix check before submit vs ranked search, E4B, same run | Remaining failures were wrong fixes (amendment 21) | 5 vs 4, p = 1.0; submissions after a failing own test rose 15 to 25 |
| agent-e4b-retrieval-ceiling-gold-files-46tasks | E4B told the files the gold fix changes, 46 tasks | Retrieval ceiling for the small model (amendment 22) | 5 of 46; 39 wrong fixes in the right file; limit is writing the fix |

## Score work after the B runtime failure (registered before results)

| Notebook | Descriptive name | Why it ran | What it showed |
|---|---|---|---|
| agent-31b-arm-n-presubmit-smoke-4tasks | The exact arm N submission zip, 4 scorable tasks N solved before | Check the zip before the 17 Nov slot (amendment 25) | Saved without GPU; run by a teammate |
| agent-31b-edit-by-15th-call-vs-no-search-72 | Edit by the 15th tool call (ED) vs no search step (N), same session, 72 scorable tasks | Amendment 26 | Saved without GPU; run by a teammate |
