# Research Statement (draft)  -  Context Management for LLM Agents

> Draft for PhD applications. Tailor the opening to each target lab. Keep claims calibrated (see research-landscape.md).

## Motivation
Recent work from ETH Zurich (Gloaguen, Mundler, Muller, Raychev, Vechev  -  "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?", arXiv 2602.11988) finds that providing repository-level context files (AGENTS.md/CLAUDE.md) does *not* generally improve coding-agent task success while *increasing* inference cost by over 20%  -  across LLMs, agents, and both generated and human-written files. This exposes a core tension: agents need persistent context, but naive always-on context is expensive and frequently unhelpful. My work asks whether *how* context is structured and loaded  -  rather than whether it exists  -  can resolve this.

## What I built (evidence of ability)
Working from my own multi-project research workflow, I designed and released a **context configuration system** that stratifies persistent memory by *access pattern*:
- an always-on tier (rules + lean indexes),
- an on-demand tier (per-project context loaded only when engaged),
- a query-only tier (semantic mirror).
A registry decouples *activation* from *presence*, and a cross-project provenance graph links facts to the deliverables that consume them, with explicit measured-vs-claim labeling.

Using a real BPE tokenizer, I measured a 24.5% per-turn token reduction at 4 projects versus a monolithic baseline, scaling to a projected 85% at 100 projects (asymptote 90.6%)  -  reproducible, with honest limitations documented. These results are consistent with independently reported gains from tiered/selective context.

## The research questions (what I want to pursue)
1. **Automatic tier assignment.** Current systems (mine and prior work) assign tiers by hand. Can content be classified into always-on / on-demand / query-only from *measured* access frequency and task signals?
2. **Activation as a learned policy.** Which context to activate for a given task is a decision problem; can it be predicted rather than toggled?
3. **Cross-project knowledge transfer.** Most memory work is single-context/session; structured cross-project provenance is under-explored  -  including its effect on accuracy.
4. **Accuracy under tiering at scale.** Extend the ETH-style evaluation to many-project, many-turn settings with task-success metrics, not just cost.

## Fit
This agenda sits at measurement-driven agent systems  -  directly extending the ETH context-file line, and adjacent to efficiency work (MIT Han Lab) and self-improving agents (Berkeley). I bring working systems, an empirical/benchmarking mindset, and calibrated claims.

## Honesty note (do not remove)
The tiering *technique* is not my invention; my contribution is the portable, registry-governed packaging, the cross-project graph, and the measurements  -  and, going forward, the open questions above. Frame accordingly; do not overclaim novelty to a group that authored the foundational study.
