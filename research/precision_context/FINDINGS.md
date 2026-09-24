# Precision-Aware Context: Empirical Basis

> This module connects Consistent Context Kit's cost-tiering thesis to MEASURED evidence from the
> companion study `quant-memorization-study`. Same core principle on two axes:
> **spend the expensive resource only where it changes model behavior.**

## The shared principle
Consistent Context Kit tiers *context* by access pattern: always-on (cheap, every turn) vs on-demand
(loaded only when a task needs it) vs zero-cost (searchable). The goal is to stop paying for context
that doesn't change the outcome.

The quantization study asks the analogous question on the *precision* axis: when you compress a model
(FP16 -> INT8 -> INT4), what behavior actually changes? If aggregate factual recall is unaffected by
INT4 but verbatim memorization degrades, then "how much precision to spend" should depend on the
workload  -  exactly like "how much context to load" depends on the task.

## Measured evidence (from quant-memorization-study, 6 real models)
- **Factuality is robust to INT4** (N=100 PopQA, replicated across models): INT4 statistically
  indistinguishable from FP16 (McNemar p=1.0/1.0/0.38 on the three paired models; CIs straddle 0).
  -> aggressive quantization is *safe* for factual-recall-style workloads.
- **Memorization is dominated by MODEL SCALE, not precision** (6 models): a clean monotonic
  "INT4 erases memorization" seen on a single 0.5B model did **not** replicate  -  2/3 paired models
  declined with INT4 but Llama-3.2-1B increased (GAP 0.065->0.074), and larger INT4-only models
  memorize *more* (Qwen2.5-3B 0.105, Phi-3.5-mini 0.088). -> the honest claim is "scale drives
  memorization; INT4's effect is small and inconsistent," NOT "compression erases memorization."
- **Methodology:** an N=8 factuality pilot false positive AND a single-model memorization artifact
  were both corrected by scaling (to N=100 and to 6 models). Same discipline this kit applies to
  context-cost claims: measure, replicate, don't assert.

## Design implication for context provisioning
The DEFENSIBLE cross-axis principle is the **factuality null**: aggressive compression is safe when it
doesn't change the behavior you care about (factual recall)  -  mirroring the kit's finding that
always-on monolithic context is wasteful when it doesn't change task outcome. The memorization side is
NOT settled at these model sizes (see study RESULTS_multimodel.md); the precision_advisor reflects this
by refusing to over-claim on memorization.
- Factual-lookup / synthesis tasks -> tolerate aggressive compression AND lean (on-demand) context.
- Verbatim / exact-recall tasks -> treat with caution and preserve resources, but note the memorization
  evidence at small scale is inconclusive pending larger-model tests.

The `precision_advisor.py` tool operationalizes this: it reads the study's real analysis JSON and
emits a workload-aware recommendation grounded in the measured CIs  -  and honestly reports
"underpowered / can't conclude" on memorization rather than asserting a decline. No hardcoded claims.
