# Changelog

All notable changes to context-config-builder are documented here.
Format based on Keep a Changelog; this project uses semantic versioning.

## [0.2.0] - 2026-09-04
### Added
- `scripts/rules-builder.sh` — manage the rules/debug list as data (list/add/remove/check).
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
