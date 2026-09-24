# CCK Gemma Agent Port (DRAFT / UNTESTED)

Status: DRAFT scaffold. No access to the real competition harness at authoring time.
Nothing here has been evaluated on the competition. All performance claims below are
carried over from the CCK retrieval study (benchmark/POWERED_RESULTS.json) and are
labeled as such. This document proposes a mapping and a config skeleton only. It does
NOT report any Gemma-agent result, because none has been measured.

## What this is

A candidate submission for a SWE-bench-style agent-config competition whose base model
is fixed to gemma-4-31b-it-qat-w4a16-ct. The submission is an agent-config zip
(agent.yaml plus prompts, skills, adapters). This directory is the draft of that config,
built from the Consistent Context Kit (CCK) idea: select context by access pattern and
prefer cheap lexical retrieval for identifier-dense code recall.

## The measured finding this port is built on

Source: benchmark/POWERED_RESULTS.json (N=195 across three public repos: requests,
click, black). Proxy metric: answerable-in-context (a co-location proxy), NOT task
success. Lift over the no_context baseline is the signal.

Measured values (do not alter; use only these):
- no_context: answerable 0.0, avg_tokens 0
- monolithic: answerable 1.0, avg_tokens 471812
- summarized_L0.5: answerable 1.0, avg_tokens 471551
- retrieval_bm25 k3: answerable 0.9846, ci95 [0.9641, 1.0], avg_tokens 309
- retrieval_bm25 k6: answerable 0.9897, ci95 [0.9744, 1.0], avg_tokens 624
- retrieval_bm25 k10: answerable 0.9949, ci95 [0.9846, 1.0], avg_tokens 1061

Pilot (N=44, benchmark/ALGORITHM_RESULTS.md) additionally measured a lexical-vs-semantic
gap on identifier-dense recall: BM25 top6 answerable 0.909 vs semantic top6 0.614 at
near-identical token cost, diagnosed by chunk-contains-fact rate 0.93 (BM25) vs 0.68
(semantic). Label: pilot, not powered. The powered run scaled only the BM25 arm.

Takeaway the port relies on: for identifier-dense retrieval (function and class names,
symbols, exact tokens), lexical term overlap ranks the chunk that literally contains the
symbol higher than a general-purpose embedding does. Retrieval of a few chunks reaches
near-monolithic answerable at roughly three orders of magnitude fewer tokens.

## Mapping CCK onto the competition harness tools

The harness provides: get_code_neighbors, search_similar_code (embeddings),
get_code_subgraph, and read / edit / write / run_command. CCK's three tiers map on as
an access-pattern policy over these tools rather than as preloaded text.

Tier 1 (always-on): the smallest instructions the agent needs every turn. In this port
that is the system prompt and the repo_navigation skill trigger text only. Kept minimal,
consistent with the CCK cost model (metadata-to-body ratio drives the savings).

Tier 2 (on-demand retrieval): fetched only for the current sub-task, analogous to CCK's
BM25 top-k arm.
- Identifier-dense lookups (a named function, class, symbol, or exact token appears in the
  task text): route to lexical-first tools. get_code_neighbors and get_code_subgraph are
  structural and identifier-anchored (they resolve a named symbol to its call or dependency
  neighborhood), so they match the regime where the CCK study measured lexical winning.
  Prefer these when the query carries an exact identifier.
- Conceptual or paraphrase lookups (behavior described in prose, no exact symbol given):
  route to search_similar_code (embeddings). This is where semantic retrieval is expected
  to help and where the pilot noted the question set underrepresented, so the port uses it
  as a fallback and for intent-level search, not for exact-symbol recall.

Tier 3 (query-only): read / write / edit / run_command touch file bodies and the
environment only when a specific action needs them, never preloaded.

Design rule derived from the finding: extract identifiers from the task first; if present,
try get_code_neighbors and get_code_subgraph on those identifiers before search_similar_code.
Fall back to embeddings when no exact identifier resolves or when the need is conceptual.
This is a hypothesis for the harness, grounded in the CCK answerable proxy; it is not yet
validated on task success.

## Files in this directory

- agent.yaml            candidate config: root coder agent + analyzer sub-agent + skill
- prompts/system.md     root agent system prompt (identifier-first retrieval policy)
- prompts/analyzer.md   analyzer sub-agent prompt (localize before edit)
- skills/repo_navigation.md   the on-demand navigation policy over the harness tools

## Honest limits

- No competition harness access here. The tool names, signatures, and config schema are
  taken from the provided overview; exact field names may differ and must be reconciled
  against the real harness before submission.
- The CCK metric is an answerable-in-context proxy on a research/text corpus, not
  SWE-bench task success on code. Transfer is a hypothesis.
- The lexical-vs-semantic result is a pilot (N=44) for the semantic arm; only BM25 was
  scaled to N=195. Treat the routing rule as motivated, not proven.
- get_code_neighbors and get_code_subgraph are structural graph tools, not BM25. The claim
  is that they occupy the same identifier-anchored regime, not that they are the same
  algorithm.
