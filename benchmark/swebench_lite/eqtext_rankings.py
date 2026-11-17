"""SWE-bench Lite retrieval with recorded gold ranks and the equal-text chunk-length comparison.

Same queries, targets, chunking, retrievers and k as the registered SWE-bench Lite run
(research/PREREG_tiered_context_gemma_harness.md, SWE-bench Lite sections); the earlier columns are computed by the
same code, so a rerun must reproduce them. Added per task: the rank of the first gold chunk for every retriever
(hit at any k is then rank < k), and the equal-text columns:
  W400   = words in the top 6 whole 400-word chunks returned (dense, and separately BM25)
  k_eq   = smallest k whose top-k 8-line results (same retriever) contain at least W400 words (primary)
  k_med  = ceil(W400 / median words per 8-line chunk) (sensitivity, the median-based reading)
  dense_lines8_eqtext = gold 8-line chunk ranked < k_eq (dense); bm25_lines8_eqtext likewise for BM25;
  *_eqtext_med use k_med.
Known limit, kept for reproducibility: the 25 percent coverage sample indexes chunks in os.walk order, which differs
between filesystems; reruns on Kaggle reproduce the registered run, other machines may not for that column.
Params (env or defaults): SHARD_REPOS (comma list), SLICE ("start:end" over the shard's sorted eligible tasks),
TASK_IDS (comma list, top-up runs), OUT (output path), SMOKE ("1" = first 2 eligible tasks), GUARD_S (stop and save after this many seconds).
"""
import subprocess, sys, os, json, re, hashlib, collections, random, math, time, urllib.request, statistics

SHARD_REPOS = os.environ.get('SHARD_REPOS', 'pallets/flask').split(',')
SLICE = os.environ.get('SLICE', ':')
OUT = os.environ.get('OUT', 'SWEBENCH_LITE_eqtext.json')
SMOKE = os.environ.get('SMOKE', '0') == '1'
GUARD_S = float(os.environ.get('GUARD_S', str(10.5 * 3600)))
WORK = os.environ.get('WORK', '/tmp/swl_work')
CODE_SHA = '248667dab55462ab200229a0ca1df6c558be6f2f'  # committed BM25 and tokenizer, as in the registered run

os.makedirs(WORK, exist_ok=True)
REPO = os.path.join(WORK, 'cck')
if not os.path.isdir(REPO):
    subprocess.run(f'git clone -q https://github.com/pupa3066/context-configuration-builder.git {REPO}', shell=True, check=True)
subprocess.run(f'git -C {REPO} checkout -q {CODE_SHA}', shell=True, check=True)
sys.path.insert(0, os.path.join(REPO, 'benchmark'))
from compare_algorithms import BM25, toks  # noqa: E402
import numpy as np  # noqa: E402
from fastembed import TextEmbedding  # noqa: E402
EMB = TextEmbedding('BAAI/bge-small-en-v1.5')


def bm25_order(texts, q):
    bm = BM25(texts); qt = toks(q)
    return sorted(range(bm.N), key=lambda i: bm.score(qt, bm.docs[i]), reverse=True)


rows, off = [], 0
while True:
    url = ('https://datasets-server.huggingface.co/rows?dataset=princeton-nlp%2FSWE-bench_Lite&config=default'
           f'&split=test&offset={off}&length=100')
    d = json.load(urllib.request.urlopen(url, timeout=60)); rows += [r['row'] for r in d['rows']]; off += 100
    if off >= d['num_rows_total']: break
TEST_RE = re.compile(r'(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$')
HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+', re.M)


def gold_edits(patch):
    edits = collections.defaultdict(list)
    for part in re.split(r'(?m)^diff --git ', patch):
        m = re.search(r'^--- a/(\S+)', part, re.M)
        if not m: continue
        cur = m.group(1)
        for h in HUNK.finditer(part):
            a = int(h.group(1)); n = int(h.group(2)) if h.group(2) is not None else 1
            edits[cur].append((a, a + max(n, 1) - 1))
    return {p: r for p, r in edits.items() if p.endswith('.py') and not TEST_RE.search(p)}


