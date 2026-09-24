#!/usr/bin/env python3
"""compare_algorithms_scaled.py - POWERED version of the context-algorithm comparison.

Turns the N=44 pilot (compare_algorithms.py, private questions) into a reproducible, PUBLIC-corpus
study with larger N, a k-sweep, and bootstrap confidence intervals - the "scale it up" step.

WHAT THIS ADDS over the pilot:
  1. PUBLIC corpus: clones open-source repos (no private/patent data) so anyone can reproduce.
  2. LARGER N: auto-generates identifier-dense questions from the code (verifiable ground truth =
     the symbol's own definition line), plus optional curated questions from a public JSON.
  3. k-SWEEP: runs retrieval/hybrid at multiple top-k to show the token/fidelity frontier.
  4. BOOTSTRAP CIs: every answerable rate reported with a 95% CI, so results are POWERED not pilot.

HONESTY: this measures token-cost + answerable-in-context (a co-location proxy), NOT task success.
Auto-generated questions are identifier-recall by construction; label them as such. Reuses the pilot's
BM25 / semantic / summarize logic (imported) so the method is identical, only the scale changes.

Runs CPU-only for BM25 + tokens (no GPU needed); semantic arm needs fastembed (optional).

USAGE (local or Kaggle):
  # clone a few public repos first (example):
  #   git clone --depth 1 https://github.com/psf/requests
  python compare_algorithms_scaled.py --repos requests:./requests flask:./flask \
      --n-auto 150 --k-sweep 3,6,10 --bootstrap 1000 --out scaled_results.json
"""
from __future__ import annotations
import os, sys, json, re, random, argparse, statistics, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# reuse the pilot's identical method code (single source of truth)

try:
    from compare_algorithms import chunk, BM25, fact_present, answerable, q_keywords, ntok, read
except Exception as e:
    print("ERROR importing pilot helpers from compare_algorithms.py:", e, file=sys.stderr)
    raise

_SYM = re.compile(r"(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]{3,})")

def load_repo_text(path):
    parts=[]
    for f in glob.glob(os.path.join(path,"**","*.py"), recursive=True):
        try:
            if os.path.getsize(f) < 200_000:
                parts.append(read(f))
        except OSError: pass
    return "\n".join(parts)

def auto_questions(text, n):
    """Generate identifier-recall questions with VERIFIABLE ground truth: for a def/class symbol,
    the question asks 'what is defined as <symbol>' and the fact is the symbol string itself, which
    must appear in the code. This is identifier-dense by construction (the regime semantic retrieval
    struggled with in the pilot). Labeled auto/identifier."""
    syms = list(dict.fromkeys(_SYM.findall(text)))  # unique, ordered
    random.Random(0).shuffle(syms)
    out=[]
    for s in syms[:n]:
        out.append({"q": f"Which function or class is named {s} and where is it defined?",
                    "facts": [s], "category": "auto_identifier"})
    return out

def bootstrap_ci(hits, n_boot=1000):
    """95% bootstrap CI on the mean of a 0/1 list."""
    if not hits: return (None, None, None)
    rng=random.Random(0); N=len(hits); means=[]
    for _ in range(n_boot):
        s=sum(hits[rng.randrange(N)] for _ in range(N))
        means.append(s/N)
    means.sort()
    return (round(statistics.mean(hits),4),
            round(means[int(0.025*n_boot)],4),
            round(means[int(0.975*n_boot)],4))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="+", required=True, help="name:path pairs of PUBLIC repos")
    ap.add_argument("--n-auto", type=int, default=150, help="auto identifier questions per repo")
    ap.add_argument("--curated", default=None, help="optional public JSON of curated questions")
    ap.add_argument("--k-sweep", default="3,6,10")
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--out", default="scaled_results.json")
    a=ap.parse_args()

    repos={}
    for pair in a.repos:
        name,path=pair.split(":",1); repos[name]=path
    corpus={n: load_repo_text(p) for n,p in repos.items()}
    corpus_tok={n: ntok(corpus[n]) for n in corpus}
    chunks={n: chunk(corpus[n]) for n in corpus}
    bm25={n: BM25(chunks[n]) for n in corpus}

    # build questions: auto identifier + optional curated
    questions=[]
    for n,txt in corpus.items():
        for q in auto_questions(txt, a.n_auto):
            q["project"]=n; questions.append(q)
    if a.curated and os.path.exists(a.curated):
        for q in json.load(open(a.curated)).get("questions",[]):
            questions.append(q)
    # presence gate
    testable=[q for q in questions if all(fact_present(corpus[q["project"]],f) for f in q["facts"])]
    print(f"scaled: repos={list(repos)} corpus_tok={corpus_tok} N_testable={len(testable)}")

    ks=[int(x) for x in a.k_sweep.split(",")]
    results={}
    def inj(algo,q,K):
        p=q["project"]; body=corpus[p]
        if algo=="monolithic": return body
        if algo=="summarized_L0.5":
            from compare_algorithms import summarize; return summarize(body,0.5)
        if algo=="retrieval_bm25": return "\n".join(bm25[p].topk(q["q"]+" "+" ".join(q["facts"]),K))
        if algo=="no_context": return ""
        raise ValueError(algo)

    # no_context baseline (for lift), monolithic, summarized, and BM25 at each k
    def eval_algo(algo,K=6):
        hits=[]
        for q in testable:
            ctx=inj(algo,q,K); kw=q_keywords(q["q"])|{f.lower() for f in q["facts"]}
            hits.append(1 if all(answerable(ctx,f,kw) for f in q["facts"]) else 0)
        m,lo,hi=bootstrap_ci(hits,a.bootstrap)
        toks=round(statistics.mean([ntok(inj(algo,q,K)) for q in testable]),0)
        return {"answerable":m,"ci95":[lo,hi],"avg_tokens":toks}

    results["no_context"]=eval_algo("no_context")
    results["monolithic"]=eval_algo("monolithic")
    results["summarized_L0.5"]=eval_algo("summarized_L0.5")
    for K in ks:
        results[f"retrieval_bm25_k{K}"]=eval_algo("retrieval_bm25",K)

    print(f"\n{'algorithm':<22}{'answerable [95% CI]':>26}{'avg_tokens':>12}")
    for name,r in results.items():
        ci=f"{r['answerable']} [{r['ci95'][0]}, {r['ci95'][1]}]"
        print(f"{name:<22}{ci:>26}{r['avg_tokens']:>12.0f}")
    base=results["no_context"]["answerable"]
    print(f"\nno_context baseline answerable = {base} (lift over this is the real signal)")
    json.dump({"n_testable":len(testable),"corpus_tok":corpus_tok,"bootstrap":a.bootstrap,
               "results":results,"note":"identifier-recall auto questions; token-cost + answerable "
               "proxy, NOT task success; lift over no_context is the signal"},
              open(a.out,"w"),indent=1)
    print(f"\nwrote {a.out}")

if __name__=="__main__":
    main()
