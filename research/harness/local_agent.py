"""local_agent.py — run the SWE-bench study on a LOCAL model via MLX (Apple Silicon).

Zero API cost. Requires: mlx_lm installed and a CODE-CAPABLE model (e.g.
mlx-community/Qwen2.5-Coder-7B-Instruct-4bit). Token counts are the real
tokenizer token counts of the prompt and generated completion.

IMPORTANT (modality): SWE-bench needs a code-generation model. Vision LoRAs
(SmolVLM/SDXL) trained for image tasks are NOT valid here and will score ~0
across all conditions — that measures nothing about context tiering. Use a
code/instruct LLM as the backend.

Usage via swebench_run.py:  --agent local:mlx-community/Qwen2.5-Coder-7B-Instruct-4bit
"""
from __future__ import annotations

SYSTEM = (
    "You are a software engineering agent. Given a repository issue and optional "
    "context, output ONLY a unified diff (git patch) that resolves the issue. "
    "No prose, no fences — just the diff starting with 'diff --git'."
)

def _build_prompt(task_prompt: str, context: str) -> str:
    ctx = f"\n\n# Repository context\n{context}\n" if context else ""
    return (f"<|system|>\n{SYSTEM}\n<|user|>\n# Issue\n{task_prompt}{ctx}\n"
            f"\n# Output a unified diff.\n<|assistant|>\n")

class LocalMLXAgent:
    def __init__(self, model_path: str, max_tokens: int = 2048, temp: float = 0.0):
        from mlx_lm import load, generate
        self._generate = generate
        self.model, self.tokenizer = load(model_path)
        self.max_tokens, self.temp = max_tokens, temp

    def solve(self, task_prompt: str, context: str):
        prompt = _build_prompt(task_prompt, context)
        # real prompt token count from the model's own tokenizer
        in_tok = len(self.tokenizer.encode(prompt))
        text = self._generate(self.model, self.tokenizer, prompt=prompt,
                              max_tokens=self.max_tokens, verbose=False)
        out_tok = len(self.tokenizer.encode(text))
        return text, in_tok, out_tok, 1

def make_local_agent(model_path: str):
    return LocalMLXAgent(model_path)
