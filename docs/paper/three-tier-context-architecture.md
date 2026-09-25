# A Three-Tier, Cost-Stratified Context Architecture for Persistent Multi-Project Memory in AI Coding Agents

**Author:** Purnima Pathak
**Status:** Working paper / preprint draft, v0.2 (2026-09-25)

## Abstract

AI coding agents lose project context between sessions, and the common remedy -- loading all relevant context on every turn -- scales token cost linearly with the amount of remembered information. We present a context architecture that **stratifies persistent memory by access pattern rather than by topic**, mapping three token-cost regimes to three loading mechanisms: (1) *always-on* content in continuously-loaded steering files, kept minimal; (2) *on-demand* per-project content in skills whose bodies load only when invoked; and (3) *zero-cost-until-queried* content in a semantic knowledge base. A single editable **registry** governs which projects are active, decoupling enablement from file presence. On a **real deployment across four active projects, measured with a real BPE tokenizer**, the tiered scheme uses **24.5% fewer tokens per turn** than a monolithic always-on baseline, rising to **85.3% at 100 projects**. We further report a controlled **retrieval study** (N=240 conceptual questions, 3 public repositories, bootstrap CIs) that diagnoses a common evaluation artifact: a large lexical-over-semantic code-retrieval gap (0.87 vs 0.44) is almost entirely produced by **index truncation bias** -- asymmetric corpus coverage that disadvantages the semantic arm; at full index budget both retrievers score identically (0.87 vs 0.87, overlapping CIs). This addresses a tension identified by ETH Zurich (Gloaguen et al., arXiv:2602.11988): repository-level context files often fail to improve task success while adding 20%+ inference cost -- motivating structuring context by access pattern rather than loading it wholesale.

## 1. Introduction

Large-language-model coding agents operate within a bounded context window that is re-billed every turn. Practical "agent memory" schemes tend to either (a) re-derive context each session (expensive in latency and redundant reads) or (b) preload large context blocks that persist every turn (expensive in tokens). Neither addresses multi-project settings, where knowledge produced in one project is relevant to deliverables in another.

We ask: *can persistent, cross-project agent memory be made both durable and token-efficient?* Our answer separates the two concerns -- durability (does the agent remember?) and cost (what does remembering cost per turn?) -- and shows they can be optimized jointly by matching content to a loading tier by its access frequency. We additionally ask: *does retrieval method choice matter for code comprehension, and how should that choice be evaluated?* A controlled index-size ablation reveals that the answer depends critically on evaluation methodology.

## 2. Problem formulation and cost model

Let a session consist of $T$ turns. Always-on content of size $s$ costs $\approx s \cdot T$. On-demand content costs a fixed metadata amount $m$ every turn plus a body amount $b$ only on invoked turns ($k \le T$): $\approx m T + b k$. Query-only content costs only on explicit retrieval. For per-project detail where $k \ll T$, the on-demand tier is strictly cheaper whenever $bk + mT < bT$. For $N$ projects with fixed always-on tier $A$, per-turn context is $A + N\bar b$ (monolithic) vs. $A + N\bar m$ (tiered); reduction $= 1 - (A+N\bar m)/(A+N\bar b)$ rises with $N$, asymptoting to $1 - \bar m/\bar b$. Section 4 measures $A, \bar b, \bar m$ on a real deployment.

## 3. Architecture

**Tier 1 -- Always-on (steering).** Rules and lean indexes: a portfolio index (one line per project), a cross-links graph, and the registry. Held small by construction.

**Tier 2 -- On-demand (skills).** One skill per project carrying deep context (what/why, debug approach, data plan, key facts). Metadata (name + trigger description) loads at startup; the body loads only when the project is engaged.

**Tier 3 -- Query-only (knowledge base).** A semantic mirror of all tiers, contributing nothing to per-turn context until queried.

**Registry-governed activation.** An editable table marks each project active/inactive. Activation is decided by the registry, *not* by whether a skill file exists -- enabling a large on-disk corpus with a small active working set.

**Cross-project provenance graph.** Shared facts are recorded once with origin and consumers, labeled `[MEASURED]` (verified) or `[CLAIM]` (unverified), so downstream reasoning inherits calibrated confidence.

## 4. Token cost measurement

We instrument a live deployment with a **real BPE tokenizer** (GPT-2), a fixed always-on tier, and four active-project skills.

**Measured (tokens):** always-on tier $A = 3{,}859$; mean per-project skill body $\bar b = 774$; mean per-project metadata $\bar m = 73$.

**Per-turn token cost vs. a monolithic always-on baseline.**

| Projects $N$ | Monolithic (tokens) | Tiered (tokens) | Reduction |
|---|---|---|---|
| 4 (directly measured) | 6,958 | 5,253 | **24.5%** |
| 10 | 11,599 | 5,363 | 53.8% |
| 25 | 23,209 | 6,458 | 72.2% |
| 50 | 42,559 | 8,283 | 80.5% |
| 100 | 81,259 | 11,933 | 85.3% |
| $\to\infty$ | -- | -- | 90.6% ($1-\bar m/\bar b$) |

The N=4 row is directly measured; larger-N rows apply the measured per-project averages to the Section 2 closed form. The reductions are *CCB-marginal*: measured with the agent's default resource loading disabled, so the steering is the sole context. For agents without a disable knob, the agent's own system prompt adds a fixed overhead to both arms; the absolute token delta is unchanged but the percentage reduction is diluted. Both figures are reported by `benchmark.py --agent-baseline B`.

## 5. Retrieval study: diagnosing an evaluation artifact in code comprehension

