# Consistent Context Kit  -  agent-independent core

The architecture is agent-neutral. Only the **loading mechanism** differs per agent, handled by a thin **adapter**.

## Neutral layout

The kit stores context in an agent-neutral home (default `~/.context-config-builder/`):

```
~/.context-config-builder/
|-- always-on/          # Tier 1: rules + lean indexes (loaded every turn)
|   |-- rules.md
|   |-- portfolio.md
|   |-- cross-links.md
|   `-- context-registry.md
|-- projects/           # Tier 2: one file per project (loaded on demand)
|   `-- <name>.md
`-- index/              # Tier 3: optional; source for a KB/embedding mirror
```

This is plain markdown  -  no agent-specific syntax. The three tiers and the registry work identically everywhere.

## Adapters map the neutral core onto a specific agent

| Agent | Always-on tier | On-demand tier | Adapter |
|---|---|---|---|
| Kiro CLI | `~/.kiro/steering/*.md` | `~/.kiro/skills/*/SKILL.md` | `adapters/kiro.sh` |
| Claude Code | `CLAUDE.md` / project memory | referenced files loaded on demand | `adapters/claude-code.sh` |
| Cursor | `.cursor/rules/*.mdc` | referenced docs | `adapters/cursor.sh` |
| Generic / any LLM | concatenated preamble file | `@include` on request | `adapters/generic.sh` |

An adapter is a small script that **projects** the neutral core into the target agent's expected files/locations (usually by copying or symlinking, adding any required frontmatter). Change agents by running a different adapter against the same core  -  your context is written once.

## Why this matters

- **Portable:** your context isn't locked to one vendor. Move between Kiro, Claude Code, Cursor without rewriting.
- **Same cost model:** always-on stays tiny; per-project detail loads on demand; the registry gates activation  -  regardless of agent.
- **Future-proof:** a new agent = a new ~30-line adapter, not a rewrite.

## Quick start

```sh
./install.sh                      # scaffolds ~/.context-config-builder (neutral)
./adapters/kiro.sh apply          # project onto Kiro CLI
# or
./adapters/generic.sh build       # produce a single preamble.md for any LLM
```
