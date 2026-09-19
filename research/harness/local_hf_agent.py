"""local_hf_agent.py — run the SWE-bench study on a LOCAL model via Transformers on CUDA (or CPU).

Counterpart to local_agent.py (MLX / Apple Silicon). Same solve() contract, same prompt, same
token accounting (prompt and completion counted with the model's own tokenizer), so runs on the
two backends are comparable. Additive: the MLX path is untouched.

Requires: torch (CUDA build matching your GPU), transformers, and for --int4/--int8 bitsandbytes.
Weights are loaded from a LOCAL directory with local_files_only=True (no model download at run time).

RTX 50-series (Blackwell, sm_120): the default cu121 PyTorch wheels report
torch.cuda.is_available() == True but every kernel fails. Install the cu128 build:
    pip install torch --index-url https://download.pytorch.org/whl/cu128
and check `torch.cuda.get_arch_list()` lists sm_120.

Usage via swebench_run.py:
    --agent local-hf:models/Qwen2.5-Coder-7B-Instruct           # fp16/bf16
    --agent local-hf:models/Qwen2.5-Coder-7B-Instruct@int4       # bitsandbytes nf4
    --agent local-hf:models/Qwen2.5-Coder-7B-Instruct@int8

MODALITY: SWE-bench needs a code-generation model. Vision LoRAs score ~0 and measure nothing.
"""
from __future__ import annotations
import os

from local_agent import _build_prompt  # identical prompt to the MLX agent

# Offline applies to MODEL loading only (set local_files_only below); the dataset fetch in
# swebench_run.py still needs the Hub unless it is already cached.


class LocalHFAgent:
    def __init__(self, model_path: str, precision: str = "fp16",
                 max_tokens: int = 2048, temp: float = 0.0, device: str | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cuda":
            # Fail loudly on the sm_120/cu121 mismatch instead of erroring on the first kernel.
            cap = torch.cuda.get_device_capability()
            arch = f"sm_{cap[0]}{cap[1]}"
            if arch not in torch.cuda.get_arch_list():
                raise RuntimeError(
                    f"GPU is {arch} but this torch build has no {arch} kernels "
                    f"({torch.cuda.get_arch_list()}). Install a matching wheel "
                    f"(RTX 50-series: --index-url https://download.pytorch.org/whl/cu128).")
            free_b, total_b = torch.cuda.mem_get_info()
            free_gb, total_gb = free_b / 2**30, total_b / 2**30
            print(f"[local-hf] {torch.cuda.get_device_name(0)} {arch}: "
                  f"{free_gb:.1f} / {total_gb:.1f} GB VRAM free", flush=True)
            if free_gb < 1.5:
                raise RuntimeError(
                    f"only {free_gb:.1f} GB VRAM free; another process holds the GPU "
                    f"(check nvidia-smi / `ollama ps`). Free it before running, or OOM will hit "
                    f"the long-context conditions first and bias the comparison.")

        kw = {"device_map": self.device}
        if precision in ("int4", "int8"):
            from transformers import BitsAndBytesConfig
            kw["quantization_config"] = (
                BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                   bnb_4bit_compute_dtype=torch.float16)
                if precision == "int4" else BitsAndBytesConfig(load_in_8bit=True))
        elif precision == "bf16":
            kw["torch_dtype"] = torch.bfloat16
        else:
            kw["torch_dtype"] = torch.float16 if self.device == "cuda" else torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True, **kw).eval()
        self.max_tokens, self.temp, self.precision = max_tokens, temp, precision
        self._torch = torch

    def solve(self, task_prompt: str, context: str):
        prompt = _build_prompt(task_prompt, context)
        enc = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        in_tok = int(enc["input_ids"].shape[1])
        gen_kw = {"max_new_tokens": self.max_tokens,
                  "pad_token_id": self.tokenizer.eos_token_id}
        if self.temp > 0:
            gen_kw.update(do_sample=True, temperature=self.temp)
        else:
            gen_kw["do_sample"] = False
        with self._torch.no_grad():
            out = self.model.generate(**enc, **gen_kw)
        new = out[0, in_tok:]
        text = self.tokenizer.decode(new, skip_special_tokens=True)
        return text, in_tok, int(new.shape[0]), 1


def make_local_hf_agent(spec: str):
    """spec: '<local model dir>[@fp16|bf16|int8|int4]'."""
    path, _, prec = spec.partition("@")
    return LocalHFAgent(path, precision=prec or "fp16")
