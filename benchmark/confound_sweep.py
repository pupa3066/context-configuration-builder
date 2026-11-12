#!/usr/bin/env python3
"""confound_sweep.py - controlled test of two confounds in lexical-vs-semantic code retrieval.

Factors varied (everything else is the committed pipeline, imported, not reimplemented):
  chunker : lines8 (committed default, control), lines32, words400
  cap     : semantic index budget (chunks per repo); BM25 always sees every chunk

Reused unchanged from the committed code: question miner and corpus loader
(conceptual_semantic_vs_lexical), BM25 and line chunker (compare_algorithms),
SemanticRetriever (semantic_retriever), m1/m2 metrics and cosine (conceptual_fair_metrics).
Only change: FastSem.topk ranks by a numpy dot product on L2-normalised vectors. This is the same
cosine ranking as the committed pure-Python loop (stable sort keeps tie order); lines8 must
reproduce SWEEP_cap_*.json, which is the check that the speedup changed nothing.

Adds what the committed runner lacks: per-question hits saved, paired bootstrap of the BM25 minus
semantic difference, exact McNemar counts, chunk token lengths against the embedder tokenizer.
"""
from __future__ import annotations
import os, sys, json, argparse, random, math, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import conceptual_semantic_vs_lexical as base
from compare_algorithms import BM25, chunk as chunk_lines
from semantic_retriever import SemanticRetriever, available as sem_available
from conceptual_fair_metrics import m1_substring, m2_defline, _cos


def chunk_words(text, size=400, overlap=50):
    w = text.split(); out = []; i = 0
    while i < len(w):
        out.append(" ".join(w[i:i + size])); i += size - overlap
    return out


CHUNKERS = {
    "lines8": lambda t: chunk_lines(t),          # committed default, identical call
    "lines32": lambda t: chunk_lines(t, 32),
    "words400": chunk_words,
}


class FastSem(SemanticRetriever):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        M = np.asarray(self._emb, dtype=np.float32)
        self._Mn = M / np.maximum(np.linalg.norm(M, axis=1, keepdims=True), 1e-9)

    def topk(self, query, k):
        if not len(self.chunks):
            return []
        q = np.asarray(list(self._model.embed([query]))[0], dtype=np.float32)
        q = q / max(float(np.linalg.norm(q)), 1e-9)
        idx = np.argsort(-(self._Mn @ q), kind="stable")[:k]
        return [self.chunks[i] for i in idx]


class WindowSem:
    """Dense retriever that sees the WHOLE chunk: each chunk is split into token windows that fit the
    embedder (exact character spans from the tokenizer's offset mapping), every window is embedded,
    and a chunk scores the max cosine over its windows. Returned items are the original full chunks,
    so the text handed to the metrics is identical to the whole-chunk condition; only truncation is
    removed. The cap is applied exactly as SemanticRetriever does (even sample over the chunk list)."""
    def __init__(self, chunks, model_name, max_chunks, tokenizer, win=480, stride=400, batch=64):
        from fastembed import TextEmbedding
        if len(chunks) > max_chunks:
            step = len(chunks) / max_chunks
            chunks = [chunks[int(i * step)] for i in range(max_chunks)]
        self.chunks = chunks; self.n_indexed = len(chunks)
        self._model = TextEmbedding(model_name)
        texts, owner = [], []
        for ci, c in enumerate(chunks):
            off = tokenizer(c, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
            if len(off) <= win:
                texts.append(c); owner.append(ci); continue
            s = 0
            while s < len(off):
                e = min(s + win, len(off))
                texts.append(c[off[s][0]:off[e - 1][1]]); owner.append(ci)
                if e == len(off): break
                s += stride
        emb = []
        for i in range(0, len(texts), batch):
            emb.extend(self._model.embed(texts[i:i + batch]))
        W = np.asarray(emb, dtype=np.float32)
        self._Wn = W / np.maximum(np.linalg.norm(W, axis=1, keepdims=True), 1e-9)
        self._owner = np.asarray(owner)
        self.n_windows = len(texts)

    def topk(self, query, k):
        if not len(self.chunks):
            return []
        q = np.asarray(list(self._model.embed([query]))[0], dtype=np.float32)
        q = q / max(float(np.linalg.norm(q)), 1e-9)
        sims = self._Wn @ q
        best = np.full(len(self.chunks), -np.inf, dtype=np.float32)
        np.maximum.at(best, self._owner, sims)
        idx = np.argsort(-best, kind="stable")[:k]
        return [self.chunks[i] for i in idx]


def window_probe(model_name, positions=(128, 400, 600, 1200, 3000, 7000)):
    """Measures the embedder's effective input window: two texts share N filler tokens and differ
    only in the tail. If their embeddings are (near) identical, the model never saw the tail."""
    from fastembed import TextEmbedding
    m = TextEmbedding(model_name)
    tails = (" def parse_config(path): return load(path)", " class TokenBucket: rate limiter for sockets")
    out = {}
    for n in positions:
        filler = " ".join(["value"] * n)
        a, b = list(m.embed([filler + tails[0], filler + tails[1]]))
        out[str(n)] = round(float(_cos(a, b)), 6)
    seen = [int(n) for n, c in out.items() if c < 0.9999]
    return {"cosine_by_filler_words": out, "tail_seen_up_to_filler_words": max(seen) if seen else 0}


def git_head(path):
    try:
        return subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True,
                              text=True).stdout.strip() or None
    except Exception:
        return None


