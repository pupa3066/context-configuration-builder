# A Three-Tier, Cost-Stratified Context Architecture for Persistent Multi-Project Memory in AI Coding Agents

**Author:** Purnima Pathak
**Status:** Working paper / preprint draft, v0.1 (2026-09-04)

## Abstract

AI coding agents lose project context between sessions, and the common remedy — loading all relevant context on every turn — scales token cost linearly with the amount of remembered information. We present a context architecture that **stratifies persistent memory by access pattern rather than by topic**, mapping three token-cost regimes to three loading mechanisms: (1) *always-on* content in continuously-loaded steering files, kept minimal; (2) *on-demand* per-project content in skills whose bodies load only when invoked; and (3) *zero-cost-until-queried* content in a semantic knowledge base. A single editable **registry** governs which projects are active, decoupling enablement from file presence. We further introduce an **incremental cross-project provenance graph** with explicit measured-vs-claim labeling. On a **real five-tier deployment across four active projects**, we measure a **40.9% reduction in per-turn context size** versus a monolithic always-on baseline; using measured per-project averages, the reduction follows a scaling law rising to **85.0% at 100 projects** and asymptoting to **89.0%** (the metadata-to-body ratio). In a **battery of fresh-session recall probes (5/5 correct)**, agents with no prior conversation recalled measured cross-project facts, resolved a repository-provenance ambiguity, and correctly excluded inactive projects. The novelty is the **cost-stratified composition plus registry-governed activation**, and we show it is both durable and measurably cheap.

## 1. Introduction

Large-language-model coding agents operate within a bounded context window that is re-billed every turn. Practical "agent memory" schemes tend to either (a) re-derive context each session (expensive in latency and redundant reads) or (b) preload large context blocks that persist every turn (expensive in tokens). Neither addresses multi-project settings, where knowledge produced in one project is relevant to deliverables in another.

We ask: *can persistent, cross-project agent memory be made both durable and token-efficient?* Our answer separates the two concerns — durability (does the agent remember?) and cost (what does remembering cost per turn?) — and shows they can be optimized jointly by matching content to a loading tier by its access frequency.

## 2. Problem formulation and cost model

Let a session consist of $T$ turns. Always-on content of size $s$ costs $\approx s \cdot T$. On-demand content costs a fixed metadata amount $m$ every turn plus a body amount $b$ only on invoked turns ($k \le T$): $\approx m T + b k$. Query-only content costs only on explicit retrieval. For per-project detail where $k \ll T$, the on-demand tier is strictly cheaper whenever $bk + mT < bT$. For $N$ projects with fixed always-on tier $A$, per-turn context is $A + N\bar b$ (monolithic) vs. $A + N\bar m$ (tiered); reduction $= 1 - (A+N\bar m)/(A+N\bar b)$ rises with $N$, asymptoting to $1 - \bar m/\bar b$. Section 4 measures $A, \bar b, \bar m$ on a real deployment.

## 3. Architecture

**Tier 1 — Always-on (steering).** Rules and lean indexes: a portfolio index (one line per project), a cross-links graph, and the registry. Held small by construction.

**Tier 2 — On-demand (skills).** One skill per project carrying deep context (what/why, debug approach, data plan, key facts). Metadata (name + trigger description) loads at startup; the body loads only when the project is engaged.

**Tier 3 — Query-only (knowledge base).** A semantic mirror of all tiers, contributing nothing to per-turn context until queried.

**Registry-governed activation.** An editable table marks each project active/inactive. Activation is decided by the registry, *not* by whether a skill file exists — enabling a large on-disk corpus with a small active working set.

**Cross-project provenance graph.** Shared facts are recorded once with origin and consumers, labeled `[MEASURED]` (verified) or `[CLAIM]` (unverified), so downstream reasoning inherits calibrated confidence.

## 4. Verification

## 4. Measured results

We instrument a live deployment: a fixed always-on tier and four active-project skills.

**Measured tier sizes (bytes):** always-on tier $A = 11{,}808$; mean per-project skill body $\bar b = 2{,}502$; mean per-project skill metadata $\bar m = 274$.

**Per-turn context reduction vs. a monolithic always-on baseline**, using the measured $A,\bar b,\bar m$ in the §2 closed form:

| Projects $N$ | Monolithic (bytes) | Tiered (bytes) | Reduction |
|---|---|---|---|
| 4 (directly measured) | 21,816 | 12,904 | **40.9%** |
| 10 | 36,828 | 14,548 | 60.5% |
| 25 | 74,358 | 18,658 | 74.9% |
| 50 | 136,908 | 25,508 | 81.4% |
| 100 | 262,008 | 39,208 | 85.0% |
| $\to\infty$ | — | — | 89.0% ($1-\bar m/\bar b$) |

The four-project row is directly measured; larger-$N$ rows apply the measured per-project averages to the closed-form model.

## 5. Fresh-session recall experiment

To test durability, we issued a battery of probes to **fresh agent sessions with no prior conversation**, tools disabled, answering from loaded context alone. Result: **5/5 correct**.

| Probe | Result |
|---|---|
| Recall a measured cross-project quantitative fact (Int4 compression 3.7×) | PASS |
| Attribute a bug to its originating project | PASS |
| Recall a measured metric (composition zero-interference, Jaccard 0.0) | PASS |
| Enumerate the active-context project set | PASS |
| Correctly exclude an inactive (registry-disabled) project | PASS |

We report the raw count (5/5) rather than a rate given the small battery; larger-scale evaluation is future work.

## 6. Related work and novelty

Retrieval-augmented generation, memory buffers, and project-instruction files each address parts of the problem. The contribution here is their **cost-stratified composition**: assigning content to a loading tier by access frequency, adding a **registry indirection** that separates activation from presence, and layering an **explicit provenance graph with confidence labels** for multi-project reasoning. To our knowledge this specific composition, framed by a measured per-turn cost model, is not packaged elsewhere.

**Agent-independence.** The architecture is neutral markdown; only the loading mechanism is agent-specific. We demonstrate thin adapters projecting the same neutral core onto four distinct agents (Kiro CLI, Claude Code, Cursor, and a generic single-preamble target), showing the cost model and registry semantics transfer without rewriting context. A new agent requires only a small adapter, not a new context corpus.

## 7. Limitations

The reduction figures combine one directly-measured deployment (N=4) with a closed-form projection using measured per-project averages; they measure context *size*, and token counts are proportional estimates, not tokenizer-exact. The recall battery is small (5 probes) and deterministic. Tier behavior depends on the host agent's loading semantics. A controlled study measuring tokenizer-exact tokens-per-turn and task success across many projects and turns is future work.

## 8. Conclusion

Separating agent memory by access pattern — and governing activation with a registry — yields durable, cross-project context whose per-turn cost grows sublinearly with the number of projects (measured 40.9% reduction at N=4, projected 85% at N=100). We release the design as an open template (`kiro-context-kit`).

## Reproducibility

Templates, install scripts, and a clean-room demo (`demo/demo.sh`) accompany this paper. Tier-size measurements are reproducible with `wc` over the steering and skill files; the recall battery is reproducible in any agent environment supporting always-on and on-demand context resources.
