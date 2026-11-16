import json, collections, statistics as st
R = json.load(open('/tmp/swesmith/audit_rows.json'))
def q(v): v=sorted(v); return f"median {st.median(v):.0f}, p25 {v[len(v)//4]}, p75 {v[3*len(v)//4]}, p90 {v[int(.9*len(v))]}"
print('rows', len(R), 'models', collections.Counter(r['model'] for r in R).most_common(3))
print('resolved', sum(r['resolved'] for r in R))
res = [r for r in R if r['resolved']]
print('unique repos (all)', len({r['repo'] for r in R}), '| resolved', len({r['repo'] for r in res}))
COMP = ['fastapi','requests','rich','httpx','starlette','pydantic','urllib3','click','typer','anyio']
for c in COMP:
    hits = sorted({r['repo'] for r in R if c in r['repo'].lower().split('__')[-1].replace('-','_').split('_') or r['repo'].lower().endswith('__'+c)})
    if hits: print('overlap', c, hits, sum(r['repo'] in hits for r in res), 'resolved rows')
print('bug kinds (resolved)', collections.Counter(r['kind'] for r in res).most_common(12))
print('tools (resolved, calls)', sum((collections.Counter(r['tools']) for r in res), collections.Counter()).most_common(10))
sa = sum((collections.Counter(dict(r['sub_actions'])) for r in res), collections.Counter())
print('str_replace_editor subcommands not split; action heads', sa.most_common(10))
print('last action is submit (resolved)', sum(r['last_submit'] for r in res), 'of', len(res))
print('content tokens (Gemma 4 tokenizer, chat template excluded), resolved:', q([r['ntok'] for r in res]))
for L in (8000, 12000, 16000, 24000, 32000):
    print(f'  resolved fitting {L}:', sum(r['ntok'] <= L for r in res), '| and last submit:', sum(r['ntok'] <= L and r['last_submit'] for r in res))
print('messages per run, resolved:', q([r['msgs'] for r in res]))
print('patch files, resolved:', q([r['files'] for r in res]), '| non-test .py files:', q([r['src'] for r in res]), '| multi-src-file', sum(r['src']>1 for r in res))
print('patch changed lines, resolved:', q([r['add']+r['rem'] for r in res]))
print('runs with extra files besides source (repro scripts etc.):', sum(r['files']>r['src'] for r in res))
EXC = {'encode__starlette','pydantic__pydantic','pallets__click'}
U = [r for r in res if r['last_submit'] and r['src'] >= 1 and r['repo'] not in EXC]
print('\nUSABLE base (resolved, ends in submit, edits >=1 non-test .py, no overlapping repo):', len(U), 'runs,', len({r['repo'] for r in U}), 'repos')
print('  models', collections.Counter(r['model'] for r in U).most_common())
for L in (8000, 12000, 16000, 24000): print(f'  fitting {L} content tokens:', sum(r['ntok'] <= L for r in U))
U16 = [r for r in U if r['ntok'] <= 16000]
print('  within 16k: bug kinds', collections.Counter(r['kind'] for r in U16).most_common(6))
print('  within 16k: changed lines', q([r['add']+r['rem'] for r in U16]), '| multi-src-file', sum(r['src']>1 for r in U16))
print('  all usable: changed lines', q([r['add']+r['rem'] for r in U]))
print('resolved with empty patch field:', sum(r['files']==0 for r in res))
