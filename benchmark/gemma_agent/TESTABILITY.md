# What is testable now vs needs the competition harness (DRAFT)

No performance number in this directory is a Gemma-agent result. This file separates what
can be checked locally, with no harness access, from what can only be measured on the real
competition harness.

## Testable now (local, no harness, no network out)

1. Config well-formedness. agent.yaml parses as valid YAML; referenced files
   (prompts/system.md, prompts/analyzer.md, skills/repo_navigation.md) all exist and the
   paths resolve. Checkable with a YAML load and a path existence check.
2. Structural completeness. The config declares exactly the intended pieces: one root
   coder agent, one analyzer sub-agent, one repo_navigation skill, the fixed base model
   string gemma-4-31b-it-qat-w4a16-ct, and the tool list from the overview.
3. Constraint invariants. Analyzer has no edit/write/run_command tools (read-only
   localizer). Base model name is unchanged. temperature is 0.
4. Prompt policy consistency. The identifier-first ordering is stated the same way across
   system.md, analyzer.md, and repo_navigation.md (no contradictory guidance).
5. Grounding integrity. Every quantitative claim in this directory traces to
   benchmark/POWERED_RESULTS.json (N=195) or the labeled N=44 pilot in
   benchmark/ALGORITHM_RESULTS.md, with no altered or invented numbers.
6. The underlying CCK retrieval finding itself is already reproducible locally via
   benchmark/compare_algorithms_scaled.py on public repos (requests, click, black). That
   validates the premise (lexical wins on identifier-dense recall), not the Gemma agent.

A lightweight local check for items 1-4 can be a simple YAML-load-and-assert script; it is
NOT written here to avoid implying results exist. It would report pass/fail only.

## Needs the competition harness (cannot be measured here)

1. Any task-success number. SWE-bench-style resolved rate for this agent config on
   gemma-4-31b-it-qat-w4a16-ct. Unknown until run on the harness.
2. Token and step cost of the agent config under the real tool implementations.
3. Whether identifier-first routing (structural tools before embeddings) actually beats an
   embedding-first or embedding-only policy on task success. This is the core hypothesis;
   the CCK study only supports it as an answerable-in-context proxy on a text corpus.
4. The right default_top_k for this harness and metric (the CCK k-sweep is a proxy on a
   different corpus).
5. Exact tool signatures and config schema field names. Taken from the overview here;
   must be reconciled against the real harness before submission.
6. Sub-agent orchestration semantics: whether the harness supports a root/sub-agent split
   as expressed in agent.yaml, and how delegation is invoked.

## Honest bottom line

This is a motivated, PII-free draft scaffold. The premise (lexical beats semantic for
identifier-dense recall, retrieval reaches near-monolithic answerable at a fraction of the
tokens) is measured in CCK. The port of that premise to a Gemma agent-config on a
SWE-bench-style harness is a hypothesis and has zero measured results yet.
