"""Automatic tier assignment (the algorithmic contribution, RESEARCH_PLAN H4).

Problem: given context sections and observed task->section access, assign each
section to a tier {ALWAYS_ON, ON_DEMAND, QUERY_ONLY} to minimize expected
per-turn tokens subject to a coverage constraint (needed sections must be
loadable when a task references them).

Policy (frequency-threshold, interpretable baseline for the learned version):
- access_freq(s) = P(task references s) estimated from history.
- ALWAYS_ON  if access_freq >= tau_hi  (cheaper to always keep than reload often)
- QUERY_ONLY if access_freq <  tau_lo  (rarely needed; keep out of steering + skills metadata)
- ON_DEMAND  otherwise
Thresholds derived from the per-turn cost model:
  keeping s always-on costs body(s) every turn;
  on-demand costs meta(s) every turn + body(s) only when accessed (freq).
  => prefer always-on over on-demand when body*1 < meta + body*freq
     i.e. body*(1-freq) < meta  ->  freq > 1 - meta/body   (tau_hi, per-section)
This makes tau_hi PRINCIPLED (derived from measured meta/body), not arbitrary.
"""
from __future__ import annotations
from dataclasses import dataclass

ALWAYS_ON, ON_DEMAND, QUERY_ONLY = "always_on", "on_demand", "query_only"

@dataclass
class Section:
    key: str
    body_tokens: int
    meta_tokens: int
    access_freq: float   # in [0,1], estimated from task history

class TierAssigner:
    def __init__(self, tau_lo: float = 0.05):
        self.tau_lo = tau_lo  # below this: query-only (semantic KB), not in per-turn context

    def _tau_hi(self, s: Section) -> float:
        # principled threshold from the cost model: freq beyond which always-on wins
        if s.body_tokens <= 0:
            return 1.0
        return max(0.0, 1.0 - s.meta_tokens / s.body_tokens)

    def assign(self, s: Section) -> str:
        if s.access_freq < self.tau_lo:
            return QUERY_ONLY
        if s.access_freq >= self._tau_hi(s):
            return ALWAYS_ON
        return ON_DEMAND

    def expected_tokens_per_turn(self, sections: list[Section]) -> float:
        """Expected per-turn tokens under the assignment (the objective)."""
        total = 0.0
        for s in sections:
            tier = self.assign(s)
            if tier == ALWAYS_ON:
                total += s.body_tokens
            elif tier == ON_DEMAND:
                total += s.meta_tokens + s.access_freq * s.body_tokens
            # query_only: 0 per-turn
        return total

    def select(self, sections: dict, references) -> dict:
        """Harness hook: which section bodies to load given task references."""
        refset = set(references)
        keep = {}
        for k, body in sections.items():
            # load if referenced, or if it would be always-on
            approx = Section(k, body_tokens=max(1, len(body)//4), meta_tokens=8, access_freq=0.0)
            if k in refset or self.assign(approx) == ALWAYS_ON:
                keep[k] = body
        return keep

def monolithic_tokens_per_turn(sections: list[Section]) -> float:
    return float(sum(s.body_tokens for s in sections))
