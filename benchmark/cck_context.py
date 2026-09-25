#!/usr/bin/env python3
"""cck_context.py - the CCK context-assembly algorithm as ONE reusable, callable function.

WHY THIS FILE EXISTS
--------------------
The CCK tiering policy was previously tangled inside compare_algorithms.py's `injected(algo, q)`,
coupled to a PRIVATE questions file and to the author's LOCAL ~/.kiro steering files. That made it
non-portable (any other consumer got zero or the author's personal content) and impossible to reuse
outside that one benchmark loop.

This module extracts the SAME policy into a single clean function AND decouples the Tier-1 header
from Kiro-CLI's default steering. The always-on header now comes from the repo's OWN bundled,
agent-neutral consumer rules (core/templates/always-on/*.md) - generic and portable - or from a
header the caller passes in. It never reads ~/.kiro. So any consumer gets the CCK algorithm +
portable rules, with nothing personal and no Kiro dependency.

Reuses the existing, unchanged retrieval primitives (no algorithm change):
  - build_corpus / chunk / BM25         from compare_algorithms.py
  - SemanticRetriever                   from semantic_retriever.py (fastembed bge-small, CPU/ONNX)

PUBLIC API
----------
  load_portable_header(repo_root=None) -> str
      Concatenate the bundled always-on consumer rules (rules, context-registry, portfolio,
      cross-links) from core/templates/always-on/. NO ~/.kiro, NO personal files.

  RepoContext(repo_path, header=..., max_chunks=...).assemble(query, method, k) -> ContextResult
  assemble_context(repo_path, query, method="bm25", k=6, header=..., ...) -> ContextResult

METHODS (the CCK context arms, faithful to compare_algorithms.py)
  "full"        : whole repo corpus (monolithic baseline).
  "bm25"        : Tier-2 lexical retrieval, top-k chunks (CCK identifier-first default).
  "semantic"    : Tier-2 embedding retrieval, top-k by cosine (bge-small). Requires fastembed.
  "hybrid_bm25" : Tier-1 portable header + BM25 top-k. The CCK tiered-context arm.
  "hybrid_sem"  : Tier-1 portable header + semantic top-k. Requires fastembed.

HONESTY
  - No fabricated fallback: a semantic method with fastembed unavailable RAISES, never silently
    returns lexical results mislabeled as semantic.
  - Capping is reported (.capped / .n_chunks_indexed), never hidden.
  - Assembles context ONLY. Does not run a model, grade a patch, or measure task success.
"""
from __future__ import annotations

import os
import re
import sys
import math
from collections import Counter
from dataclasses import dataclass
from typing import Optional, List

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../benchmark
_REPO_ROOT = os.path.dirname(_HERE)                          # repo root
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# --- Retrieval primitives, INLINED VERBATIM from compare_algorithms.py -------------------------
# Copied unchanged (build_corpus, chunk, toks, BM25) so this module is self-contained and does NOT
# transitively import transformers (compare_algorithms hard-imports the gpt2 tokenizer at module
# top). Behavior is identical to the committed benchmark; only the tokenizer coupling is removed.
_WORD = re.compile(r"[A-Za-z0-9_.\-]+")
STOP = set("the a an of to in on for and or is are was were be by with vs at as it its this that what which who whose how many each give state per module does".split())


def read(p):
    return open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""


def build_corpus(root, rels):
    import subprocess
    parts = []
    for rel in rels:
        t = read(os.path.join(root, rel))
        if t:
            parts.append(t)

    def _git(a):
        try:
            return subprocess.run(["git", "-C", root] + a, capture_output=True, text=True, timeout=15).stdout
        except Exception:
            return ""

    parts.append(_git(["log", "--all", "--oneline", "-n", "400"]))
    parts.append(_git(["reflog", "-n", "200"]))
    tracked = _git(["ls-files"]).splitlines()
    exts = (".md", ".py", ".txt", ".yaml", ".yml", ".toml", ".cff", ".json", ".tex", ".sh")
    for rel in tracked:
        if rel.endswith(exts) and rel not in rels:
            fp = os.path.join(root, rel)
            try:
                if os.path.getsize(fp) < 200_000:
                    t = read(fp)
                    if t:
                        parts.append(t)
            except OSError:
                pass
    return "\n".join(parts)


