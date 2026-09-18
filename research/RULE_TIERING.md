# Rule-Tiering: Moving Formatting Rules Off the Always-On Path

> Branch: feature/token-cost-rule-tiering. A measured application of the CCK tiering thesis to the
> agent's OWN rule set: formatting rules that only matter when drafting public text were moved from
> the always-on tier to an on-demand appendix, with a one-line stub kept always-on so the rules still
> fire. Measured on the author's live deployment (real gpt2-BPE). Structure/cost result, not task quality.

## The problem
Governance rules were tiered to on-demand earlier (always-on fell to ~3068 tokens). Then four
formatting rules (10b-10e: identifier-plain-text, prose-only markup, punctuation, spelling, no
meta-commentary) were added to the always-on rule file, which grew it back to 4273 tokens per turn.
Those rules only apply when DRAFTING PUBLIC TEXT (Figshare/GitHub/ORCID/README/PR/paper); on a debug,
commit, or measurement turn they are dead weight loaded every turn.

## The change
Same lossless pattern as the governance and three-location work:
- Full detail of 10b-10e moved to on-demand: ~/.kiro/on-demand/formatting-appendix.md (loads only when
  a task involves drafting public text; bootstrap step 2b triggers it).
- A one-line stub kept in the always-on rule file, so the rule still fires every turn ("identifier
  fields plain; markup only in prose; plain punctuation; American English; left-align; no
  meta-commentary; [detail: appendix]").

## Measured result (real gpt2-BPE, live deployment)
| State | always-on tokens/turn |
|---|---|
| Before (formatting rules always-on) | 4273 |
| After (stub always-on, detail on-demand) | 3304 |
| Saving | 969 tokens/turn (22.7%) |

```
tokens/turn (always-on)
4273 | ####################################  before
3304 | ###########################           after   (-969, -22.7%)
     +----------------------------------------------
       formatting-rule detail moved to on-demand; stub retained
```

## Regression test (rules must still fire)
Lossless tiering requires the rule to remain bindable. Verified:
- Formatting stub present in always-on core: PASS (fires every turn).
- All four rules (10b, 10c, 10d, 10e) resolvable in the on-demand appendix: PASS.
- Key facts reachable (em-dash ban, meta-commentary ban, American English, plain identifier fields,
  left-align/no-justify): PASS in both stub and appendix.
- Bootstrap triggers the appendix load on public-text tasks: PASS.
No rule lost; the change is lossless relocation, not deletion.

## Difference vs sibling branches
- three-location-tiering: moved governance + cross-links off always-on (3-location structure). This
  branch extends the same idea to the FORMATTING rules specifically.
- lossless / summarization branches: about PROJECT context (skills). This branch is about the agent's
  RULE tier.

## Scope
Measured, live, structure/cost only. Not a task-quality claim. Reproduce with the steering token
measurement (research/measure_three_location.py counts steering + on-demand + skills).
