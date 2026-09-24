# Running the Full SWE-bench Study (turnkey)

This executes the real experiment (RESEARCH_PLAN.md) end-to-end and produces real data.

## Requirements
- Python 3.10+; `pip install -r research/harness/requirements.txt`
- **Docker** running (SWE-bench grades patches by executing tests in containers)
- A model backend  -  either:
  - API: `export OPENAI_API_KEY=...` or `export ANTHROPIC_API_KEY=...`
  - **Local (zero API cost, Apple Silicon):** `pip install mlx-lm` and a **code-capable** MLX model, e.g. `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`. Agent spec: `--agent local:<model-path>`.
- Disk + time: SWE-bench images are large; grading is minutes/task. Budget accordingly.

> MODALITY WARNING: SWE-bench needs a **code-generation** model. Vision LoRAs
> (SmolVLM/SDXL) trained for image tasks are NOT valid backends  -  they score ~0 across
> all conditions and measure nothing about tiering. Use a code/instruct LLM.

## 1. Sanity-check config (no API, no cost)
```sh
python research/harness/swebench_run.py --agent local:mlx-community/Qwen2.5-Coder-7B-Instruct-4bit \
  --split verified --limit 5 --dry-config
```
Prints the resolved run configuration and exits.

## 2. Pilot run (small, real, cheap-ish)
```sh
python research/harness/swebench_run.py \
  --agent openai:gpt-4o-mini --split verified --limit 10 \
  --conditions C0,C1,C2,C3 --repeats 1 \
  --out research/harness/runs_pilot.jsonl
```
Use the pilot to (a) confirm grading works in your Docker env, (b) get variance
estimates to finalize N via the power analysis.

## 3. Full run
```sh
python research/harness/swebench_run.py \
  --agent openai:gpt-4o-mini --split verified --limit 0 \
  --conditions C0,C1,C2,C3 --repeats 3 \
  --out research/harness/runs.jsonl
```
`--repeats 3` with temperature=0 quantifies residual nondeterminism.

## 4. Analyze (computes the answer)
```sh
python research/harness/analysis.py research/harness/runs.jsonl --delta 0.02 > research/harness/analysis.json
cat research/harness/analysis.json
```
Reports per-condition resolved rate + tokens, McNemar (C2/C3 vs C1), bootstrap CIs,
non-inferiority verdict, Pareto frontier. **This is where "is my method better?" is answered.**

## Interpreting the verdict
- "BETTER" requires **non-inferior quality** (lower CI bound of C2-C1 > -delta) **AND** fewer tokens.
- If quality drops, you get a characterized cost/quality tradeoff  -  still a publishable result.
- Report effect sizes + CIs, not just the verdict.

## Cost control
- Start with `--limit 10` and one condition to estimate per-task \$ before the full run.
- `gpt-4o-mini` / cheaper models first; escalate model only if needed.
- Every row logs real token usage; sum them for actual spend.

## Provenance
Each JSONL row embeds the full run config (agent, split, conditions). Pin model
version strings in publications. Errors are logged per-row (never silently dropped).
