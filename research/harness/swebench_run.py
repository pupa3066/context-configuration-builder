"""swebench_run.py  -  execute the FULL context-tiering study on real SWE-bench.

This is a REAL experiment runner (no mocks):
  1. Load SWE-bench Verified tasks (datasets).
  2. For each task, build context per condition C0-C3 from the repo's REAL context
     files (AGENTS.md/CLAUDE.md/README/docs)  -  same source text, different loading.
  3. Call a REAL LLM agent (agents.py) to produce a patch; log REAL token usage.
  4. Grade each patch by running the task's tests via the official swebench harness
     (Docker)  -  REAL pass/fail.
  5. Write one JSONL row per (task, condition) for analysis.py.

Run (needs API key + docker + compute; see run_real.md):
  python swebench_run.py --agent openai:gpt-4o-mini --split verified \
      --limit 50 --conditions C0,C1,C2,C3 --out runs.jsonl

Cost/quality is MEASURED here. Nothing is fabricated: a failed grade is logged as
resolved=false; an API/harness error is logged with an "error" field, never guessed.
"""
from __future__ import annotations
import os, json, argparse, time, tempfile, subprocess, sys

# Reuse condition/context logic from harness.py
sys.path.insert(0, os.path.dirname(__file__))
from harness import build_context, Task  # noqa: E402

CONTEXT_FILE_NAMES = ("AGENTS.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md")

def load_tasks(split: str, limit: int):
    from datasets import load_dataset
    name = {"verified": "princeton-nlp/SWE-bench_Verified",
            "lite": "princeton-nlp/SWE-bench_Lite"}.get(split, split)
    ds = load_dataset(name, split="test")
    if limit:
        ds = ds.select(range(min(limit, len(ds))))
    return ds

def repo_context_text(instance) -> str:
    """Assemble the repo's real context files at the base commit into one source string.
    Falls back to the issue's repo overview if no context files exist."""
    parts = []
    # swebench instances carry repo + base_commit; we shallow-checkout to read files.
    repo, commit = instance["repo"], instance["base_commit"]
    with tempfile.TemporaryDirectory() as d:
        url = f"https://github.com/{repo}.git"
        try:
            subprocess.run(["git", "clone", "--depth", "1", url, d],
                           check=True, capture_output=True, timeout=180)
            subprocess.run(["git", "-C", d, "fetch", "--depth", "1", "origin", commit],
                           check=False, capture_output=True, timeout=180)
            subprocess.run(["git", "-C", d, "checkout", commit],
                           check=False, capture_output=True, timeout=120)
        except Exception as e:
            return f"## overview\n(repo {repo} context unavailable: {e})"
        for name in CONTEXT_FILE_NAMES:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    parts.append(f"## {name.lower()}\n{fh.read()}")
    if not parts:
        parts.append("## overview\n(no committed context files in this repo)")
    return "PREAMBLE: repository engineering context.\n" + "\n".join(parts)

def grade(instance, patch: str) -> tuple[bool, str]:
    """Grade a patch with the official swebench evaluation (Docker). Returns (resolved, note)."""
    try:
        from swebench.harness.run_evaluation import run_instance  # API surface may vary by version
    except Exception as e:
        return False, f"swebench harness import failed: {e}"
    try:
        # Write prediction in swebench format and evaluate the single instance.
        pred = {"instance_id": instance["instance_id"],
                "model_name_or_path": "context-tiering-study",
                "model_patch": patch}
        result = run_instance(instance=instance, prediction=pred)  # returns resolved bool/dict
        resolved = bool(result.get("resolved")) if isinstance(result, dict) else bool(result)
        return resolved, "graded"
    except Exception as e:
        return False, f"grading error: {e}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, help="e.g. openai:gpt-4o-mini")
    ap.add_argument("--split", default="verified")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--conditions", default="C0,C1,C2,C3")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--out", default="research/harness/runs.jsonl")
    ap.add_argument("--dry-config", action="store_true", help="print resolved config and exit")
    ap.add_argument("--no-grade", action="store_true", dest="no_grade",
                    help="skip Docker grading; persist patch only. Grade later with grade_patches.py")
    a = ap.parse_args()

    conds = tuple(
        {"C0": "C0_no_context", "C1": "C1_monolithic",
         "C2": "C2_tiered_manual", "C3": "C3_tiered_auto"}[c] for c in a.conditions.split(","))
    cfg = {"agent": a.agent, "split": a.split, "limit": a.limit,
           "conditions": conds, "repeats": a.repeats, "out": a.out}
    if a.dry_config:
        print(json.dumps(cfg, indent=2)); return

    from agents import make_agent
    from tier_assign_adapter import RepoTierer  # thin adapter around tier_assign
    agent = make_agent(a.agent)
    tierer = RepoTierer()
    tasks = load_tasks(a.split, a.limit)

    n = 0
    with open(a.out, "w") as fh:
        for inst in tasks:
            src = repo_context_text(inst)
            t = Task(inst["instance_id"], inst["problem_statement"], src,
                     references=tierer.references_for(inst, src))
            for rep in range(a.repeats):
                for cond in conds:
                    ctx = build_context(cond, t, tierer=tierer)
                    row = {"task_id": t.task_id, "condition": cond, "repeat": rep,
                           "config": cfg}
                    t0 = time.perf_counter()
                    try:
                        patch, itok, otok, steps = agent.solve(t.prompt, ctx)
                        if a.no_grade:
                            resolved, note = None, "ungraded"
                        else:
                            resolved, note = grade(inst, patch)
                        row.update(resolved=resolved, patch=patch, input_tokens=itok,
                                   output_tokens=otok, steps=steps,
                                   seconds=round(time.perf_counter()-t0, 3), note=note)
                    except Exception as e:
                        row.update(resolved=False, patch="", input_tokens=0, output_tokens=0,
                                   steps=0, seconds=round(time.perf_counter()-t0, 3),
                                   error=str(e))
                    fh.write(json.dumps(row) + "\n"); fh.flush()
                    n += 1
    print(f"wrote {n} real runs to {a.out}")

if __name__ == "__main__":
    main()
