"""agents.py  -  real LLM agents for the SWE-bench pipeline (NOT mocks).

Each agent takes (task_prompt, context) and returns a unified-diff patch plus
REAL token counts from the provider response. Providers are pluggable; keys via env.

Usage is exercised by swebench_run.py. Requires: openai and/or anthropic installed
and OPENAI_API_KEY / ANTHROPIC_API_KEY set. No fabricated numbers: token counts come
from the API usage fields; if a call fails, it raises (logged as an error, not faked).
"""
from __future__ import annotations
import os
from tenacity import retry, wait_exponential, stop_after_attempt

SYSTEM = (
    "You are a software engineering agent. Given a repository issue and optional "
    "context, output ONLY a unified diff (git patch) that resolves the issue. "
    "No prose, no fences  -  just the diff starting with 'diff --git'."
)

def _build_user(task_prompt: str, context: str) -> str:
    ctx = f"\n\n# Repository context\n{context}\n" if context else ""
    return f"# Issue\n{task_prompt}{ctx}\n\n# Output: a unified diff that resolves the issue."

class OpenAIAgent:
    def __init__(self, model="gpt-4o-mini", temperature=0.0):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model, self.temperature = model, temperature

    @retry(wait=wait_exponential(min=2, max=30), stop=stop_after_attempt(4))
    def solve(self, task_prompt: str, context: str):
        r = self.client.chat.completions.create(
            model=self.model, temperature=self.temperature,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": _build_user(task_prompt, context)}],
        )
        patch = r.choices[0].message.content or ""
        u = r.usage
        return patch, u.prompt_tokens, u.completion_tokens, 1  # steps=1 (single-shot)

class AnthropicAgent:
    def __init__(self, model="claude-3-5-sonnet-20241022", temperature=0.0, max_tokens=4096):
        import anthropic
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens

    @retry(wait=wait_exponential(min=2, max=30), stop=stop_after_attempt(4))
    def solve(self, task_prompt: str, context: str):
        r = self.client.messages.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            system=SYSTEM,
            messages=[{"role": "user", "content": _build_user(task_prompt, context)}],
        )
        patch = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return patch, r.usage.input_tokens, r.usage.output_tokens, 1

def make_agent(spec: str):
    """spec like 'openai:gpt-4o-mini', 'anthropic:claude-...', or
    'local:mlx-community/Qwen2.5-Coder-7B-Instruct-4bit' (MLX, zero API cost)."""
    provider, _, model = spec.partition(":")
    if provider == "openai":
        return OpenAIAgent(model or "gpt-4o-mini")
    if provider == "anthropic":
        return AnthropicAgent(model or "claude-3-5-sonnet-20241022")
    if provider == "local":
        from local_agent import make_local_agent
        if not model:
            raise ValueError("local agent requires a model path")
        return make_local_agent(model)
    if provider == "local-hf":
        from local_hf_agent import make_local_hf_agent
        if not model:
            raise ValueError("local-hf agent requires a model path, e.g. "
                             "local-hf:google/gemma-2b-it")
        return make_local_hf_agent(model)
    raise ValueError(f"unknown provider: {provider}")
