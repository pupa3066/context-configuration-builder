# E4B distillation LoRA, amendment 10. Loss on assistant turns only.
import subprocess, glob, sys, os, json, time, re, math
whl = glob.glob('/kaggle/input/**/peft-*.whl', recursive=True)[0]
tw = glob.glob('/kaggle/input/**/transformers-5.13.1-*.whl', recursive=True)[0]
WH = os.path.dirname(tw)  # organizers' wheelhouse: transformers with Gemma 4 support and its pinned dependencies
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-index', '--find-links', WH, tw], check=True)
subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '-q', whl], check=True)
import torch, torch.nn.functional as F, transformers, peft
print('torch', torch.__version__, '| transformers', transformers.__version__, '| peft', peft.__version__, '| gpus', torch.cuda.device_count())
cfgs = [p for p in glob.glob('/kaggle/input/**/config.json', recursive=True) if 'e4b' in p.lower() and 'qat' not in p.lower()]
print('candidate configs', cfgs[:4]); MP = os.path.dirname(cfgs[0])
TOOLS = json.load(open(glob.glob('/kaggle/input/**/tools.json', recursive=True)[0]))
RECS = [json.loads(l) for l in open(glob.glob('/kaggle/input/**/sft_train.jsonl', recursive=True)[0])]
assert all(r['split'] == 'train' and not r['task'].startswith('rich_') for r in RECS)
from transformers import AutoTokenizer, AutoModelForCausalLM
tok = AutoTokenizer.from_pretrained(MP)
def render(msgs, gen=False):
    return tok.apply_chat_template(msgs, tools=TOOLS, tokenize=False, add_generation_prompt=gen)
MAXLEN = 16384; DATA = []; skipped = 0
for r in RECS:
    m = r['messages']; full = render(m)
    spans = []; ok = True
    for i, x in enumerate(m):
        if x['role'] != 'assistant': continue
        pre = render(m[:i], gen=True); upto = render(m[:i + 1])
        if not (full.startswith(upto) and upto.startswith(pre)): ok = False; break
        spans.append((len(pre), len(upto)))
    if not ok: skipped += 1; continue
    enc = tok(full, add_special_tokens=False, return_offsets_mapping=True)
    ids = enc['input_ids']; off = enc['offset_mapping']
    lab = [any(a <= s < b for a, b in spans) for s, _ in off]
    ids, lab = ids[:MAXLEN], lab[:MAXLEN]
    DATA.append((r['task'], ids, lab))
print('records', len(RECS), 'usable', len(DATA), 'skipped (template not prefix-consistent)', skipped)
print('tokens per record: median', sorted(len(d[1]) for d in DATA)[len(DATA) // 2], 'max', max(len(d[1]) for d in DATA),
      '| labeled tokens median', sorted(sum(d[2]) for d in DATA)[len(DATA) // 2])
print('render sample tail:', repr(render(RECS[0]['messages'][:4])[-600:]))
assert DATA, 'no usable records'
model = AutoModelForCausalLM.from_pretrained(MP, dtype=torch.bfloat16, device_map='auto')
print('model class', type(model).__name__)
qn = [n for n, _ in model.named_modules() if n.endswith('q_proj')]; print('q_proj modules', len(qn), qn[:2], qn[-1:])
TARGET = r'^(?!.*(vision|audio)).*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)$'
model.config.use_cache = False
model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False}); model.enable_input_require_grads()
model = peft.get_peft_model(model, peft.LoraConfig(r=16, lora_alpha=32, lora_dropout=0.0, target_modules=TARGET, task_type='CAUSAL_LM'))
model.print_trainable_parameters()
opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
dev = next(model.parameters()).device; ACC = 4; step = 0; t0 = time.time()
for ep in range(2):
    for j, (task, ids, lab) in enumerate(DATA):
        x = torch.tensor([ids], device=dev)
        pos = [k - 1 for k in range(1, len(ids)) if lab[k]]
        keep = torch.tensor(pos, device=dev); tgt = torch.tensor([ids[k + 1] for k in pos], device=dev)
        logits = model(input_ids=x, logits_to_keep=keep).logits[0]
        tgt = tgt.to(logits.device); loss = 0.0
        for a in range(0, logits.shape[0], 1024):
            loss = loss + F.cross_entropy(logits[a:a + 1024].float(), tgt[a:a + 1024], reduction='sum')
        loss = loss / len(pos); (loss / ACC).backward()
        if (j + 1) % ACC == 0 or j == len(DATA) - 1:
            opt.step(); opt.zero_grad(); step += 1
        print(f'epoch {ep} rec {j} {task} tokens {len(ids)} labeled {len(pos)} loss {loss.item():.4f} t {time.time()-t0:.0f}s', flush=True)
OUT = '/kaggle/working/adapters/main_lora'; model.save_pretrained(OUT)
for f in os.listdir(OUT):
    if not f.endswith(('.json', '.safetensors')): os.remove(os.path.join(OUT, f))
print('saved', {f: os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)}, '| optimizer steps', step)
print(json.load(open(os.path.join(OUT, 'adapter_config.json'))))
