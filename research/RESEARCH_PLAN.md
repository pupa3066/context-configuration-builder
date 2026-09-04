# Research Plan: Access-Pattern-Tiered Context for Coding Agents

**Status:** design v1 (2026-09-04). Pre-registration-style plan; results section to be filled after runs.

## 1. Problem & prior result

Gloaguen et al. (ETH Zurich, arXiv:2602.11988, "Evaluating AGENTS.md") show, on SWE-bench and repos with developer-committed context files, that repository-level context files do **not** generally raise task-success rate and **increase inference cost by >20%**, across LLMs and agents. Instructions are followed; repository *overviews* are not helpful.

This establishes a negative result about *monolithic* context provisioning. It leaves open a constructive question:

> **RQ:** Does loading context by *access pattern* (tiered/selective) — rather than wholesale — recover task success at lower cost, and can the tier assignment be produced automatically?

## 2. Hypotheses (falsifiable, pre-registered)

- **H1 (cost):** Tiered context has lower mean tokens/turn than monolithic context. (Directional; strongly expected — partial support already: 24.5%→85% by project count in a size benchmark.)
- **H2 (quality non-inferiority):** Tiered context achieves task-success rate **not worse** than monolithic by a margin δ=2pp on SWE-bench-Verified. (Non-inferiority test.)
- **H3 (quality vs. no-context):** Tiered context achieves task-success **≥** no-context (i.e., it avoids the degradation ETH observed for monolithic files). 
- **H4 (auto-tiering):** An automatic tier assignment (access-frequency classifier) yields cost/quality within a tolerance ε of an oracle/manual tiering. (This is the algorithmic contribution.)

A result of "H1 holds but H2 fails" is itself publishable (cost-quality tradeoff characterization), so the plan is not success-contingent.

## 3. Conditions (independent variable = context provisioning)

| Cond | Description |
|---|---|
| C0 no-context | agent gets task only (ETH control) |
| C1 monolithic | full context file always in prompt (ETH treatment) |
| C2 tiered-manual | always-on (rules+index) + on-demand project section loaded when task references it |
| C3 tiered-auto | C2 but tiers assigned by the automatic classifier (§ tier_assign) |

Held constant: agent scaffold, model, temperature, max steps, tool set, repo snapshot.

## 4. Benchmark & sample

- **Primary:** SWE-bench Verified (human-validated subset) for reliable pass/fail via test execution.
- **Secondary (external validity):** the ETH "developer-committed context files" repo collection, to compare on their own data.
- **Sample size:** power analysis for a non-inferiority test at δ=2pp, α=0.05, power=0.8 → target N tasks (compute in analysis.py). Report achieved power.

## 5. Metrics (dependent variables)

- **Primary quality:** resolved rate (SWE-bench test pass).
- **Cost:** total input+output tokens/task; agent steps; wall-clock (secondary).
- **Efficiency frontier:** resolved-rate vs tokens — report Pareto position, not a single number.
- Per-condition variance; paired where tasks are shared.

## 6. Statistics

- Paired designs across conditions on the same tasks. McNemar's test for paired binary success; bootstrap CIs for rate differences.
- Non-inferiority: one-sided CI on (C2 − C1) success rate vs −δ.
- Cost: Wilcoxon signed-rank on paired token counts.
- Multiple-comparison correction (Holm) across H1–H4.
- Report effect sizes + CIs, not just p-values. Pre-register δ, ε, α before running.

## 7. Threats to validity

- **Construct:** token count ≠ dollar cost across providers; report tokens and note pricing separately.
- **Internal:** agent nondeterminism → fix seeds/temperature=0 where possible; run k repeats, report variance.
- **External:** SWE-bench Python-centric; the ETH secondary set mitigates. State scope limits.
- **Confound:** tiered vs monolithic differ in *content*, not just loading — control by deriving C2 tiers from the SAME source text as C1 (no new information, only reorganized/selectively loaded).
- **Researcher DoF:** pre-registered hypotheses + fixed metrics to avoid p-hacking.

## 8. Novelty delta (what is actually new)

- Not new: tiering as a technique; context files help/hurt (ETH); agent long-term memory (SimpleMem, MemAgent, ACE).
- New: (a) **automatic access-pattern tier assignment** evaluated on task-success, not just cost; (b) a controlled C0/C1/C2/C3 comparison that turns ETH's negative result into a constructive test; (c) cross-project registry activation as an explicit variable.

## 9. Deliverable path

arXiv preprint → LLM/agents or ML4Code **workshop** submission (realistic first venue) → cold-outreach to relevant labs with reproduction+extension in hand.

## 10. Reproducibility

Harness (`research/harness/`) logs full config, seeds, per-task traces, token counts to JSONL. `analysis.py` recomputes all stats from logs. Fixed model/version pins recorded per run.
