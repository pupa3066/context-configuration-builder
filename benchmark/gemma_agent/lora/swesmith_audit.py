import pyarrow.parquet as pq, json, re, glob, collections, statistics as st, sys
from tokenizers import Tokenizer
tok = Tokenizer.from_file('/tmp/g4tok.json')
COMP = ['fastapi','requests','rich','httpx','starlette','pydantic','urllib3','click','typer','anyio']
def patch_stats(p):
    files = re.findall(r'^diff --git a/(\S+)', p or '', re.M)
    add = len(re.findall(r'^\+(?!\+\+)', p or '', re.M)); rem = len(re.findall(r'^-(?!--)', p or '', re.M))
    src = [f for f in files if f.endswith('.py') and not re.search(r'(^|/)(tests?|testing)/|test_|_test\.py|reproduce|repro', f)]
    return files, src, add, rem
rows = []
for f in sorted(glob.glob('/tmp/swesmith/tool-*.parquet')):
    for b in pq.ParquetFile(f).iter_batches(batch_size=200, columns=['messages','instance_id','resolved','model','patch']):
        for r in b.to_pylist():
            m = json.loads(r['messages'])
            iid = r['instance_id']; repo = iid.split('.')[0]; kind = iid.split('.')[2].split('__')[0] if iid.count('.') >= 2 else '?'
            tools = collections.Counter(tc['function']['name'] for x in m for tc in (x.get('tool_calls') or []))
            acts = [ (x.get('action') or '') for x in m if x.get('role') == 'assistant']
            sub = [a.split()[0] if a else '' for a in acts]
            text = []
            for x in m:
                c = x.get('content')
                text.append(c if isinstance(c, str) else ''.join(p.get('text','') for p in (c or []) if isinstance(p, dict)))
                for tc in (x.get('tool_calls') or []): text.append(tc['function'].get('arguments',''))
            ntok = len(tok.encode('\n'.join(text)).ids)
            files, src, add, rem = patch_stats(r['patch'])
            rows.append(dict(repo=repo, kind=kind, resolved=r['resolved'], model=r['model'], msgs=len(m), tools=dict(tools),
                             last_submit=bool(acts) and acts[-1].strip().startswith('submit'), ntok=ntok,
                             files=len(files), src=len(src), add=add, rem=rem,
                             sub_actions=collections.Counter(s for s in sub if s).most_common(8)))
    print(f, len(rows), flush=True)
json.dump(rows, open('/tmp/swesmith/audit_rows.json','w'))
print('DONE')