**Setup.** We compare BM25 (lexical) against bge-small-en-v1.5 (semantic, via fastembed ONNX) on N=240 conceptual questions mined from public repository docstrings (requests, click, black). Query is the question only -- no fact leak. Three scoring metrics: m1 (substring anywhere; favors lexical), m2 (definition line only; stricter), m3 (substring or cosine-credit >= 0.72; favors semantic). Bootstrap CIs, 1,000 resamples, run on Kaggle CPU (16GB, ONNX deterministic across machines).

**Index-size ablation.** BM25 scores all chunks regardless of index budget. The semantic arm embedded a truncated sample. We vary the index budget from 1,000 to 100,000 chunks per repository (effectively unconstrained: the largest repository has 6,975 chunks) while holding all else fixed. BM25 scores are flat across all budget levels -- the internal control confirming index budget is the sole variable.

| Cap | m1 BM25 | m1 Semantic | m2 BM25 | m2 Semantic |
|---|---|---|---|---|
| 1,000 | 0.867 [0.825, 0.908] | 0.442 [0.379, 0.508] | 0.821 [0.771, 0.867] | 0.279 [0.221, 0.338] |
| 3,000 | 0.867 [0.825, 0.908] | 0.758 [0.704, 0.813] | 0.821 [0.771, 0.867] | 0.650 [0.592, 0.713] |
| 100,000 (full) | 0.867 [0.825, 0.908] | **0.867 [0.821, 0.908]** | 0.821 [0.771, 0.867] | **0.813 [0.763, 0.858]** |

**Finding.** At full index budget the gap disappears: m1 point estimates are identical (0.867 vs 0.867); m2 gap is 0.008 with fully overlapping CIs. The original large gap (0.867 vs 0.442 at budget=1,000) is almost entirely an **index truncation artifact** -- the semantic arm was never given the chunks it needed, not because embeddings are weak at code, but because the evaluation design structurally disadvantaged them through asymmetric corpus coverage.

**Implication for code comprehension.** Retrieval method choice matters less than index budget completeness. Evaluations that compare lexical and semantic retrievers under a truncated semantic index are measuring index truncation bias, not retriever quality. For deployment, both methods are equivalent at full corpus coverage; the choice should be driven by latency and infrastructure constraints, not by truncated-index accuracy comparisons.

## 6. Fresh-session recall experiment

To test durability, we issued a battery of probes to **fresh agent sessions with no prior conversation**, tools disabled, answering from loaded context alone. Result: **5/5 correct**.

| Probe | Result |
|---|---|
| Recall a measured cross-project quantitative fact (Int4 compression 3.7x) | PASS |
| Attribute a bug to its originating project | PASS |
| Recall a measured metric (composition zero-interference, Jaccard 0.0) | PASS |
| Enumerate the active-context project set | PASS |
| Correctly exclude an inactive (registry-disabled) project | PASS |

We report the raw count (5/5) rather than a rate given the small battery; larger-scale evaluation is future work.

## 7. Related work and novelty

Retrieval-augmented generation, memory buffers, and project-instruction files each address parts of the problem. The contribution here is their **cost-stratified composition**: assigning content to a loading tier by access frequency, adding a **registry indirection** that separates activation from presence, and layering an **explicit provenance graph with confidence labels** for multi-project reasoning.

The retrieval study contributes to the benchmarking and code-comprehension literature. Prior comparisons of lexical and semantic retrieval for code (e.g. CodeBERT-style embeddings vs BM25) typically use fixed, often small indexes. Our index-size ablation shows that reported gaps between methods may be index truncation artifacts rather than intrinsic properties of the retrievers, which has direct implications for how code-comprehension retrieval benchmarks should be designed.

**Agent-independence.** The architecture is neutral markdown; only the loading mechanism is agent-specific. We demonstrate thin adapters projecting the same neutral core onto four distinct agents (Kiro CLI, Claude Code, Cursor, and a generic single-preamble target), showing the cost model and registry semantics transfer without rewriting context.

**ETH Zurich extension.** Gloaguen et al. (arXiv:2602.11988) show that monolithic repository context files do not improve task success and add >20% cost. Our tiered architecture directly addresses the cost side of that finding, and our agent-config submission to the Gemma harness tests whether selective loading recovers task success at lower cost -- the constructive question their study left open.

## 8. Limitations

The N=4 token-cost reduction is directly measured; larger-N rows are closed-form projections from measured per-project averages. The recall battery is small (5 probes) and deterministic. The retrieval study uses three Python repositories (one language, one domain) and docstring-mined questions (formulaic, not human-written). The index truncation finding does not imply that semantic and lexical retrievers are equivalent in all settings -- it implies they are equivalent for this corpus and question type at full index budget. Task-success validation on the Gemma harness is pending and is the critical next step.

## 9. Conclusion

Separating agent memory by access pattern -- and governing activation with a registry -- yields durable, cross-project context whose per-turn cost grows sublinearly with the number of projects (measured 24.5% reduction at N=4, projected 85.3% at N=100). A controlled index-size ablation reveals that widely reported lexical-over-semantic code-retrieval gaps are largely index truncation artifacts from asymmetric corpus coverage; at full index budget both retrievers perform equivalently. We release the architecture, benchmark code, and agent-config as open templates.

## Reproducibility

Token-cost measurements: `benchmark/benchmark.py` over the steering and skill files, GPT-2 BPE tokenizer, reproducible from any clone. Retrieval study: `benchmark/conceptual_fair_metrics.py` on public repositories (psf/requests, pallets/click, psf/black), fastembed ONNX (deterministic across machines), Kaggle CPU notebook. All result JSONs committed to the repository.
