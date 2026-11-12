# =============================================================================
# CCK Fair-Metric Sweep -- Kaggle notebook runner
# Run all cells top to bottom. Outputs three JSON files in /kaggle/working/:
#   SWEEP_bge_base_full.json      -- bge-base-en-v1.5 at full corpus, thresh=0.72
#   SWEEP_threshold_0.65.json     -- bge-small at full corpus, thresh=0.65
#   SWEEP_threshold_0.80.json     -- bge-small at full corpus, thresh=0.80
# Download these three files and commit to benchmark/ in the repo.
# =============================================================================

# ── Cell 1: install deps ──────────────────────────────────────────────────────
# !pip install fastembed rank-bm25 transformers --quiet

# ── Cell 2: clone repos ───────────────────────────────────────────────────────
# !git clone --depth=200 https://github.com/psf/requests.git /tmp/requests
# !git clone --depth=200 https://github.com/pallets/click.git /tmp/click
# !git clone --depth=200 https://github.com/psf/black.git    /tmp/black

# ── Cell 3: copy benchmark source from repo dataset or paste inline ───────────
# If the CCK repo is attached as a Kaggle dataset, adjust the path below.
# Otherwise paste the source of conceptual_fair_metrics.py, compare_algorithms.py,
# conceptual_semantic_vs_lexical.py, and semantic_retriever.py inline.
# The simplest approach: attach pupa3066/context-configuration-builder as a dataset
# (path will be /kaggle/input/context-configuration-builder/) then:
# import sys; sys.path.insert(0, '/kaggle/input/context-configuration-builder/benchmark')

# ── Cell 4: main runner (paste this whole block as one cell) ──────────────────

from __future__ import annotations
import os, sys, re, json, math, random, statistics, ast, glob

# ---- minimal inline copies of the four required modules ----
# (avoids needing the repo attached as a dataset)

# --- semantic_retriever (inline) ---
try:
    from fastembed import TextEmbedding
    _HAVE_FASTEMBED = True
except Exception:
    _HAVE_FASTEMBED = False