eligible = [(r, gold_edits(r['patch'])) for r in rows]
excluded = sum(1 for r, e in eligible if not e)
eligible = sorted([(r, e) for r, e in eligible if e], key=lambda x: x[0]['instance_id'])
eligible = [x for x in eligible if x[0]['repo'] in SHARD_REPOS]
a, b = SLICE.split(':'); eligible = eligible[int(a) if a else None:int(b) if b else None]
TASK_IDS = [x for x in os.environ.get('TASK_IDS', '').split(',') if x]  # top-up runs: exact task list, selection only
if TASK_IDS: eligible = [x for x in eligible if x[0]['instance_id'] in TASK_IDS]
if SMOKE: eligible = eligible[:2]
print('tasks in this run:', len(eligible), '| repos:', dict(collections.Counter(r['repo'] for r, _ in eligible)), flush=True)


def repo_dir(repo):
    d = os.path.join(WORK, 'src', repo.replace('/', '__'))
    if not os.path.isdir(d):
        subprocess.run(f'git clone -q --filter=blob:none https://github.com/{repo}.git {d}', shell=True, check=True)
    return d


def files_at(repo, commit):
    d = repo_dir(repo)
    subprocess.run(f'git -C {d} checkout -q -f {commit}', shell=True, check=True)
    out = {}
    for root, ds, fs in os.walk(d):
        ds[:] = [x for x in ds if x != '.git']
        for f in fs:
            if f.endswith('.py'):
                p = os.path.join(root, f); rel = os.path.relpath(p, d)
                if TEST_RE.search(rel): continue
                try: out[rel] = open(p, encoding='utf-8', errors='replace').read()
                except OSError: pass
    return out


def chunks_lines(files, n=8):
    meta = []
    for rel, txt in files.items():
        L = txt.splitlines()
        for i in range(0, len(L), n):
            blk = L[i:i + n]
            if any(x.strip() for x in blk): meta.append((rel, i + 1, i + len(blk), '\n'.join(blk)))
    return meta


def chunks_words(files, n=400):
    meta = []
    for rel, txt in files.items():
        L = txt.splitlines(); start = 0; words = 0
        for i, line in enumerate(L):
            words += len(line.split())
            if words >= n or i == len(L) - 1:
                blk = L[start:i + 1]
                if any(x.strip() for x in blk): meta.append((rel, start + 1, i + 1, '\n'.join(blk)))
                start = i + 1; words = 0
    return meta


CACHE = {}


def embed(texts):
    keys = [hashlib.sha1(t.encode()).hexdigest() for t in texts]
    todo = [i for i, k in enumerate(keys) if k not in CACHE]
    if todo:
        for k, v in zip([keys[i] for i in todo], EMB.embed([texts[i] for i in todo], batch_size=64)):
            CACHE[k] = np.asarray(v, dtype=np.float32)
    M = np.stack([CACHE[k] for k in keys]); return M / np.linalg.norm(M, axis=1, keepdims=True)


def windows(text, win=400, stride=300):
    w = text.split()
    if len(w) <= win: return [text]
    return [' '.join(w[i:i + win]) for i in range(0, max(1, len(w) - win + stride), stride)]


def qvec(q):
    v = np.asarray(next(iter(EMB.query_embed([q]))), dtype=np.float32); return v / np.linalg.norm(v)


def overlaps(j, meta, edits):
    rel, s, e, _ = meta[j]
    return any(s <= y and x <= e for x, y in edits.get(rel, []))


def is_hit(sel, meta, edits):
    return int(any(overlaps(j, meta, edits) for j in sel))


def first_rank(order, meta, edits):
    for r, j in enumerate(order):
        if overlaps(j, meta, edits): return r
    return None


def nwords(meta, sel):
    return sum(len(meta[j][3].split()) for j in sel)


