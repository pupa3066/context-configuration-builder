# Debug Rules (always-on stub)

> Per-project debug detail lives in each project's skill file. These are cross-project invariants.

- Exact versions in bug reports — never "current" or "latest".
- Minimal reproducer anyone can run without your private files.
- Environment specs committed before filing any issue.
- Kaggle runs: K1 fresh session clone first; K2 absolute paths; K3 verify model name + download size before trusting numbers; K4 wrong-config run is invalid, never record its numbers.
- Multi-machine git: pull before push (G1). Rejected push = other machine already pushed; pull to merge, never force-push.
