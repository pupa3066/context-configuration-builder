---
name: bm25-localize
description: Ranks 8-line chunks of every non-test Python file in the repository for the current issue with BM25, offline. Use it to find where a fix belongs.
---

# bm25-localize

Call `run_skill_script` with:

- `skill_name`: `bm25-localize`
- `file_path`: `scripts/localize.py`
- `args`: `{"issue": "<key sentences, identifiers, file names and error messages from the problem statement>", "k": 10}`

It prints one line per candidate, most likely first: `rank  score  path:start-end  first line`.
Read the top candidates with `read_file` using the printed line range.
