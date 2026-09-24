# STATUS  -  built vs. pending (read this honestly)

## Built & tested (this apparatus)
- `RESEARCH_PLAN.md`  -  pre-registration-style design: 4 hypotheses, C0 - C3 conditions, SWE-bench, statistics, threats to validity.
- `harness/harness.py`  -  runnable harness, 4 conditions, JSONL logging + mock-data generator (`--gen N`). **Self-test passes.**
- `harness/analysis.py`  -  full statistics layer: per-condition rates/cost, McNemar, bootstrap CIs, non-inferiority test, Pareto frontier, structured verdict. **Runs end-to-end** on run logs.
- `tier_assign/tier_assign.py`  -  automatic tier assignment with a **cost-model-derived principled threshold**. **6/6 unit tests pass.**
- `RELATED_WORK.md`  -  positioning vs. verified ETH result + adjacent literature.

## What the current numbers ARE and ARE NOT
- The harness self-test and `analysis.py` on `--gen` mock data prove the **measurement + statistics pipeline is correct**.
- The MockAgent is RIGGED (resolves by string-match; never fails). Its "BETTER" verdict and ~0.83 token reduction are ARTIFACTS OF THE MOCK, not evidence. McNemar b=c=0 (no disagreements) is the tell. **NO scientific claim follows from mock runs.**
- Whether the method is actually better is **UNANSWERED** pending a real-agent run.

## Pending (required for a publishable result  -  real work, real cost)
The pipeline to produce real data is now BUILT (agents.py, swebench_run.py, tier_assign_adapter.py, run_real.md). Remaining is to EXECUTE it in an environment with:
1. `pip install -r research/harness/requirements.txt` (datasets, swebench, openai/anthropic).
2. An LLM API key (OPENAI_API_KEY / ANTHROPIC_API_KEY) + a token/$ budget.
3. Docker running (SWE-bench grades patches by executing tests in containers).
Then: `run_real.md` steps 2 - 4 produce `runs.jsonl` -> `analysis.py` computes the verdict.

Structurally verified offline (this session): all modules compile; `--dry-config` runs
with no key/network; agent construction fails cleanly without deps (no fabrication).

## Estimated cost/effort to real result
SWE-bench Verified x 4 conditions x repeats = real API spend + Docker compute hours.
Start with `--limit 10` to estimate per-task cost, then scale.

## Honest bottom line
This is a rigorous, runnable research *foundation*  -  the kind of apparatus a reviewer expects  -  but the empirical result that would make it publishable is NOT yet produced. Producing it is the next real step.
