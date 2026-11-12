#!/usr/bin/env python3
"""bm25-localize: offline, standard-library BM25 over 8-line chunks of every non-test .py file.

Tokenizer, stopword list, chunk length and parameters (k1=1.5, b=0.75) follow
benchmark/compare_algorithms.py of the project repository; chunks are formed per file so that
results carry file and line locations. Prints one line per chunk, best first:
    rank  score  path:start-end  first non-empty line
"""
import argparse, math, os, re
from collections import Counter

W = re.compile(r"[A-Za-z0-9_.\-]+")
STOP = set("the a an of to in on for and or is are was were be by with vs at as it its this that what which "
           "who whose how many each give state per module does".split())
TEST_RE = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$")
SKIP = {".git", "__pycache__", "node_modules", ".venv", ".tox", "build", "dist"}


def toks(s):
    return [w.lower() for w in W.findall(s) if w.lower() not in STOP and len(w) > 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--root", default=None)
    a = ap.parse_args()
    root = a.root or ("/workspace" if os.path.isdir("/workspace") else os.getcwd())
    chunks = []
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in SKIP]
        for f in fs:
            if not f.endswith(".py"):
                continue
            p = os.path.join(r, f); rel = os.path.relpath(p, root)
            if TEST_RE.search(rel):
                continue
            try:
                lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
            except OSError:
                continue
            for i in range(0, len(lines), 8):
                b = lines[i:i + 8]
                if any(x.strip() for x in b):
                    chunks.append((rel, i + 1, b))
    docs = [toks("\n".join(b)) for _, _, b in chunks]
    n = len(docs)
    if not n:
        print("no Python source files found under", root); return
    avg = sum(map(len, docs)) / n
    df = Counter(w for d in docs for w in set(d))
    q = toks(a.issue)

    def score(d):
        c = Counter(d); s = 0.0
        for w in q:
            if w in c:
                m = df[w]; tf = c[w]
                s += math.log(1 + (n - m + 0.5) / (m + 0.5)) * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * len(d) / avg))
        return s

    ranked = sorted(range(n), key=lambda i: -score(docs[i]))[:max(1, min(a.k, 20))]
    for rank, i in enumerate(ranked, 1):
        rel, start, b = chunks[i]
        first = next((x.strip() for x in b if x.strip()), "")[:120]
        print(f"{rank:>2}  {score(docs[i]):6.2f}  {rel}:{start}-{start + len(b) - 1}  {first}")


if __name__ == "__main__":
    main()
