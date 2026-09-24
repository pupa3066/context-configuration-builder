"""tier_assign_adapter.py  -  connect real repo context to the tier-assignment algorithm.

Turns a repo's assembled context text into Sections with token counts, estimates
access frequency (from keyword overlap between the issue and each section as a
lightweight proxy until access history is available), and drives C3 selection.
"""
from __future__ import annotations
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tier_assign"))
from tier_assign import Section, TierAssigner  # noqa: E402

_WORD = re.compile(r"[a-zA-Z_]{4,}")

def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)

def _sections(src: str):
    blocks = src.split("\n## ")
    out = {}
    for b in blocks[1:]:
        key = b.splitlines()[0].strip().lower().split()[0] if b.strip() else "x"
        out[key] = "## " + b
    return out

class RepoTierer:
    def __init__(self):
        self.ta = TierAssigner()

    def references_for(self, instance, src: str):
        """Proxy access signal: sections whose keywords overlap the issue text.
        (Replace with real access-frequency history for the learned-policy study.)"""
        issue = (instance.get("problem_statement", "") or "").lower()
        issue_words = set(_WORD.findall(issue))
        refs = []
        for key, body in _sections(src).items():
            body_words = set(_WORD.findall(body.lower()))
            overlap = len(issue_words & body_words)
            if overlap >= 3:  # threshold proxy; documented as a limitation
                refs.append(key)
        return refs

    def select(self, sections: dict, references):
        """C3: assign tiers by the algorithm; load referenced + always-on bodies."""
        refset = set(references)
        keep = {}
        for k, body in sections.items():
            s = Section(k, body_tokens=_approx_tokens(body), meta_tokens=8,
                        access_freq=1.0 if k in refset else 0.0)
            tier = self.ta.assign(s)
            if k in refset or tier == "always_on":
                keep[k] = body
        return keep
