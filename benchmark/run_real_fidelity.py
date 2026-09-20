#!/usr/bin/env python3
"""run_real_fidelity.py — fidelity benchmark on REAL ground-truth questions (not synthetic).

Fixes the two validity flaws of run_fidelity.py:
  (1) REAL gpt2 BPE token counts (not len//4).
  (2) Needed-facts are Pupa's real Q/A (oracle-defined, independent of the summarizer),
      and retention is measured two ways so it is not circular with the keep-code operator:
        - token_present:       every fact string appears somewhere in the compressed text.
        - answerable_in_ctx:   every fact appears on a line ALSO containing a question keyword
                               (co-location = the fact is still usable to answer, not a stray token).

PRESENCE GATE: a question is scored for fidelity ONLY if its facts are present in the FULL
(uncompressed) project context. Otherwise it is flagged not_in_source and excluded from the
fidelity denominator (that is corpus coverage, not summarization loss).

RECENT-STATE: category == "recent" is reported SEPARATELY (its ground truth is dynamic session
state, not stable doc context) so it does not contaminate the summarization-fidelity number.

Requires: transformers (gpt2 tokenizer, offline OK). Uses summarize() from summarized_tier.py.
Reads questions_real.local.json (PRIVATE; may contain patent-track answers -> never publish values).
Output: prints aggregate retention vs token_saving per compression level; writes a PRIVATE results
file with per-id booleans only (no answer values), safe to keep locally.
"""
from __future__ import annotations
import os, sys, json, glob, re, statistics, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "research", "harness"))
from summarized_tier import summarize  # noqa: E402

from transformers import AutoTokenizer
_tok = AutoTokenizer.from_pretrained("gpt2")
def ntok(s: str) -> int: return len(_tok.encode(s))

_WORD = re.compile(r"[A-Za-z0-9]+")

def read(p: str) -> str:
    return open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""

def load_full_context(root: str, rels: list) -> str:
    parts = []
    for rel in rels:
        p = os.path.join(root, rel)
        t = read(p)
        if t:
            parts.append(f"\n\n===== {rel} =====\n{t}")
    # CONTEXT IS NOT JUST DOCS: include .kiro/steering, tracked text/code, and git history —
    # anything the agent can actually retrieve to answer a question (per Pupa: a log item counts).
    import subprocess
    def _git(args):
        try:
            return subprocess.run(["git", "-C", root] + args, capture_output=True,
                                  text=True, timeout=15).stdout
        except Exception:
            return ""
    # git log (all branches) + reflog + stash: recent-state / decision facts live here
    parts.append("\n\n===== git log --all =====\n" + _git(["log", "--all", "--oneline", "-n", "400"]))
    parts.append("\n\n===== git reflog =====\n" + _git(["reflog", "-n", "200"]))
    # tracked text/code files (bounded) — code comments/configs are context too
    tracked = _git(["ls-files"]).splitlines()
    exts = (".md", ".py", ".txt", ".yaml", ".yml", ".toml", ".cff", ".json", ".tex", ".sh")
    for rel in tracked:
        if rel.endswith(exts) and rel not in rels:
            fp = os.path.join(root, rel)
            try:
                if os.path.getsize(fp) < 200_000:
                    t = read(fp)
                    if t:
                        parts.append(f"\n\n===== {rel} =====\n{t}")
            except OSError:
                pass
    return "".join(parts)

def fact_present(text: str, fact: str) -> bool:
    # case-insensitive substring; facts are distinctive identifiers/numbers
    return fact.lower() in text.lower()

def answerable(text: str, fact: str, q_keywords: set) -> bool:
    """fact appears on a line that also contains at least one question keyword -> usable in context."""
    fl = fact.lower()
    for line in text.splitlines():
        ll = line.lower()
        if fl in ll:
            line_words = set(_WORD.findall(ll))
            if q_keywords & line_words:
                return True
    return False

