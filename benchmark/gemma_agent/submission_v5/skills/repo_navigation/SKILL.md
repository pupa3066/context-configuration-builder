---
name: repo_navigation
description: Identifier-first code search policy. Load when locating code for an issue.
---

# Repo navigation policy

Always try grep first. Identifier-dense queries (named function, class, error string) find the target faster than any other tool.

| Query type | First action | Follow-up |
|---|---|---|
| Named symbol | grep -rn "symbol" /workspace | read_file on the matched lines |
| Caller lookup | grep -rn "symbol" /workspace | find call sites |
| Behavior only | grep -rn "keyword" /workspace | read surrounding context |
| Known location | read_file start_line end_line | none |

Rule: read line ranges only, never whole files. Extract identifiers from the issue before searching.
