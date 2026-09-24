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
