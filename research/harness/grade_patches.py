"""grade_patches.py — grade patches persisted by swebench_run.py.

Decouples grading (needs Docker, CPU, disk) from generation (needs the GPU), so the two can run on
different hosts. Uses the official `python -m swebench.harness.run_evaluation` CLI with a
predictions file, the stable public entrypoint; `run_instance()` is internal and its signature has
changed across versions (the inline grade() in swebench_run.py targets an older one).

swebench evaluates one prediction per instance per run, so each (condition, repeat) group is
graded as its own run. Results are written to a copy of the runs file with `resolved` filled in.

Usage:
  python research/harness/grade_patches.py research/harness/runs_pilot_cuda.jsonl \
      [--workers 2] [--timeout 1800] [--out ...graded.jsonl] [--run-id tag]

Needs: Docker running, `swebench` installed (tested with 5.0.2), several GB disk per distinct repo.
Verified with swebench 5.0.2: report is written to <report_dir>/<model_name>.<run_id>.json and
contains resolved_ids / unresolved_ids / error_ids / completed_ids / empty_patch_ids.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile, time

DATASETS = {"verified": "SWE-bench/SWE-bench_Verified", "lite": "SWE-bench/SWE-bench_Lite"}


def load_rows(path):
    with open(path) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def looks_like_diff(p: str) -> bool:
    p = p.lstrip()
    return p.startswith("diff --git") or p.startswith("--- ") or "\ndiff --git" in p or "\n--- a/" in p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--split", default=None, help="verified|lite (default: from row config)")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--out", default=None)
    ap.add_argument("--run-id", default=None)
    a = ap.parse_args()

    rows = load_rows(a.runs)
    split = a.split or rows[0].get("config", {}).get("split", "verified")
    dataset = DATASETS.get(split, split)
    run_tag = a.run_id or f"ccb{int(time.time())}"
    out = a.out or a.runs.replace(".jsonl", ".graded.jsonl")

    # group rows by (condition, repeat); within a group instance_ids are unique
    groups: dict[tuple, list[int]] = {}
    for i, r in enumerate(rows):
        r.setdefault("resolved", None)
        patch = r.get("patch") or ""
        if not patch.strip():
            r["resolved"], r["note"] = False, "empty patch"; continue
        if not looks_like_diff(patch):
            r["resolved"], r["note"] = False, "no diff in output"; continue
        groups.setdefault((r["condition"], r.get("repeat", 0)), []).append(i)

    if not groups:
        print("nothing gradable"); sys.exit(1)

    with tempfile.TemporaryDirectory() as d:
        for (cond, rep), idxs in sorted(groups.items()):
            name = f"ccb__{cond}__r{rep}"
            run_id = f"{run_tag}_{cond}_r{rep}"
            pred_path = os.path.join(d, f"{name}.jsonl")
            with open(pred_path, "w") as fh:
                for i in idxs:
                    fh.write(json.dumps({"instance_id": rows[i]["task_id"],
                                         "model_name_or_path": name,
                                         "model_patch": rows[i]["patch"]}) + "\n")
            ids = [rows[i]["task_id"] for i in idxs]
            cmd = [sys.executable, "-m", "swebench.harness.run_evaluation",
                   "--dataset_name", dataset, "--split", "test",
                   "--predictions_path", pred_path, "--instance_ids", *ids,
                   "--max_workers", str(a.workers), "--timeout", str(a.timeout),
                   "--run_id", run_id, "--report_dir", d]
            print(f"\n=== grading {cond} r{rep}: {len(ids)} instances ===", flush=True)
            subprocess.run(cmd, check=False)

            rp = os.path.join(d, f"{name}.{run_id}.json")
            if not os.path.isfile(rp):
                print(f"WARN: no report at {rp}; marking group as error")
                for i in idxs:
                    rows[i]["resolved"], rows[i]["note"] = False, "grading error: no report"
                continue
            rep_json = json.load(open(rp))
            resolved = set(rep_json.get("resolved_ids", []))
            errored = set(rep_json.get("error_ids", []))
            completed = set(rep_json.get("completed_ids", []))
            for i in idxs:
                iid = rows[i]["task_id"]
                rows[i]["resolved"] = iid in resolved
                rows[i]["note"] = ("resolved" if iid in resolved else
                                   "grading error" if iid in errored else
                                   "unresolved" if iid in completed else "not run")

    with open(out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    by: dict[str, list[int]] = {}
    for r in rows:
        c = r["condition"]; by.setdefault(c, [0, 0]); by[c][1] += 1; by[c][0] += bool(r["resolved"])
    print(f"\nwrote {out}")
    for c, (k, n) in sorted(by.items()):
        print(f"  {c:20s} {k}/{n} resolved")


if __name__ == "__main__":
    main()
