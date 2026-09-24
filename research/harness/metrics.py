"""metrics.py  -  measurement instruments for the context-tiering study.

Adds the extra measured axes requested for CCK evaluation, on TOP of the
existing (resolved, tokens, steps, seconds) schema in harness.py:

  - memory:   peak resident set size (RSS) during a solve, in MiB
  - latency:  wall seconds + time-to-first-token (TTFT) seconds
  - behavior: output determinism across repeats (fraction of identical outputs)
  - factors:  model label + operating system, captured from the environment

DESIGN HONESTY (rule 6a): these are INSTRUMENTS, not results. They record what a
real run measures. A mock run measures the mock. No metric here fabricates a value;
if an instrument is unavailable (e.g. no psutil), it records None and says so  - 
never a guessed number.

Deliberately EXCLUDED: factuality. Factuality is the precision axis of the companion
quant-memorization-study (PopQA/LLM recall), not a coding-agent metric. Measuring it
inside a SWE-bench coding harness would be a category error; see research/STATUS.md.
"""
from __future__ import annotations
import os, sys, time, platform, hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional

# ---- peak-RSS sampling (best-effort; records None if unavailable) ----
def _rss_mib() -> Optional[float]:
    """Current process RSS in MiB, or None if it can't be measured on this platform."""
    try:
        import resource  # POSIX (macOS + Linux)
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS reports bytes, Linux reports kilobytes  -  normalize.
        if sys.platform == "darwin":
            return round(r / (1024 * 1024), 2)
        return round(r / 1024, 2)
    except Exception:
        try:
            import psutil  # cross-platform fallback (incl. Windows)
            return round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
        except Exception:
            return None


def env_factors(model_label: str) -> dict:
    """Capture the experimental factors that vary across runs: model + OS.
    These are recorded on every row so analysis can group by them."""
    return {
        "model": model_label,
        "os": platform.system(),          # 'Darwin' | 'Linux' | 'Windows'
        "os_release": platform.release(),
        "machine": platform.machine(),     # arm64 / x86_64
        "python": platform.python_version(),
    }


@dataclass
class Measured:
    """The extra measured axes for one solve, merged into the run row by the runner."""
    wall_seconds: float
    ttft_seconds: Optional[float]        # time to first token, if the agent reports it
    peak_rss_mib_before: Optional[float]
    peak_rss_mib_after: Optional[float]
    rss_delta_mib: Optional[float]
    output_sha: str                      # hash of the solution text (for determinism check)

    def as_dict(self) -> dict:
        return asdict(self)


def measure_solve(agent, prompt: str, context: str, model_label: str) -> tuple:
    """Run agent.solve while measuring wall time, TTFT (if reported), peak RSS, and
    hashing the output for a determinism metric.

    Returns (solution, input_tokens, output_tokens, steps, Measured).

    Agent contract stays the SAME as harness.Agent (solve -> (sol, itok, otok, steps)).
    If the agent optionally exposes .last_ttft (seconds to first token), we record it;
    otherwise ttft is None (not fabricated).
    """
    rss0 = _rss_mib()
    t0 = time.perf_counter()
    sol, itok, otok, steps = agent.solve(prompt, context)
    wall = time.perf_counter() - t0
    rss1 = _rss_mib()
    ttft = getattr(agent, "last_ttft", None)
    delta = round(rss1 - rss0, 2) if (rss0 is not None and rss1 is not None) else None
    m = Measured(
        wall_seconds=round(wall, 4),
        ttft_seconds=(round(ttft, 4) if isinstance(ttft, (int, float)) else None),
        peak_rss_mib_before=rss0,
        peak_rss_mib_after=rss1,
        rss_delta_mib=delta,
        output_sha=hashlib.sha256((sol or "").encode()).hexdigest()[:16],
    )
    return sol, itok, otok, steps, m


def determinism(output_shas: list[str]) -> Optional[float]:
    """Behavior metric: fraction of runs whose output matches the modal output.
    1.0 = fully deterministic; lower = more behavioral variance. None if <2 samples."""
    if len(output_shas) < 2:
        return None
    from collections import Counter
    c = Counter(output_shas)
    modal = c.most_common(1)[0][1]
    return round(modal / len(output_shas), 4)


if __name__ == "__main__":
    # Self-test: instruments run and record real values (or honest None), no fabrication.
    class _Mock:
        last_ttft = 0.001
        def solve(self, p, c):
            return ("PASS" if "TOKEN" in c else "FAIL"), max(1, len(c)//4), 20, 1
    sol, it, ot, st, m = measure_solve(_Mock(), "x NEEDS: TOKEN", "## a\nTOKEN filler", "mock:selftest")
    print("env:", env_factors("mock:selftest"))
    print("measured:", m.as_dict())
    shas = [m.output_sha, m.output_sha, "deadbeef"]
    print("determinism(3 runs, 2 identical):", determinism(shas))
    assert m.wall_seconds >= 0 and m.output_sha
    print("metrics.py self-test OK")
