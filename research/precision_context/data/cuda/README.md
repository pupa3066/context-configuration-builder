# CUDA replication data (vendored)

Analysis JSONs copied verbatim from
[pupa3066/quant-memorization-study](https://github.com/pupa3066/quant-memorization-study) `results/`
at v1.1.0 (commit ca0bec9, merged PR #1). Produced on an NVIDIA RTX 5060 Laptop GPU via the
study's `--backend hf` path (Transformers + bitsandbytes, offline). Same probes and analysis code as
the original Apple-Silicon/MLX runs; only the model-loading/inference backend differs.

| file | experiment |
|---|---|
| `analysis_cuda_popqa_qwen05.json` | Qwen2.5-0.5B fp16 vs int4, PopQA 50/bin (N=100) |
| `analysis_cuda_mem_qwen05.json` | Qwen2.5-0.5B fp16 vs int4, memorization probe (small N) |
| `analysis_scale_qwen05.json` | Qwen2.5-0.5B **int4 only**, 40-passage mem corpus |
| `analysis_scale_qwen15.json` | Qwen2.5-1.5B int4 only |
| `analysis_scale_qwen3b.json` | Qwen2.5-3B int4 only |

Contributor: Akshay Upadhyay (@akshbhu, ORCID 0009-0000-1531-3198). Vendored so
`precision_advisor.py` can be run offline against cross-hardware data; regenerate from the study's
`docs/CUDA_REPLICATION.md` reproduce block.
