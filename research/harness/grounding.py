"""grounding.py  -  grounding / context-fidelity NULL-CONTROL for the lossless study.

Question this answers (the CCK analog of "factuality" for a coding agent):
    When context is tiered LOSSLESSLY (defer full body; load on demand), does the
    agent still receive every fact it needs? For lossless tiering the answer MUST be
    "yes, identical to monolithic"  -  this module MEASURES that rather than asserting it.

It is a NULL CONTROL: we expect NO degradation for C2/C3 vs C1 because CCK's current
tiering never summarizes (tier_assign.py loads full `body`, verified). A non-null result
here would be a BUG (a needed section wasn't loaded), not a fidelity/summarization loss.

Metric  -  grounding coverage per (task, condition):
    needed_facts(task)  = the ground-truth section keys / fact-tokens the gold patch depends on
    present_facts(ctx)  = which of those appear verbatim in the context actually given
    coverage = |present intersect needed| / |needed|      (1.0 = fully grounded)

For the LOSSLESS claim we test: coverage(C2)=coverage(C1) for every task where the needed
section is loadable (i.e. the tierer selected it). Any C2<C1 gap is an information-loss bug.

No fabrication: if needed_facts can't be determined for a task, coverage is None (excluded),
never guessed.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

_TOKENISH = re.compile(r"[A-Za-z_][A-Za-z0-9_\.]{3,}")


@dataclass
class Grounding:
    condition: str
    needed: int
    present: int
    coverage: Optional[float]     # present/needed, or None if needed==0/unknown
    missing_keys: list            # needed facts absent from the given context (should be [] for lossless)


def needed_facts_from_gold(gold_patch: str, context_source: str) -> set:
    """Ground-truth facts a solution depends on: identifiers/paths in the gold patch that
    also appear in the repo context source. These are the things the agent must be grounded on.
    Uses the gold patch (available in SWE-bench instances)  -  real signal, not a heuristic guess."""
    if not gold_patch:
        return set()
    patch_syms = set(_TOKENISH.findall(gold_patch))
    src_syms = set(_TOKENISH.findall(context_source or ""))
    # a "needed fact" = a symbol the fix touches that is documented in the repo context
    return patch_syms & src_syms


def measure(condition: str, given_context: str, needed: set) -> Grounding:
    if not needed:
        return Grounding(condition, 0, 0, None, [])
    present_syms = set(_TOKENISH.findall(given_context or ""))
    present = needed & present_syms
    missing = sorted(needed - present_syms)
    return Grounding(condition, len(needed), len(present),
                     round(len(present) / len(needed), 4), missing)


def lossless_holds(by_condition: dict) -> dict:
    """Given {condition: [Grounding,...]} decide the null-control verdict:
    lossless tiering PASSES iff mean coverage(C2/C3) == coverage(C1) (within float eps).
    Returns a structured verdict; a FAIL means a needed section was not loaded (a bug to fix)."""
    def mean_cov(rows):
        cs = [g.coverage for g in rows if g.coverage is not None]
        return round(sum(cs) / len(cs), 4) if cs else None
    c1 = mean_cov(by_condition.get("C1_monolithic", []))
    out = {"baseline_C1_coverage": c1, "verdict": {}}
    for cond in ("C2_tiered_manual", "C3_tiered_auto"):
        cc = mean_cov(by_condition.get(cond, []))
        if c1 is None or cc is None:
            out["verdict"][cond] = {"coverage": cc, "status": "INSUFFICIENT_DATA"}
        elif abs(cc - c1) < 1e-9:
            out["verdict"][cond] = {"coverage": cc, "status": "NULL_CONFIRMED (lossless preserves grounding)"}
        elif cc < c1:
            out["verdict"][cond] = {"coverage": cc,
                                    "status": f"DEGRADED by {round(c1-cc,4)}  -  INFORMATION-LOSS BUG (a needed section was not loaded)"}
        else:
            out["verdict"][cond] = {"coverage": cc, "status": "HIGHER_THAN_C1 (unexpected  -  investigate)"}
    return out


if __name__ == "__main__":
    # self-test: lossless C2 must equal C1; a simulated missing section must be flagged.
    src = "PREAMBLE\n## auth\ndef login(user_token): ...\n## db\nclass ConnPool: ..."
    gold = "diff --git a/auth.py\n+ login(user_token) fix ConnPool"
    needed = needed_facts_from_gold(gold, src)
    c1 = measure("C1_monolithic", src, needed)                       # full context
    c2 = measure("C2_tiered_manual", src, needed)                    # lossless: same full bodies
    c2_bug = measure("C2_tiered_manual", "PREAMBLE\n## auth\ndef login(user_token): ...", needed)  # db missing
    v = lossless_holds({"C1_monolithic": [c1], "C2_tiered_manual": [c2]})
    v_bug = lossless_holds({"C1_monolithic": [c1], "C2_tiered_manual": [c2_bug]})
    print("needed facts:", sorted(needed))
    print("C1:", c1); print("C2 (lossless):", c2)
    print("verdict lossless:", v["verdict"]["C2_tiered_manual"]["status"])
    print("verdict with missing section:", v_bug["verdict"]["C2_tiered_manual"]["status"])
    assert "NULL_CONFIRMED" in v["verdict"]["C2_tiered_manual"]["status"]
    assert "BUG" in v_bug["verdict"]["C2_tiered_manual"]["status"]
    print("grounding.py self-test OK")
