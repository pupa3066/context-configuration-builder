#!/usr/bin/env python3
"""compare_algorithms.py - head-to-head of context algorithms for a RESEARCH agent.

Same corpus, same 50 real questions, both axes measured consistently:
  - per-turn tokens: what the agent actually injects to answer THAT question (real gpt2 BPE).
  - answerable retention: fraction of testable questions whose ground-truth facts are still
    answerable-in-context (fact co-located with a question keyword) in the injected context.

ALGORITHMS
  monolithic         : inject the full project corpus every turn (baseline).
  tiered_lossless    : inject an always-on header (rules+metadata proxy) + the full body only
                       for the active project (deferral, no compression).
  summarized_L{lv}   : inject summarize(full corpus, lv) every turn (lossy compression).
  retrieval_top{k}   : chunk the corpus; inject only the top-k chunks scored against the question
                       (BM25-lite: idf-weighted term overlap). No always-on body.
  hybrid_top{k}      : always-on header + top-k retrieved chunks from the active project body.

Per-turn token cost is computed PER QUESTION (retrieval/hybrid vary by question), then averaged.
Real gpt2 tokenizer. Recent-state questions excluded (dynamic ground truth). PRIVATE inputs.
"""
from __future__ import annotations
import os, sys, json, re, math, statistics, argparse
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "research", "harness"))
from summarized_tier import summarize  # noqa: E402
from transformers import AutoTokenizer
_tok = AutoTokenizer.from_pretrained("gpt2")
def ntok(s): return len(_tok.encode(s))

_WORD = re.compile(r"[A-Za-z0-9_.\-]+")
STOP = set("the a an of to in on for and or is are was were be by with vs at as it its this that what which who whose how many each give state per module does".split())

def read(p): return open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""

def build_corpus(root, rels):
    import subprocess
    parts = []
    for rel in rels:
        t = read(os.path.join(root, rel))
        if t: parts.append(t)
    def _git(a):
        try: return subprocess.run(["git","-C",root]+a,capture_output=True,text=True,timeout=15).stdout
        except Exception: return ""
    parts.append(_git(["log","--all","--oneline","-n","400"]))
    parts.append(_git(["reflog","-n","200"]))
    tracked=_git(["ls-files"]).splitlines()
    exts=(".md",".py",".txt",".yaml",".yml",".toml",".cff",".json",".tex",".sh")
    for rel in tracked:
        if rel.endswith(exts) and rel not in rels:
            fp=os.path.join(root,rel)
            try:
                if os.path.getsize(fp)<200_000:
                    t=read(fp)
                    if t: parts.append(t)
            except OSError: pass
    return "\n".join(parts)

def chunk(text, size_lines=8):
    lines=[l for l in text.splitlines()]
    return ["\n".join(lines[i:i+size_lines]) for i in range(0,len(lines),size_lines) if any(lines[i:i+size_lines])]

def toks(s): return [w.lower() for w in _WORD.findall(s) if w.lower() not in STOP and len(w)>2]

class BM25:
    def __init__(self, chunks):
        self.chunks=chunks; self.docs=[toks(c) for c in chunks]
        self.N=len(self.docs); self.avgdl=(sum(len(d) for d in self.docs)/self.N) if self.N else 1
        df=Counter()
        for d in self.docs:
            for w in set(d): df[w]+=1
        self.idf={w:math.log(1+(self.N-n+0.5)/(n+0.5)) for w,n in df.items()}
    def score(self,q,d):
        k1,b=1.5,0.75; dl=len(d); c=Counter(d); s=0.0
        for w in q:
            if w in c:
                idf=self.idf.get(w,0); tf=c[w]
                s+=idf*(tf*(k1+1))/(tf+k1*(1-b+b*dl/self.avgdl))
        return s
    def topk(self,query,k):
        q=toks(query)
        scored=sorted(range(self.N),key=lambda i:self.score(q,self.docs[i]),reverse=True)
        return [self.chunks[i] for i in scored[:k]]

