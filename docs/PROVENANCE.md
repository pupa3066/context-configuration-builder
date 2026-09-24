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

## Evidence artifacts
- `docs/paper/three-tier-context-architecture.md`  -  the novelty write-up.
- `docs/paper/results.json`  -  raw measured data (reproducible via `wc` + fresh-session probes).
- `demo/demo.sh`  -  clean-room reproduction of the workflow.

## Verified behaviors (this repo's history)
- Non-destructive, idempotent install (Kiro path + neutral core).
- Four working adapters (Kiro, Claude Code, Cursor, generic), tested clean-room.
- Measured per-turn context reduction 40.9% at N=4, projected 85% at N=100 (89% asymptote).
- Fresh-session cross-project recall: 5/5 probes.
