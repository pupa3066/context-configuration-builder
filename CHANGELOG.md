# Changelog

All notable changes to context-config-builder are documented here.
Format based on Keep a Changelog; this project uses semantic versioning.

## Unreleased (feat/agent-parity)
- Agent parity between Kiro and Claude Code, verified each session by hooks/ccb-parity-check.sh.
- hooks/ccb-project-context.sh: project steering index (8,723 to 140 GPT-2 tokens at session start),
  per-project files on demand, repository steering mirrored for Claude Code via CLAUDE.local.md.
- ccb-bootstrap.sh: sets chat.defaultAgent=default and chat.agentEngine=v1; migrates the direct loader hook.
- adapters/claude-code.sh wire: live wiring to the Kiro install (no copies).
- scripts/agent-parity-probe.sh and research/AGENT_PARITY.md.

## [Unreleased] - 2026-09-18
### Added
- Self-installing Kiro bootstrap (`ccb-bootstrap.sh`): one idempotent, self-verifying installer that
  wires automatic session-start activation. It installs the hook scripts, copies always-on steering
  (non-destructive), sets `chat.disableInheritingDefaultResources=true` in `settings/cli.json`, declares
  the CCB `resources[]` and registers the `agentSpawn` hooks in `agents/default.json` (integrity check
  ordered first, timestamped backup before any edit), then runs the integrity check and prints PASS/FAIL.
  Honors `KIRO_HOME` and supports `--dry-run`. Verified: clean install PASSes all five checks; a second
  run is idempotent (no backup, no duplicate hooks/resources).
- Vendored agent-neutral hooks into `hooks/`: `ccb-integrity-check.sh` (session-start verifier, now
  honors `KIRO_HOME` and reads the override from `cli.json` when the live CLI is unavailable),
  `project-steering-loader.sh`, and `steering-loader-guard.sh` (self-heal wrapper).
- Design registry: each tiering design is a named, defined, claim-paired, runnable unit.
  `benchmark/DESIGNS.md` + `benchmark/designs.json` (token-cost axis) + `benchmark/designs_fidelity.json`
  (fidelity axis), run via `benchmark/run_designs.py` and `benchmark/run_fidelity.py` against a committed
  `benchmark/sample/` corpus, so a contributor can test any design without branch-hopping or a private setup.
- Two labeled metric axes with explicit non-comparability: token-cost (always-on tokens + rule-firing
  integrity) vs fidelity (grounding retention vs token saving). "Better" is defined per axis.
- Contributor safeguard: `scripts/check_pr.py` + `.github/workflows/pr-safeguard.yml` scan every PR/fork
  for sensitive-info leaks (personal paths, secrets, hostname emails) and surface the attribution gate;
  a failing check blocks merge. Verified by injected-leak test.
- Measured results (structure/cost, real gpt2-BPE, sample corpus): monolithic to 3-location tiering
  reduces per-turn tokens with full rule-firing integrity; summarization has a grounding safe frontier
  before a fidelity cliff. NOT task quality (that needs a real-agent SWE-bench run).
### Changed
- Agent-independent measurement: `benchmark/benchmark.py` and `research/harness/compare_all.py` accept a
  context root via argument or `CCK_CONTEXT_ROOT` (default retained), so any agent's deployment can be
  measured, not only the default path.
- De-branded documentation: prose, examples, and marketing refer to a generic CLI agent rather than one
  specific agent; the four adapters (including the Kiro adapter) remain as the agent-independence feature,
  and research model names are unchanged.

## [0.2.0] - 2026-09-04
### Added
- `scripts/rules-builder.sh`: manage the rules/debug list as data (list/add/remove/check).
  Priority rules (R0..Rn) read first; R0 protected; custom rules use stable [Cn] IDs.
- Agent-independent core + adapters (Kiro, Claude Code, Cursor, generic).

## [0.1.0] - 2026-09-04
### Added
- Three-tier context architecture templates (steering / skills / knowledge base).
- Editable `context-registry.md` governing which projects are active.
- POSIX `install.sh` (non-destructive, idempotent, `--dry-run`).
- `scripts/add-project.sh` and `scripts/remove-project.sh` lifecycle helpers.
- `demo/demo.sh` clean-room walkthrough.
- `docs/ARCHITECTURE.md` (token-cost design) and `docs/paper/` (novelty write-up).
- Marketing: launch post and go-to-market strategy under `marketing/`.
- Business Source License 1.1 (converts to Apache-2.0 on the Change Date).