def _cos(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

class SemanticRetriever:
    def __init__(self, chunks, model_name="BAAI/bge-small-en-v1.5", max_chunks=100000, batch=64):
        self.capped = len(chunks) > max_chunks
        if self.capped:
            step = len(chunks)/max_chunks
            chunks = [chunks[int(i*step)] for i in range(max_chunks)]
        self.chunks = chunks
        self.n_indexed = len(chunks)
        self._model = TextEmbedding(model_name)
        emb = []
        for i in range(0, len(chunks), batch):
            emb.extend(self._model.embed(chunks[i:i+batch]))
        self._emb = emb
    def topk(self, query, k):
        if not self._emb: return []
        qv = list(self._model.embed([query]))[0]
        scored = sorted(range(len(self.chunks)), key=lambda i: _cos(qv, self._emb[i]), reverse=True)
        return [self.chunks[i] for i in scored[:k]]

# --- BM25 (inline, no external dep) ---
import math as _math
from collections import Counter as _Counter

_WORD = re.compile(r"[A-Za-z0-9_]+")
_STOP = set("the a an of to in on for and or is are was were be by with vs at as it its this that what which who whose how many each".split())

def _tokenize(s):
    return [w.lower() for w in _WORD.findall(s) if w.lower() not in _STOP]

def chunk(text, size=400, overlap=50):
    words = text.split()
    out = []
    i = 0
    while i < len(words):
        out.append(" ".join(words[i:i+size]))
        i += size - overlap
    return out

class BM25:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.chunks = chunks
        self.k1 = k1; self.b = b
        self.N = len(chunks)
        toks = [_tokenize(c) for c in chunks]
        self.avgdl = sum(len(t) for t in toks) / max(self.N, 1)
        self.tf = [_Counter(t) for t in toks]
        df = _Counter()
        for t in toks:
            for w in set(t): df[w] += 1
        self.idf = {w: _math.log((self.N - df[w] + 0.5)/(df[w] + 0.5) + 1) for w in df}
    def score(self, query, idx):
        dl = sum(self.tf[idx].values())
        s = 0.0
        for w in _tokenize(query):
            if w not in self.idf: continue
            tf = self.tf[idx].get(w, 0)
            s += self.idf[w] * (tf*(self.k1+1)) / (tf + self.k1*(1 - self.b + self.b*dl/self.avgdl))
        return s
    def topk(self, query, k):
        scores = sorted(range(self.N), key=lambda i: self.score(query, i), reverse=True)
        return [self.chunks[i] for i in scores[:k]]

# --- corpus loader + question miner (inline) ---
def load_repo_text(path):
    parts = []
    for f in glob.glob(os.path.join(path, "**", "*.py"), recursive=True):
        try:
            if os.path.getsize(f) < 200_000:
                parts.append(open(f, encoding="utf-8", errors="ignore").read())
        except OSError:
            pass
    return "\n".join(parts)

def mine_conceptual(path, n):
    qs = []
    for f in glob.glob(os.path.join(path, "**", "*.py"), recursive=True):
        try:
            if os.path.getsize(f) > 200_000: continue
            tree = ast.parse(open(f, encoding="utf-8", errors="ignore").read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                if not doc: continue
                name = node.name
                if len(name) < 4 or name.startswith("_"): continue
                first = re.split(r"(?<=[.!?])\s", doc.strip())[0].strip()
                if len(first) < 25 or len(first) > 200: continue
                if name.lower() in first.lower(): continue
                q = f"Which function or class {first[0].lower()+first[1:]}"
                qs.append({"q": q, "fact": name})
    random.Random(0).shuffle(qs)
    seen = set(); out = []
    for it in qs:
        if it["fact"] in seen: continue
        seen.add(it["fact"]); out.append(it)
        if len(out) >= n: break
    return out

def bootstrap_ci(hits, nb=1000):
    if not hits: return (None, None, None)
    rng = random.Random(0); N = len(hits); ms = []
    for _ in range(nb):
        ms.append(sum(hits[rng.randrange(N)] for _ in range(N))/N)
    ms.sort()
    return (round(statistics.mean(hits), 4),
            round(ms[int(0.025*nb)], 4),
            round(ms[int(0.975*nb)], 4))

# --- metric functions ---
def m1_substring(chunks_list, fact):
    return fact.lower() in "\n".join(chunks_list).lower()

_defre_cache = {}
def m2_defline(chunks_list, fact):
    if fact not in _defre_cache:
        _defre_cache[fact] = re.compile(r"(?:def|class)\s+" + re.escape(fact) + r"\b")
    pat = _defre_cache[fact]
    return any(pat.search(c) for c in chunks_list)

# --- main sweep function ---
def run_sweep(repo_paths, n_per_repo, k, bootstrap, max_chunks, embed_model, sem_threshold, out_path):
    print(f"\n{'='*60}")
    print(f"model={embed_model}  thresh={sem_threshold}  max_chunks={max_chunks}")
    print(f"{'='*60}", flush=True)

    repos = repo_paths  # dict: name -> path
    corpus = {n: load_repo_text(p) for n, p in repos.items()}
    chunks_map = {n: chunk(corpus[n]) for n in corpus}
    bm25_map = {n: BM25(chunks_map[n]) for n in corpus}

    print(f"embedding (model={embed_model})...", flush=True)
    sem_map = {n: SemanticRetriever(chunks_map[n], model_name=embed_model, max_chunks=max_chunks)
               for n in corpus}

    # reuse the same model instance for m3 fact embeddings
    model_inst = sem_map[list(sem_map)[0]]._model

    Q = []
    for n, p in repos.items():
        for it in mine_conceptual(p, n_per_repo):
            if it["fact"].lower() in corpus[n].lower():
                it["project"] = n
                Q.append(it)
    print(f"N={len(Q)} questions across {list(repos.keys())}", flush=True)

    # precompute fact embeddings for m3
    facts = [q["fact"] for q in Q]
    fact_emb = dict(zip(facts, model_inst.embed([f"definition of {f}" for f in facts])))

    def retrieve(arm, q):
        p = q["project"]
        return bm25_map[p].topk(q["q"], k) if arm == "bm25" else sem_map[p].topk(q["q"], k)

    def score_all(arm):
        h1, h2, h3 = [], [], []
        for q in Q:
            ch = retrieve(arm, q)
            fact = q["fact"]
            s1 = m1_substring(ch, fact)
            s2 = m2_defline(ch, fact)
            if s1:
                s3 = True
            else:
                ce = list(model_inst.embed(ch))
                fe = fact_emb[fact]
                s3 = any(_cos(fe, c) >= sem_threshold for c in ce)
            h1.append(int(s1)); h2.append(int(s2)); h3.append(int(s3))
        return h1, h2, h3

    result = {
        "N": len(Q), "k": k, "max_chunks": max_chunks,
        "embed_model": embed_model, "sem_threshold": sem_threshold,
        "repos": list(repos.keys()),
        "metrics_explained": {
            "m1": "substring anywhere (favors lexical)",
            "m2": "def/class defline (stricter, neither favored)",
            "m3": f"substring OR semantic-credit cos>={sem_threshold} (favors semantic)"
        },
        "arms": {}
    }

    print("scoring arms...", flush=True)
    for arm in ("bm25", "semantic"):
        h1, h2, h3 = score_all(arm)
        result["arms"][arm] = {
            "m1_substring": bootstrap_ci(h1, bootstrap),
            "m2_defline":   bootstrap_ci(h2, bootstrap),
            "m3_sem_credit": bootstrap_ci(h3, bootstrap),
        }

    # print summary
    print(f"\n{'metric':<18}{'bm25 [CI]':>30}{'semantic [CI]':>30}")
    for m in ("m1_substring", "m2_defline", "m3_sem_credit"):
        b = result["arms"]["bm25"][m]
        s = result["arms"]["semantic"][m]
        print(f"{m:<18}{f'{b[0]} [{b[1]},{b[2]}]':>30}{f'{s[0]} [{s[1]},{s[2]}]':>30}")

    with open(out_path, "w") as f:
        json.dump(result, f, indent=1)
    print(f"wrote {out_path}")
    return result

# ── Cell 5: run all three sweeps ──────────────────────────────────────────────

REPOS = {
    "requests": "/tmp/requests",
    "click":    "/tmp/click",
    "black":    "/tmp/black",
}
N_PER_REPO = 80   # 80 x 3 repos = 240 total (matches Kaggle N=240 run in CURRENT_STATE.md)
K = 6
BOOTSTRAP = 1000
MAX_CHUNKS = 100000  # full corpus -- the key variable under test

OUT_DIR = "/kaggle/working"  # outputs land here; download after run

results = {}

# Sweep 1: bge-base at full corpus (tests: does gap disappear with a larger model?)
results["bge_base"] = run_sweep(
    REPOS, N_PER_REPO, K, BOOTSTRAP, MAX_CHUNKS,
    embed_model="BAAI/bge-base-en-v1.5",
    sem_threshold=0.72,
    out_path=os.path.join(OUT_DIR, "SWEEP_bge_base_full.json"),
)

# Sweep 2: bge-small, threshold=0.65 (tests: is m3 conclusion sensitive to threshold?)
results["thresh_065"] = run_sweep(
    REPOS, N_PER_REPO, K, BOOTSTRAP, MAX_CHUNKS,
    embed_model="BAAI/bge-small-en-v1.5",
    sem_threshold=0.65,
    out_path=os.path.join(OUT_DIR, "SWEEP_threshold_0.65.json"),
)

# Sweep 3: bge-small, threshold=0.80 (upper bound of threshold sensitivity range)
results["thresh_080"] = run_sweep(
    REPOS, N_PER_REPO, K, BOOTSTRAP, MAX_CHUNKS,
    embed_model="BAAI/bge-small-en-v1.5",
    sem_threshold=0.80,
    out_path=os.path.join(OUT_DIR, "SWEEP_threshold_0.80.json"),
)

# ── Cell 6: summary table ─────────────────────────────────────────────────────
print("\n\n=== FINAL SUMMARY (all gaps should be within overlapping CIs at full corpus) ===")
for label, r in results.items():
    print(f"\n{label}  N={r['N']}  model={r['embed_model']}  thresh={r['sem_threshold']}")
    for m in ("m1_substring", "m2_defline", "m3_sem_credit"):
        b = r["arms"]["bm25"][m]
        s = r["arms"]["semantic"][m]
        gap = round(b[0] - s[0], 4)
        overlap = b[1] <= s[2] and s[1] <= b[2]
        print(f"  {m:<20} BM25={b[0]} sem={s[0]}  gap={gap}  CI_overlap={'YES' if overlap else 'NO -- INVESTIGATE'}")

print("\nDone. Download SWEEP_*.json from /kaggle/working and commit to benchmark/.")
