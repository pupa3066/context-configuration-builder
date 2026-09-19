#!/usr/bin/env python3
"""quality_benchmark.py — does TIERED context preserve answer QUALITY, not just save tokens?

The shipped benchmark.py and benchmark_measured.py measure TOKEN COST only. Neither checks whether
an agent still answers correctly when project bodies are left unloaded. This script measures that
with a real local model on GPU.

Design
------
* Generate N synthetic projects, each a real SKILL.md-style file (frontmatter + body) with F
  planted, un-guessable facts (e.g. "build tag is qz-4481"). Facts are random tokens so the model
  cannot know them from pretraining — recall requires the fact to be IN the prompt.
* Two context conditions per question, same always-on steering text in both:
    MONOLITHIC = always-on + ALL N project bodies
    TIERED     = always-on + ALL N metadata blocks + only the k ACTIVE project bodies
* Two question types:
    in-active   : fact lives in an active project  -> tiered has the body; should match monolithic
    in-inactive : fact lives in an inactive project -> tiered lacks the body; measures the real cost
                  of tiering that token benchmarks never show
* Scoring: exact normalized substring match of the planted value in the model's greedy answer.
* Also records tokens, and (separately flagged) prefill latency + peak VRAM for the hardware owner.

HONESTY
-------
* Simulates tiering by constructing prompts; does NOT exercise Kiro's actual skill:// loader.
* Small local models (<=3B) have weaker long-context recall than frontier models; absolute recall
  will be pessimistic. The RELATIVE tiered-vs-monolithic gap is the reliable signal.
* Latency/VRAM are hardware-specific (one laptop GPU); reported under "hardware_personal" and
  excluded from the headline findings.
* If monolithic overflows the model context window, that row is recorded as overflow, not invented.

Usage:
  python benchmark/quality_benchmark.py --model models/Qwen2.5-1.5B-Instruct \
      --ns 4,10,25 --k 1,2 --facts 5 --out benchmark/results_quality.json
"""
import os, sys, json, re, random, time, argparse, glob

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True, help="local model dir (offline)")
ap.add_argument("--steering", default="templates/steering")
ap.add_argument("--example-skill", default="templates/skills/_example/SKILL.md")
ap.add_argument("--ns", default="4,10,25")
ap.add_argument("--k", default="1,2", help="active projects per turn")
ap.add_argument("--facts", type=int, default=5, help="planted facts per project")
ap.add_argument("--questions-per-cell", type=int, default=20)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--precision", choices=("fp16", "int4"), default="fp16")
ap.add_argument("--max-ctx", type=int, default=32768)
ap.add_argument("--out", default="benchmark/results_quality.json")
a = ap.parse_args()

os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
assert torch.cuda.is_available(), "CUDA required"
rng = random.Random(a.seed)

# ---------------- load model ----------------
tok = AutoTokenizer.from_pretrained(a.model, local_files_only=True)
kw = {"device_map": "cuda", "local_files_only": True}
if a.precision == "int4":
    from transformers import BitsAndBytesConfig
    kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                   bnb_4bit_compute_dtype=torch.float16)
else:
    kw["dtype"] = torch.float16
model = AutoModelForCausalLM.from_pretrained(a.model, **kw).eval()
model_ctx = min(a.max_ctx, getattr(model.config, "max_position_embeddings", a.max_ctx))

def ntok(s): return len(tok.encode(s))

# ---------------- always-on tier (real shipped steering) ----------------
always_on = "\n\n".join(open(f, encoding="utf-8", errors="ignore").read()
                        for f in sorted(glob.glob(os.path.join(a.steering, "*.md"))))

# ---------------- synthetic projects with planted facts ----------------
ex = open(a.example_skill, encoding="utf-8", errors="ignore").read().splitlines()
end = next(i for i in range(1, len(ex)) if ex[i].strip() == "---")
body_template = "\n".join(ex[end+1:])

FACT_KEYS = ["build tag", "primary contact handle", "staging hostname", "release codename",
             "ticket prefix", "default region", "license key suffix", "on-call rotation name"]
def rand_val():
    return "".join(rng.choice("abcdefghjkmnpqrstuvwxyz") for _ in range(2)) + "-" + str(rng.randint(1000, 9999))

def make_project(i):
    name = f"project-{i:03d}"
    keys = rng.sample(FACT_KEYS, a.facts)
    facts = {k: rand_val() for k in keys}
    meta = (f"---\nname: {name}-context\n"
            f"description: Deep context for {name}. Use when working in {name}.\n---")
    fact_lines = "\n".join(f"- The {k} for {name} is {v}." for k, v in facts.items())
    body = f"# {name}\n\n## Key facts\n{fact_lines}\n\n{body_template}"
    return {"name": name, "meta": meta, "body": body, "facts": facts}

# ---------------- prompt builders ----------------
SYS = ("You are a coding assistant. Answer using ONLY the project context provided. "
       "Reply with just the value, nothing else. If the value is not in the context, reply UNKNOWN.")

def build_prompt(ctx, question):
    msgs = [{"role": "system", "content": SYS},
            {"role": "user", "content": f"{ctx}\n\n---\nQuestion: {question}"}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

def mono_ctx(projects):
    return always_on + "\n\n" + "\n\n".join(p["meta"] + "\n" + p["body"] for p in projects)

def tiered_ctx(projects, active_idx):
    parts = [always_on] + [p["meta"] for p in projects]           # all metadata
    parts += [projects[i]["meta"] + "\n" + projects[i]["body"] for i in active_idx]  # active bodies
    return "\n\n".join(parts)

def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())

