# STATUS — built vs. pending (read this honestly)

## Built & tested (this apparatus)
- `RESEARCH_PLAN.md` — pre-registration-style design: 4 hypotheses, C0–C3 conditions, SWE-bench, statistics, threats to validity.
- `harness/harness.py` — runnable harness, 4 conditions, JSONL logging + mock-data generator (`--gen N`). **Self-test passes.**
- `harness/analysis.py` — full statistics layer: per-condition rates/cost, McNemar, bootstrap CIs, non-inferiority test, Pareto frontier, structured verdict. **Runs end-to-end** on run logs.
- `tier_assign/tier_assign.py` — automatic tier assignment with a **cost-model-derived principled threshold**. **6/6 unit tests pass.**
- `RELATED_WORK.md` — positioning vs. verified ETH result + adjacent literature.

## What the current numbers ARE and ARE NOT
- The harness self-test and `analysis.py` on `--gen` mock data prove the **measurement + statistics pipeline is correct**.
- The MockAgent is RIGGED (resolves by string-match; never fails). Its "BETTER" verdict and ~0.83 token reduction are ARTIFACTS OF THE MOCK, not evidence. McNemar b=c=0 (no disagreements) is the tell. **NO scientific claim follows from mock runs.**
- Whether the method is actually better is **UNANSWERED** pending a real-agent run.

## Pending (required for a publishable result — real work, real cost)
1. Plug a real agent (via the `Agent` protocol) — e.g. an SWE-bench-capable scaffold + a real LLM.
2. Obtain SWE-bench Verified tasks + the ETH developer-committed-context repo set.
3. Run C0–C3 with fixed seeds/temperature=0, k repeats; log to JSONL.
4. `analysis.py` (to write): power analysis, McNemar, bootstrap CIs, non-inferiority test, Pareto frontier.
5. Learned tier assignment (upgrade the frequency-threshold policy to a learned classifier) for H4.

## Estimated cost/effort to real result
SWE-bench runs across 4 conditions × k repeats = significant API spend + compute hours. This is a multi-week effort, not a session. Budget and pin model versions before running.

## Honest bottom line
This is a rigorous, runnable research *foundation* — the kind of apparatus a reviewer expects — but the empirical result that would make it publishable is NOT yet produced. Producing it is the next real step.
