# Provenance  -  how this was built

> Development lineage, for the novelty/marketing record and to establish authorship timestamps.

## Origin
Extracted from a real multi-project research workflow (on-device ML on Apple Silicon).
The context system was first built and battle-tested managing the author's own repositories,
then generalized  -  with all personal data removed  -  into this kit.

## Lineage (git + PR trail; nothing deleted)
- `9f7fa2a`  -  Initial release v0.1.0 (Kiro-native templates, install, lifecycle scripts, marketing, paper).
- `51908a2`  -  Paper backed with measured data (tier sizes, scaling law, 5/5 recall).
- Branch `feat/agent-independent` (commit `12e04e3`) -> **PR #1** -> merge commit `92971b6`:
  made the kit agent-independent (neutral core + adapters for Kiro, Claude Code, Cursor, generic).

Branches and PRs are preserved (not deleted) so the "what led to what" trail is auditable.

## Fair-metric re-test lineage (branch fair-metrics-wip, 2026-09-25)
What led to what, in order:
- The conceptual semantic-vs-lexical pilot (N=100 local, N=180 Kaggle) reported a large
  lexical advantage. A reviewer-style critique (caveat #4) noted the original metric
  (substring present anywhere) structurally favors lexical retrieval, since the ground
  truth is an identifier string.
- To test that honestly without overwriting any committed value, conceptual_fair_metrics.py
  was added: it re-scores under three metrics side by side. m1 substring (favors lexical);
  m2 defline, def/class definition line (stricter); m3 semantic-credit, cosine >= 0.72
  (favors semantic). Original runners and results were left untouched.
- N=90 pilot (2 repos, cap 1000): BM25 0.90 / 0.86 / 0.98 vs semantic 0.54 / 0.43 / 0.81.
  Committed at benchmark/CONCEPTUAL_FAIR_RESULTS.json.
- N=240 (3 repos, cap 3000, Kaggle): BM25 0.83 / 0.80 / 0.93 vs semantic 0.75 / 0.66 / 0.88.
  Reported from a Kaggle run (output at /kaggle/working/CONCEPTUAL_FAIR_KAGGLE.json); not
  yet committed to this repo.
- Reading across scales: semantic gained about 20 points on m1 (0.54 to 0.75) when the index
  cap rose and N grew, while BM25 (uncapped by construction) barely moved. Inference: the
  pilot gap was partly an asymmetric index-capping artifact, not solely retriever quality.
  m2 (definition-line) is the one metric where lexical wins persist with non-overlapping CIs
  at both scales.
- Added cck_context.py: extracts the tiered-context assembly into one callable function with
  a portable Tier-1 header from the repo's own core/templates/always-on files, decoupled from
  any local ~/.kiro steering. This is the seam for a future task-success harness; it assembles
  context only, runs no model and grades no patch.

Open re-tests (planned, not yet run): a cap sweep at fixed embedder and an embedder sweep at
fixed uncapped index, to decompose how much of the pilot gap was cap vs embedder vs sample
size; plus an m3 cosine-threshold sensitivity sweep (0.65 to 0.80).

All numbers above are a grounding-retention proxy (is the answer present in retrieved
context), not agent task success. Preliminary until the sweeps land.

Branches and PRs remain preserved for an auditable trail.

## Evidence artifacts
- `docs/paper/three-tier-context-architecture.md`  -  the novelty write-up.
- `docs/paper/results.json`  -  raw measured data (reproducible via `wc` + fresh-session probes).
- `demo/demo.sh`  -  clean-room reproduction of the workflow.

## Verified behaviors (this repo's history)
- Non-destructive, idempotent install (Kiro path + neutral core).
- Four working adapters (Kiro, Claude Code, Cursor, generic), tested clean-room.
- Measured per-turn context reduction 40.9% at N=4, projected 85% at N=100 (89% asymptote).
- Fresh-session cross-project recall: 5/5 probes.
