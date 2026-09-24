# Skill: repo_navigation (DRAFT / UNTESTED)

On-demand policy for choosing a retrieval tool by query type. Loaded only when the root
agent engages navigation, so it costs nothing on turns that do not navigate (CCK Tier 1
stays minimal; this is Tier 2, on-demand).

## Tool selection table

| Query type | Signal in the task | First tool | Fallback |
|---|---|---|---|
| Exact symbol lookup | a function, class, method, or token name is named | get_code_neighbors | get_code_subgraph |
| Dependency or call context | need callers, callees, imports of a named symbol | get_code_subgraph | get_code_neighbors |
| Conceptual or behavioral | prose description, no exact symbol | search_similar_code | re-anchor on found identifiers, then structural |
| File or line inspection | a specific location is already known | read | none |

## Why this ordering

Grounded in the CCK retrieval study (benchmark/POWERED_RESULTS.json, N=195, and the N=44
pilot in benchmark/ALGORITHM_RESULTS.md). On identifier-dense recall, lexical term overlap
ranked the chunk that literally contains a named symbol above a general-purpose embedding
(pilot: BM25 top6 answerable 0.909 vs semantic top6 0.614 at near-equal token cost;
chunk-contains-fact 0.93 vs 0.68). The structural tools here (get_code_neighbors,
get_code_subgraph) are identifier-anchored: they resolve a named symbol to its code
neighborhood, occupying the same regime where lexical matching won. search_similar_code
uses embeddings and is expected to help on conceptual or paraphrase queries, which the CCK
question set underrepresented, so it is the fallback and the intent-search entry point.

This is a hypothesis for THIS harness. The CCK metric is an answerable-in-context proxy on
a text/research corpus, not SWE-bench task success on code. Validate before trusting.

## k guidance

The CCK powered k-sweep measured k in {3, 6, 10} on the answerable/token frontier
(k3 0.9846 at 309 tok, k6 0.9897 at 624 tok, k10 0.9949 at 1061 tok). k6 is a reasonable
default, but these numbers are a proxy on a different corpus and metric; the right k for
this harness is unknown until measured. Start at 6, adjust only from measured harness data.

## Rules

- Extract identifiers before any retrieval; prefer structural tools when they exist.
- Retrieve the minimum; do not pull whole files or repos.
- Fall back to embeddings only when no identifier resolves or the need is conceptual.
- Never mislabel a lexical or structural result as semantic, or the reverse.
