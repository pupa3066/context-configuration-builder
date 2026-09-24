#!/usr/bin/env python3
"""conceptual_semantic_vs_lexical.py - the decisive test: does lexical retrieval beat semantic
embedding retrieval on CONCEPTUAL questions about code, at powered scale?

FIXES a confound in compare_algorithms_scaled.py: that script's retrieval query included the
ground-truth fact ("q + facts"), which trivially favors lexical string-match. Here the retrieval
QUERY IS THE QUESTION ONLY - the retriever never sees the answer, like a real agent. The fact is used
ONLY for scoring (did the retrieved chunk contain it), never for retrieval.

CONCEPTUAL questions at scale: mined from function/class DOCSTRINGS in the public repos. A docstring's
first sentence becomes a natural-language question; the ground-truth fact = the symbol name (verifiably
present in the code). These are genuinely conceptual (worded in prose, not the symbol), which is where
semantic retrieval SHOULD win if it ever does - the fair test of the contrarian claim.

Arms: bm25 (lexical) vs semantic (fastembed bge-small cosine), both top-k, query=question only.
Scoring: answerable-in-context = ground-truth symbol present in the retrieved chunks. Bootstrap CI.
CPU-only. Reuses chunk/BM25/ntok from compare_algorithms; SemanticRetriever from semantic_retriever.
"""
from __future__ import annotations
import os, sys, re, ast, glob, json, random, argparse, statistics

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from compare_algorithms import chunk, BM25, ntok, read
from semantic_retriever import SemanticRetriever, available as sem_available

def load_repo_text(path):
    parts=[]
    for f in glob.glob(os.path.join(path,"**","*.py"), recursive=True):
        try:
            if os.path.getsize(f)<200_000: parts.append(read(f))
        except OSError: pass
    return "\n".join(parts)

def mine_conceptual(path, n):
    """Extract (question, symbol) from docstringed defs/classes. Question = first docstring sentence
    (prose, conceptual); fact = the symbol name. Only keeps items where the docstring does NOT contain
    the symbol name (so the question is genuinely conceptual, not a giveaway)."""
    qs=[]
    for f in glob.glob(os.path.join(path,"**","*.py"), recursive=True):
        try:
            if os.path.getsize(f)>200_000: continue
            tree=ast.parse(read(f))
        except Exception: continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                doc=ast.get_docstring(node)
                if not doc: continue
                name=node.name
                if len(name)<4 or name.startswith("_"): continue
                first=re.split(r"(?<=[.!?])\s", doc.strip())[0].strip()
                if len(first)<25 or len(first)>200: continue
                if name.lower() in first.lower(): continue      # not a giveaway -> genuinely conceptual
                q=f"Which function or class {first[0].lower()+first[1:]}"
                qs.append({"q": q, "fact": name})
    random.Random(0).shuffle(qs)
    # dedup by fact
    seen=set(); out=[]
    for it in qs:
        if it["fact"] in seen: continue
        seen.add(it["fact"]); out.append(it)
        if len(out)>=n: break
    return out

_W=re.compile(r"[A-Za-z0-9_]+")
def answerable(chunks_text, fact):
    return fact.lower() in chunks_text.lower()

