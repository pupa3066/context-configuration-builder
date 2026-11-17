"""Pool SWE-bench Lite shard outputs and run the registered tests.

Usage: python3 pool_swebench_lite.py OUT.json shard1.json shard2.json ...
Checks: no task twice, and every column of the earlier registered run is reproduced for tasks it covered
(earlier files: SWEBENCH_LITE_retrieval_django.json and the two _partial.json files in this folder).
Tests (exact McNemar, two-sided; Holm within the retrieval family of plan amendment 24):
  coverage:  dense_full vs dense_cap25
  method:    bm25 vs dense_full
  eqtext:    dense_lines8_eqtext vs dense_words400_whole (prediction: short chunks at least as good)
Secondary, uncorrected: bm25_lines8_eqtext vs bm25_words400; the median-based k; best segment vs whole chunk.
"""
import json, math, os, random, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
EARLIER = ['SWEBENCH_LITE_retrieval_django.json', 'SWEBENCH_LITE_retrieval_sympy_partial.json',
           'SWEBENCH_LITE_retrieval_sklearn-matplotlib-astropy-xarray-seaborn_partial.json']
COLS = ['bm25', 'dense_full', 'dense_cap25', 'gold_in_cap25', 'dense_words400_whole', 'dense_words400_bestseg',
        'bm25_words400']


def mcnemar(a, b):
    x = sum(1 for i, j in zip(a, b) if i and not j); y = sum(1 for i, j in zip(a, b) if j and not i); n = x + y
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(x, y) + 1)) / 2 ** n) if n else 1.0
    return dict(first_only=x, second_only=y, p=p)


def boot(h, nb=1000):
    rng = random.Random(0); n = len(h)
    ms = sorted(sum(h[rng.randrange(n)] for _ in range(n)) / n for _ in range(nb))
    return [round(sum(h) / n, 4), round(ms[25], 4), round(ms[975], 4)]


def paired_diff(a, b, nb=10000, seed=0):
    n = len(a); rng = random.Random(seed); d = [x - y for x, y in zip(a, b)]
    ms = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(nb))
    lo, hi = ms[int(0.05 * nb)], ms[int(0.95 * nb) - 1]
    verdict = 'worse' if hi < 0 else ('non-inferior' if lo > -0.10 else 'inconclusive')
    return dict(diff=round(sum(d) / n, 4), ci90=[round(lo, 4), round(hi, 4)], margin_supported=round(max(0.0, -lo), 4),
                verdict_margin_0_10=verdict)


def holm(named):
    s = sorted(named.items(), key=lambda kv: kv[1]); m = len(s); run = 0.0; out = {}
    for i, (k, p) in enumerate(s):
        run = max(run, min(1.0, (m - i) * p)); out[k] = run
    return out


def main(out, files):
    rows, seen, partial = [], set(), []
    for f in files:
        d = json.load(open(f))
        if d.get('partial'): partial.append(f)
        for r in d['rows']:
            assert r['task'] not in seen, f'duplicate task {r["task"]}'
            seen.add(r['task']); rows.append(r)
    old = {}
    for f in EARLIER:
        p = os.path.join(HERE, f)
        if os.path.isfile(p):
            for r in json.load(open(p))['rows']: old[r['task']] = r
    rep = collections.Counter(); diff = []
    for r in rows:
        if r['task'] in old:
            same = all(old[r['task']][c] == r[c] for c in COLS); rep['same' if same else 'different'] += 1
            if not same: diff.append(r['task'])
    H = {c: [r[c] for r in rows] for c in rows[0] if isinstance(rows[0][c], int)}
    tests = {'coverage_dense_full_vs_cap25': mcnemar(H['dense_full'], H['dense_cap25']),
             'method_bm25_vs_dense_full': mcnemar(H['bm25'], H['dense_full']),
             'eqtext_dense_lines8_vs_words400_whole': mcnemar(H['dense_lines8_eqtext'], H['dense_words400_whole'])}
    tests['eqtext_dense_lines8_vs_words400_whole'].update(paired_diff(H['dense_lines8_eqtext'], H['dense_words400_whole']))
    adj = holm({k: v['p'] for k, v in tests.items()})
    for k in tests: tests[k]['holm_family_retrieval'] = adj[k]
    e = tests['eqtext_dense_lines8_vs_words400_whole']
    if e['verdict_margin_0_10'] == 'non-inferior' and e['diff'] > 0 and e['holm_family_retrieval'] < 0.05:
        e['verdict_margin_0_10'] = 'better'
    sec = {'eqtext_bm25_lines8_vs_words400': dict(mcnemar(H['bm25_lines8_eqtext'], H['bm25_words400']),
                                                    **paired_diff(H['bm25_lines8_eqtext'], H['bm25_words400'])),
           'eqtext_median_k_dense': mcnemar(H['dense_lines8_eqtext_med'], H['dense_words400_whole']),
           'bestseg_vs_whole_words400': mcnemar(H['dense_words400_bestseg'], H['dense_words400_whole'])}
    res = dict(N=len(rows), repos=dict(collections.Counter(r['repo'] for r in rows)), partial_inputs=partial,
               reproduction_vs_earlier=dict(rep), reproduction_differences=diff,
               rates={k: boot(v) for k, v in H.items()}, primary=tests, secondary=sec,
               median_k_eq_dense=sorted(r['eqtext']['k_eq_dense'] for r in rows)[len(rows) // 2])
    json.dump(dict(res, rows=rows), open(out, 'w'), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
