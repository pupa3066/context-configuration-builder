#!/usr/bin/env python3
"""semantic_retriever.py — real semantic top-k retrieval for context selection.

Embeds chunks once (BAAI/bge-small-en-v1.5 via fastembed: ONNX, CPU, no torch — fits an 8GB box),
then selects the top-k chunks by cosine similarity to the query. This is the semantic upgrade over
BM25-lite (lexical): it catches paraphrase/synonym matches BM25 misses, which is the gap that kept
lexical retrieval under 0.95 answerable in the algorithm comparison.

GRACEFUL FALLBACK: if fastembed/model is unavailable, is_semantic=False and the caller should skip
the semantic arm (do NOT silently fall back to lexical and mislabel it semantic — that would be a
false result). No network needed after the model is cached once.
"""
from __future__ import annotations
import math

try:
    from fastembed import TextEmbedding
    _HAVE = True
except Exception:
    _HAVE = False


def available() -> bool:
    return _HAVE


def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class SemanticRetriever:
    """Embed a fixed chunk list once; retrieve top-k per query by cosine similarity.
    Memory-safe on 8GB: caps chunk count (transparently reported via .n_indexed / .capped) and embeds
    in batches so the full embedding set does not spike RAM. Capping samples evenly across the chunk
    list to preserve coverage; the cap is reported so results state the indexed fraction honestly."""
    def __init__(self, chunks, model_name="BAAI/bge-small-en-v1.5", max_chunks=1200, batch=64):
        if not _HAVE:
            raise RuntimeError("fastembed not available")
        self.capped = len(chunks) > max_chunks
        if self.capped:
            step = len(chunks) / max_chunks
            chunks = [chunks[int(i*step)] for i in range(max_chunks)]  # even sample across the repo
        self.chunks = chunks
        self.n_indexed = len(chunks)
        self._model = TextEmbedding(model_name)
        emb = []
        for i in range(0, len(chunks), batch):
            emb.extend(self._model.embed(chunks[i:i+batch]))   # batched: bounded peak memory
        self._emb = emb
        self.dim = len(self._emb[0]) if self._emb else 0

    def topk(self, query, k):
        if not self._emb:
            return []
        qv = list(self._model.embed([query]))[0]
        scored = sorted(range(len(self.chunks)),
                        key=lambda i: _cos(qv, self._emb[i]), reverse=True)
        return [self.chunks[i] for i in scored[:k]]


if __name__ == "__main__":
    print("fastembed available:", available())
    if available():
        r = SemanticRetriever(["the auth module validates tokens",
                               "the database pool caps at 32 connections",
                               "cross-attention layers carry identity"])
        print("dim:", r.dim)
        print("top1 for 'who checks login credentials':",
              r.topk("who checks login credentials", 1))