def fact_present(text,f): return f.lower() in text.lower()
def q_keywords(q): return {w for w in toks(q)}
def answerable(text,fact,kw):
    fl=fact.lower()
    for line in text.splitlines():
        ll=line.lower()
        if fl in ll and (kw & set(w.lower() for w in _WORD.findall(ll))):
            return True
    return False

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--k",type=int,default=6)
    ap.add_argument("--questions",default=os.path.join(HERE,"questions_real.local.json"))
    a=ap.parse_args()
    cfg=json.load(open(a.questions)); roots=cfg["source_roots"]; sources=cfg["sources"]
    corpus={p:build_corpus(roots[p],sources[p]) for p in roots}
    corpus_tok={p:ntok(corpus[p]) for p in corpus}
    chunks={p:chunk(corpus[p]) for p in corpus}
    bm25={p:BM25(chunks[p]) for p in corpus}
    # semantic retriever (fastembed bge-small); skip arm entirely if unavailable (no false fallback)
    try:
        from semantic_retriever import SemanticRetriever, available as sem_available
    except Exception:
        sem_available=lambda:False
    SEM=sem_available()
    sem={p:SemanticRetriever(chunks[p]) for p in corpus} if SEM else {}
    # always-on header proxy = current live steering always-on (rules+registry+portfolio+bootstrap)
    header_tok=sum(ntok(read(os.path.expanduser(f"~/.kiro/steering/{f}")))
                   for f in ("00-rules.md","bootstrap.md","context-registry.md","portfolio.md"))

    stable=[q for q in cfg["questions"] if q["category"]!="recent"]
    # presence gate: fact must exist in full corpus
    testable=[q for q in stable if all(fact_present(corpus[q["project"]],f) for f in q["facts"])]

    K=a.k
    algos=["monolithic","tiered_lossless","summarized_L0.33","summarized_L0.5","summarized_L0.66",
           f"retrieval_top{K}",f"hybrid_top{K}"]
    if SEM:
        algos += [f"semantic_top{K}", f"hybrid_semantic_top{K}"]

    def injected(algo,q):
        p=q["project"]; body=corpus[p]
        if algo=="monolithic": return body, 0
        if algo=="tiered_lossless": return body, header_tok
        if algo.startswith("summarized_"):
            lv=float(algo.split("L")[1]); return summarize(body,lv), 0
        if algo.startswith("hybrid_semantic_top"):
            return "\n".join(sem[p].topk(q["q"]+" "+" ".join(q["facts"]),K)), header_tok
        if algo.startswith("semantic_top"):
            return "\n".join(sem[p].topk(q["q"]+" "+" ".join(q["facts"]),K)), 0
        if algo.startswith("retrieval_top"):
            return "\n".join(bm25[p].topk(q["q"]+" "+" ".join(q["facts"]),K)), 0
        if algo.startswith("hybrid_top"):
            return "\n".join(bm25[p].topk(q["q"]+" "+" ".join(q["facts"]),K)), header_tok
        raise ValueError(algo)

    print(f"corpus tokens/project: {corpus_tok}")
    print(f"always-on header (live steering): {header_tok} tok | testable Q: {len(testable)} | top-k={K}")
    print(f"\n{'algorithm':<20}{'avg tok/turn':>13}{'answerable':>12}{'safe>=0.95':>11}")
    print("-"*56)
    results={}
    for algo in algos:
        tks,ans=[],[]
        for q in testable:
            ctx,extra=injected(algo,q)
            tks.append(ntok(ctx)+extra)
            kw=q_keywords(q["q"])|{f.lower() for f in q["facts"]}
            ans.append(all(answerable(ctx,f,kw) for f in q["facts"]))
        at=round(statistics.mean(tks),0); ar=round(sum(ans)/len(ans),4)
        results[algo]={"avg_tokens":at,"answerable":ar}
        print(f"{algo:<20}{at:>13.0f}{ar:>12.4f}{str(ar>=0.95):>11}")

    # pick: min tokens among algos with answerable >= 0.95
    safe={k:v for k,v in results.items() if v["answerable"]>=0.95}
    best=min(safe,key=lambda k:safe[k]["avg_tokens"]) if safe else None
    print("-"*56)
    print(f"BEST (min tokens at answerable>=0.95): {best}" if best else "no algo reaches 0.95 answerable")
    if best:
        mono=results["monolithic"]["avg_tokens"]
        print(f"  {best}: {results[best]['avg_tokens']:.0f} tok/turn vs monolithic {mono:.0f} "
              f"= {100*(1-results[best]['avg_tokens']/mono):.1f}% reduction, answerable {results[best]['answerable']}")
    json.dump({"testable":len(testable),"k":K,"header_tok":header_tok,"results":results,
               "note":"PRIVATE; aggregate metrics only, no answer values"},
              open(os.path.join(HERE,"algo_comparison_results.local.json"),"w"),indent=1)
    print("private results: benchmark/algo_comparison_results.local.json")

if __name__=="__main__":
    main()