def chunk(text, size_lines=8):
    lines = [l for l in text.splitlines()]
    return ["\n".join(lines[i:i + size_lines]) for i in range(0, len(lines), size_lines) if any(lines[i:i + size_lines])]


def toks(s):
    return [w.lower() for w in _WORD.findall(s) if w.lower() not in STOP and len(w) > 2]


class BM25:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs = [toks(c) for c in chunks]
        self.N = len(self.docs)
        self.avgdl = (sum(len(d) for d in self.docs) / self.N) if self.N else 1
        df = Counter()
        for d in self.docs:
            for w in set(d):
                df[w] += 1
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}

    def score(self, q, d):
        k1, b = 1.5, 0.75
        dl = len(d)
        c = Counter(d)
        s = 0.0
        for w in q:
            if w in c:
                idf = self.idf.get(w, 0)
                tf = c[w]
                s += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / self.avgdl))
        return s

    def topk(self, query, k):
        q = toks(query)
        scored = sorted(range(self.N), key=lambda i: self.score(q, self.docs[i]), reverse=True)
        return [self.chunks[i] for i in scored[:k]]


try:
    from semantic_retriever import SemanticRetriever, available as _sem_available
except Exception:  # pragma: no cover
    SemanticRetriever = None

    def _sem_available() -> bool:
        return False

# Optional real tokenizer (same gpt2 BPE the benchmark uses). Assembly must not hard-depend on it.
try:
    from transformers import AutoTokenizer

    _TOK = AutoTokenizer.from_pretrained("gpt2")

    def _ntok(s: str) -> Optional[int]:
        return len(_TOK.encode(s))
except Exception:  # pragma: no cover
    _TOK = None

    def _ntok(s: str) -> Optional[int]:  # type: ignore[misc]
        return None


# --- Tier-1 portable header: bundled consumer rules, NOT ~/.kiro ------------------------------
# These ship with the repo and are agent-neutral and generic. Order mirrors the CCK bootstrap:
# rules first, then the context registry, portfolio, and cross-links.
_ALWAYS_ON_FILES = ("rules.md", "context-registry.md", "portfolio.md", "cross-links.md")


def load_portable_header(repo_root: Optional[str] = None) -> str:
    """Load the bundled, portable, agent-neutral always-on rules as the Tier-1 header.

    Reads core/templates/always-on/*.md from the CCK repo - never ~/.kiro, never personal files.
    Returns "" if the templates are absent, so the function degrades safely for any consumer.
    """
    root = repo_root or _REPO_ROOT
    base = os.path.join(root, "core", "templates", "always-on")
    parts: List[str] = []
    for name in _ALWAYS_ON_FILES:
        p = os.path.join(base, name)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    parts.append(fh.read())
            except OSError:
                pass
    return "\n\n".join(parts)


_EMBED_METHODS = {"semantic", "hybrid_sem"}
_HEADER_METHODS = {"hybrid_bm25", "hybrid_sem"}
_VALID = {"full", "bm25", "semantic", "hybrid_bm25", "hybrid_sem"}

# Sentinel so callers can distinguish "use bundled portable header" from "no header" ("").
_DEFAULT_HEADER = object()


@dataclass
class ContextResult:
    text: str
    method: str
    k: int
    n_tokens: Optional[int]
    header_tokens: Optional[int]
    n_chunks_indexed: int
    capped: bool

    def as_dict(self) -> dict:
        return {
            "method": self.method,
            "k": self.k,
            "n_tokens": self.n_tokens,
            "header_tokens": self.header_tokens,
            "n_chunks_indexed": self.n_chunks_indexed,
            "capped": self.capped,
        }


