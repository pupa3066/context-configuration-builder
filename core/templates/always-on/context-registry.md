# Context Loader Registry (agent-neutral)

> Controls which projects are ACTIVE. Marker: [x] active, [ ] inactive.
> Enablement is decided HERE, not by file presence. Adapters read this to know what to project.

## Active
| Enabled | Project | Origin | Context file | Repo path |
|---|---|---|---|---|
| [x] | example-project | you/example-project | projects/example-project.md | Projects/example-project |

## Inactive
| Enabled | Project | Reason |
|---|---|---|
| [ ] | some-fork | upstream fork  -  enable on demand |

## Rule
- Only [x] rows are active. Cross-project reasoning draws only from enabled projects.
- To add/remove: use scripts, then re-run your agent's adapter.
