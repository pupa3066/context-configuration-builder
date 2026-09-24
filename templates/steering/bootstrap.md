# Session Bootstrap Protocol

> Auto-loaded every session (global steering). Keep lean.

## On session / task start
1. `portfolio.md`, `cross-links.md`, and `context-registry.md` are already in context (steering). Read them first.
2. The ACTIVE context = only the projects marked [x] in `context-registry.md`. Ignore non-enabled projects even if their skill files exist.
3. Identify which active project(s) the task touches.
4. Load that project's DEEP context on demand by invoking its skill: `/<project>-context`
   (skills load full content only when invoked  -  near-zero token cost until then).
5. For a repo you're working inside, its `.kiro/steering/*.md` auto-loads (workspace steering).

## Adding / removing a project from context
- Edit `context-registry.md` (flip [x]/[ ]). That single edit is the source of truth for what's active.
- Enablement is decided by the registry, NOT by whether a skill file exists on disk.

## While working (incremental update  -  cheapest path)
- New fact/decision -> append ONE entry to the project's skill and, if cross-project, ONE line in `cross-links.md`.
- Refresh ONLY the changed file in the knowledge base. Do not re-index the whole tree.

## Cost model (why it's structured this way)
- steering (`file://`) = always in context every turn -> keep tiny (rules + indexes only).
- skills (`skill://`) = metadata at startup, full body on demand -> holds the bulk (per-project detail).
- knowledge base = 0 cost until queried -> semantic recall across everything.
