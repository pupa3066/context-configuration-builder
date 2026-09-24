"""Evaluation harness for the context-tiering study (research/RESEARCH_PLAN.md).

Runs a coding agent over tasks under 4 context conditions (C0/C1/C2/C3),
logging task success, token cost, and steps to JSONL for analysis.py.

Design goals:
- Agent-agnostic: plug in any agent via the Agent protocol.
- Runnable offline with MockAgent (for harness testing without API cost).
- Deterministic logging schema so analysis is reproducible.

This is the APPARATUS. Real results require a real agent + SWE-bench tasks
(see RESEARCH_PLAN Section4). Nothing here fabricates results.
"""
from __future__ import annotations
import json, time, hashlib, argparse, sys
from dataclasses import dataclass, asdict, field
from typing import Protocol, Callable

# ---- Conditions (independent variable) ----
CONDITIONS = ("C0_no_context", "C1_monolithic", "C2_tiered_manual", "C3_tiered_auto")

@dataclass
class Task:
    task_id: str
    prompt: str
    context_source: str            # full context text (shared source for C1/C2/C3)
    references: list[str] = field(default_factory=list)  # project keys this task touches
    verify: Callable[[str], bool] | None = None          # returns True if solution passes

@dataclass
class RunResult:
    task_id: str
    condition: str
    resolved: bool
    input_tokens: int
    output_tokens: int
    steps: int
    seconds: float

class Agent(Protocol):
    def solve(self, prompt: str, context: str) -> tuple[str, int, int, int]:
        """Return (solution_text, input_tokens, output_tokens, steps)."""
        ...

# ---- Context builders per condition (control: same SOURCE, different loading) ----
def build_context(condition: str, task: Task, tierer=None) -> str:
    if condition == "C0_no_context":
        return ""
    if condition == "C1_monolithic":
        return task.context_source                      # everything, always
    if condition in ("C2_tiered_manual", "C3_tiered_auto"):
        # always-on = first section (rules/index); on-demand = only referenced sections
        always_on, sections = _split_sections(task.context_source)
        if condition == "C3_tiered_auto" and tierer is not None:
            keep = tierer.select(sections, task.references)
        else:
            keep = {k: v for k, v in sections.items() if k in set(task.references)}
        loaded = always_on + "\n" + "\n".join(keep.values())
        return loaded.strip()
    raise ValueError(condition)

def _split_sections(text: str):
    """Split a context file into (always_on_preamble, {section_key: body})."""
    blocks = text.split("\n## ")
    always_on = blocks[0]
    sections = {}
    for b in blocks[1:]:
        head = b.splitlines()[0].strip().lower().split()[0] if b.strip() else "x"
        sections[head] = "## " + b
    return always_on, sections

# ---- Runner ----
def run(agent: Agent, tasks: list[Task], conditions=CONDITIONS, tierer=None, out="research/harness/runs.jsonl"):
    n = 0
    with open(out, "w") as fh:
        for t in tasks:
            for c in conditions:
                ctx = build_context(c, t, tierer=tierer)
                t0 = time.perf_counter()
                sol, itok, otok, steps = agent.solve(t.prompt, ctx)
                dt = time.perf_counter() - t0
                resolved = bool(t.verify(sol)) if t.verify else False
                r = RunResult(t.task_id, c, resolved, itok, otok, steps, round(dt, 4))
                fh.write(json.dumps(asdict(r)) + "\n")
                n += 1
    return n

# ---- Mock agent for harness self-test (no API cost, deterministic) ----
class MockAgent:
    """Deterministic stand-in: 'resolves' if the needed section is present in context.
    Token cost proportional to context length. Lets us test the HARNESS, not the science."""
    def solve(self, prompt: str, context: str):
        need = prompt.split("NEEDS:")[-1].strip() if "NEEDS:" in prompt else ""
        itok = max(1, len(context) // 4)
        otok = 20
        steps = 1 + (0 if need and need in context else 1)  # extra step if info missing
        sol = "PASS" if (need and need in context) else "FAIL"
        return sol, itok, otok, steps

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gen", type=int, default=0, help="generate N mock tasks for pipeline testing")
    a = ap.parse_args()
    if a.selftest:
        src = ("PREAMBLE rules and index\n"
               "## alpha\nalpha details TOKENALPHA\n"
               "## beta\nbeta details TOKENBETA\n")
        tasks = [
            Task("t1", "fix alpha NEEDS: TOKENALPHA", src, references=["alpha"],
                 verify=lambda s: s == "PASS"),
            Task("t2", "fix beta NEEDS: TOKENBETA", src, references=["beta"],
                 verify=lambda s: s == "PASS"),
        ]
        n = run(MockAgent(), tasks, out="research/harness/selftest_runs.jsonl")
        print(f"selftest: wrote {n} runs to research/harness/selftest_runs.jsonl")
    elif a.gen:
        import random as _r
        _r.seed(0)
        # synthetic corpus with many sections; each task needs one section's token
        secs = [f"s{i}" for i in range(8)]
        src = "PREAMBLE rules and index\n" + "".join(
            f"## {s}\n{s} details TOKEN_{s.upper()} " + ("filler " * 30) + "\n" for s in secs)
        tasks = []
        for i in range(a.gen):
            s = _r.choice(secs)
            tasks.append(Task(f"t{i}", f"fix {s} NEEDS: TOKEN_{s.upper()}", src,
                              references=[s], verify=lambda x: x == "PASS"))
        n = run(MockAgent(), tasks, out="research/harness/runs.jsonl")
        print(f"gen: wrote {n} runs to research/harness/runs.jsonl (MOCK  -  pipeline test only)")
