"""grade_patches.py - grade persisted patches from a --no-grade run.

Reads runs.jsonl rows where resolved=None (ungraded), grades each patch
via the official swebench harness (requires Docker), writes resolved=True/False back.

Usage:
  python grade_patches.py --runs /kaggle/working/runs_pilot.jsonl \
                          --out /kaggle/working/runs_pilot_graded.jsonl

Requires: pip install swebench datasets docker
"""
from __future__ import annotations
import json, argparse, subprocess, sys, os

def grade_patch(instance_id: str, patch: str) -> tuple[bool, str]:
    try:
        from swebench.harness.run_evaluation import run_instance
    except Exception as e:
        return False, f"swebench import failed: {e}"
    try:
        from datasets import load_dataset
        ds = load_dataset("SWE-bench/SWE-bench_Verified", split="test")
        inst = next((r for r in ds if r["instance_id"] == instance_id), None)
        if inst is None:
            return False, f"instance_id {instance_id} not found in dataset"
        pred = {"instance_id": instance_id,
                "model_name_or_path": "ccb-context-tiering",
                "model_patch": patch}
        result = run_instance(instance=inst, prediction=pred)
        resolved = bool(result.get("resolved")) if isinstance(result, dict) else bool(result)
        return resolved, "graded"
    except Exception as e:
        return False, f"grading error: {e}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="input runs.jsonl from --no-grade run")
    ap.add_argument("--out", required=True, help="output graded runs.jsonl")
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.runs) if l.strip()]
    ungraded = [r for r in rows if r.get("resolved") is None]
    already = len(rows) - len(ungraded)
    print(f"{len(rows)} rows: {len(ungraded)} ungraded, {already} already graded")

    with open(a.out, "w") as fh:
        for i, row in enumerate(rows):
            if row.get("resolved") is None and row.get("patch"):
                resolved, note = grade_patch(row["task_id"], row["patch"])
                row["resolved"] = resolved
                row["note"] = note
                print(f"[{i+1}/{len(ungraded)}] {row['task_id']} {row['condition']}: "
                      f"resolved={resolved}")
            fh.write(json.dumps(row) + "\n")
    print(f"wrote {len(rows)} rows to {a.out}")

if __name__ == "__main__":
    main()
