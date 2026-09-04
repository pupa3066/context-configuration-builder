# Related Work & Novelty Delta

> Verified citations only. Where an arXiv ID is from search (not fetched), it is marked [unverified-id].

## Directly adjacent
- **Gloaguen, Mündler, Müller, Raychev, Vechev — "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?"** arXiv:2602.11988 (v2, 2026, CC-BY). [VERIFIED]
  Negative result: repository context files don't generally raise SWE-bench success, add >20% cost. We build the *constructive* counterpart: does access-pattern-tiered loading recover success at lower cost?

## Agent memory / context engineering
- **ACE — "Evolving Contexts for Self-Improving Language Models"** arXiv:2510.04618 [unverified-id]. Contexts as evolving playbooks (generate/reflect/curate). Related to our incremental-update + registry idea, but focuses on content evolution, not access-pattern tiering evaluated on task success.
- **SimpleMem / "Efficient Lifelong Memory for LLM Agents"** arXiv:2601.02553 [unverified-id]. Up to ~30× token reduction via lifelong memory management; conversational-memory framing, not repo-level coding-agent context nor a tier-assignment policy.
- **MemAgent** arXiv:2507.02259, **InfMem (System-2 memory control)** arXiv:2602.02704, **AgentMemBench** arXiv:2608.00009 [unverified-ids]. Long-context/conversational memory management + a benchmark. Adjacent; none evaluate an *automatic access-pattern tier assignment* against coding-task success with a monolithic baseline.

## Efficiency / systems
- **MIT Han Lab — DuoAttention** (retrieval+streaming heads) [unverified-id]. Reduces long-context *inference* memory at the attention level — orthogonal (kernel/systems layer), complementary to our prompt-composition layer.

## Novelty delta (precise)
| Claim | Prior | Ours |
|---|---|---|
| Context files help/hurt | ETH 2602.11988 (negative) | turn it into a constructive C0–C3 test |
| Tiering technique | blogs, manual practice, ACE (content) | **automatic access-pattern tier assignment** with a cost-model-derived, principled threshold |
| Evaluation | ETH: success+cost on monolithic | success+cost on **tiered + auto-tiered**, non-inferiority design |
| Memory scope | mostly single-session/conversational | **cross-project** registry activation as an explicit variable |

## What is NOT claimed as novel
Tiering as an idea; that context files can hurt; long-term memory compression. Stated plainly to keep the contribution defensible (the algorithmic + evaluation delta is the contribution).
