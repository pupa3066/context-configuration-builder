"""sweep.py  -  factor-grid runner producing metrics-instrumented rows.

Generates one JSONL row per (task x condition x model x project_count x repeat),
each carrying the extended metrics (memory/latency/behavior/factors) from metrics.py.

Two modes:
  --mock  : uses harness.MockAgent across a simulated model/OS/scaling grid. Rows are
            tagged non-empirical; this validates the measurement + analysis pipeline
            WITHOUT API cost or fabricating science (rule 6a).
  (real)  : for a real experiment use swebench_run.py with a real --agent; that path
            grades patches in Docker. This sweep file is the offline pipeline harness.

Scaling is modeled by growing the context source with project_count sections, mirroring
the real deployment (always-on tier fixed; on-demand tier selected per task).
"""
from __future__ import annotations
import json, argparse, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from harness import Task, build_context, MockAgent           # noqa: E402
from metrics import measure_solve, env_factors               # noqa: E402

CONDITIONS = ("C0_no_context", "C1_monolithic", "C2_tiered_manual", "C3_tiered_auto")


def _corpus(project_count: int) -> str:
    secs = [f"p{i}" for i in range(project_count)]
    body = "".join(
        f"## {s}\n{s} details TOKEN_{s.upper()} " + ("filler " * 30) + "\n" for s in secs)
    return "PREAMBLE rules and index\n" + body, secs


def run(models, project_counts, repeats, out):
    n = 0
    with open(out, "w") as fh:
        for pc in project_counts:
            src, secs = _corpus(pc)
            # one task per project_count, needing one section
            need = secs[pc // 2]
            task = Task(f"task_pc{pc}", f"fix {need} NEEDS: TOKEN_{need.upper()}",
                        src, references=[need], verify=lambda s: s == "PASS")
            for model in models:
                agent = MockAgent()
                factors = env_factors(model)  # real OS captured; model is the label
                for cond in CONDITIONS:
                    ctx = build_context(cond, task)
                    for rep in range(repeats):
                        sol, itok, otok, steps, m = measure_solve(
                            agent, task.prompt, ctx, model)
                        row = {
                            "task_id": task.task_id, "condition": cond,
                            "project_count": pc, "repeat": rep,
                            "resolved": (task.verify(sol) if task.verify else False),
                            "input_tokens": itok, "output_tokens": otok, "steps": steps,
                            **factors, **m.as_dict(),
                        }
                        fh.write(json.dumps(row) + "\n")
                        n += 1
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="run the mock factor-grid (pipeline test)")
    ap.add_argument("--models", default="mock:A,mock:B")
    ap.add_argument("--project-counts", default="4,10,25")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", default="research/harness/sweep_runs.jsonl")
    a = ap.parse_args()
    if not a.mock:
        print("Refusing to run without --mock. For REAL metrics use swebench_run.py "
              "with a real --agent (needs API key + Docker). This file is the offline "
              "pipeline harness only.", file=sys.stderr)
        sys.exit(2)
    models = a.models.split(",")
    pcs = [int(x) for x in a.project_counts.split(",")]
    n = run(models, pcs, a.repeats, a.out)
    print(f"sweep(mock): wrote {n} rows to {a.out} "
          f"({len(models)} models x {len(pcs)} project-counts x 4 conditions x {a.repeats} repeats). "
          f"NON-EMPIRICAL  -  pipeline test only.")
