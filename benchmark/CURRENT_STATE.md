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
