# ETH-Fidelity Audit

> Does our harness faithfully test "according to" Gloaguen et al. (arXiv:2602.11988v2)?
> Verified against the paper's Sections 3-4 (fetched 2026-09-04).

## Their actual methodology (verified)
- **Conditions (3):** `None` (no context file) / `LLM` (agent-generated context file) / `Dev` (developer-committed context file; CTXbench only).
- **Datasets:** SWE-bench **Lite** (300 tasks, popular repos, no dev context files) + **CTXbench** (138 instances, 12 niche repos WITH developer-committed context files).
- **Agents (real, multi-step):** Claude Code+Sonnet-4.5; Codex+GPT-5.2 / GPT-5.1-mini; Qwen Code+Qwen3-30b-coder (local via vLLM). temp=0 (Qwen 0.7). Sampled once.
- **Metrics:** success rate (all tests pass, `exec_{RoX}(T)=pass`); **# steps** (env interactions); **cost (USD)**; reasoning tokens.
- **Stats:** Cochran-Mantel-Haenszel (success, stratified by repo); **stratified permutation tests** (steps, cost). Grading = run test suite T in Docker.
- **Headline result:** None vs LLM success p=0.87 (SWE-bench) / 0.37 (CTXbench)  -  NOT significant; cost +20-23% (p<0.001). Dev > LLM (p=0.038).

## Where our harness ALIGNS
- Success = real test-execution pass/fail via SWE-bench Docker grading (swebench_run.py `grade()`). [ok]
- Per-(task,condition) logging of success + tokens + steps to JSONL. [ok]
- temp=0, single sample. [ok]
- Uses SWE-bench (add Lite split) + can add CTXbench. [ok]

## Where our design DIFFERS (extension, not replication  -  stated honestly)
| Aspect | ETH | Ours | Implication |
|---|---|---|---|
| Conditions | None/LLM/Dev | C0 none / C1 monolithic / C2 tiered / C3 auto-tiered | We add TIERED loading  -  the constructive step they left open. Keep None+(a full-file) to bridge to their result. |
| Agent | real multi-step harnesses | single-shot patch (baseline) | Our steps~=1; we CANNOT reproduce their step/cost dynamics until we use a real multi-step harness. Documented limitation. |
| Cost metric | USD + steps + reasoning tokens | tokens (+steps) | Report tokens; map to USD via provider price like they do for Qwen. |
| Stats | CMH + stratified permutation | McNemar + bootstrap | Add CMH (repo-stratified) + permutation to match their tests. |

## Required changes for faithful comparison (TODO before claiming a result)
1. Add ETH's exact conditions (None / LLM / Dev) alongside ours, so C1~="a full context file" bridges to their `LLM`/`Dev`.
2. Use a **real multi-step agent harness** (their step/cost effects vanish with single-shot). This is the biggest fidelity gap.
3. Implement **Cochran-Mantel-Haenszel** (stratify by repo) and **stratified permutation** tests in analysis.py to match their significance testing.
4. Run on **SWE-bench Lite (300)** + ideally CTXbench (138).
5. Report per-repo success (they note SWE-bench is django-heavy -> noisy per-repo).

## Honest bottom line
Our harness is a VALID foundation and grades success the same way (real tests), but it is currently a **single-shot extension**, not a faithful replication of the ETH multi-step-agent study. To claim results comparable to theirs, items 1-4 above are required. Our novel angle (tiered/auto-tiered) is a legitimate extension of their open question, not a contradiction of their finding.
