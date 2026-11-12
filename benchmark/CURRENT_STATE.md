# Benchmark Current State

Date: 2026-09-25 (updated with cap sweep and fair-metric results)

Scope: dated record of all result sets. All numbers are measured with a real gpt2 BPE tokenizer
(token cost study) or bootstrap CIs on real public repositories (retrieval studies). Both retrieval
studies score a grounding-retention proxy (is the needed content present in the assembled context),
NOT task success.

## Study one: token cost (POWERED_RESULTS.json)

N=195 identifier-recall auto questions. Corpus: requests, click, black. Bootstrap resamples: 1000.
Metric: answerable proxy (grounding retention) and average per-turn tokens.

| Strategy            | Answerable proxy | 95 percent interval | Avg tokens |
|---------------------|------------------|---------------------|------------|
| no_context          | 0.0              | 0.0 to 0.0          | 0          |
| monolithic          | 1.0              | 1.0 to 1.0          | 471812     |
| summarized_L0.5     | 1.0              | 1.0 to 1.0          | 471551     |
| retrieval_bm25 k3   | 0.9846           | 0.9641 to 1.0       | 309        |
| retrieval_bm25 k6   | 0.9897           | 0.9744 to 1.0       | 624        |
| retrieval_bm25 k10  | 0.9949           | 0.9846 to 1.0       | 1061       |

Finding: keyword retrieval cut per-turn tokens by roughly 99.8 percent versus monolithic at k3 while
retaining at least 0.98 of the grounding proxy. Summarization saved almost nothing on code
(471551 versus 471812 tokens), because identifiers are the part you cannot safely drop.

## Study two: semantic versus lexical (CONCEPTUAL_RESULTS.json)

N=100 conceptual (docstring-mined) questions. k=6. Query is question-only with no fact leak. The
semantic index was capped at 1200 chunks per repo to fit an 8GB machine.

| Retriever            | Answerable proxy | 95 percent interval |
|----------------------|------------------|---------------------|
| BM25 (lexical)       | 0.90             | 0.84 to 0.95        |
| bge-small (semantic) | 0.65             | 0.55 to 0.74        |

Paired questions: 30 answerable only by BM25, 5 answerable only by semantic. Verdict: lexical wins
for this identifier-heavy fact recall. Version numbers, function names, and ids carry little meaning
for an embedding model, so it misses exact lines a keyword match finds.

## Study three: fair-metric cap sweep -- EMPIRICAL THRESHOLD REACHED (2026-09-25)

[MEASURED] Runner: conceptual_fair_metrics.py. N=240 conceptual questions, 3 repos (requests, click,
black), k=6, bootstrap=1000. Three metrics scored simultaneously: m1_substring (original, favors
lexical), m2_defline (stricter: definition line only), m3_sem_credit (favors semantic: substring OR
cosine-credit >= 0.72). bge-small-en-v1.5 via fastembed (ONNX, CPU). Results on Kaggle (16GB CPU).

BM25 is flat across all caps -- cap-independent by construction. Internal control holds.

Cap sweep (bge-small-en-v1.5, N=240):

| Cap | m1 BM25 | m1 Semantic | m2 BM25 | m2 Semantic | m3 BM25 | m3 Semantic |
|-----|---------|-------------|---------|-------------|---------|-------------|
| 1000 | 0.8667 [0.825,0.9083] | 0.4417 [0.3792,0.5083] | 0.8208 [0.7708,0.8667] | 0.2792 [0.2208,0.3375] | 0.9583 [0.9333,0.9833] | 0.7125 [0.6542,0.7708] |
| 3000 | 0.8667 [0.825,0.9083] | 0.7583 [0.7042,0.8125] | 0.8208 [0.7708,0.8667] | 0.65 [0.5917,0.7125] | 0.9583 [0.9333,0.9833] | 0.8625 [0.8167,0.9042] |
| 100000 (uncapped) | 0.8667 [0.825,0.9083] | 0.8667 [0.8208,0.9083] | 0.8208 [0.7708,0.8667] | 0.8125 [0.7625,0.8583] | 0.9583 [0.9333,0.9833] | 0.9333 [0.9,0.9625] |

