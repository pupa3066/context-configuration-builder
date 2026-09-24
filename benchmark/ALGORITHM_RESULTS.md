# Context-Algorithm Comparison: Empirical Results

Measured comparison of context-selection algorithms for a research agent, on a held-out set of real
ground-truth questions. Token-cost axis uses a real GPT-2 BPE tokenizer. Fidelity axis uses answerable
retention: the fraction of testable questions whose ground-truth facts remain answerable-in-context
(the fact appears co-located with a query keyword) in the injected context.

## Setup

- Corpus: three research projects, full retrievable context per project (curated docs, code, project
  steering, and git log/reflog history), not a hand-picked doc list. A fact counts as recoverable if
  it appears anywhere the agent could read, including version-control history.
- Questions: 50 author-written ground-truth questions with answers defined independently of any
  algorithm. 2 recent-state questions (dynamic ground truth) are scored separately. 4 questions fail
  the presence gate (exact fact string not found in the full corpus, mostly hyphenation or phrasing
  variants) and are excluded from the fidelity denominator. N = 44 testable.
- Retrieval arms chunk the corpus (8 lines per chunk) and select top-k=6. Lexical retrieval uses
  BM25. Semantic retrieval uses a bge-small ONNX embedding model with cosine similarity.

## Results (N=44 testable, real GPT-2 BPE)

| algorithm | tokens/turn | answerable | vs monolithic |
|---|---|---|---|
| monolithic | 231,048 | 0.977 | baseline |
| tiered_lossless | 234,835 | 0.977 | -1.6% |
| summarized L0.33 | 216,887 | 0.977 | 6.1% |
| summarized L0.50 | 216,887 | 0.977 | 6.1% |
| summarized L0.66 | 168,735 | 0.591 | 27.0% |
| retrieval BM25 top6 | 911 | 0.909 | 99.6% |
| hybrid BM25 top6 | 4,698 | 0.909 | 98.0% |
| semantic top6 | 924 | 0.614 | 99.6% |
| hybrid semantic top6 | 4,711 | 0.614 | 98.0% |

Figures: figures/pareto_token_vs_fidelity.png, figures/answerable_by_algorithm.png,
figures/tokens_by_algorithm.png. Data: results.csv, results_table.md.

## Findings

1. Retrieval cuts per-turn tokens by about 99.6 percent versus injecting the full context, while
   keeping answerable retention at 0.909. On a large research corpus, retrieving a few relevant
   chunks per question dominates every whole-context method on token cost.

2. Summarization is a weak token lever on this corpus. Below the safe frontier it saves about 6
   percent because the content is identifier and code dense with little prose to drop; past the
   frontier (level 0.66) retention collapses from 0.98 to 0.59. This reproduces the frontier-and-cliff
   shape on real questions.

3. For fact recall, lexical retrieval beats semantic retrieval (0.909 versus 0.614 answerable), at
   near-identical token cost. Diagnosis, verified directly: the ground-truth answers are identifiers
   and numbers (DOIs, ORCIDs, p-values, module names, memory figures) that carry little semantic
   signal, so the embedding model does not rank the chunks containing the exact strings into the top-k;
   BM25 term overlap does. Chunk-contains-fact rate was 0.93 for BM25 versus 0.68 for semantic. This
   refines the common assumption that semantic retrieval is uniformly preferable.

4. Tiered-lossless deferral is the right tool for small must-always-load content (rules), but for the
   large research body it is no better than monolithic, because one full body plus an always-on header
   is still the whole body. Rules and bulk research context call for different algorithms.

## Honest limits

- N = 44 is a pilot, not a powered study. Treat the numbers as a preliminary demonstration.
- Answerable retention is a proxy for usable-in-context, not task success. It does not measure whether
  an agent solves a downstream task; that needs a multi-step agent run.
- Retrieval quality depends on chunking and k. Only top-k=6 and top-k=10 were tested.
- The semantic result is specific to identifier-dense recall questions. Semantic retrieval may win on
  conceptual or paraphrase questions, which this question set underrepresents.
- Recent-state questions are excluded from the fidelity number and belong to a live-fetch tier, not a
  preloaded one.
