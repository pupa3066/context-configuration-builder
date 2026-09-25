# The Story

## Why I built this

I wasn't trying to make a product. I was drowning in my own projects.

I run a dozen-plus repositories at once, model training, a hardware paper, shipping apps, research notes. Every morning I'd open my AI agent and spend the first twenty minutes re-explaining what a project was, what I'd decided yesterday, and how a result in one repo mattered to a paper in another. The agent was brilliant and amnesiac. Every session started from zero.

The obvious fix, paste everything into the agent's context so it "remembers", just moved the pain to my token bill. Context that loads every single turn gets expensive fast, and most of it is irrelevant to the task in front of you.

So I asked a sharper question: **what if you separate what the agent remembers from what it costs to remember it?**

## The insight

Split context by *how often it's needed*, not by topic:
- A tiny **always-on** layer: rules + a one-line index of every project + the links between them.
- An **on-demand** layer: each project's deep context, loaded only when I actually touch that project.
- A **zero-cost** layer: a searchable mirror that costs nothing until I query it.

Then a one-line **registry** decides which projects are "awake." Flip a marker, a project enters or leaves the agent's working memory.

## The moment it clicked

I tested it honestly, fresh agent session, no prior chat, tools off. I asked it what data my hardware paper still needed. It answered correctly: *another project had already measured it, here are the numbers, and here's what's still missing.* It had turned a pile of disconnected repos into one queryable research graph. Measured: 40.9% smaller per-turn context at four projects, scaling toward ~89% as projects grow. That's the difference between an agent that autocompletes and one that remembers.

## What it became

I extracted the mechanism from my personal data, made it work on any agent (Kiro, Claude Code, Cursor, or a plain LLM preamble), and wrote it up. The same system that untangled my own work is now something anyone juggling many projects can install in one command.

I built persistent memory for my AI because I needed it. It changed how I work. That's the whole pitch.

## What the measurements showed (2026-09-25 update)

The kit made a specific, testable claim: for code, keyword retrieval surfaces the right chunk better than embedding similarity, because identifiers carry the signal. I tested that, then tried hard to break my own result.

A first pass compared BM25 (keyword) against a compact embedding model on conceptual questions mined from code. Keyword retrieval won by a wide margin. But a fair critic would note the scoring favored keywords: the answer was an identifier string, and keyword search matches strings. So I re-scored under three metrics, including one deliberately built to favor the embedding model (it counts a hit when a retrieved chunk is merely close in meaning, no exact token needed).

At a small pilot the keyword advantage looked large across all three metrics. When I scaled up (more questions, three repositories, a larger index budget), the picture changed honestly: the embedding model recovered a lot of ground, gaining about twenty points on the loosest metric. Reading across the two scales, much of the pilot's large gap turned out to be an artifact of an index cap that had starved the embedding arm, not a fundamental weakness. The one place keyword retrieval kept a clean, repeatable lead was the strictest metric: surfacing the actual definition line, where the symbol is defined and where an editing agent needs to land.

So the honest headline is narrower and stronger than the pilot suggested: keyword retrieval holds a modest, dependable edge for finding where code is defined, once you control for how much of the codebase each method is allowed to see. Whether that retrieval edge translates into an agent fixing more bugs is a separate question, measured by a separate experiment that is still to come. These numbers describe retrieval, not task success.

## What I learned by measuring it

Once the tiering worked, a sharper question followed: when an agent needs a fact from a big codebase,
what is the cheapest way to put that fact in front of it? I turned that into a measured comparison,
not an opinion. On a set of real questions with a real tokenizer, I compared injecting the whole
context, tiering it, summarizing it, and retrieving only the relevant pieces.

Two results stood out, and I report them as a pilot, not a settled law:
- Retrieving a few relevant pieces cost about 99 percent fewer per-turn tokens than injecting the
  whole context, while still answering most questions.
- For fact recall on identifier-heavy questions, plain keyword retrieval beat semantic embedding
  retrieval. The reason is simple once measured: identifiers like version numbers, function names,
  and ids carry little meaning for an embedding model, so it misses the exact lines a keyword match
  finds. Summarizing the context saved almost nothing here, because code and identifiers are the part
  you cannot safely drop.

The honest caveat: this is a small-sample study on structure and cost, not task success. The code,
the questions, and the numbers are public in the repo so anyone can rerun and check them. The through
line with the memory work is one idea: spend the expensive resource only where it changes the outcome.

## What the measurements showed

Why: once tiering worked, the sharper question was how to put a needed fact in front of an agent for
the fewest tokens without losing the fact. I ran two pilot studies with a real gpt2 BPE tokenizer on
real public repositories and report them as preliminary, not settled. Both studies score a
grounding-retention proxy (is the needed content present in the assembled context), NOT task success.

What (study one, token cost, N=195 identifier-recall questions on requests, click, black): injecting
the whole context (monolithic) answered the proxy at 1.0 but cost 471812 tokens per turn. Summarizing
first (summarized_L0.5) cost 471551 tokens, saving almost nothing, because code and identifiers are
the part you cannot safely drop. Keyword retrieval of a few relevant chunks held grounding retention
at or above 0.98 while collapsing cost: BM25 k3 kept 0.9846 at 309 tokens, k6 kept 0.9897 at 624
tokens, k10 kept 0.9949 at 1061 tokens. Against monolithic that is roughly a 99.8 percent per-turn
token cut at k3 while retaining at least 0.98 of the grounding proxy. No context answered 0.

What (study two, semantic versus lexical, N=100 conceptual questions, question-only queries with no
fact leak): plain keyword retrieval beat semantic embedding retrieval. BM25 scored 0.90 with a 95
percent interval of 0.84 to 0.95; a bge-small semantic index scored 0.65 with an interval of 0.55 to
0.74. On paired questions, 30 were answerable only by BM25 and 5 only by semantic. The verdict was
that lexical wins for this identifier-heavy fact recall, because version numbers, function names, and
ids carry little meaning for an embedding model, so it misses the exact lines a keyword match finds.

How this connects: it is the same idea as the memory tiering, spend the expensive resource only where
it changes the outcome. The code, questions, and numbers are public so anyone can rerun them:
benchmark/POWERED_RESULTS.json, benchmark/CONCEPTUAL_RESULTS.json,
benchmark/conceptual_semantic_vs_lexical.py, and benchmark/compare_algorithms_scaled.py. These are
pilot-scale results on structure and cost, a grounding-retention proxy NOT task success.
