# Architecture

## Design principle: split context by access pattern, not by topic

The cost of agent context is dominated by what's loaded **every turn**. So the system separates content by how often it's needed:

1. **Always-on (steering, `file://`)**  -  loaded every turn. Cost = size x turns. Keep it tiny: only rules and lean indexes (portfolio, cross-links, registry).
2. **On-demand (skills, `skill://`)**  -  only metadata (name + description) is loaded at startup; the full body loads when invoked. Cost ~= 0 until you enter that project. This holds the bulk of per-project detail.
3. **Zero-cost (knowledge base)**  -  nothing in context until queried. A searchable mirror of everything for semantic recall.

## The registry indirection

Enablement is decided by `context-registry.md`, not by which files exist on disk. This means:
- You can keep many project skills on disk but only activate a few.
- Add/remove a project from the agent's active context with a one-line edit.
- Cross-project reasoning is scoped to enabled projects only.

## Incremental update discipline

As work produces results, append one entry to the relevant project skill and (if cross-project) one line to cross-links.md, then refresh only that file in the KB. This keeps the graph current without expensive full rewrites.

## Provenance labeling

Facts are labeled `[MEASURED]` (verified) vs `[CLAIM]` (unverified). This keeps the context trustworthy and prevents assumptions from hardening into "facts."
