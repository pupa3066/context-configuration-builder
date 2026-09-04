# The Story

## Why I built this

I wasn't trying to make a product. I was drowning in my own projects.

I run a dozen-plus repositories at once — model training, a hardware paper, shipping apps, research notes. Every morning I'd open my AI agent and spend the first twenty minutes re-explaining what a project was, what I'd decided yesterday, and how a result in one repo mattered to a paper in another. The agent was brilliant and amnesiac. Every session started from zero.

The obvious fix — paste everything into the agent's context so it "remembers" — just moved the pain to my token bill. Context that loads every single turn gets expensive fast, and most of it is irrelevant to the task in front of you.

So I asked a sharper question: **what if you separate what the agent remembers from what it costs to remember it?**

## The insight

Split context by *how often it's needed*, not by topic:
- A tiny **always-on** layer: rules + a one-line index of every project + the links between them.
- An **on-demand** layer: each project's deep context, loaded only when I actually touch that project.
- A **zero-cost** layer: a searchable mirror that costs nothing until I query it.

Then a one-line **registry** decides which projects are "awake." Flip a marker, a project enters or leaves the agent's working memory.

## The moment it clicked

I tested it honestly — fresh agent session, no prior chat, tools off. I asked it what data my hardware paper still needed. It answered correctly: *another project had already measured it, here are the numbers, and here's what's still missing.* It had turned a pile of disconnected repos into one queryable research graph. Measured: 40.9% smaller per-turn context at four projects, scaling toward ~89% as projects grow. That's the difference between an agent that autocompletes and one that remembers.

## What it became

I extracted the mechanism from my personal data, made it work on any agent (Kiro, Claude Code, Cursor, or a plain LLM preamble), and wrote it up. The same system that untangled my own work is now something anyone juggling many projects can install in one command.

I built persistent memory for my AI because I needed it. It changed how I work. That's the whole pitch.
