# Agent Parity: Two Coding Agents Load the Same Context

> Status: verified configuration behavior, one headless probe per condition (2026-09-25).
> These are deterministic wiring effects, not a statistical result and not a task-success claim.

Environment: macOS (Darwin 25.6.0); agent A = Kiro CLI 2.24.0 (kiro-cli); agent B = Claude Code 2.1.282; agent A's config directory = ~/.kiro; tokenizer GPT-2 BPE (transformers 5.17.0, the same tokenizer as benchmark/benchmark.py).

## Question
CCB is agent-neutral: one set of steering files, session-start hooks, and project skills is meant to put
the same context in front of any agent. Do two coding agents, started from the same directory on the
same machine, actually receive the same context?

## Method
`scripts/agent-parity-probe.sh` sends one prompt to each agent in headless mode. The prompt asks each
agent to quote its session-start output verbatim from loaded context, with tools disabled, so each
answer shows what reached the model rather than what exists on disk. The probe was run from the home
directory (no repository) and from inside an active repository.

## Findings before the fix
1. A plain agent A session ran the agent's built-in default profile, not the CCB profile. Always-on
   steering still loaded, so the session looked configured, but none of the session-start hooks ran:
   no integrity line, no project context.
2. With the CCB profile selected, agent A's runtime engines v2 (the default in this version) and v3
   still skipped the session-start hooks. Only engine v1 ran them.
3. The per-project steering dump from the home directory was 26,690 bytes (8,723 tokens). Agent B kept
   a short preview and saved the rest to a file; agent A received the first project twice (the
   self-heal guard and the loader both printed it) and then truncated. In both agents, two of the three
   projects with steering never reached context.
4. In every case above, the integrity check still printed PASS. It verified that the loader was
   installed, not that its output was delivered.
5. Inside a repository, agent A loads that repository's steering directory natively (workspace
   steering); agent B did not load it at all.
6. Project skills were available in agent A only, and would have appeared under different names in
   agent B (folder name instead of the skill's declared name).

## Fix (this branch)
- The installer pins agent A to the CCB profile and to engine v1, and replaces the direct loader hook
  with `ccb-project-context.sh`.
- `hooks/ccb-project-context.sh` wraps the loader, saves each project's steering to its own file, and
  prints only an index. For agent B it keeps a local project instruction file in each active
  repository that imports that repository's steering files (live imports, excluded through
  `.git/info/exclude`, never committed), which matches agent A's workspace steering.
- `hooks/steering-loader-guard.sh` keeps its config self-heal but no longer prints the dump.
- The agent B adapter's `wire` command points agent B at the same files agent A reads (steering
  imports, the same session-start hooks, skills linked under their declared names). Nothing is copied,
  so an edit applies to both agents at once.
- `hooks/ccb-parity-check.sh` runs in both agents every session and prints the same report: steering
  fingerprint, agent A profile and engine, identical hook sets, steering imports, skill names,
  repository steering. A deliberate break (one repository's instruction file removed) produced FAIL.

## Findings after the fix
From both launch directories, both agents quoted the same integrity line, the same parity line and
steering fingerprint, the same project index, and the same skill names, with zero duplicated project
blocks. Inside a repository both agents quoted that repository's steering. The remaining answer
differences were model accuracy on the same loaded text (one agent misidentified which of the real
headings came last), not missing context.

## Token cost of session-start context (measured, GPT-2 BPE)
| Session-start component | Bytes | Tokens |
|---|---|---|
| Always-on steering (4 files) | 13,466 | 3,902 |
| Project context, full dump (before) | 26,690 | 8,723 |
| Project context, index (after) | 382 | 140 |
| Other session-start hook output | 2,485 | 748 |

Raw values: `research/agent_parity/session_start_tokens.json`.

Replacing the dump with an index cut the project-context part of every session start from 8,723 to 140
tokens (a 98.4 percent reduction for that component, measured on one deployment with three projects
that have steering). The detail is not lost: it is read on demand from the saved file, which is the
same tiering idea the rest of CCB measures. Unlike the earlier dump, the index is not truncated, so
every project is reachable.

## Reproduce
```
sh ccb-bootstrap.sh                       # agent A side (hooks, settings, profile wiring)
sh adapters/claude-code.sh wire           # agent B side (live imports, hooks, skills)
sh scripts/agent-parity-probe.sh          # same probe in both agents, from $HOME
sh scripts/agent-parity-probe.sh <repo>   # and from inside a repository
```