def token_stats(chunks_by_repo, model_name, limit=512, sample=600):
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(model_name)
    except Exception as e:
        return {"error": str(e)[:120]}
    allc = [c for cs in chunks_by_repo.values() for c in cs]
    rng = random.Random(0)
    pick = rng.sample(allc, min(sample, len(allc)))
    L = sorted(len(tok.encode(c, add_special_tokens=False)) for c in pick)
    return {"sampled": len(L), "median": L[len(L) // 2], "p90": L[int(0.9 * len(L))],
            "frac_over_limit": round(sum(1 for x in L if x > limit) / len(L), 4), "limit": limit}


def paired(hb, hs, nb, seed=0):
    n = len(hb); d = [b - s for b, s in zip(hb, hs)]
    rng = random.Random(seed); ms = []
    for _ in range(nb):
        ms.append(sum(d[rng.randrange(n)] for _ in range(n)) / n)
    ms.sort()
    b_only = sum(1 for b, s in zip(hb, hs) if b and not s)
    s_only = sum(1 for b, s in zip(hb, hs) if s and not b)
    m = b_only + s_only
    if m:
        t = min(b_only, s_only)
        p = min(1.0, 2 * sum(math.comb(m, i) for i in range(t + 1)) / 2 ** m)
    else:
        p = 1.0
    return {"mean_diff_bm25_minus_sem": round(sum(d) / n, 4),
            "ci95": [round(ms[int(0.025 * nb)], 4), round(ms[int(0.975 * nb)], 4)],
            "bm25_only": b_only, "sem_only": s_only, "mcnemar_exact_p": round(p, 6)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="+", required=True)
    ap.add_argument("--chunker", choices=list(CHUNKERS), required=True)
    ap.add_argument("--caps", type=int, nargs="+", required=True)
    ap.add_argument("--n-per-repo", type=int, default=80)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--embed-model", default="BAAI/bge-small-en-v1.5")
    ap.add_argument("--sem-threshold", type=float, default=0.72)
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--sem-mode", choices=["whole", "maxwin"], default="whole",
                    help="whole = embed each chunk as one input (default, committed behavior); "
                         "maxwin = embed token windows and score a chunk by its best window")
    ap.add_argument("--token-limit", type=int, default=512,
                    help="documented input limit of the embedder, used for chunk length stats")
    ap.add_argument("--tag", default="", help="extra label in the output file name")
    ap.add_argument("--embed-batch", type=int, default=64,
                    help="chunks per embedding call; lower it for long-input embedders to bound memory")
    a = ap.parse_args()
    if not sem_available():
        print("fastembed unavailable"); sys.exit(1)

    repos = dict(p.split(":", 1) for p in a.repos)
    corpus = {n: base.load_repo_text(p) for n, p in repos.items()}
    Q = []
    for n, p in repos.items():
        for it in base.mine_conceptual(p, a.n_per_repo):
            if it["fact"].lower() in corpus[n].lower():
                it["project"] = n; Q.append(it)
    print(f"N={len(Q)} questions; chunker={a.chunker}", flush=True)

    chunks = {n: CHUNKERS[a.chunker](corpus[n]) for n in corpus}
    n_chunks = {n: len(c) for n, c in chunks.items()}
    print("chunks per repo:", n_chunks, flush=True)
    tstats = token_stats(chunks, a.embed_model, limit=a.token_limit)
    probe = window_probe(a.embed_model)
    print("embedder window probe:", probe, flush=True)
    wtok = None
    if a.sem_mode == "maxwin":
        from transformers import AutoTokenizer
        wtok = AutoTokenizer.from_pretrained(a.embed_model)
    print("chunk token stats vs embedder limit:", tstats, flush=True)
    bm25 = {n: BM25(chunks[n]) for n in corpus}
    prov = {"repo_heads": {n: git_head(p) for n, p in repos.items()},
            "runner_head": git_head(os.path.dirname(HERE))}

    for cap in a.caps:
        print(f"\n=== chunker={a.chunker} cap={cap}", flush=True)
        if a.sem_mode == "maxwin":
            sem = {n: WindowSem(chunks[n], a.embed_model, cap, wtok, batch=a.embed_batch) for n in corpus}
            print("windows embedded per repo:", {n: sem[n].n_windows for n in sem}, flush=True)
        else:
            sem = {n: FastSem(chunks[n], model_name=a.embed_model, max_chunks=cap, batch=a.embed_batch) for n in corpus}
        indexed = {n: sem[n].n_indexed for n in sem}
        model = sem[list(sem)[0]]._model
        facts = [q["fact"] for q in Q]
        fact_emb = dict(zip(facts, model.embed([f"definition of {f}" for f in facts])))

        def score(arm):
            h1, h2, h3 = [], [], []
            for q in Q:
                p = q["project"]
                ch = bm25[p].topk(q["q"], a.k) if arm == "bm25" else sem[p].topk(q["q"], a.k)
                f = q["fact"]; s1 = m1_substring(ch, f); s2 = m2_defline(ch, f)
                if s1:
                    s3 = True
                else:
                    s3 = any(_cos(fact_emb[f], c) >= a.sem_threshold for c in model.embed(ch))
                h1.append(int(s1)); h2.append(int(s2)); h3.append(int(s3))
            return {"m1_substring": h1, "m2_defline": h2, "m3_sem_credit": h3}

        hits = {arm: score(arm) for arm in ("bm25", "semantic")}
        # Gold-chunk coverage: is a chunk holding the answer's def/class line in the full corpus, and in
        # the dense index at this cap? Same definition-line pattern as metric m2.
        import re as _re
        gold_in_corpus, gold_indexed = [], []
        for q in Q:
            pat = _re.compile(r"(?:def|class)\s+" + _re.escape(q["fact"]) + r"\b")
            gold_in_corpus.append(int(any(pat.search(c) for c in chunks[q["project"]])))
            gold_indexed.append(int(any(pat.search(c) for c in sem[q["project"]].chunks)))
        def _cond(h, mask):
            sel = [x for x, g in zip(h, mask) if g]
            return {"n": len(sel), "rate": round(sum(sel) / len(sel), 4) if sel else None}
        gold = {"gold_in_corpus": gold_in_corpus, "gold_indexed": gold_indexed,
                "frac_gold_indexed": round(sum(gold_indexed) / len(Q), 4),
                "dense_given_gold_indexed": {m: _cond(hits["semantic"][m], gold_indexed) for m in hits["semantic"]},
                "dense_given_gold_missing": {m: _cond(hits["semantic"][m], [g and not i for g, i in zip(gold_in_corpus, gold_indexed)]) for m in hits["semantic"]}}
        print("gold chunk indexed fraction:", gold["frac_gold_indexed"], "| dense m1 given gold indexed:",
              gold["dense_given_gold_indexed"]["m1_substring"], "| given gold missing:", gold["dense_given_gold_missing"]["m1_substring"], flush=True)
        summary = {"arms": {arm: {m: base.bootstrap_ci(h, a.bootstrap) for m, h in hits[arm].items()}
                            for arm in hits},
                   "paired": {m: paired(hits["bm25"][m], hits["semantic"][m], a.bootstrap)
                              for m in hits["bm25"]}}
        out = {"N": len(Q), "k": a.k, "chunker": a.chunker, "cap": cap, "embed_model": a.embed_model,
               "sem_threshold": a.sem_threshold, "n_chunks": n_chunks, "n_indexed": indexed,
               "indexed_fraction": {n: round(indexed[n] / max(n_chunks[n], 1), 4) for n in indexed},
               "chunk_token_stats": tstats, "provenance": prov, "summary": summary, "hits": hits, "gold": gold}
        os.makedirs(a.out_dir, exist_ok=True)
        out["sem_mode"] = a.sem_mode; out["window_probe"] = probe
        if a.sem_mode == "maxwin":
            out["n_windows"] = {n: sem[n].n_windows for n in sem}
        parts = [a.chunker] + ([a.sem_mode] if a.sem_mode != "whole" else []) + ([a.tag] if a.tag else [])
        fn = os.path.join(a.out_dir, f"CONFOUND_{'_'.join(parts)}_cap{cap}.json")
        json.dump(out, open(fn, "w"), indent=1)
        for m in ("m1_substring", "m2_defline", "m3_sem_credit"):
            b = summary["arms"]["bm25"][m]; s = summary["arms"]["semantic"][m]; pr = summary["paired"][m]
            print(f"{m:<15} BM25 {b[0]} [{b[1]},{b[2]}]  sem {s[0]} [{s[1]},{s[2]}]  "
                  f"diff {pr['mean_diff_bm25_minus_sem']} CI {pr['ci95']}  McNemar p={pr['mcnemar_exact_p']}",
                  flush=True)
        print("indexed fraction:", out["indexed_fraction"], "-> wrote", fn, flush=True)


if __name__ == "__main__":
    main()
