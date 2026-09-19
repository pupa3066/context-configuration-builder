# Precision-Aware Context: Empirical Basis

> This module connects Consistent Context Kit's cost-tiering thesis to MEASURED evidence from the
> companion study `quant-memorization-study`. Same core principle on two axes:
> **spend the expensive resource only where it changes model behavior.**

## The shared principle
Consistent Context Kit tiers *context* by access pattern: always-on (cheap, every turn) vs on-demand
(loaded only when a task needs it) vs zero-cost (searchable). The goal is to stop paying for context
that doesn't change the outcome.

The quantization study asks the analogous question on the *precision* axis: when you compress a model
(FP16 → INT8 → INT4), what behavior actually changes? If aggregate factual recall is unaffected by
INT4 but verbatim memorization degrades, then "how much precision to spend" should depend on the
workload — exactly like "how much context to load" depends on the task.

## Measured evidence (from quant-memorization-study, 6 real models)
- **Factuality is robust to INT4** (N=100 PopQA, replicated across models): INT4 statistically
  indistinguishable from FP16 (McNemar p=1.0/1.0/0.38 on the three paired models; CIs straddle 0).
  → aggressive quantization is *safe* for factual-recall-style workloads.
- **Memorization is dominated by MODEL SCALE, not precision** (6 models): a clean monotonic
  "INT4 erases memorization" seen on a single 0.5B model did **not** replicate — 2/3 paired models
  declined with INT4 but Llama-3.2-1B increased (GAP 0.065→0.074), and larger INT4-only models
  memorize *more* (Qwen2.5-3B 0.105, Phi-3.5-mini 0.088). → the honest claim is "scale drives
  memorization; INT4's effect is small and inconsistent," NOT "compression erases memorization."
- **Methodology:** an N=8 factuality pilot false positive AND a single-model memorization artifact
  were both corrected by scaling (to N=100 and to 6 models). Same discipline this kit applies to
  context-cost claims: measure, replicate, don't assert.

## Cross-hardware replication (NVIDIA CUDA, study v1.1.0)
The original runs were Apple Silicon / MLX. The study's v1.1.0 added a Transformers + bitsandbytes
backend (`--backend hf`) and re-ran the two load-bearing probes on an RTX 5060 (Blackwell, sm_120),
offline, with the same probe and analysis code. Analysis JSONs are vendored in `data/cuda/` so the
advisor below can be run against them without a GPU.

| probe | hardware | result |
|---|---|---|
| Factuality, Qwen2.5-0.5B fp16 vs int4, PopQA N=100 | M-series / MLX | McNemar p=1.0, CI straddles 0 |
| same | RTX 5060 / CUDA | McNemar p=**1.0**, acc diff −0.01, CI **[−0.07, +0.05]** |
| Memorization, Qwen2.5 family, **int4 fixed**, 0.5B → 1.5B → 3B | RTX 5060 / CUDA | mem GAP **0.008 → 0.025 → 0.095** (monotonic, ~11×) |

Two things this adds to the evidence base:
1. **The factuality null is not an MLX artifact.** Same delta (~0), same p, on a different backend,
   quantization kernel (bitsandbytes nf4 vs MLX affine), and GPU vendor. Absolute accuracy differs
   (different PopQA sample), which is why only the fp16-vs-int4 delta is compared.
2. **The scale claim now has a controlled design.** The original 6-model sweep mixed families and had
   missing precision cells. The CUDA ladder holds family and precision constant and varies only size,
   so the monotonic rise in GAP can't be attributed to precision or family. This is the direct test of
   "scale, not precision" that the original sweep could only suggest.

Caveats carried over from the study: memorization N is small (40 passages/model), GAPs are small in
absolute terms and the ordering is the signal, no CI on the trend, one family (Qwen2.5). The
`precision_advisor.py --scale` output states these limits alongside the verdict.

```
python precision_advisor.py data/cuda/analysis_cuda_popqa_qwen05.json --workload factual
  → "INT4 safe for factual recall (diff CI [-0.07,0.05], p=1.0)"
python precision_advisor.py data/cuda/analysis_cuda_popqa_qwen05.json \
  --scale data/cuda/analysis_scale_qwen{05,15,3b}.json
  → "mem_GAP rises monotonically with size at fixed int4 (0.0083 -> 0.025 -> 0.095, 11x)"
```

## Design implication for context provisioning
The DEFENSIBLE cross-axis principle is the **factuality null**: aggressive compression is safe when it
doesn't change the behavior you care about (factual recall) — mirroring the kit's finding that
always-on monolithic context is wasteful when it doesn't change task outcome. The memorization side is
NOT settled at these model sizes (see study RESULTS_multimodel.md); the precision_advisor reflects this
by refusing to over-claim on memorization.
- Factual-lookup / synthesis tasks → tolerate aggressive compression AND lean (on-demand) context.
- Verbatim / exact-recall tasks → treat with caution and preserve resources, but note the memorization
  evidence at small scale is inconclusive pending larger-model tests.

The `precision_advisor.py` tool operationalizes this: it reads the study's real analysis JSON and
emits a workload-aware recommendation grounded in the measured CIs — and honestly reports
"underpowered / can't conclude" on memorization rather than asserting a decline. No hardcoded claims.
