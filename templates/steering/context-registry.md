# Context Loader Registry

> Controls which projects are in the ACTIVE agent context.
> Marker: [x] = active, [ ] = inactive. Enablement is decided HERE, not by file presence.

## Active context (only these feed the agent's reasoning)
| Enabled | Project | Origin | Skill | Repo path |
|---|---|---|---|---|
| [ ] | example-project | you/example-project | /example-project-context | Projects/example-project |
<!-- Activate a row (flip [ ] -> [x]) only after the repo path exists on disk.
     Add rows with scripts/add-project.sh. -->

## Inactive (present on disk, NOT in context unless enabled)
| Enabled | Project | Reason inactive |
|---|---|---|
| [ ] | some-fork | upstream fork — enable on demand |

## Loader rule (enforced by bootstrap.md)
- ONLY rows marked [x] are treated as active context.
- Cross-project reasoning draws ONLY from enabled projects.
- A skill may exist on disk without being active — the registry decides.

## After editing this file
1. Add: `scripts/add-project.sh <name>`. Remove: `scripts/remove-project.sh <name>` + flip the row.
2. Refresh the knowledge base on `~/.kiro/steering` and `~/.kiro/skills`.
3. Set your own visibility/privacy policy in 00-rules.md.
