# Competitive Positioning

> How to launch publicly in a crowded "AI agent memory" market. Based on landscape research (2026).

## The market is real and crowded  -  acknowledge it

The "LLMs are stateless, they forget between sessions" framing is now mainstream. Existing players:

| Category | Examples | What they do | Their limitation |
|---|---|---|---|
| Managed memory service | **Mem0** (leader) | MCP-server semantic memory; cross-tool, cross-machine sync | Hosted service / dependency; a moving part to run; memory is opaque (not human-editable files you own) |
| Native memory files | CLAUDE.md, AGENTS.md, `.cursor/rules` | Per-repo instructions, built in, free | Per-repo (no cross-project graph); no cost model; agent-specific |
| OSS rules frameworks | claude-anchor, agentmemory | Rules + behavioral consistency | Mostly single-agent (Claude Code); no explicit token-cost tiering |

Do NOT pretend you're first. Launching as "the first AI memory tool" invites instant "isn't this just Mem0/CLAUDE.md?" pushback. Instead, position in the *gap they leave*.

## The three gaps we own

1. **Cross-project, not just cross-session.** Mem0's own blog admits auto-memory "doesn't carry context between separate repos even if you're the one working across all of them." Our cross-links graph is built for exactly that: a result in project A is explicitly linked to the paper in project B.
2. **An explicit token-cost model.** Nobody else frames memory as a *cost* problem with a measured answer (40.9%->89% per-turn context reduction). "Memory that stays cheap" is our lane.
3. **Own your files, no service to run.** Mem0 is a hosted dependency; we're plain markdown you own and git-version, projected onto any agent by a ~30-line adapter. No server, no vendor lock, no data leaving your machine.

## One-line positioning

**"Cross-project memory for AI agents  -  plain files you own, that stay cheap as you scale."**

Not competing with Mem0 on managed-sync convenience. Competing on ownership, cross-project structure, and cost transparency.

## Why "similar products exist" is actually good for launch

A crowded market = validated demand. Mem0 raising the "agents forget" awareness does our education for free. We ride the wave with a sharper wedge, not a cold-start category.

## Honest risks (say these internally, not in the launch post)

- Native memory files are free and improving; we must clearly beat "just use CLAUDE.md"  -  our answer is the cross-project graph + cost model + multi-agent portability.
- Mem0 could add a files-based / cross-repo mode. Our moat is being the *simple, owned, portable* option and moving first in that niche (see gtm-strategy.md).
- The measured savings are size-based, N=4 directly measured; be precise about that when challenged (see docs/paper).

## Making it public: sequence

1. Keep it private until the launch post + demo GIF are ready (provenance timestamp already established via git + PR history).
2. Launch with the honest wedge above  -  lead with cross-project + cost, name the alternatives, show the gap.
3. Post to Show HN / r/LocalLLaMA / dev.to; expect "how is this different from Mem0/CLAUDE.md?" as the top comment  -  answer it in the post itself, preemptively.
