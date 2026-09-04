# Context Configuration Builder

**Persistent, token-efficient, cross-project memory for AI coding agents.**

Your AI agent forgets everything between sessions and re-reads your whole codebase to catch up. Context Configuration Builder (CCB) gives it durable memory it loads once and updates as you work — with an explicit, measured token-cost model so context stays cheap. Configure *which* projects and *which* rules are active as editable lists; project the same context onto any agent.

> License: Business Source License 1.1 (source-available). Free for personal/internal use. Commercial redistribution or hosted resale requires a license until the Change Date, when it converts to Apache-2.0. See [LICENSE](LICENSE).

## The problem

- Agents lose context every session → you re-explain your projects.
- Dumping everything into always-on context is expensive (tokens every turn).
- Multi-project work has cross-links (a result in project A matters to paper B) that nothing tracks.

## The approach: three tiers by access pattern

| Tier | Mechanism | Token cost | Holds |
|---|---|---|---|
| Always-on | steering (`file://`) | small × every turn | rules + lean indexes |
| On-demand | skills (`skill://`) | ~0 until invoked | per-project deep context |
| Zero-cost | knowledge base | 0 until queried | searchable full mirror |

An editable **registry** decides which projects are active — add/remove with a one-line edit.

## Install

```bash
git clone <your-repo> context-config-builder && cd context-config-builder
./install.sh            # non-destructive: won't overwrite an existing ~/.kiro
```

Then:
1. Edit `~/.kiro/steering/00-rules.md` — your rules + visibility policy.
2. Edit `~/.kiro/steering/context-registry.md` — add your projects.
3. `./scripts/add-project.sh my-project` — scaffold a project skill.
4. Index `~/.kiro/steering` and `~/.kiro/skills` into your agent's knowledge base.

Start a new session; steering auto-loads. Verify with `/context show`.

## Verified behavior

These are behaviors confirmed in a working Kiro CLI environment (not marketing claims):
- Steering files placed in `~/.kiro/steering/` auto-load into a fresh session's context.
- A project skill loads its full body only when invoked (`/<name>-context`).
- Flipping ✅/⬜ in the registry changes which projects the agent treats as active, verified by querying a fresh session.

Your mileage depends on your agent version and configuration.

## What's included

- `templates/steering/` — rules, bootstrap protocol, registry, portfolio, cross-links (all generic, no personal data)
- `templates/skills/_example/` — the skill format
- `install.sh`, `scripts/add-project.sh`, `scripts/remove-project.sh`
- `demo/demo.sh` — clean-room walkthrough (basis for the demo GIF)
- `docs/ARCHITECTURE.md` — the token-cost design
- `docs/paper/` — novelty write-up (three-tier cost-stratified context architecture)
- `marketing/` — launch post + go-to-market strategy

## Try it in 30 seconds (safe, no changes to your setup)

```sh
sh demo/demo.sh
```

## Managing the rules/debug list (editable, like projects)

Rules are a configurable list too — add/remove/list without hand-editing prose:

```sh
scripts/rules-builder.sh list                                  # show all rules
scripts/rules-builder.sh add "Confirm before bulk deletes" --section "Repository"
scripts/rules-builder.sh add "No writes to foreign repos" --priority   # -> R1, R2, ...
scripts/rules-builder.sh remove C1        # remove a custom rule
scripts/rules-builder.sh check            # validate (R0 present, no dup IDs)
```

Priority rules (`R0`, `R1`, …) override everything and are read first. `R0` (rule governance) is protected and cannot be removed by the builder. Custom rules use stable `[C1]`, `[C2]` … IDs so they survive edits and reordering.

## Compatibility — agent-independent

The architecture is **agent-neutral**; only the loading mechanism differs per agent, handled by a thin **adapter**. Your context is written once (plain markdown in `~/.context-config-builder/`) and projected onto any supported agent.

| Agent | Adapter |
|---|---|
| Kiro CLI | `adapters/kiro.sh apply` |
| Claude Code | `adapters/claude-code.sh apply` |
| Cursor | `adapters/cursor.sh apply` |
| Any LLM / generic | `adapters/generic.sh build` (single preamble) |

```sh
./install-core.sh            # scaffold agent-neutral ~/.context-config-builder
./adapters/<agent>.sh ...    # project onto your agent
```

See `core/README.md` for the neutral layout and how to add a new agent (~30-line adapter).

### Kiro-native quick start (original path, still supported)
```bash
./install.sh                 # installs directly into ~/.kiro (steering + skills)
```
Concepts port to any agent framework with an always-on + on-demand context mechanism.
