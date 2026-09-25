# Working Rules

> Auto-loaded every session (global steering). Keep lean  -  costs tokens every turn.
> Customize these for how you work. Examples below.

## Core
1. Use measured facts and real data  -  label unverified claims as [CLAIM], verified as [MEASURED].
2. Keep long command output in files, not streamed into context.
3. Be efficient  -  minimize tokens and steps.

## Repository Visibility (customize)
4. Set your default visibility policy here (e.g., "private by default; public only on explicit instruction").
5. Never commit secrets or trained weights. Gitignore first; verify before staging.

## Context Bootstrap (see bootstrap.md)
6. At task start read portfolio.md + cross-links.md + context-registry.md. Load a project's skill on demand.
7. Update context incrementally; refresh only changed files in the KB.
8. Agent parity: every agent you use (e.g. Model and Claude Code) must load the same context. ccb-parity-check.sh reports PASS/FAIL at each session start; on FAIL, fix wiring before trusting the session. Change one agent's wiring and the other's in the same step.
