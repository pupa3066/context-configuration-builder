# Context-algorithm comparison (N=44 real questions, real gpt2 BPE)

| algorithm | tokens/turn | answerable | vs monolithic |
|---|---|---|---|
| monolithic | 231,048 | 0.977 | +0.0% |
| tiered_lossless | 234,835 | 0.977 | -1.6% |
| summarized_L0.33 | 216,887 | 0.977 | +6.1% |
| summarized_L0.50 | 216,887 | 0.977 | +6.1% |
| summarized_L0.66 | 168,735 | 0.591 | +27.0% |
| retrieval_bm25_top6 | 911 | 0.909 | +99.6% |
| hybrid_bm25_top6 | 4,698 | 0.909 | +98.0% |
| semantic_top6 | 924 | 0.614 | +99.6% |
| hybrid_semantic_top6 | 4,711 | 0.614 | +98.0% |

Preliminary: pilot N; answerable = ground-truth fact co-located with a query keyword (a proxy for usable-in-context, NOT task success). Retrieval arms use top-k=6. Finding: on an identifier/number-dense research corpus, lexical (BM25) retrieval recalls facts better than semantic embedding retrieval (0.909 vs 0.614), because DOIs/ORCIDs/p-values/module-names carry little semantic signal; both cut tokens ~99.6% vs monolithic. Safe summarization saves little (~6%).
