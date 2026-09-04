"""Unit tests for tier_assign — the algorithmic contribution.
Run: python -m pytest research/tier_assign/test_tier_assign.py -q
     (or: python research/tier_assign/test_tier_assign.py)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tier_assign import Section, TierAssigner, monolithic_tokens_per_turn, ALWAYS_ON, ON_DEMAND, QUERY_ONLY

def test_query_only_for_rare():
    ta = TierAssigner(tau_lo=0.05)
    s = Section("rare", body_tokens=800, meta_tokens=70, access_freq=0.01)
    assert ta.assign(s) == QUERY_ONLY

def test_always_on_for_frequent():
    ta = TierAssigner()
    # meta/body = 70/800 => tau_hi ~ 0.9125; freq above it => always_on
    s = Section("hot", body_tokens=800, meta_tokens=70, access_freq=0.95)
    assert ta.assign(s) == ALWAYS_ON

def test_on_demand_for_middle():
    ta = TierAssigner()
    s = Section("mid", body_tokens=800, meta_tokens=70, access_freq=0.3)
    assert ta.assign(s) == ON_DEMAND

def test_threshold_is_principled():
    ta = TierAssigner()
    # small meta relative to body -> tau_hi close to 1 (rarely worth always-on)
    s = Section("x", body_tokens=1000, meta_tokens=50, access_freq=0.0)
    assert abs(ta._tau_hi(s) - 0.95) < 1e-9

def test_tiered_beats_monolithic_on_expected_cost():
    ta = TierAssigner()
    # realistic mix from measured deployment (bodies ~774, meta ~73)
    secs = [
        Section("p1", 774, 73, 0.5),
        Section("p2", 774, 73, 0.2),
        Section("p3", 774, 73, 0.05),
        Section("p4", 774, 73, 0.02),  # -> query_only
    ]
    tiered = ta.expected_tokens_per_turn(secs)
    mono = monolithic_tokens_per_turn(secs)
    assert tiered < mono, (tiered, mono)
    # and the win should be substantial for low-frequency sections
    assert tiered <= 0.7 * mono

def test_objective_monotonic_in_freq():
    ta = TierAssigner()
    lo = [Section("a", 774, 73, 0.05)]
    hi = [Section("a", 774, 73, 0.9)]
    assert ta.expected_tokens_per_turn(lo) < ta.expected_tokens_per_turn(hi)

if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn(); passed += 1; print(f"PASS {fn.__name__}")
    print(f"\n{passed}/{len(fns)} tests passed")