STOP = set("the a an of to in on for and or is are was were be by with vs at as it its this that what which who whose how many each give state per".split())
def q_keywords(q: str) -> set:
    return {w for w in (x.lower() for x in _WORD.findall(q)) if w not in STOP and len(w) > 2}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="0.0,0.33,0.5,0.66")
    ap.add_argument("--questions", default=os.path.join(HERE, "questions_real.local.json"))
    a = ap.parse_args()
    levels = [float(x) for x in a.levels.split(",")]
    cfg = json.load(open(a.questions))
    roots = cfg["source_roots"]; sources = cfg["sources"]

    # build full context per project once
    full_ctx = {proj: load_full_context(roots[proj], sources[proj]) for proj in roots}
    full_tok = {proj: ntok(full_ctx[proj]) for proj in full_ctx}

    stable = [q for q in cfg["questions"] if q["category"] != "recent"]
    recent = [q for q in cfg["questions"] if q["category"] == "recent"]

    # PRESENCE GATE on full context
    testable, not_in_source = [], []
    for q in stable:
        ctx = full_ctx[q["project"]]
        if all(fact_present(ctx, f) for f in q["facts"]):
            testable.append(q)
        else:
            missing = [f for f in q["facts"] if not fact_present(ctx, f)]
            not_in_source.append((q["id"], q["project"], missing))

    print(f"real-fidelity: {len(cfg['questions'])} questions | stable={len(stable)} recent={len(recent)}")
    print(f"presence gate: testable(fact in FULL ctx)={len(testable)}  not_in_source={len(not_in_source)}")
    if not_in_source:
        print("  not_in_source (id, project, missing facts) — excluded from fidelity denominator:")
        for i, p, m in not_in_source:
            print(f"    #{i:<2} {p:<26} missing={m}")

    # summarize project contexts per level, measure retention on testable questions
    print("\n=== REAL-QUESTION FIDELITY (retention vs token_saving; real gpt2 tokens) ===")
    print(f"{'level':>6} {'tok_saving':>11} {'token_present':>14} {'answerable':>11} {'safe(ans=1.0)':>14}")
    per_id_records = {}
    for lv in levels:
        summ = {proj: (full_ctx[proj] if lv <= 0 else summarize(full_ctx[proj], lv)) for proj in full_ctx}
        summ_tok = {proj: ntok(summ[proj]) for proj in summ}
        savings = [1 - summ_tok[p] / max(1, full_tok[p]) for p in summ]
        tok_hits, ans_hits = [], []
        for q in testable:
            ctx = summ[q["project"]]
            kw = q_keywords(q["q"]) | {f.lower() for f in q["facts"]}
            tp = all(fact_present(ctx, f) for f in q["facts"])
            an = all(answerable(ctx, f, kw) for f in q["facts"])
            tok_hits.append(tp); ans_hits.append(an)
            per_id_records.setdefault(q["id"], {})[str(lv)] = {"token_present": tp, "answerable": an}
        tp_ret = round(sum(tok_hits) / len(tok_hits), 4) if tok_hits else None
        an_ret = round(sum(ans_hits) / len(ans_hits), 4) if ans_hits else None
        save = round(statistics.mean(savings), 4)
        print(f"{lv:6.2f} {save:11.4f} {tp_ret:14.4f} {an_ret:11.4f} {str(an_ret==1.0):>14}")

    # write PRIVATE results (booleans only, no answer values)
    out = {"n_total": len(cfg["questions"]), "n_stable": len(stable), "n_recent": len(recent),
           "n_testable": len(testable), "not_in_source_ids": [i for i,_,_ in not_in_source],
           "levels": levels, "per_id": per_id_records,
           "note": "PRIVATE. Booleans only, no answer values. token_present=weak, answerable_in_ctx=strong."}
    outp = os.path.join(HERE, "real_fidelity_results.local.json")
    json.dump(out, open(outp, "w"), indent=1)
    print(f"\nRecent-state questions (scored separately, dynamic ground truth): {[q['id'] for q in recent]}")
    print(f"private results written: {os.path.relpath(outp, ROOT)} (booleans only)")

if __name__ == "__main__":
    main()
