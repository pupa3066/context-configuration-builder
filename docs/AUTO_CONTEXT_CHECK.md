# Automatic Context Consistency Check

> Design fix so research/context drift is caught automatically  -  never re-checked by hand,
> runs in parallel to any project on every CLI-agent session.

## The problem it solves
Research facts live in multiple files (study `RESULTS_multimodel.md`, kit
`precision_context/FINDINGS.md`, steering `cross-links.md`, the context registry). When one is
updated, the others can silently go stale. This actually happened: an overturned single-model
"INT4 erases memorization" claim lingered in `FINDINGS.md` after the 6-model run corrected it.

## The fix (two parts)
1. **`~/.kiro/hooks/context-check.sh`**  -  a fast, dependency-free verifier that checks:
   - **Stale-claim detection:** the specific overturned memorization claim isn't re-cited anywhere.
   - **Registry <-> reality:** every `[x]` active project path in `context-registry.md` exists on disk.
   - **Cross-project link:** `precision_advisor.py` still runs on the study's real analysis JSON.
   - **Uncommitted research data** in the public study repo.
   It prints a one-line status to stdout (added to agent context) and never blocks the session.

2. **`~/.kiro/agents/default.json` `agentSpawn` hook**  -  runs the check automatically every time a
   a CLI-agent session starts, in ANY working directory. Its stdout becomes part of the agent's context,
   so the agent (and you) see "[context-check] OK" or the specific drift, with zero manual effort.

## Why agentSpawn (the documented mechanism)
CLI-agent hooks: `agentSpawn` fires on session start, is never cached, and its stdout (exit 0) is added
to context. This is the supported way to run something in parallel to all projects  -  see the CLI
Hooks System docs.

## Verifying / using it
- See configured hooks in a session: `/hooks`
- Run the check manually anytime: `~/.kiro/hooks/context-check.sh`
- It already caught real drift on first run (a wrong PhotoBack registry path), which was then fixed.

## Extending it
Add new invariants as `grep`/exit checks in `context-check.sh`. Keep it fast (<a few seconds) and
non-blocking (always exit 0; warn in stdout). The rule: any fact that lives in >1 place gets a
drift check here so it can never silently go stale again.
