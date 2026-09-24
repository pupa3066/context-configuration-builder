# Context-algorithm comparison (N=195 real questions, 3 real PyPI corpora, real gpt2 BPE)

| algorithm | tokens/turn | answerable | 95% CI | vs monolithic tokens |
|---|---|---|---|---|
| no_context | 0 | 0.0000 | [0.0000, 0.0000] | n/a |
| monolithic | 471,812 | 1.0000 | [1.0000, 1.0000] | +0.00% |
| summarized_L0.5 | 471,551 | 1.0000 | [1.0000, 1.0000] | +0.06% |
| retrieval_bm25_k3 | 309 | 0.9846 | [0.9641, 1.0000] | +99.93% |
| retrieval_bm25_k6 | 624 | 0.9897 | [0.9744, 1.0000] | +99.87% |
| retrieval_bm25_k10 | 1,061 | 0.9949 | [0.9846, 1.0000] | +99.78% |

Preliminary: answerable = ground-truth identifier recalled in the assembled context (a proxy for usable-in-context, NOT task success); lift over no_context (0.0) is the signal. Corpora: requests, click, black (real PyPI source). Retrieval arms are BM25 at k=3/6/10. Finding: BM25 retrieval reaches 0.9846 (k=3), 0.9897 (k=6), and 0.9949 (k=10) answerable while cutting tokens versus the monolithic full-context arm (471,812 tokens/turn) by 99.93%, 99.87%, and 99.78% respectively. Safe summarization at L=0.5 saves only 0.06% of tokens (471,551) because lossless-safe compression cannot drop identifier content. CIs are 1000-sample bootstrap.
