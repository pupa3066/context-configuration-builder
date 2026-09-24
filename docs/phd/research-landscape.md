# Research Landscape  -  verified citations (2026)

> For PhD application framing. All entries from located sources; verify each arXiv ID before citing formally.

## The most directly relevant work

**ETH Zurich (Vechev group / SRILab)**  -  *"Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?"*
Gloaguen, Mundler, Muller, Raychev, Vechev. arXiv **2602.11988** (v2, Jun 2026, CC-BY). [VERIFIED against arXiv abstract.]
- Verified finding (from the abstract): providing context files does **not generally improve** task success rates while **increasing inference cost by >20%** on average  -  across LLMs, agents, and both LLM-generated and developer-committed files. Instructions are followed, but repository *overviews* are not helpful.
- CORRECTION: the widely-quoted "tiered injection reduces context 60 - 80%" line is from a *secondary blog*, NOT this paper. Do NOT attribute it to the ETH authors. Cite only the verified finding above.
- Adjacent from this group: Hofer, Debenedetti, Tramer  -  prompt-injection in agentic environments (arXiv 2606.10525). SRILab = safe/reliable ML + program analysis. Strong fit for measurement-driven agent-context work.

## Other groups / directions on agent context & memory

- **UC Berkeley (Sky/RISE-lineage, EECS)**  -  "Toward Scalable and Self-Improving LLM Agents" (EECS-2026-213). Self-improving agentic systems.
- **MIT (Han Lab, Song Han)**  -  long-context inference efficiency: DuoAttention (retrieval+streaming heads), KV-cache reduction. Systems/efficiency angle.
- **Agentic Context Engineering (ACE)**  -  "Evolving Contexts for Self-Improving LMs" (arXiv 2510.04618): contexts as evolving playbooks (generation/reflection/curation)  -  close cousin of the registry/incremental-update idea.
- **Long-term agent memory**  -  SimpleMem / "Efficient Lifelong Memory for LLM Agents" (arXiv 2601.02553, up to 30x token reduction); MemAgent (2507.02259); InfMem System-2 memory control (2602.02704); AgentMemBench (2608.00009) benchmark.
- **Agentic long-context inference optimization**  -  arXiv 2509.09505, 2605.30842 (context management / decoupled long-context models).

## Where this project sits
- The *tiering technique* and *memory compression* are active, published areas (above). NOT novel on its own.
- Under-explored, and where this work contributes: **cross-project (not just cross-session) provenance graphs**, **registry-governed activation as an explicit policy layer**, and **portable, agent-independent packaging** with a measured per-turn cost model.
- Open questions worth a PhD: automatic tier assignment by measured access frequency; learned activation policy; accuracy-under-tiering at project-scale; cross-project knowledge transfer.

## Target labs (fit, in rough priority)
1. ETH Zurich  -  Vechev SRILab (directly published the context-file study; measurement + reliability focus).
2. MIT  -  Han Lab (efficiency/systems for long context).
3. UC Berkeley  -  agentic systems (self-improving agents).
