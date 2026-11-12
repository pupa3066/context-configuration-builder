---
name: repo_navigation
description: How to pick a code search tool by query type (identifier-first). Load when locating code for an issue.
---

# Repo navigation: pick the search tool by query type

| Query type | Signal in the issue | First tool | Then |
|---|---|---|---|
| Exact symbol | a function, class, method or error string is named | run_command grep -rn "<name>" | get_code_neighbors on the match |
| Callers / dependencies | need who calls or imports a named symbol | get_code_neighbors | get_code_subgraph on the set |
| Behavior only | prose description, no exact name | search_similar_code | grep the identifiers it reveals |
| Known location | file and line already known | read_file with start_line/end_line | none |

Why identifier-first: on identifier-heavy code questions, exact term matching found the chunk containing the named symbol more often than embedding similarity did, and far more often on the definition line. Embeddings help when the issue describes behavior without names.

Rules: extract identifiers before searching; read line ranges, not whole files; never label an embedding result as an exact match.
