---
name: repo_navigation
description: Code search policy. Load when locating code for an issue.
---

# Repo navigation policy

Follow the search order in the system prompt. Two retrievers are available, and both see the whole repository: the lexical retriever /tmp/bm25.py (BM25 over 8-line chunks of every .py file) and search_similar_code (dense search over the provided embeddings).

Read line ranges only, never whole files. Extract identifiers from the issue before searching.
