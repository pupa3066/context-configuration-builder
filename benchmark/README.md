# Benchmark

Token-accurate comparison of **tiered** context (this tool) vs. a **monolithic** always-on baseline (the naive "put everything in context" approach, e.g. one big always-loaded instruction file).

## Method
`benchmark.py` uses a real BPE tokenizer (GPT-2 via `transformers`) to count exact tokens:
- **Always-on tier** = all steering/always-on files.
- **Skill body** = full per-project context; **metadata** = frontmatter only.
- **Monolithic per-turn** = always-on + every project body (all loaded, always).
- **Tiered per-turn** = always-on + every project's metadata + one active project body.

Run: `python benchmark.py [steering_dir] [skills_dir]` (defaults to a Kiro deployment).

## Results (measured, this deployment)
| N projects | Monolithic (tok) | Tiered (tok) | Reduction |
|---|---|---|---|
| 4 (measured) | 6,958 | 5,253 | 24.5% |
| 10 | 11,599 | 5,363 | 53.8% |
| 25 | 23,209 | 6,458 | 72.2% |
| 50 | 42,559 | 8,283 | 80.5% |
| 100 | 81,259 | 11,933 | 85.3% |
| ∞ | — | — | 90.6% |

Raw data: `results.json`.

## Does this exist elsewhere?
The *tiered-injection technique* is validated independently (ETH Zurich study: 60–80% context reduction vs monolithic). Token-optimization stacks exist for specific agents (e.g. Claude Code). This tool's distinct contribution is packaging it as a **portable, agent-independent, registry-governed configuration builder** (projects + rules as editable lists) with a **cross-project provenance graph** — not the tiering idea alone. Our measured numbers corroborate the published range.

## Honest notes
- N=4 is directly measured; larger N is a closed-form projection from measured per-project averages.
- Tiered counts one active project body/turn; multi-project turns load more.
- Measures token cost, not task quality; the ETH study reports accuracy is maintained or improved.

## Measured at every N (reproducible from this repo)
`benchmark_measured.py` builds real skill files from the shipped template at N=1…100 and measures
them instead of projecting, and also varies active-projects-per-turn and body length. Results and
caveats: [`MEASURED_FINDINGS.md`](MEASURED_FINDINGS.md). The projection above holds to within 0.1pt;
the headline % depends on your metadata/body ratio and on how many projects a turn touches.
