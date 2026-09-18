"""summarized_tier.py — C4: LOSSY tiering study (fidelity-vs-token tradeoff).

Unlike the lossless study (defer full bodies; grounding is a null control), this study
adds a FOURTH condition C4 where a tier is SUMMARIZED / COMPRESSED to save more tokens
than lossless deferral can. Here factuality/grounding CAN degrade — and measuring that
degradation vs the token saving is the whole point.

    C4_tiered_summarized: always-on + metadata + a COMPRESSED version of the active body

Central research question (the one Pupa's instinct pointed at):
    How far can a tier be compressed before the agent loses the facts it needs?
    → a fidelity-vs-cost curve: token_saving(level) and grounding_loss(level).

Honesty (rule 6a/6b): this is APPARATUS. It defines the compression operator and the
fidelity metric and validates them on synthetic/self-test input. Real degradation numbers
require the real-agent SWE-bench run (swebench_run.py, C4 enabled) with a budget. No
compression ratio or loss number here is a claim until measured on real tasks.

Compression is deliberately made TUNABLE and EXPLICIT (not a black-box LLM summarizer) so
the tradeoff is attributable to a known operator:
    level 0.0 = lossless (identity)      level 1.0 = maximal compression (headers only)
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

_SENT = re.compile(r"(?<=[.!?])\s+")
_TOKENISH = re.compile(r"[A-Za-z_][A-Za-z0-9_\.]{3,}")
_CODEISH = re.compile(r"`[^`]+`|def\s+\w+|class\s+\w+|\b\w+\([^)]*\)")


def summarize(body: str, level: float) -> str:
    """Deterministic, explicit compression operator (NOT an LLM — so loss is attributable).
    level in [0,1]:
      0.0  -> identity (lossless)
      mid  -> keep headers + code-signature lines + the first sentence of each paragraph
      1.0  -> headers/code-signatures only (maximal, most lossy)
    Code-bearing lines are preserved LONGEST because coding tasks depend on them — the
    operator degrades prose before identifiers. This is a design choice to be validated."""
    if level <= 0:
        return body
    lines = body.splitlines()
    kept = []
    for ln in lines:
        s = ln.strip()
        is_header = s.startswith("#") or s.startswith("##")
        is_code = bool(_CODEISH.search(ln)) or ln.startswith(("    ", "\t")) or "=" in s[:40]
        if is_header or is_code:
            kept.append(ln)              # always keep structure + code
        elif level < 1.0:
            # keep prose proportionally: first sentence of the paragraph at low levels
            sents = _SENT.split(s)
            if sents and level < 0.66:
                kept.append(sents[0])    # keep lead sentence
            # level in [0.66,1.0): drop prose entirely
    out = "\n".join(kept)
    return out if out.strip() else "\n".join(l for l in lines if l.strip().startswith("#"))


def token_estimate(text: str) -> int:
    return max(1, len(text) // 4)  # replace with real BPE in the measured run


@dataclass
class FidelityPoint:
    level: float
    body_tokens: int
    summarized_tokens: int
    token_saving: float               # 1 - summarized/original
    needed: int
    retained: int
    grounding_retention: Optional[float]  # fraction of needed facts still present after summarization
    lost_facts: list


def fidelity_curve(body: str, needed_facts: set, levels=(0.0, 0.33, 0.66, 1.0)) -> list:
    """For each compression level, measure token saving AND grounding retention.
    grounding_retention < 1.0 means summarization dropped a fact the task needs — the
    exact factuality-degradation Pupa asked about. The curve shows the safe compression frontier."""
    orig_tok = token_estimate(body)
    out = []
    for lv in levels:
        summ = summarize(body, lv)
        summ_syms = set(_TOKENISH.findall(summ))
        retained = needed_facts & summ_syms if needed_facts else set()
        lost = sorted(needed_facts - summ_syms) if needed_facts else []
        ret = (round(len(retained) / len(needed_facts), 4) if needed_facts else None)
        out.append(FidelityPoint(
            level=lv, body_tokens=orig_tok, summarized_tokens=token_estimate(summ),
            token_saving=round(1 - token_estimate(summ) / orig_tok, 4),
            needed=len(needed_facts), retained=len(retained),
            grounding_retention=ret, lost_facts=lost))
    return out


def safe_frontier(curve: list, min_retention: float = 1.0) -> Optional[float]:
    """Highest compression level that still retains >= min_retention of needed facts.
    This is the actionable output: 'you may compress up to level X before losing grounding.'"""
    ok = [p.level for p in curve if p.grounding_retention is None or p.grounding_retention >= min_retention]
    return max(ok) if ok else None


if __name__ == "__main__":
    body = ("## auth module\n"
            "The authentication subsystem validates tokens.\n"
            "def login(user_token): return verify(user_token)\n"
            "It also refreshes sessions periodically for active users.\n"
            "## db\n"
            "class ConnPool: pass\n"
            "The pool caps at 32 connections under load.")
    needed = {"login", "user_token", "ConnPool", "verify"}  # facts a fix would depend on
    print("=== fidelity-vs-compression curve (apparatus self-test) ===")
    curve = fidelity_curve(body, needed)
    for p in curve:
        print(f"  level={p.level:.2f}  tok_saving={p.token_saving:.2f}  "
              f"grounding_retention={p.grounding_retention}  lost={p.lost_facts}")
    frontier = safe_frontier(curve, min_retention=1.0)
    print(f"safe compression frontier (100% grounding kept): level {frontier}")
    # self-test invariants: level 0 is lossless (retention 1.0, saving 0); higher levels lose more
    assert curve[0].grounding_retention == 1.0 and curve[0].token_saving == 0.0
    assert curve[-1].token_saving > 0  # max compression saves tokens
    print("summarized_tier.py self-test OK (apparatus only — real loss numbers need the SWE-bench run)")
