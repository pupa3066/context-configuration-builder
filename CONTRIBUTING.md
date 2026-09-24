# Contributing

Thanks for your interest in context-config-builder.

## License note
This project is under Business Source License 1.1. By contributing, you agree your
contributions are licensed under the same terms. Commercial redistribution/hosting
requires a license from the maintainer until the Change Date (see LICENSE).

## Ground rules
- Keep steering templates LEAN  -  they load into context every turn. Detail belongs in skills.
- No personal data in templates or examples. Keep them generic.
- POSIX `sh` for scripts (no bashisms). Test with `sh -n` and shellcheck if available.
- Label facts `[MEASURED]` vs `[CLAIM]` in any docs.

## Dev workflow
```sh
# lint scripts
for f in install.sh scripts/*.sh demo/*.sh; do sh -n "$f"; done
# clean-room test
sh demo/demo.sh
```

## Reporting issues
Include: OS + shell, your agent and its version, exact command, and expected vs actual behavior.

## Contributing an empirical run (better hardware wanted)
The token-cost and fidelity results are measured; the **task-success** result (does tiered context
match monolithic on SWE-bench) needs **Docker + a code model** and is best run on a GPU/Docker box or
with an API budget  -  not an 8GB laptop. If you have that hardware, you can run it and contribute the
data back:

```sh
pip install -r research/harness/requirements.txt   # swebench, datasets, an agent SDK
# API backend:  export OPENAI_API_KEY=...    OR   local model:  --agent local:<mlx-coder-model>
python research/harness/contribute_run.py \
  --agent openai:gpt-4o-mini --limit 10 --label <your-hw, e.g. rtx4090> \
  --contributor-name "Your Name" --orcid 0000-0000-0000-0000
```
This auto-captures your hardware/software environment, runs the pilot via the unmodified harness, and
writes a bundle `research/harness/contrib_<label>/` (runs.jsonl + provenance.json). Open a PR with that
bundle. See `research/harness/run_real.md` for pilot->full details and cost control.

### Attribution & provenance (maintainer pre-merge gate)
Contributor data is credited and merged only after ALL of the following (mechanical gate):
1. Contributor posted **name AND ORCID** (or explicit "no ORCID")  -  `contribute_run.py` prints this block.
2. Contributor posted **provenance confirmation**  -  the bundle's `provenance.json` records the exact
   run config + environment; confirm results came from `swebench_run.py` unmodified.
3. **CITATION.cff + codemeta.json updated** with the contributor's credit BEFORE merge.
4. Merge happens only after 1 - 3 are on record (merge timestamp AFTER confirmation).
This mirrors the cross-hardware replication contributed to the companion quant-memorization study.
