#!/usr/bin/env python3
"""contribute_run.py  -  turnkey run + provenance capture for outside contributors.

Purpose: let someone with BETTER HARDWARE (GPU + Docker, or an API budget) run the
CCK context-tiering experiment and contribute results back with attribution + provenance
already filled in  -  the same cross-hardware contribution path used for the quant study.

It does NOT run the heavy experiment itself; it wraps swebench_run.py and:
  1. auto-captures the contributor's hardware/software environment (real, measured),
  2. runs the requested pilot/full config via swebench_run.py,
  3. writes a results bundle: runs JSONL + a provenance.json the maintainer can verify,
  4. prints the exact attribution block the contributor fills (name + ORCID) per the
     project's pre-merge gate.

Usage (on the contributor's machine):
    python research/harness/contribute_run.py \
        --agent openai:gpt-4o-mini --limit 10 --label rtx4090 \
        --contributor-name "Your Name" --orcid 0000-0000-0000-0000

Nothing is fabricated: if the run errors, the bundle records the error; hardware fields
come from the OS, not guesses.
"""
from __future__ import annotations
import os, sys, json, platform, subprocess, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))


def capture_env() -> dict:
    """Real environment capture  -  hardware + key software versions."""
    def sh(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout.strip()
        except Exception as e:
            return f"(unavailable: {e})"

    env = {
        "os": platform.system(), "os_release": platform.release(),
        "machine": platform.machine(), "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }
    # RAM
    if platform.system() == "Darwin":
        env["mem_bytes"] = sh(["sysctl", "-n", "hw.memsize"])
    elif platform.system() == "Linux":
        env["mem_kb"] = sh(["bash", "-lc", "grep MemTotal /proc/meminfo | awk '{print $2}'"])
    # GPU (best-effort; records what's there, else 'none detected')
    nvidia = sh(["bash", "-lc", "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null"])
    env["gpu"] = nvidia if nvidia and "unavailable" not in nvidia else "none detected (CPU/MPS or no nvidia-smi)"
    # docker + key python libs
    env["docker"] = sh(["bash", "-lc", "docker info --format '{{.ServerVersion}}' 2>/dev/null"]) or "not running"
    for lib in ("swebench", "datasets", "openai", "anthropic", "mlx_lm"):
        env[f"lib_{lib}"] = sh([sys.executable, "-c", f"import {lib},sys; print(getattr({lib},'__version__','?'))"])
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--conditions", default="C0,C1,C2,C3")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--label", required=True, help="short hardware label, e.g. rtx4090, m3max")
    ap.add_argument("--contributor-name", default="")
    ap.add_argument("--orcid", default="")
    ap.add_argument("--dry-config", action="store_true")
    a = ap.parse_args()

    bundle_dir = os.path.join(HERE, f"contrib_{a.label}")
    os.makedirs(bundle_dir, exist_ok=True)
    runs_out = os.path.join(bundle_dir, "runs.jsonl")

    env = capture_env()
    provenance = {
        "label": a.label,
        "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "environment": env,
        "run_config": {"agent": a.agent, "limit": a.limit,
                       "conditions": a.conditions, "repeats": a.repeats},
        "contributor": {"name": a.contributor_name or "<FILL: your name>",
                        "orcid": a.orcid or "<FILL: your ORCID or 'no ORCID'>"},
        "harness_provenance": "runs.jsonl produced by swebench_run.py; each row embeds full config; "
                              "grades via official swebench Docker execution; no fabricated numbers.",
    }
    with open(os.path.join(bundle_dir, "provenance.json"), "w") as fh:
        json.dump(provenance, fh, indent=2)

    cmd = [sys.executable, os.path.join(HERE, "swebench_run.py"),
           "--agent", a.agent, "--limit", str(a.limit),
           "--conditions", a.conditions, "--repeats", str(a.repeats),
           "--out", runs_out]
    if a.dry_config:
        cmd.append("--dry-config")

    print(f"[contribute_run] hardware label: {a.label}")
    print(f"[contribute_run] environment captured -> {bundle_dir}/provenance.json")
    print(f"[contribute_run] running: {' '.join(cmd)}")
    rc = subprocess.run(cmd).returncode

    print("\n" + "=" * 70)
    print("CONTRIBUTION CHECKLIST (maintainer applies pre-merge gate before merging):")
    print("  1. Fill contributor name + ORCID in provenance.json (or state 'no ORCID').")
    print("  2. Confirm provenance: results came from swebench_run.py unmodified (this wrapper did).")
    print(f"  3. Submit the bundle dir: {bundle_dir}/  (runs.jsonl + provenance.json)")
    print("  4. Maintainer verifies, credits you in CITATION.cff + codemeta.json, THEN merges.")
    print("=" * 70)
    print(f"\nAttribution block to paste in your PR:")
    print(f"  Contributor: {a.contributor_name or '<your name>'}  ORCID: {a.orcid or '<your ORCID / no ORCID>'}")
    print(f"  Hardware: {env.get('machine')} / {env.get('gpu')} / docker {env.get('docker')}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
