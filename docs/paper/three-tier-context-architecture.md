# A Three-Tier, Cost-Stratified Context Architecture for Persistent Multi-Project Memory in AI Coding Agents

**Author:** Purnima Pathak
**Status:** Working paper / preprint draft, v0.3 (2026-09-25)

## Abstract

We make two contributions. First, a controlled index-size ablation (N=240 conceptual questions, 3 public repositories, 95% bootstrap CIs) shows that a widely reported lexical-over-semantic code-retrieval gap (0.867 vs 0.442 on m1 at index budget 1,000) is almost entirely an **index truncation artifact**: BM25 scores all corpus chunks regardless of budget and is flat across all budget levels; the semantic arm improves monotonically as budget rises, converging to identical performance at full budget (0.867 vs 0.867, overlapping CIs on all three metrics). Evaluations that fix a truncated semantic index are measuring corpus coverage asymmetry, not retriever quality. Second, we present a context architecture that **stratifies persistent agent memory by access pattern**, mapping three token-cost regimes to three loading mechanisms: always-on steering files (kept minimal), on-demand per-project skills (body loads only when invoked), and a zero-cost knowledge base. On a real deployment across four active projects, measured with a real BPE tokenizer, the tiered scheme uses **24.5% fewer tokens per turn** than a monolithic baseline (directly measured, N=4). Token savings scale with project count following a closed-form cost model. This addresses the problem identified by ETH Zurich (Gloaguen et al., arXiv:2602.11988): monolithic context files add >20% inference cost without improving task success -- our architecture makes context selective rather than wholesale. Task-success validation on the Gemma harness is in progress.

## 1. Introduction

Large-language-model coding agents operate within a bounded context window that is re-billed every turn. Practical agent memory schemes tend to either re-derive context each session (expensive in latency and redundant reads) or preload large context blocks that persist every turn (expensive in tokens). Neither addresses multi-project settings, where knowledge produced in one project is relevant to deliverables in another.

We ask two questions. First: *can persistent, cross-project agent memory be made both durable and token-efficient?* Second: *does retrieval method choice matter for code comprehension, and how should retrieval be evaluated?* Our index-size ablation gives a precise answer to the second question -- the answer depends on whether the evaluation holds corpus coverage equal across compared methods. Task-success validation of the full tiered system on the Gemma agent harness is in progress and not reported here.

## 2. Problem formulation and cost model

Let a session consist of $T$ turns. Always-on content of size $s$ costs $\approx s \cdot T$. On-demand content costs a fixed metadata amount $m$ every turn plus a body amount $b$ only on invoked turns ($k \le T$): $\approx m T + b k$. Query-only content costs only on explicit retrieval. For per-project detail where $k \ll T$, the on-demand tier is strictly cheaper whenever $bk + mT < bT$. For $N$ projects with fixed always-on tier $A$, per-turn context is $A + N\bar b$ (monolithic) vs. $A + N\bar m$ (tiered); reduction $= 1 - (A+N\bar m)/(A+N\bar b)$ rises with $N$, asymptoting to $1 - \bar m/\bar b$. Section 4 measures $A, \bar b, \bar m$ on a real deployment.

## 3. Architecture

**Tier 1 -- Always-on (steering).** Rules and lean indexes: a portfolio index (one line per project), a cross-links graph, and the registry. Held small by construction.

**Tier 2 -- On-demand (skills).** One skill per project carrying deep context (what/why, debug approach, data plan, key facts). Metadata (name + trigger description) loads at startup; the body loads only when the project is engaged.

**Tier 3 -- Query-only (knowledge base).** A semantic mirror of all tiers, contributing nothing to per-turn context until queried.

**Registry-governed activation.** An editable table marks each project active/inactive. Activation is decided by the registry, not by whether a skill file exists -- enabling a large on-disk corpus with a small active working set.

**Cross-project provenance graph.** Shared facts are recorded once with origin and consumers, labeled `[MEASURED]` (verified) or `[CLAIM]` (unverified), so downstream reasoning inherits calibrated confidence.

## 4. Token cost measurement

We instrument a live deployment with a real BPE tokenizer (GPT-2), a fixed always-on tier, and four active-project skills.

**Measured (tokens):** always-on tier $A = 3{,}859$; mean per-project skill body $\bar b = 774$; mean per-project metadata $\bar m = 73$.

**Per-turn token cost vs. a monolithic always-on baseline.**

| Projects $N$ | Monolithic (tokens) | Tiered (tokens) | Reduction |
|---|---|---|---|
| 4 (directly measured) | 6,958 | 5,253 | **24.5%** |
| 10 (projected) | 11,599 | 5,363 | 53.8% |
| 25 (projected) | 23,209 | 6,458 | 72.2% |
| 50 (projected) | 42,559 | 8,283 | 80.5% |
| 100 (projected) | 81,259 | 11,933 | 85.3% |

The N=4 row is directly measured; all other rows apply the measured per-project averages to the closed-form model in Section 2 and are projections, not measurements. The reductions are CCB-marginal: measured with the agent's default resource loading disabled so the steering is the sole context. For agents without a disable knob, the agent's own system prompt adds a fixed per-turn overhead $B$ to both arms; the absolute token delta is unchanged but the percentage reduction is diluted. Both figures are reported by `benchmark.py --agent-baseline B`.

## 5. Retrieval study: index truncation bias in code comprehension benchmarks

