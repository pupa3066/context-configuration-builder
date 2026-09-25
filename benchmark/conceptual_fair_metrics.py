#!/usr/bin/env python3
"""conceptual_fair_metrics.py - RE-TEST of the semantic-vs-lexical finding under FAIRER scoring
metrics, to address caveat #4 (the original 'answerable = substring present anywhere' metric
structurally favors lexical/BM25, because the ground truth IS a token string).

DOES NOT change or overwrite the original runner (conceptual_semantic_vs_lexical.py) or its committed
results. This is an ADDITIONAL measurement. It reports THREE metrics side by side so a reviewer can see
whether 'lexical wins' survives a metric that no longer favors lexical:

  m1_substring   : original metric - fact string appears anywhere in retrieved chunks (favors lexical).
  m2_defline     : STRICTER - fact appears on a 'def <fact>' / 'class <fact>' line (surfaced the actual
                   DEFINITION, not just any mention). Harder for pure string-spraying.
  m3_sem_credit  : FAVORS SEMANTIC - counts a hit if the fact string is present OR any retrieved chunk
                   is highly cosine-similar to the fact's own definition text (semantic match without
                   the exact token). This actively removes the anti-semantic bias.

If lexical still wins under m2 and m3, the finding is robust to the metric-bias critique.
Reuses the exact retrievers/corpus/question-mining from the committed runner (import), so only the
SCORING differs. Query = question only (no fact leak), same as the original. CPU-only.
"""
from __future__ import annotations
import os, sys, re, json, argparse, statistics, random

HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import conceptual_semantic_vs_lexical as base   # reuse load_repo_text, mine_conceptual, bootstrap_ci
from compare_algorithms import chunk, BM25
from semantic_retriever import SemanticRetriever, available as sem_available

def m1_substring(chunks_list, fact):
    return fact.lower() in "\n".join(chunks_list).lower()

_defre=lambda fact: re.compile(r"(?:def|class)\s+"+re.escape(fact)+r"\b")
def m2_defline(chunks_list, fact):
    pat=_defre(fact)
    return any(pat.search(c) for c in chunks_list)

def _cos(a,b):
    import math
    d=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return d/(na*nb) if na and nb else 0.0

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repos",nargs="+",required=True)
    ap.add_argument("--n-per-repo",type=int,default=50)
    ap.add_argument("--k",type=int,default=6)
    ap.add_argument("--bootstrap",type=int,default=1000)
    ap.add_argument("--max-chunks",type=int,default=1200,dest="max_chunks")
    ap.add_argument("--embed-model",default="BAAI/bge-small-en-v1.5",dest="embed_model",
                    help="fastembed model for the semantic arm. Default bge-small (original). "
                         "Try BAAI/bge-base-en-v1.5 or jinaai/jina-embeddings-v2-base-en to test "
                         "whether the lexical>semantic finding survives a stronger/larger embedder.")
    ap.add_argument("--out",default="conceptual_fair_results.json")
    ap.add_argument("--sem-threshold",type=float,default=0.72,dest="sem_threshold",
                    help="cosine cutoff for the m3 semantic-credit hit (default 0.72). Sweep "
                         "0.65 to 0.80 to show the lexical-vs-semantic conclusion is stable "
                         "and not driven by this threshold choice.")
    a=ap.parse_args()
    if not sem_available():
        print("fastembed unavailable"); sys.exit(1)

    repos=dict(p.split(":",1) for p in a.repos)
    corpus={n:base.load_repo_text(p) for n,p in repos.items()}
    chunks={n:chunk(corpus[n]) for n in corpus}
    bm25={n:BM25(chunks[n]) for n in corpus}
    print(f"embedding (model={a.embed_model}, max_chunks/repo={a.max_chunks})...",flush=True)
    sem={n:SemanticRetriever(chunks[n],model_name=a.embed_model,max_chunks=a.max_chunks) for n in corpus}
    model=sem[list(sem)[0]]._model  # reuse the embedding model for m3 semantic-credit

    Q=[]
    for n,p in repos.items():
        for it in base.mine_conceptual(p,a.n_per_repo):
            if it["fact"].lower() in corpus[n].lower():
                it["project"]=n; Q.append(it)
    print(f"N={len(Q)} conceptual questions (query=question only)")

    # precompute fact-definition embeddings for m3 (the semantic-credit reference)
    facts=[q["fact"] for q in Q]
    fact_emb=dict(zip(facts, model.embed([f"definition of {f}" for f in facts])))

    def retrieve(arm,q):
        p=q["project"]
        return bm25[p].topk(q["q"],a.k) if arm=="bm25" else sem[p].topk(q["q"],a.k)

    def score_all(arm):
        h1=[];h2=[];h3=[]
        for q in Q:
            ch=retrieve(arm,q); fact=q["fact"]
            s1=m1_substring(ch,fact); s2=m2_defline(ch,fact)
            # m3: substring OR a retrieved chunk cosine-similar to the fact definition
            if s1: s3=True
            else:
                ce=list(model.embed(ch)); fe=fact_emb[fact]
                s3=any(_cos(fe,c)>=a.sem_threshold for c in ce)   # m3 semantic-credit cutoff (--sem-threshold)
            h1.append(int(s1));h2.append(int(s2));h3.append(int(s3))
        return h1,h2,h3

    out={"N":len(Q),"k":a.k,"max_chunks":a.max_chunks,"embed_model":a.embed_model,"sem_threshold":a.sem_threshold,
         "metrics_explained":{"m1":"substring anywhere (favors lexical)",
                              "m2":"def/class defline (stricter)",
                              "m3":f"substring OR semantic-credit cos>={a.sem_threshold} (favors semantic)"},
         "arms":{}}
    for arm in ("bm25","semantic"):
        h1,h2,h3=score_all(arm)
        out["arms"][arm]={
            "m1_substring":base.bootstrap_ci(h1,a.bootstrap),
            "m2_defline":base.bootstrap_ci(h2,a.bootstrap),
            "m3_sem_credit":base.bootstrap_ci(h3,a.bootstrap)}
    print(f"\n{'metric':<16}{'bm25 [CI]':>26}{'semantic [CI]':>26}")
    for m in ("m1_substring","m2_defline","m3_sem_credit"):
        b=out["arms"]["bm25"][m]; s=out["arms"]["semantic"][m]
        print(f"{m:<16}{f'{b[0]} [{b[1]},{b[2]}]':>26}{f'{s[0]} [{s[1]},{s[2]}]':>26}")
    json.dump(out,open(a.out,"w"),indent=1)
    print(f"\nwrote {a.out}  (original results untouched; this is an ADDITIONAL fair-metric re-test)")

if __name__=="__main__":
    main()