@torch.no_grad()
def answer(prompt):
    ids = tok(prompt, return_tensors="pt").to("cuda")
    n_in = ids["input_ids"].shape[1]
    if n_in > model_ctx:
        return None, n_in, None, None
    torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize(); t0 = time.perf_counter()
    out = model.generate(**ids, max_new_tokens=24, do_sample=False, pad_token_id=tok.eos_token_id)
    torch.cuda.synchronize(); dt = (time.perf_counter() - t0) * 1000
    text = tok.decode(out[0, n_in:], skip_special_tokens=True)
    return text, n_in, round(dt, 1), round(torch.cuda.max_memory_allocated() / 2**20, 1)

# ---------------- run ----------------
ns = [int(x) for x in a.ns.split(",")]; ks = [int(x) for x in a.k.split(",")]
cells = []
print(f"model={os.path.basename(a.model)} prec={a.precision} ctx_limit={model_ctx} "
      f"always_on={ntok(always_on)} tok", file=sys.stderr)

for n in ns:
    projects = [make_project(i) for i in range(n)]
    for k in ks:
        if k >= n: continue
        active = list(range(k))                     # first k projects are "active"
        inactive = list(range(k, n))
        # sample questions: half from active, half from inactive
        qs = []
        for _ in range(a.questions_per_cell):
            src = "in-active" if len(qs) % 2 == 0 else "in-inactive"
            pi = rng.choice(active if src == "in-active" else inactive)
            key, val = rng.choice(list(projects[pi]["facts"].items()))
            qs.append({"src": src, "project": projects[pi]["name"], "key": key, "gold": val,
                       "q": f"What is the {key} for {projects[pi]['name']}?"})
        mctx = mono_ctx(projects); tctx = tiered_ctx(projects, active)
        res = {"n": n, "k_active": k, "tokens": {"mono": ntok(mctx), "tiered": ntok(tctx)},
               "mono": {"in-active": [0, 0], "in-inactive": [0, 0], "overflow": False},
               "tiered": {"in-active": [0, 0], "in-inactive": [0, 0], "unknown_on_inactive": 0},
               "hardware_personal": {"mono_prefill_ms": [], "tiered_prefill_ms": [],
                                     "mono_peak_vram_mb": None, "tiered_peak_vram_mb": None},
               "examples": []}
        for q in qs:
            for cond, ctx in (("mono", mctx), ("tiered", tctx)):
                text, n_in, ms, vram = answer(build_prompt(ctx, q["q"]))
                if text is None:
                    res[cond]["overflow"] = True; continue
                hit = norm(q["gold"]) in norm(text)
                res[cond][q["src"]][1] += 1; res[cond][q["src"]][0] += int(hit)
                if cond == "tiered" and q["src"] == "in-inactive" and "unknown" in text.lower():
                    res["tiered"]["unknown_on_inactive"] += 1
                hp = res["hardware_personal"]; hp[f"{cond}_prefill_ms"].append(ms)
                hp[f"{cond}_peak_vram_mb"] = max(hp[f"{cond}_peak_vram_mb"] or 0, vram)
                if len(res["examples"]) < 4:
                    res["examples"].append({"cond": cond, "src": q["src"], "q": q["q"],
                                            "gold": q["gold"], "got": text.strip()[:40], "hit": hit})
        # summarize
        def rate(c): return round(c[0] / c[1], 3) if c[1] else None
        res["recall"] = {cond: {src: rate(res[cond][src]) for src in ("in-active", "in-inactive")}
                         for cond in ("mono", "tiered")}
        for cond in ("mono", "tiered"):
            tot = [res[cond]["in-active"][i] + res[cond]["in-inactive"][i] for i in (0, 1)]
            res["recall"][cond]["overall"] = rate(tot)
        hp = res["hardware_personal"]
        for cond in ("mono", "tiered"):
            v = hp[f"{cond}_prefill_ms"]; hp[f"{cond}_prefill_ms"] = round(sum(v)/len(v), 1) if v else None
        res["token_reduction"] = round(1 - res["tokens"]["tiered"] / res["tokens"]["mono"], 3)
        cells.append(res)
        r = res["recall"]
        print(f"N={n:>3} k={k} | tok mono={res['tokens']['mono']:>6} tiered={res['tokens']['tiered']:>6} "
              f"(-{res['token_reduction']:.0%}) | recall mono act={r['mono']['in-active']} inact={r['mono']['in-inactive']} "
              f"| tiered act={r['tiered']['in-active']} inact={r['tiered']['in-inactive']}"
              f"{' | MONO OVERFLOW' if res['mono']['overflow'] else ''}", file=sys.stderr)

out = {
    "model": os.path.basename(a.model), "precision": a.precision, "context_limit": model_ctx,
    "always_on_tokens": ntok(always_on), "facts_per_project": a.facts,
    "questions_per_cell": a.questions_per_cell, "seed": a.seed,
    "scoring": "normalized substring match of planted value in greedy 24-token answer",
    "note": ("Facts are random un-guessable strings; recall requires the fact to be in the prompt. "
             "'in-inactive' under TIERED measures the true cost of not loading a project body. "
             "hardware_personal fields are single-laptop-GPU measurements, excluded from headline findings."),
    "cells": cells,
}
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
json.dump(out, open(a.out, "w"), indent=2)
print(f"wrote {a.out}", file=sys.stderr)