class RepoContext:
    """Prepared, reusable per-repo state (corpus, chunks, retrievers). Build ONCE per repo, then
    call .assemble(query, method, k) many times so a harness scoring N tasks does not re-embed."""

    def __init__(
        self,
        repo_path: str,
        rels: Optional[list] = None,
        size_lines: int = 8,
        max_chunks: int = 1200,
        header=_DEFAULT_HEADER,
        repo_root: Optional[str] = None,
    ):
        self.repo_path = repo_path
        self.corpus = build_corpus(repo_path, rels or [])
        self.chunks = chunk(self.corpus, size_lines=size_lines)
        self.bm25 = BM25(self.chunks)
        # Header: bundled portable rules by default; caller may pass a custom string or "" for none.
        if header is _DEFAULT_HEADER:
            self.header = load_portable_header(repo_root)
        else:
            self.header = header or ""
        self.header_tokens = _ntok(self.header) if self.header else 0
        self.max_chunks = max_chunks
        self._sem = None  # lazy: only build the embedding index if a semantic method is requested

    def _semantic(self):
        if not _sem_available():
            raise RuntimeError(
                "semantic method requested but fastembed is unavailable; refusing to fall back to "
                "lexical (that would mislabel the result). Install fastembed or use a bm25 method."
            )
        if self._sem is None:
            self._sem = SemanticRetriever(self.chunks, max_chunks=self.max_chunks)
        return self._sem

    def assemble(self, query: str, method: str = "bm25", k: int = 6) -> ContextResult:
        if method not in _VALID:
            raise ValueError(f"unknown method {method!r}; valid: {sorted(_VALID)}")

        capped = False
        n_indexed = len(self.chunks)

        if method == "full":
            body = self.corpus
        elif method in ("bm25", "hybrid_bm25"):
            body = "\n".join(self.bm25.topk(query, k))
        else:  # semantic / hybrid_sem
            sem = self._semantic()
            body = "\n".join(sem.topk(query, k))
            capped = sem.capped
            n_indexed = sem.n_indexed

        use_header = method in _HEADER_METHODS and bool(self.header)
        text = (self.header + "\n" + body) if use_header else body
        header_tok = self.header_tokens if use_header else 0

        return ContextResult(
            text=text,
            method=method,
            k=k,
            n_tokens=_ntok(text),
            header_tokens=(header_tok if _TOK is not None else None),
            n_chunks_indexed=n_indexed,
            capped=capped,
        )


def assemble_context(
    repo_path: str,
    query: str,
    method: str = "bm25",
    k: int = 6,
    header=_DEFAULT_HEADER,
    max_chunks: int = 1200,
    size_lines: int = 8,
    rels: Optional[list] = None,
    repo_root: Optional[str] = None,
) -> ContextResult:
    """One-shot wrapper: prepare a repo and assemble context for a single query. For many queries
    against one repo, build a RepoContext once and call .assemble repeatedly instead."""
    ctx = RepoContext(
        repo_path,
        rels=rels,
        size_lines=size_lines,
        max_chunks=max_chunks,
        header=header,
        repo_root=repo_root,
    )
    return ctx.assemble(query, method=method, k=k)


def semantic_available() -> bool:
    return _sem_available()


def tokenizer_available() -> bool:
    return _TOK is not None


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Assemble CCK context for a repo+query (one method).")
    ap.add_argument("--repo", required=True, help="path to a checked-out repo")
    ap.add_argument("--query", required=True)
    ap.add_argument("--method", default="bm25", choices=sorted(_VALID))
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--max-chunks", type=int, default=1200, dest="max_chunks")
    ap.add_argument("--no-header", action="store_true", help="force empty Tier-1 header")
    ap.add_argument("--show-text", action="store_true")
    a = ap.parse_args()

    hdr = "" if a.no_header else _DEFAULT_HEADER
    res = assemble_context(a.repo, a.query, method=a.method, k=a.k,
                           max_chunks=a.max_chunks, header=hdr)
    print(json.dumps(res.as_dict(), indent=1))
    if a.show_text:
        print("----- assembled context -----")
        print(res.text)