Finding (EMPIRICAL -- N=240, bootstrap CIs, controlled single-variable sweep):

At full index (cap=100000, which covers all chunks in all three repos), BM25 and bge-small are
statistically indistinguishable across all three metrics. m1 gap: 0.000 (identical point estimates).
m2 gap: 0.008 (CIs fully overlap). m3 gap: 0.025 (CIs overlap). The original large gap
(0.8667 vs 0.4417 at cap=1000) is almost entirely an evaluation artifact of asymmetric index
capping: BM25 always sees all chunks; the capped semantic arm was never given the chunks it needed.

Validation of all prior semantic numbers:
- Local N=100 semantic 0.65 (cap 1200): valid at stated cap. Interpolates between cap=1000 (0.44)
  and cap=3000 (0.76). Correctly labeled as capped in prior CURRENT_STATE versions.
- Kaggle N=180 semantic 0.717 (cap 3000): valid at stated cap. Consistent with cap=3000 giving
  ~0.76 in the fair-metric sweep (N and repo-count variation accounts for the difference).
- All BM25 numbers across all runs: valid unconditionally. BM25 never depended on the cap.

## Honest caveats (updated)

- Grounding-retention proxy, NOT task success.
- Three Python repos, one language. Does not generalize to other languages without further testing.
- One embedder (bge-small). Whether larger or code-specialized embedders beat BM25 at full index
  is the next open question; the --embed-model flag in conceptual_fair_metrics.py supports this test.
- m3 threshold (cosine >= 0.72) is a free parameter; sensitivity sweep across 0.65-0.80 is pending.
- Docstring-mined questions, not human-written; real developer queries may differ.

## What is on fair-metrics-wip now

- benchmark/conceptual_fair_metrics.py (cap sweep + fair metrics runner, --embed-model flag)
- benchmark/SWEEP_cap_1000.json, SWEEP_cap_3000.json, SWEEP_cap_100000.json (on Kaggle, not yet committed)
- benchmark/POWERED_RESULTS.json (study one raw numbers)
- benchmark/CONCEPTUAL_RESULTS.json (study two original numbers, untouched)
- benchmark/conceptual_semantic_vs_lexical.py (study two runner)
- benchmark/CURRENT_STATE.md (this record)

## Next steps

Fair-metric results by run (answerable proxy, not task success):

| Run | N | repos | cap | metric | BM25 [95% CI] | semantic [95% CI] |
|-----|---|-------|-----|--------|---------------|-------------------|
| pilot (local) | 90 | 2 | 1000 | m1 | 0.90 [0.84, 0.96] | 0.54 [0.44, 0.63] |
| pilot (local) | 90 | 2 | 1000 | m2 | 0.86 [0.79, 0.92] | 0.43 [0.33, 0.53] |
| pilot (local) | 90 | 2 | 1000 | m3 | 0.98 [0.94, 1.00] | 0.81 [0.73, 0.89] |
| Kaggle cap sweep | 240 | 3 | 1000 | m1 | 0.8667 [0.825, 0.908] | 0.4417 [0.379, 0.508] |
| Kaggle cap sweep | 240 | 3 | 1000 | m2 | 0.8208 [0.771, 0.867] | 0.2792 [0.221, 0.338] |
| Kaggle cap sweep | 240 | 3 | 1000 | m3 | 0.9583 [0.933, 0.983] | 0.7125 [0.654, 0.771] |
| Kaggle cap sweep | 240 | 3 | 3000 | m1 | 0.8667 [0.825, 0.908] | 0.7583 [0.704, 0.813] |
| Kaggle cap sweep | 240 | 3 | 3000 | m2 | 0.8208 [0.771, 0.867] | 0.65 [0.592, 0.713] |
| Kaggle cap sweep | 240 | 3 | 3000 | m3 | 0.9583 [0.933, 0.983] | 0.8625 [0.817, 0.904] |
| Kaggle uncapped | 240 | 3 | 100000 | m1 | 0.8667 [0.825, 0.908] | 0.8667 [0.821, 0.908] |
| Kaggle uncapped | 240 | 3 | 100000 | m2 | 0.8208 [0.771, 0.867] | 0.8125 [0.763, 0.858] |
| Kaggle uncapped | 240 | 3 | 100000 | m3 | 0.9583 [0.933, 0.983] | 0.9333 [0.900, 0.963] |

