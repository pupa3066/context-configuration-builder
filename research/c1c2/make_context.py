#!/usr/bin/env python3
"""Generate one repository context file from a source snapshot (condition A2 of PREREG_c1c2_gemma_harness.md).

Deterministic and snapshot-only: package layout, each module's first docstring line and top-level public names,
test layout, and pytest settings copied from the repository's own config files. No outside information is added.
The same text feeds C1 (monolithic, in the system prompt) and C2 (tiered, one skill per repository).

Usage: python make_context.py <repo_dir> <name> <commit> [--max-words 1200] > context.md
"""
import argparse, ast, os, re, sys

SKIP_DIRS = {".git", ".github", "docs", "tests", "test", "testing", "scripts", "benchmarks", "examples", "docs_src",
             "build", "dist", "__pycache__", ".venv", "venv", "site"}


def first_doc_line(tree):
    doc = ast.get_docstring(tree) or ""
    line = doc.strip().splitlines()[0].strip() if doc.strip() else ""
    return re.sub(r"\s+", " ", line)[:120]


def public_names(tree, limit=8):
    names = [n.name for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
             and not n.name.startswith("_")]
    return names[:limit], max(0, len(names) - limit)


def packages(root):
    out = []
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if d in SKIP_DIRS or not os.path.isdir(p):
            continue
        if os.path.isfile(os.path.join(p, "__init__.py")):
            out.append(d)
        elif d == "src":
            out += ["src/" + s for s in sorted(os.listdir(p)) if os.path.isfile(os.path.join(p, s, "__init__.py"))]
    return out


def module_entries(root, pkg):
    rows = []
    for r, ds, fs in os.walk(os.path.join(root, pkg)):
        ds[:] = sorted(x for x in ds if x not in SKIP_DIRS)
        for f in sorted(fs):
            if not f.endswith(".py"):
                continue
            path = os.path.join(r, f); rel = os.path.relpath(path, root)
            try:
                tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
            except SyntaxError:
                rows.append((rel, "", [], 0)); continue
            names, more = public_names(tree)
            rows.append((rel, first_doc_line(tree), names, more))
    return rows


def pytest_settings(root):
    lines = []
    for cfg in ("pyproject.toml", "setup.cfg", "tox.ini", "pytest.ini"):
        p = os.path.join(root, cfg)
        if not os.path.isfile(p):
            continue
        text = open(p, encoding="utf-8", errors="replace").read().splitlines()
        grab = False
        for ln in text:
            s = ln.strip()
            if s.startswith("["):
                grab = s in ("[tool.pytest.ini_options]", "[tool:pytest]", "[pytest]")
                if grab:
                    lines.append(f"{cfg} {s}")
                continue
            if grab and s and not s.startswith("#"):
                lines.append("  " + s[:140])
    return lines[:25]


def test_layout(root):
    for d in ("tests", "test"):
        p = os.path.join(root, d)
        if os.path.isdir(p):
            n = sum(1 for r, _, fs in os.walk(p) for f in fs if f.startswith("test") and f.endswith(".py"))
            return d, n
    return None, 0


def docs_src_summary(root):
    p = os.path.join(root, "docs_src")
    if not os.path.isdir(p):
        return None
    subs = sorted(d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d)))
    n = sum(1 for r, _, fs in os.walk(p) for f in fs if f.endswith(".py"))
    return n, subs


def render(root, name, commit, max_words):
    head = [f"# Repository context: {name}", "", f"Source: snapshot at commit {commit[:12]}.", ""]
    tdir, tn = test_layout(root)
    test = ["## Tests", ""]
    if tdir:
        test.append(f"Tests live in `{tdir}/` ({tn} test files).")
    settings = pytest_settings(root)
    if settings:
        test += ["", "Pytest settings from the repository's own config:", "", "```"] + settings + ["```"]
    test.append("")
    ds = docs_src_summary(root)
    extra = []
    if ds:
        n, subs = ds
        extra = ["## Documentation examples", "",
                 f"`docs_src/` holds {n} example Python files used by the documentation, in folders: "
                 + ", ".join(subs[:40]) + (f", and {len(subs) - 40} more." if len(subs) > 40 else "."), ""]
    rows = [(p, m) for p in packages(root) for m in module_entries(root, p)]

    def layout(detail):
        out = ["## Package layout", ""]
        for pkg, (rel, doc, names, more) in rows:
            item = f"- `{rel}`"
            if doc and detail >= 1:
                item += f": {doc}"
            if names and detail >= 2:
                item += " Defines " + ", ".join(names) + (f", and {more} more" if more else "") + "."
            out.append(item)
        return out

    for detail in (2, 1, 0):
        text = "\n".join(head + test + extra + layout(detail))
        if len(text.split()) <= max_words:
            return text + "\n"
    # Still too long: keep the first modules that fit, then say how many were left out.
    body = head + test + extra + ["## Package layout", ""]
    kept = 0
    for pkg, (rel, *_rest) in rows:
        if len("\n".join(body + [f"- `{rel}`"]).split()) > max_words - 12:
            break
        body.append(f"- `{rel}`"); kept += 1
    body.append(f"- and {len(rows) - kept} more modules under " + ", ".join(f"`{p}/`" for p in packages(root)) + ".")
    return "\n".join(body) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_dir"); ap.add_argument("name"); ap.add_argument("commit")
    ap.add_argument("--max-words", type=int, default=1200)
    a = ap.parse_args()
    sys.stdout.write(render(a.repo_dir, a.name, a.commit, a.max_words))