K = 6; ROWS = []; t0 = time.time(); stopped = False
for n_done, (r, ed) in enumerate(eligible, 1):
    if time.time() - t0 > GUARD_S:
        stopped = True; print('guard reached, saving and stopping', flush=True); break
    files = files_at(r['repo'], r['base_commit'])
    ed = {p: v for p, v in ed.items() if p in files}
    if not ed: continue
    q = r['problem_statement'][:4000]
    row = dict(task=r['instance_id'], repo=r['repo'])
    # Registered columns, same code as the earlier run.
    meta = chunks_lines(files); texts = [m[3] for m in meta]
    ob8 = bm25_order(texts, q)
    row['bm25'] = is_hit(ob8[:K], meta, ed)
    E = embed(texts); qv = qvec(q); s = E @ qv; od8 = list(np.argsort(-s))
    row['dense_full'] = is_hit(od8[:K], meta, ed)
    rng = random.Random(0); idx = sorted(rng.sample(range(len(meta)), max(1, len(meta) // 4)))
    s25 = s[idx]; oc25 = [idx[j] for j in np.argsort(-s25)]
    row['dense_cap25'] = is_hit(oc25[:K], meta, ed)
    row['gold_in_cap25'] = is_hit(idx, meta, ed)
    m4 = chunks_words(files); t4 = [m[3] for m in m4]
    s4 = embed(t4) @ qv; od4 = list(np.argsort(-s4))
    row['dense_words400_whole'] = is_hit(od4[:K], m4, ed)
    seg = []; owner = []
    for j, t in enumerate(t4):
        for w in windows(t): seg.append(w); owner.append(j)
    sw = embed(seg) @ qv; best = np.full(len(t4), -9.0)
    for o, v in zip(owner, sw): best[o] = max(best[o], v)
    obs4 = list(np.argsort(-best))
    row['dense_words400_bestseg'] = is_hit(obs4[:K], m4, ed)
    ob4 = bm25_order(t4, q)
    row['bm25_words400'] = is_hit(ob4[:K], m4, ed)
    # Added: gold ranks and equal-text columns.
    row['rank'] = dict(bm25=first_rank(ob8, meta, ed), dense_full=first_rank(od8, meta, ed),
                       dense_cap25=first_rank(oc25, meta, ed), dense_words400_whole=first_rank(od4, m4, ed),
                       dense_words400_bestseg=first_rank(obs4, m4, ed), bm25_words400=first_rank(ob4, m4, ed))
    med8 = statistics.median(len(x.split()) for x in texts)
    W400d = nwords(m4, od4[:K]); W400b = nwords(m4, ob4[:K])

    def k_cum(order, target):
        tot = 0
        for k, j in enumerate(order, 1):
            tot += len(meta[j][3].split())
            if tot >= target: return k
        return len(order)
    kd, kb = k_cum(od8, W400d), k_cum(ob8, W400b)
    kdm = max(1, math.ceil(W400d / max(med8, 1))); kbm = max(1, math.ceil(W400b / max(med8, 1)))
    row['eqtext'] = dict(med8=med8, W400_dense=W400d, W400_bm25=W400b, k_eq_dense=kd, k_eq_bm25=kb,
                         words8_at_k_eq_dense=nwords(meta, od8[:kd]), words8_at_k_eq_bm25=nwords(meta, ob8[:kb]),
                         k_med_dense=kdm, k_med_bm25=kbm)
    row['dense_lines8_eqtext'] = is_hit(od8[:kd], meta, ed)
    row['bm25_lines8_eqtext'] = is_hit(ob8[:kb], meta, ed)
    row['dense_lines8_eqtext_med'] = is_hit(od8[:kdm], meta, ed)
    row['bm25_lines8_eqtext_med'] = is_hit(ob8[:kbm], meta, ed)
    ROWS.append(row)
    print(n_done, {k: v for k, v in row.items() if k not in ('rank', 'eqtext')}, '| k_eq', kd, kb,
          f'| chunks {len(meta)} | {time.time() - t0:.0f}s', flush=True)
    json.dump(dict(rows=ROWS, partial=True), open(OUT, 'w'))

json.dump(dict(rows=ROWS, partial=stopped, shard=SHARD_REPOS, slice=SLICE, n_eligible_in_slice=len(eligible),
               excluded_no_py_edit_all300=excluded, code_sha=CODE_SHA, k=K, seconds=round(time.time() - t0)),
          open(OUT, 'w'), indent=1)
print('saved', OUT, len(ROWS), 'rows; stopped at guard:', stopped)