pilot source: benchmark/CONCEPTUAL_FAIR_RESULTS.json (committed).
Kaggle cap sweep source: /kaggle/working/SWEEP_cap_*.json (not yet committed to repo).
Also added benchmark/cck_context.py: tiered-context assembly as a callable function, portable
Tier-1 header from core/templates/always-on (not personal steering).

1. Commit SWEEP_cap_*.json from Kaggle to fair-metrics-wip.
2. Embedder sweep: run conceptual_fair_metrics.py with --embed-model BAAI/bge-base-en-v1.5 and
   jinaai/jina-embeddings-v2-base-en at cap=100000. K3 gate: download size must confirm model loaded.
3. m3 threshold sensitivity sweep (0.65-0.80) to close the forking-paths attack.
4. Task-success harness (Gemma + SWE-bench): the only path past the grounding-retention proxy.

## Study three replication: committed runner on a fresh clone (2026-11-11)

[MEASURED] Runner: conceptual_fair_metrics.py at commit b8cc6d8, run unchanged on Kaggle (CPU) on fresh
depth-200 clones of requests, click and black. N=240, k=6, bootstrap=1000, bge-small-en-v1.5,
m3 threshold 0.72. Files: benchmark/SWEEP_cap_1000.json, benchmark/SWEEP_cap_100000.json. Tables are
rebuilt from these files by benchmark/cck_kaggle_results_public.ipynb.

| Cap | m1 BM25 | m1 Semantic | m2 BM25 | m2 Semantic | m3 BM25 | m3 Semantic |
|-----|---------|-------------|---------|-------------|---------|-------------|
| 1000 | 0.8542 [0.8083,0.9] | 0.4542 [0.3917,0.525] | 0.8292 [0.7792,0.875] | 0.2958 [0.2375,0.3542] | 0.9417 [0.9125,0.9667] | 0.7042 [0.6458,0.7625] |
| 100000 | 0.8542 [0.8083,0.9] | 0.8917 [0.85,0.9292] | 0.8292 [0.7792,0.875] | 0.8 [0.7417,0.85] | 0.9417 [0.9125,0.9667] | 0.9458 [0.9167,0.9708] |

- Internal control holds: BM25 is identical at both caps on every metric.
- At cap 1000 every interval pair is disjoint; at full corpus every pair overlaps.
- Against the 2026-09-25 run, every cell differs by at most 0.025 (largest: semantic m1 at full corpus,
  0.8667 to 0.8917). BM25 shifted by the same amount at both caps, consistent with a changed corpus or
  question set from the newer clone, not with the dense budget.
- Interval overlap is not equivalence. These files lack per-question hits, so no paired test is
  possible from them; benchmark/confound_sweep.py stores hits for that.
- Invalid, do not cite: outputs of cck_kaggle_sweep.ipynb and cck_kaggle_full_corroboration.ipynb
  (inline reimplementation with 400-word chunks; the cap never bound).

## Studies four and five: coverage and chunk length as controlled factors (2026-11-12)

