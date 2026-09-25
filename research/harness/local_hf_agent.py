"""local_hf_agent.py - SWE-bench agent using HuggingFace Transformers + optional bitsandbytes.

Runs on any CUDA GPU (e.g. Kaggle T4/P100) or CPU. Zero API cost.
Use --agent local-hf:<model> in swebench_run.py.

Requirements: pip install transformers accelerate bitsandbytes
K3 gate: first printed line names the model + free VRAM at startup.
"""
from __future__ import annotations
import os

SYSTEM = (
    "You are a software engineering agent. Given a repository issue and optional "
    "context, output ONLY a unified diff (git patch) that resolves the issue. "
    "No prose, no fences - just the diff starting with 'diff --git'."
)

def _build_prompt(task_prompt: str, context: str) -> str:
    ctx = f"\n\n# Repository context\n{context}\n" if context else ""
    return (f"<|system|>\n{SYSTEM}\n<|user|>\n# Issue\n{task_prompt}{ctx}"
            f"\n\n# Output a unified diff.\n<|assistant|>\n")

class LocalHFAgent:
    def __init__(self, model_path: str, max_new_tokens: int = 2048,
                 load_in_4bit: bool = False, load_in_8bit: bool = False):
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

        if torch.cuda.is_available():
            free_gb = torch.cuda.mem_get_info()[0] / 1e9
            print(f"local-hf agent: model={model_path}  free_vram={free_gb:.1f}GB", flush=True)
            if free_gb < 1.5:
                raise RuntimeError(f"Insufficient VRAM ({free_gb:.1f}GB < 1.5GB min); "
                                   "free GPU memory before running.")
        else:
            print(f"local-hf agent: model={model_path}  device=cpu", flush=True)

        quant = None
        if load_in_4bit:
            quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
        elif load_in_8bit:
            quant = BitsAndBytesConfig(load_in_8bit=True)

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=False, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, quantization_config=quant,
            device_map="auto", torch_dtype=torch.float16,
            local_files_only=False, trust_remote_code=True)
        self.max_new_tokens = max_new_tokens

    def solve(self, task_prompt: str, context: str):
        import torch
        prompt = _build_prompt(task_prompt, context)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        in_tok = inputs["input_ids"].shape[-1]
        with torch.no_grad():
            out = self.model.generate(
                **inputs, max_new_tokens=self.max_new_tokens,
                do_sample=False, temperature=1.0, pad_token_id=self.tokenizer.eos_token_id)
        generated = out[0][in_tok:]
        text = self.tokenizer.decode(generated, skip_special_tokens=True)
        return text, in_tok, len(generated), 1


def make_local_hf_agent(model_path: str, **kwargs):
    return LocalHFAgent(model_path, **kwargs)