def bootstrap_ci(hits,nb=1000):
    if not hits: return (None,None,None)
    rng=random.Random(0); N=len(hits); ms=[]
    for _ in range(nb):
        ms.append(sum(hits[rng.randrange(N)] for _ in range(N))/N)
    ms.sort()
    return (round(statistics.mean(hits),4), round(ms[int(0.025*nb)],4), round(ms[int(0.975*nb)],4))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repos",nargs="+",required=True)
    ap.add_argument("--n-per-repo",type=int,default=60)
    ap.add_argument("--k",type=int,default=6)
    ap.add_argument("--bootstrap",type=int,default=1000)
    ap.add_argument("--max-chunks",type=int,default=1200,dest="max_chunks",
                    help="chunks indexed per repo for the semantic arm (raise on 16GB Kaggle, e.g. 5000)")
    ap.add_argument("--out",default="conceptual_results.json")
    a=ap.parse_args()
    if not sem_available():
        print("fastembed unavailable - cannot run semantic arm. Install fastembed."); sys.exit(1)

    repos=dict(p.split(":",1) for p in a.repos)
    corpus={n:load_repo_text(p) for n,p in repos.items()}
    chunks={n:chunk(corpus[n]) for n in corpus}
    bm25={n:BM25(chunks[n]) for n in corpus}
    print(f"embedding chunks (one-time; max_chunks/repo={a.max_chunks})...", flush=True)
    sem={n:SemanticRetriever(chunks[n], max_chunks=a.max_chunks) for n in corpus}
    for n in sem:
        print(f"  {n}: {len(chunks[n])} chunks -> indexed {sem[n].n_indexed}"
              f"{' (CAPPED)' if sem[n].capped else ' (full)'}", flush=True)

    # build conceptual questions; presence-gate on the fact being in the corpus
    Q=[]
    for n,p in repos.items():
        for it in mine_conceptual(p, a.n_per_repo):
            if it["fact"].lower() in corpus[n].lower():
                it["project"]=n; Q.append(it)
    print(f"conceptual questions (query=question ONLY, no fact leak): N={len(Q)} across {list(repos)}")

    K=a.k
    def run_arm(which):
        hits=[]
        for q in Q:
            p=q["project"]
            # QUERY = QUESTION ONLY - retriever never sees the answer
            if which=="bm25": ctx="\n".join(bm25[p].topk(q["q"],K))
            else: ctx="\n".join(sem[p].topk(q["q"],K))
            hits.append(1 if answerable(ctx,q["fact"]) else 0)
        return hits, bootstrap_ci(hits,a.bootstrap)

    bm_hits,bm_ci=run_arm("bm25")
    sm_hits,sm_ci=run_arm("semantic")
    # paired: on how many did they differ / each win
    bm_only=sum(1 for b,s in zip(bm_hits,sm_hits) if b and not s)
    sm_only=sum(1 for b,s in zip(bm_hits,sm_hits) if s and not b)

    print(f"\n=== SEMANTIC vs LEXICAL on CONCEPTUAL questions (query=question only, top-k={K}, N={len(Q)}) ===")
    print(f"{'arm':<12}{'answerable [95% CI]':>28}")
    print(f"{'bm25':<12}{f'{bm_ci[0]} [{bm_ci[1]}, {bm_ci[2]}]':>28}")
    print(f"{'semantic':<12}{f'{sm_ci[0]} [{sm_ci[1]}, {sm_ci[2]}]':>28}")
    print(f"\npaired: bm25-only wins={bm_only}  semantic-only wins={sm_only}  (McNemar-style split)")
    verdict=("LEXICAL wins" if bm_ci[0]>sm_ci[0] else "SEMANTIC wins" if sm_ci[0]>bm_ci[0] else "TIE")
    print(f"VERDICT: {verdict} on conceptual code questions at N={len(Q)}")
    json.dump({"N":len(Q),"k":K,"query":"question_only_no_fact_leak",
               "max_chunks_per_repo":a.max_chunks,
               "indexed":{n:{"chunks":len(chunks[n]),"indexed":sem[n].n_indexed,"capped":sem[n].capped} for n in sem},
               "bm25":{"answerable":bm_ci[0],"ci95":[bm_ci[1],bm_ci[2]]},
               "semantic":{"answerable":sm_ci[0],"ci95":[sm_ci[1],sm_ci[2]]},
               "paired":{"bm25_only":bm_only,"semantic_only":sm_only},
               "verdict":verdict,
               "note":"conceptual (docstring-mined) questions; answerable-in-context proxy NOT task success"},
              open(a.out,"w"),indent=1)
    print(f"wrote {a.out}")

if __name__=="__main__":
    main()
