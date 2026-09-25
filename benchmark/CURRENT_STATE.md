# Benchmark Current State

Date: 2026-09-24

Scope: dated record of the two pilot result sets currently on main. All numbers are measured with a
real gpt2 BPE tokenizer on real public repositories. Both studies score a grounding-retention proxy
(is the needed content present in the assembled context), NOT task success. Results are pilot-scale
and preliminary.

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

## Honest caveats

- Grounding-retention proxy, NOT task success.
- Pilot-scale and preliminary.
- Semantic index capped at 1200 chunks per repo due to an 8GB memory limit; an uncapped index may
  change the semantic score.
- Study one uses three repos (requests, click, black); study two used two repos in the paired split.
- One embedder only (bge-small); a different or larger embedder may score differently.

## What is on main now

- benchmark/POWERED_RESULTS.json (study one raw numbers)
- benchmark/CONCEPTUAL_RESULTS.json (study two raw numbers)
- benchmark/conceptual_semantic_vs_lexical.py (study two runner)
- benchmark/compare_algorithms_scaled.py (scaled comparison runner)
- benchmark/CURRENT_STATE.md (this record)

## Next step

Kaggle uncapped three-repo confirmation: rerun the semantic versus lexical comparison without the
1200-chunk cap, on three repos, to confirm whether lexical still wins once the semantic index is
uncapped.

## Update 2026-09-25: fair-metric re-test and the capping artifact

Added benchmark/conceptual_fair_metrics.py to address the metric-bias caveat without changing any
committed value. It scores three metrics: m1 substring anywhere (favors lexical); m2 def/class
definition line (stricter); m3 substring or cosine >= 0.72 semantic-credit (favors semantic).

Fair-metric results (answerable proxy, not task success):

| Run | N | repos | cap | metric | BM25 [95% CI] | semantic [95% CI] |
|-----|---|-------|-----|--------|---------------|-------------------|
| pilot | 90 | 2 | 1000 | m1 | 0.90 [0.84, 0.96] | 0.54 [0.44, 0.63] |
| pilot | 90 | 2 | 1000 | m2 | 0.86 [0.79, 0.92] | 0.43 [0.33, 0.53] |
| pilot | 90 | 2 | 1000 | m3 | 0.98 [0.94, 1.00] | 0.81 [0.73, 0.89] |
| scaled | 240 | 3 | 3000 | m1 | 0.83 [0.78, 0.88] | 0.75 [0.70, 0.81] |
| scaled | 240 | 3 | 3000 | m2 | 0.80 [0.74, 0.85] | 0.66 [0.60, 0.72] |
| scaled | 240 | 3 | 3000 | m3 | 0.93 [0.90, 0.96] | 0.88 [0.85, 0.92] |

pilot source: benchmark/CONCEPTUAL_FAIR_RESULTS.json (committed).
scaled source: Kaggle run output /kaggle/working/CONCEPTUAL_FAIR_KAGGLE.json (not committed here).

Reading: semantic gained about 20 points on m1 (0.54 to 0.75) as the cap rose from 1000 to 3000 and
N grew; BM25 (uncapped by construction) barely moved. The pilot gap was partly an asymmetric
index-capping artifact that starved the semantic arm, not solely retriever quality. At N=240 the m1
and m3 CIs overlap; only m2 (definition-line) keeps a clean non-overlapping lexical lead. m2 is also
the most task-relevant metric (find where a symbol is defined, which is where an editing agent acts).

Corrected honest claim: lexical holds a modest, metric-dependent edge, robust on definition-line
retrieval, once index budget is controlled. Still a grounding-retention proxy, not task success.

Also added benchmark/cck_context.py: the tiered-context assembly as one callable function, portable
Tier-1 header from core/templates/always-on (not personal steering). Assembly only; no model, no grading.

Open re-tests (planned): cap sweep at fixed embedder; embedder sweep (bge-small, bge-base, jina-base)
at fixed uncapped index, to decompose cap vs embedder vs N; m3 cosine-threshold sweep 0.65 to 0.80.