[MEASURED] Runner: benchmark/confound_sweep.py (imports the committed miner, BM25, line chunker, retriever and
metrics; only the dense ranking uses numpy, verified identical to the committed runner on all 12 cells of
SWEEP_cap_*.json). Kaggle CPU, N=240 per repository set, k=6, bge-small-en-v1.5 unless noted, bootstrap 1000
(10,000 for the equivalence test). Repository commits: requests 3c7baaa, click 8abb77a, black b4f1fca,
flask 49943b5, httpx b5addb6, rich 3a109cc. Every table below is rebuilt by
benchmark/cck_kaggle_results_public.ipynb.

Coverage, paired (8-line chunks). BM25 minus dense, m1, with exact McNemar on discordant questions:

| Repositories | Cap | Dense indexed fraction | m1 diff [95% CI] | McNemar p |
|---|---|---|---|---|
| requests/click/black | 1000 | 66% / 26% / 13% | 0.400 [0.325, 0.471] | < 1e-6 |
| requests/click/black | full | 100% | -0.038 [-0.088, 0.013] | 0.19 |
| flask/httpx/rich | 1000 | 43% / 45% / 15% | 0.283 [0.217, 0.354] | < 1e-6 |
| flask/httpx/rich | full | 100% | -0.033 [-0.079, 0.008] | 0.20 |

Equivalence at full coverage (paired TOST, 90% interval inside the margin): equivalent at margin 0.10 on
m1, m2 and m3 for both repository sets and pooled (N=480); smallest margins 0.023 to 0.079. Pooled m1 shows
a small dense advantage, -0.035 [-0.069, -0.002] at 95%.

Embedder and threshold at full coverage (interval overlap only; committed runner stores no per-question
hits): bge-base-en-v1.5 m1 BM25 0.854 vs dense 0.888, m2 0.829 vs 0.825, m3 0.950 vs 0.954, all intervals
overlap (SWEEP_bge_base_full_N240.json). m3 at threshold 0.65 0.979 vs 0.979, 0.72 0.942 vs 0.946, 0.80
0.867 vs 0.892, all overlap.

Chunk length at full coverage (requests/click/black):

| Chunker | Median tokens | Chunks over 512 | Dense m1 | BM25 m1 | m1 diff [95% CI] |
|---|---|---|---|---|---|
| 8 lines | 71 | 0.5% | 0.892 | 0.854 | -0.038 [-0.088, 0.013] |
| 32 lines | 301 | 3.2% | 0.821 | 0.975 | 0.154 [0.104, 0.204] |
| 400 words | 1,081 | 100% | 0.663 | 1.000 | 0.338 [0.275, 0.396] |

Embedder window probe (bge-small): a change after 128 or 400 filler words alters the embedding (cosine 0.764,
0.824); after 600 or more filler words it does not (cosine 1.000).

Truncation isolated (400-word chunks, identical questions and returned text; dense scores each chunk by its
best window of at most 480 tokens; BM25 hits identical across the two files): dense m1 0.663 to 0.888, gain
0.225 [0.171, 0.279], 56 questions fixed and 2 broken, McNemar p = 1.2e-14; m2 0.504 to 0.829, 81 fixed and 3
broken, p = 1.0e-20; m3 0.804 to 0.917, p = 4.6e-7. Windowing removes 67%, 66% and 58% of the BM25 gap on
m1, m2 and m3.

Scope and open items:
- Across chunkers the retrieved text per question differs (k=6 chunks of different sizes) and BM25 reaches
  its ceiling at 400 words, so cross-chunker gaps are compressed and partly a text-volume effect. The direction
  that holds: dense accuracy falls as chunks grow even though more text is returned.
- The residual gap after windowing (m1 0.113) and the 32-line gap are not explained by truncation; dilution of
  a single embedding over more content is one candidate, untested.
- Long-window embedder run (jina-embeddings-v2-base-en) dropped after two kernel deaths; only its window probe
  is recorded (embedding changes after 7,000 filler words).
- Docstring-mined questions, Python only, k=6, one embedder family. Retrieval proxy, not task success.
