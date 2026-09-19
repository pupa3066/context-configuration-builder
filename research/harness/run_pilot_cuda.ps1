# run_pilot_cuda.ps1 — SWE-bench pilot on a local NVIDIA GPU (Windows/WSL2 host).
# Mirrors run_real.md steps 2-4 for the local-hf agent. Run from the repo root.
# Prereqs: Docker Desktop running; requirements.txt + requirements-cuda.txt installed;
#          weights pre-downloaded to $Model (offline at run time).
param(
  [string]$Model = "models/Qwen2.5-Coder-7B-Instruct@int4",
  [string]$Split = "verified",
  [int]$Limit = 10,
  [string]$Conditions = "C0,C1,C2,C3",
  [int]$Repeats = 1,
  [string]$Out = "research/harness/runs_pilot_cuda.jsonl"
)
$env:HF_HUB_OFFLINE = "1"; $env:TRANSFORMERS_OFFLINE = "1"
python -c "import torch; cap=torch.cuda.get_device_capability(); a=f'sm_{cap[0]}{cap[1]}'; print('gpu', torch.cuda.get_device_name(0), a, 'in build:', a in torch.cuda.get_arch_list())"
if ($LASTEXITCODE -ne 0) { Write-Error "torch/CUDA check failed"; exit 1 }
python research/harness/swebench_run.py --agent "local-hf:$Model" --split $Split --limit $Limit --dry-config
if ($LASTEXITCODE -ne 0) { exit 1 }
python research/harness/swebench_run.py --agent "local-hf:$Model" --split $Split --limit $Limit `
  --conditions $Conditions --repeats $Repeats --out $Out
python research/harness/analysis.py $Out
