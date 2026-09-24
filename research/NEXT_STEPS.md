# NEXT STEPS  -  Consistent Context Kit research run

> Saved 2026-09-15. The apparatus + stats are built and verified offline (STATUS.md).
> The missing piece is REAL data. This file is the turnkey plan.

## Prereqs (must be satisfied before any real run  -  none verified yet)
1. `pip install -r research/harness/requirements.txt`
2. A code-capable backend. Cheapest = local MLX (zero API cost, Apple Silicon):
   `pip install mlx-lm` + model `mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`.
   Agent spec: `--agent local:mlx-community/Qwen2.5-Coder-7B-Instruct-4bit`.
   (Alternative: OPENAI_API_KEY / ANTHROPIC_API_KEY + budget.)
3. **Docker running** (SWE-bench grades patches by executing tests in containers).
   MODALITY WARNING: SWE-bench needs a CODE model. Vision LoRAs (SmolVLM/SDXL) score ~0  -  invalid.

## Run steps (from research/harness/run_real.md)
0. FREE sanity (no API/network/cost):
   `python research/harness/swebench_run.py --agent local:mlx-community/Qwen2.5-Coder-7B-Instruct-4bit --split verified --limit 5 --dry-config`
1. Pilot (real, small):
   `python research/harness/swebench_run.py --agent local:<model> --split verified --limit 10 --conditions C0,C1,C2,C3 --repeats 1 --out research/harness/runs_pilot.jsonl`
   -> confirm Docker grading works, get variance for power analysis, estimate per-task cost.
2. Full run:
   `... --limit 0 --repeats 3 --out research/harness/runs.jsonl`
3. Analyze (the verdict):
   `python research/harness/analysis.py research/harness/runs.jsonl --delta 0.02 > research/harness/analysis.json`

## Known open fidelity gaps (ETH_FIDELITY_AUDIT.md)  -  for a faithful comparison
- [DONE] CMH + stratified permutation tests implemented in analysis.py.
- [OPEN] Add ETH's exact conditions None/LLM/Dev alongside C0 - C3.
- [OPEN, biggest] Replace single-shot Agent.solve with a real MULTI-STEP agent (their step/cost effects vanish single-shot).
- [OPEN] Run on SWE-bench Lite (300) + ideally CTXbench (138).

## Why the current numbers are NOT a result
MockAgent is rigged (string-match, never fails); McNemar b=c=0 is the tell. No scientific claim
follows from mock runs. Real verdict only after steps 1 - 3 on a real code LLM.

## Overnight-run status (2026-09-15)
NOT started unattended. Prereqs (Docker/deps/backend) were NOT verified  -  env check was declined.
Do NOT auto-launch a run that spends API money or pulls large Docker images without confirming
the environment first. Resume by running step 0 (free) to confirm the pipeline resolves.
