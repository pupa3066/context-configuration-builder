"""eval_n6.py — N=6 measured fidelity comparison across the live 6-project deployment.

One question per active project; each question has a set of NEEDED FACTS that actually
appear in that project's source. For each question we measure, per condition:
  C1 monolithic  : full source (baseline)
  C2 lossless    : full body loaded on demand  (must equal C1 — null control)
  C4 summarized  : compressed body at levels 0.33 / 0.66 / 1.0  (fidelity-vs-token curve)

Reports grounding_retention (fraction of needed facts still present) and token_saving per
condition, plus the safe-compression frontier per question and aggregate.

Rule 6a/6b: MEASURED but PRELIMINARY — N=6 questions, keyword-based fact detection, single
compression operator, NO task-success (no agent run). It answers "does the context still
CONTAIN the needed facts", not "does the agent SOLVE better". Honest scope stated in output.
"""
import sys, re, json, statistics
sys.path.insert(0, "research/harness")
from summarized_tier import summarize, token_estimate
_T = re.compile(r"[A-Za-z_][A-Za-z0-9_\.]{3,}")

SRC = {
    "resume":    "/Users/pupa/Projects/personal-site/resume_abhilasha.md",
    "animevlog": "/Users/pupa/.kiro/skills/animevlog/SKILL.md",
    "apple-ml":  "/Users/pupa/.kiro/skills/apple-ml/SKILL.md",
    "photoback": "/Users/pupa/.kiro/skills/photoback/SKILL.md",
    "quant":     "/Users/pupa/Projects/quant-memorization-study/RESULTS_multimodel.md",
    "cck":       "/Users/pupa/Projects/consistent-context-kit/benchmark/TOKEN_COST_RESULTS.md",
}

# N=6 questions; needed facts are keywords that MUST survive for the answer to be grounded.
QUESTIONS = [
    ("Q1 my 10-year experience",        "resume",    ["TATA","Unisys","Cisco","Boulder","Engineer","Researcher"]),
    ("Q2 AnimeVlog img2anime fault",     "animevlog", ["VAE","SDXL","fp16","int4","LoRA","offloading"]),
    ("Q3 apple-ml what it does",         "apple-ml",  ["quantize","check_memory","patch_mps","Int4Linear","baddbmm"]),
    ("Q4 PhotoBack measured numbers",    "photoback", ["SmolVLM","LoRA","adapter","encoder","mlx"]),
    ("Q5 quant study headline",          "quant",     ["INT4","McNemar","memorization","factuality","GAP"]),
    ("Q6 CCK token-cost result",         "cck",       ["Tiered","Monolithic","Reduction","measured","Recall"]),
]

def present(text, needed):
    syms = set(_T.findall(text))
    return [f for f in needed if f in syms]

def retention(text, needed):
    if not needed: return None
    return round(len(present(text, needed)) / len(needed), 4)

rows = []
for qid, key, needed in QUESTIONS:
    src = open(SRC[key]).read()
    needed = [f for f in needed if f in set(_T.findall(src))]  # keep only facts truly in source
    base_tok = token_estimate(src)
    c1 = src
    c2 = summarize(src, 0.0)                       # lossless = identity
    entry = {
        "question": qid, "project": key, "needed_facts": needed,
        "C1_monolithic":   {"tok_saving": 0.0, "retention": retention(c1, needed)},
        "C2_lossless":     {"tok_saving": round(1-token_estimate(c2)/base_tok,3), "retention": retention(c2, needed),
                            "identical_to_C1": c1 == c2},
        "C4_summarized": {},
    }
    for lv in (0.33, 0.66, 1.0):
        s = summarize(src, lv)
        entry["C4_summarized"][f"level_{lv}"] = {
            "tok_saving": round(1-token_estimate(s)/base_tok, 3),
            "retention": retention(s, needed),
            "lost": [f for f in needed if f not in present(s, needed)],
        }
    # safe frontier: highest level with retention==1.0
    safe = 0.0
    for lv in (0.33, 0.66, 1.0):
        if entry["C4_summarized"][f"level_{lv}"]["retention"] == 1.0:
            safe = lv
    entry["safe_frontier"] = safe
    rows.append(entry)

# aggregate
def agg(path):
    vals=[]
    for r in rows:
        d=r
        for p in path: d=d[p]
        if isinstance(d,(int,float)): vals.append(d)
    return round(statistics.mean(vals),4) if vals else None

report = {
    "N_questions": len(rows),
    "SCOPE": "MEASURED but PRELIMINARY — N=6 questions, keyword fact-detection, one compression "
             "operator, NO agent/task-success run. Answers 'are needed facts present in context', "
             "not 'does the agent solve better' (rule 6a).",
    "aggregate": {
        "C2_lossless_all_identical_to_C1": all(r["C2_lossless"]["identical_to_C1"] for r in rows),
        "C2_mean_retention": agg(["C2_lossless","retention"]),
        "C4_level0.33_mean_retention": round(statistics.mean([r["C4_summarized"]["level_0.33"]["retention"] for r in rows if r["C4_summarized"]["level_0.33"]["retention"] is not None]),4),
        "C4_level0.33_mean_tok_saving": round(statistics.mean(r["C4_summarized"]["level_0.33"]["tok_saving"] for r in rows),4),
        "C4_level0.66_mean_retention": round(statistics.mean([r["C4_summarized"]["level_0.66"]["retention"] for r in rows if r["C4_summarized"]["level_0.66"]["retention"] is not None]),4),
        "C4_level0.66_mean_tok_saving": round(statistics.mean(r["C4_summarized"]["level_0.66"]["tok_saving"] for r in rows),4),
        "mean_safe_frontier": round(statistics.mean(r["safe_frontier"] for r in rows),4),
    },
    "per_question": rows,
}
print(json.dumps(report, indent=2))
