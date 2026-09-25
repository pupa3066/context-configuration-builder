# Research Rules (always-on stub)

> Firing stubs only. Full detail in on-demand appendix: research-governance-appendix.md.

- EMPIRICAL THRESHOLD: the moment a result becomes empirical (real data + adequate N + reproducible), say so explicitly. Until then label PRELIMINARY and name what experiment would cross the line.
- PRE-POST GATE: before any public/permanent post (DOI, preprint, public repo, outreach) run Sanity / Integrity / Credibility / Sensitive-info scan. Resolve all flags before committing. A non-zero result blocks the post.
- PROTECTION TRACK: before any public disclosure check the project's track. Patent-track or UNSET = stop and flag. Do not publish until cleared.
- METRIC HONESTY: grounding-retention proxy is NOT task success. Token count is NOT dollar cost. Label the proxy you are reporting and name the gap to the actual metric of interest.
- NO FABRICATION: mock/estimated/underpowered numbers are never presented as empirical. If a run uses a mock agent, its numbers are apparatus verification only.
- PRODUCT-NEUTRAL RESEARCH TEXT: research artifacts name the tools used during research by role, not product ("agent", "coding agent", "agent A / agent B", "agent config directory", "session-start hook"). Product names and exact versions appear once, in an Environment line. Check with scripts/research-neutrality-check.sh; a non-zero result blocks the commit.
- ADVISOR RECOMMENDATIONS: when prioritized recommendations are given, record each with hooks/agent-notes.sh rec (negatives ledger + the project's .agent/recommendations.md). Append-only; resolve only on the owner's instruction.
- PROJECT TASKS, NOT ASSISTANT MEMORY: pending items go to <repo>/.agent/tasks.md via hooks/agent-notes.sh task (private repo: committed; public repo: git-excluded, local). Read them when opening the project.