**Setup.** We compare BM25 (lexical) against bge-small-en-v1.5 (semantic, via fastembed ONNX, CPU-deterministic) on N=240 conceptual questions mined from public repository docstrings (psf/requests, pallets/click, psf/black). The retrieval query is the question only -- the ground-truth fact is withheld from the retriever and used only for scoring. Three metrics: m1 (substring anywhere; structurally favors lexical), m2 (symbol appears on a definition line; stricter, neither retriever favored), m3 (substring or cosine-credit >= 0.72 to the fact's definition embedding; actively favors semantic). Bootstrap CIs, 1,000 resamples, Kaggle CPU (16GB).

**Index-size ablation and the internal control.** BM25 operates over all corpus chunks unconditionally -- its score cannot depend on the semantic index budget. We therefore use BM25 as an internal control: if BM25 scores change as we vary the budget, some other variable changed; if they are flat, the index budget is the sole variable. BM25 is flat across all three budget levels on all three metrics (m1: 0.867 at every budget; m2: 0.821; m3: 0.958), confirming that the ablation is clean.

| Index budget | m1 BM25 | m1 Semantic | m2 BM25 | m2 Semantic | m3 BM25 | m3 Semantic |
|---|---|---|---|---|---|---|
| 1,000 | 0.867 [0.825, 0.908] | 0.442 [0.379, 0.508] | 0.821 [0.771, 0.867] | 0.279 [0.221, 0.338] | 0.958 [0.933, 0.983] | 0.713 [0.654, 0.771] |
| 3,000 | 0.867 [0.825, 0.908] | 0.758 [0.704, 0.813] | 0.821 [0.771, 0.867] | 0.650 [0.592, 0.713] | 0.958 [0.933, 0.983] | 0.863 [0.817, 0.904] |
| 100,000 (full) | 0.867 [0.825, 0.908] | **0.867 [0.821, 0.908]** | 0.821 [0.771, 0.867] | **0.813 [0.763, 0.858]** | 0.958 [0.933, 0.983] | **0.933 [0.900, 0.963]** |

**Finding.** Semantic scores improve monotonically as index budget rises. At full budget all three metric gaps disappear: m1 point estimates are identical (0.867 vs 0.867, CIs overlap); m2 gap is 0.008 (CIs overlap); m3 gap is 0.025 (CIs overlap). The m3 result is notable: even under a metric that gives semantic retrieval explicit credit for cosine-similar chunks, the pattern holds. The original large m1 gap (0.867 vs 0.442 at budget=1,000) is an index truncation artifact -- the semantic arm was never given the chunks containing the answers. BM25's flatness rules out any other explanation.

**Implication.** Retrieval method choice matters less than index budget completeness for this class of code-comprehension questions. Evaluations that fix a truncated semantic index are measuring corpus coverage asymmetry, not retriever quality. Both methods are equivalent at full corpus coverage; deployment choice should be driven by latency and infrastructure constraints.

## 6. Related work and novelty

Retrieval-augmented generation, memory buffers, and project-instruction files each address parts of the persistent-context problem. The contribution here is their cost-stratified composition: assigning content to a loading tier by access frequency, adding a registry indirection that separates activation from presence, and layering an explicit provenance graph with confidence labels for multi-project reasoning.

The retrieval study contributes to evaluation methodology for code comprehension. Prior lexical-vs-semantic comparisons for code typically hold index size fixed across methods without varying the budget as an independent variable. Our ablation isolates the budget effect and shows it accounts for nearly the entire reported gap, with direct implications for benchmark design.

**Agent-independence.** The architecture is neutral markdown; only the loading mechanism is agent-specific. Thin adapters project the same core onto four agents (Kiro CLI, Claude Code, Cursor, generic preamble) without rewriting context.

**ETH Zurich extension.** Gloaguen et al. (arXiv:2602.11988) show monolithic context files do not improve task success and add >20% cost. Our tiered architecture addresses the cost side of that finding; our Gemma agent-config tests whether selective loading recovers task success at lower cost -- the constructive question their study left open.

## 7. Limitations

The N=4 token-cost reduction is directly measured; all larger-N rows are closed-form projections from those four data points, not measurements. The retrieval study uses three Python repositories (one language, one domain) and docstring-mined questions (formulaic, not human-written developer queries). The index truncation finding holds for this corpus and question type; it does not generalize to all retrieval settings without further study. Task-success validation on the Gemma harness is pending and is the critical gap between the mechanism findings reported here and a claim about agent performance.

## 8. Conclusion

A controlled index-size ablation over three metrics and three index budgets shows that widely reported lexical-over-semantic code-retrieval gaps are index truncation artifacts: BM25 is flat (internal control confirmed), semantic scores improve monotonically with budget, and both retrievers perform equivalently at full corpus coverage. Separately, a three-tier context architecture stratifies agent memory by access pattern, yielding a directly measured 24.5% per-turn token reduction at N=4 that scales following a closed-form cost model. We release the architecture, benchmark code, and agent-config as open templates.

## Reproducibility

Token-cost measurements: `benchmark/benchmark.py`, GPT-2 BPE tokenizer, reproducible from any clone. Retrieval study: `benchmark/conceptual_fair_metrics.py` on psf/requests, pallets/click, psf/black; fastembed ONNX (CPU-deterministic across machines); result JSONs committed to the repository. Agent-config: `benchmark/gemma_agent/agent.yaml` with prompts and skills.
