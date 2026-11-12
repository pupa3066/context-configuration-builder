#!/usr/bin/env python3
"""kb_index_audit.py - audit what a retrieval index can actually see.

Two checks, both about the confounds measured in benchmark/CURRENT_STATE.md:

1. Coverage. For a corpus and an indexing policy (which file extensions are indexed, and an optional cap on
   the number of chunks), report, per file type and per code construct, the share of symbols whose
   definition line is inside some indexed chunk:
     Python: def, async def, class      Shell: name() { ... } functions
   A symbol whose definition is outside the index cannot be retrieved by any query.

2. Chunk length. For the same chunks, report token lengths under the embedder's tokenizer and the share
   above its input limit; text past the limit does not affect the chunk's embedding.

It can also audit an existing node list (for example the competition harness graph JSON, one node per
function or class) against the source: --graph PATH reports which constructs have nodes.

Standard library only, except the optional tokenizer (transformers) for chunk lengths.

Examples:
  python kb_index_audit.py --root /repo --policy all --policy md-only --chunker lines8 --chunker words400
  python kb_index_audit.py --root /snapshot --graph /data/graphs/fastapi_<commit>.json
"""
from __future__ import annotations
import argparse, ast, json, os, random, re, sys

POLICIES = {
    "all": {".py", ".sh", ".md", ".yaml", ".yml", ".txt", ".json"},
    "md-only": {".md"},
    "code-only": {".py", ".sh"},
    "py-only": {".py"},
}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".tox", "build", "dist"}
SH_FUNC = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{", re.M)


def files_under(root):
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in SKIP_DIRS]
        for f in fs:
            yield os.path.join(r, f)


def symbols(root):
    """(construct, name, relpath, line) for every Python def/async def/class and shell function."""
    out = []
    for p in files_under(root):
        rel = os.path.relpath(p, root)
        if p.endswith(".py"):
            try:
                tree = ast.parse(open(p, encoding="utf-8", errors="ignore").read())
            except Exception:
                continue
            for nd in ast.walk(tree):
                kind = ("async def" if isinstance(nd, ast.AsyncFunctionDef) else "def" if isinstance(nd, ast.FunctionDef)
                        else "class" if isinstance(nd, ast.ClassDef) else None)
                if kind:
                    out.append((kind, nd.name, rel, nd.lineno))
        elif p.endswith(".sh"):
            text = open(p, encoding="utf-8", errors="ignore").read()
            for m in SH_FUNC.finditer(text):
                out.append(("shell function", m.group(1), rel, text.count("\n", 0, m.start()) + 1))
    return out


def chunks_for(root, exts, chunker):
    """List of (relpath, start_line, end_line, text) for every indexed file under the policy."""
    out = []
    for p in files_under(root):
        if os.path.splitext(p)[1].lower() not in exts:
            continue
        rel = os.path.relpath(p, root)
        try:
            lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
        except OSError:
            continue
        if chunker == "lines8":
            for i in range(0, len(lines), 8):
                b = lines[i:i + 8]
                if any(x.strip() for x in b):
                    out.append((rel, i + 1, i + len(b), "\n".join(b)))
        elif chunker == "words400":
            # 400 words with 50 overlap, mapped back to line spans so coverage can be checked by line.
            words = [(w, ln) for ln, line in enumerate(lines, 1) for w in line.split()]
            i = 0
            while i < len(words):
                seg = words[i:i + 400]
                out.append((rel, seg[0][1], seg[-1][1], " ".join(w for w, _ in seg)))
                i += 350
        else:
            raise ValueError(chunker)
    return out


def cap_even(chunks, cap):
    if cap is None or len(chunks) <= cap:
        return chunks
    step = len(chunks) / cap
    return [chunks[int(i * step)] for i in range(cap)]


def coverage(syms, chunks):
    by_file = {}
    for rel, s, e, _ in chunks:
        by_file.setdefault(rel, []).append((s, e))
    res = {}
    for kind, name, rel, line in syms:
        hit = any(s <= line <= e for s, e in by_file.get(rel, []))
        r = res.setdefault(kind, [0, 0]); r[0] += hit; r[1] += 1
    return {k: {"indexed": v[0], "total": v[1], "share": round(v[0] / v[1], 4) if v[1] else None} for k, v in sorted(res.items())}


def token_stats(chunks, model, limit, sample=600):
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(model)
    except Exception as e:
        return {"error": f"tokenizer unavailable: {str(e)[:100]}"}
    rng = random.Random(0)
    pick = rng.sample(chunks, min(sample, len(chunks)))
    L = sorted(len(tok.encode(c[3], add_special_tokens=False)) for c in pick)
    if not L:
        return {}
    return {"sampled": len(L), "median": L[len(L) // 2], "p90": L[int(0.9 * len(L))],
            "share_over_limit": round(sum(1 for x in L if x > limit) / len(L), 4), "limit": limit}


def audit_graph(root, graph_path):
    nodes = json.load(open(graph_path))["nodes"]
    texts = [str(n.get("text", "")).lstrip() for n in nodes]
    names = {str(n.get("name", "")).split(".")[-1] for n in nodes}
    syms = symbols(root)
    src = {}
    for kind, name, _, _ in syms:
        src.setdefault(kind, set()).add(name)
    only_async = src.get("async def", set()) - src.get("def", set())
    return {"graph_nodes": len(nodes),
            "graph_async_def_nodes": sum(1 for t in texts if t.startswith("async def")),
            "graph_def_nodes": sum(1 for t in texts if t.startswith("def ")),
            "source_counts": {k: sum(1 for s in syms if s[0] == k) for k in sorted({s[0] for s in syms})},
            "async_only_names": len(only_async), "async_only_names_in_graph": len(only_async & names)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--policy", action="append", choices=list(POLICIES))
    ap.add_argument("--chunker", action="append", choices=["lines8", "words400"])
    ap.add_argument("--cap", type=int, action="append", help="chunk caps to audit (omit for no cap)")
    ap.add_argument("--embed-model", default="BAAI/bge-small-en-v1.5")
    ap.add_argument("--token-limit", type=int, default=512)
    ap.add_argument("--graph", help="audit an existing node-list index (harness graph JSON) instead")
    ap.add_argument("--out", default="kb_index_audit.json")
    a = ap.parse_args()
    if a.graph:
        res = {"root": os.path.basename(os.path.abspath(a.root)), "graph": os.path.basename(a.graph), "audit": audit_graph(a.root, a.graph)}
    else:
        syms = symbols(a.root)
        res = {"root": os.path.basename(os.path.abspath(a.root)), "symbols": len(syms), "rows": []}
        for pol in a.policy or ["all"]:
            for ch in a.chunker or ["lines8"]:
                full = chunks_for(a.root, POLICIES[pol], ch)
                for cap in (a.cap or [None]):
                    idx = cap_even(full, cap)
                    res["rows"].append({"policy": pol, "chunker": ch, "cap": cap, "chunks_total": len(full),
                                        "chunks_indexed": len(idx), "coverage": coverage(syms, idx),
                                        "chunk_tokens": token_stats(idx, a.embed_model, a.token_limit)})
                    print(json.dumps(res["rows"][-1]), flush=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
