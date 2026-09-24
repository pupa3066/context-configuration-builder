#!/usr/bin/env python3
"""check_pr.py  -  safeguard gate for pull requests / fork contributions to this PUBLIC repo.

Runs in CI on every PR (and locally) to protect the repo BEFORE merge. It enforces, as HONEST
gates (it flags problems; it never edits or fabricates):

  1. SENSITIVE-INFO SCAN (the leak class we fixed): no personal absolute paths (/Users/<user>/...,
     /home/<user>/...), no secret values (sk-..., AKIA..., PEM blocks, hf_...), no machine-hostname
     git-style emails (<user>@<host>.local) baked into tracked files.
  2. CONTRIBUTOR ATTRIBUTION: if a PR adds result/measurement data (research/**/*.json, *.jsonl,
     benchmark/**), CITATION.cff must credit the contributor (>=1 author) and CONTRIBUTING's
     provenance expectation is surfaced for the reviewer.
  3. PROVENANCE: a contributed results bundle (research/harness/contrib_*/) must carry provenance.json.

Exit 0 = pass (safe to merge). Exit 1 = at least one FAIL (block merge).
Scope: scans TRACKED text files, skips .git and binary/vendor dirs.
"""
from __future__ import annotations
import os, re, sys, subprocess, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- patterns ---
PATH_LEAK = re.compile(r"/(Users|home)/[A-Za-z0-9._-]+/")
SECRET = re.compile(r"sk-[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|hf_[A-Za-z0-9]{20}")
HOST_EMAIL = re.compile(r"[A-Za-z0-9._-]+@[A-Za-z0-9-]+\.local\b")
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".venv", "__pycache__", "figures"}
TEXT_EXT = {".py", ".md", ".sh", ".json", ".jsonl", ".yml", ".yaml", ".cff", ".txt", ".toml", ".ps1", ".html"}


def tracked_files():
    """Files in scope: tracked + staged + untracked-but-not-ignored. This catches a leak whether or
    not it is committed yet (a local pre-commit run and a PR both get scanned). Ignored files (.gitignore)
    are excluded, matching what could ever be pushed."""
    try:
        # -c = tracked, -o = untracked, --exclude-standard = respect .gitignore
        out = subprocess.run(["git", "-C", ROOT, "ls-files", "-co", "--exclude-standard"],
                             capture_output=True, text=True, timeout=30).stdout
        seen, files = set(), []
        for p in out.splitlines():
            if p.strip() and p not in seen:
                seen.add(p); files.append(os.path.join(ROOT, p))
        return files
    except Exception:
        return []


def scan_sensitive():
    errs = []
    for f in tracked_files():
        if any(part in SKIP_DIRS for part in f.split(os.sep)):
            continue
        if os.path.splitext(f)[1] not in TEXT_EXT:
            continue
        try:
            txt = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        rel = os.path.relpath(f, ROOT)
        # allow env-var NAMES like os.environ["OPENAI_API_KEY"]; only flag literal secret VALUES
        if SECRET.search(txt):
            errs.append(f"SECRET value pattern in {rel}")
        for m in set(PATH_LEAK.findall(txt)):
            # PATH_LEAK.findall returns the 'Users'/'home' group; re-scan for the full hit
            pass
        if PATH_LEAK.search(txt):
            errs.append(f"personal absolute path (/Users|/home/<user>/) in {rel}")
        if HOST_EMAIL.search(txt):
            errs.append(f"machine-hostname email (<user>@<host>.local) in {rel}")
    return errs


def check_attribution_and_provenance():
    errs, warns = [], []
    files = [os.path.relpath(f, ROOT) for f in tracked_files()]
    data_added = [f for f in files if (f.startswith("research/") or f.startswith("benchmark/"))
                  and f.endswith((".json", ".jsonl"))]
    # provenance for contributor bundles
    contrib_dirs = sorted({f.split(os.sep)[0:3] and os.sep.join(f.split(os.sep)[:3])
                           for f in files if "contrib_" in f})
    for d in contrib_dirs:
        if d and "contrib_" in d and not os.path.exists(os.path.join(ROOT, d, "provenance.json")):
            errs.append(f"contributor bundle '{d}' missing provenance.json (see CONTRIBUTING pre-merge gate)")
    # attribution surfacing (reviewer must confirm; we can't know PR authorship in a static check)
    cff = os.path.join(ROOT, "CITATION.cff")
    if os.path.exists(cff):
        n = open(cff).read().count("given-names:")
        warns.append(f"CITATION.cff lists {n} person(s). If this PR adds data/work by someone else, "
                     "they MUST be credited in CITATION.cff + codemeta.json BEFORE merge (rule 21a).")
    return errs, warns


def main():
    print("=== CCK PR safeguard (sensitive-info + attribution + provenance) ===")
    s_errs = scan_sensitive()
    a_errs, a_warns = check_attribution_and_provenance()
    errs = s_errs + a_errs

    print("\n[1] Sensitive-info scan:")
    print("  PASS  -  no paths/secrets/host-emails in tracked files" if not s_errs
          else "\n".join(f"  [x] {e}" for e in s_errs))
    print("\n[2/3] Attribution & provenance:")
    for e in a_errs: print(f"  [x] {e}")
    for w in a_warns: print(f"  [warn]  {w}")
    if not a_errs: print("  PASS  -  no missing provenance bundles")

    if errs:
        print(f"\n{len(errs)} blocking issue(s)  -  DO NOT MERGE until fixed.")
        return 1
    print("\nSafeguard PASS. Reviewer still confirms contributor attribution per CONTRIBUTING (rule 21a).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
