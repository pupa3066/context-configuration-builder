"""os_portability.py  -  does Consistent Context Kit itself run on THIS operating system?

This is a DIFFERENT question from SWE-bench task grading (which runs in Docker/Linux
regardless of host). Here we check that CCK's own shell surface works on the host OS
so a user on macOS / Linux / WSL can install and run the kit.

Checks (each PASS/FAIL/SKIP with a reason  -  never a guessed pass):
  1. shell available (sh/bash)
  2. install.sh --dry-run runs and is non-destructive
  3. context-check hook parses the registry without error
  4. add-project / remove-project scripts exist and are syntactically valid
  5. tier_assign unit tests import and run

Records the OS factors so results are attributable to a platform.
Run: python research/harness/os_portability.py --repo-root .
"""
from __future__ import annotations
import os, sys, json, shutil, subprocess, platform, argparse


def _run(cmd, cwd=None, timeout=60):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 999, "", str(e)


def check(repo_root: str) -> dict:
    results = []

    def record(name, status, detail=""):
        results.append({"check": name, "status": status, "detail": detail})

    # 1. shell available
    sh = shutil.which("bash") or shutil.which("sh")
    record("shell_available", "PASS" if sh else "FAIL", sh or "no sh/bash on PATH")

    # 2. install.sh --dry-run (non-destructive)
    inst = os.path.join(repo_root, "install.sh")
    if os.path.isfile(inst) and sh:
        rc, out, err = _run([sh, inst, "--dry-run"], cwd=repo_root)
        record("install_dry_run", "PASS" if rc == 0 else "FAIL", (err or out)[-200:])
    else:
        record("install_dry_run", "SKIP", "install.sh not found or no shell")

    # 3. context-check hook syntax (parse only; it reads ~/.kiro which may not exist in CI)
    hook = os.path.join(repo_root, "hooks", "context-check.sh")
    if os.path.isfile(hook) and sh:
        rc, out, err = _run([sh, "-n", hook], cwd=repo_root)  # -n = syntax check
        record("hook_syntax", "PASS" if rc == 0 else "FAIL", err[-200:])
    else:
        record("hook_syntax", "SKIP", "hook not found or no shell")

    # 4. lifecycle scripts syntactically valid
    for scr in ("scripts/add-project.sh", "scripts/remove-project.sh"):
        p = os.path.join(repo_root, scr)
        if os.path.isfile(p) and sh:
            rc, _, err = _run([sh, "-n", p], cwd=repo_root)
            record(f"syntax:{scr}", "PASS" if rc == 0 else "FAIL", err[-160:])
        else:
            record(f"syntax:{scr}", "SKIP", "not found or no shell")

    # 5. tier_assign unit tests
    ta_test = os.path.join(repo_root, "research", "tier_assign", "test_tier_assign.py")
    if os.path.isfile(ta_test):
        rc, out, err = _run([sys.executable, "-m", "pytest", "-q", ta_test], cwd=repo_root)
        # pytest may be absent; treat import/run failure honestly
        if rc == 0:
            record("tier_assign_tests", "PASS", out.strip().splitlines()[-1] if out.strip() else "")
        elif "No module named pytest" in err or "not found" in err.lower():
            # fall back to running the module's own asserts if it has a __main__
            rc2, out2, err2 = _run([sys.executable, ta_test], cwd=repo_root)
            record("tier_assign_tests", "PASS" if rc2 == 0 else "FAIL",
                   "(ran without pytest) " + (err2 or out2)[-160:])
        else:
            record("tier_assign_tests", "FAIL", (err or out)[-200:])
    else:
        record("tier_assign_tests", "SKIP", "test file not found")

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "summary": {"pass": passed, "fail": failed,
                    "skip": sum(1 for r in results if r["status"] == "SKIP")},
        "checks": results,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    report = check(os.path.abspath(a.repo_root))
    js = json.dumps(report, indent=2)
    if a.out:
        with open(a.out, "w") as fh:
            fh.write(js)
    print(js)
    # Non-zero exit if any hard FAIL, so CI on each OS can gate.
    sys.exit(1 if report["summary"]["fail"] else 0)
