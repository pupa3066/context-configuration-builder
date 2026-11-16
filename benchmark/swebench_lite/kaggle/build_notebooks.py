"""Build the 9 SWE-bench Lite rerun notebooks (CPU, internet on, private) from eqtext_rankings.py."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, '..', 'eqtext_rankings.py')).read()
SCI = 'matplotlib/matplotlib,scikit-learn/scikit-learn,astropy/astropy,pydata/xarray,mwaskom/seaborn'
DEV = 'pytest-dev/pytest,sphinx-doc/sphinx,psf/requests,pylint-dev/pylint,pallets/flask'
RUNS = [('django', 'django/django', ':', 'all'),
        ('sympy', 'sympy/sympy', '0:26', '1 of 3'), ('sympy', 'sympy/sympy', '26:52', '2 of 3'), ('sympy', 'sympy/sympy', '52:', '3 of 3'),
        ('scientific libs', SCI, '0:21', '1 of 3'), ('scientific libs', SCI, '21:41', '2 of 3'), ('scientific libs', SCI, '41:', '3 of 3'),
        ('dev tools web', DEV, '0:24', '1 of 2'), ('dev tools web', DEV, '24:', '2 of 2')]
for name, repos, sl, part in RUNS:
    title = f'SWE-bench Lite equal text, {name} {part}'.replace(' all', '')
    assert len(title) <= 50, title
    slug = title.lower().replace(',', '').replace(' ', '-')
    out = 'SWEBENCH_LITE_eqtext_' + slug.split('equal-text-')[1] + '.json'
    head = (f"# {title}\n\nSWE-bench Lite retrieval rerun that records gold ranks and the registered equal-text "
            "chunk-length comparison (research/PREREG_tiered_context_gemma_harness.md, implementation note). "
            f"Repositories: {repos}; task slice {sl} of the shard's eligible tasks, sorted by instance id. CPU only.")
    setup = ("import os, subprocess, sys\nsubprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'fastembed'], check=True)\n"
             f"os.environ.update(SHARD_REPOS='{repos}', SLICE='{sl}', OUT='/kaggle/working/{out}', WORK='/tmp/swl_work', GUARD_S=str(10.5 * 3600))\n")
    nb = {'cells': [{'cell_type': 'markdown', 'metadata': {}, 'source': head},
                    {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': setup},
                    {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': SRC}],
          'metadata': {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}},
          'nbformat': 4, 'nbformat_minor': 5}
    d = os.path.join(HERE, slug); os.makedirs(d, exist_ok=True)
    json.dump(nb, open(os.path.join(d, slug + '.ipynb'), 'w'), indent=1)
    json.dump({'id': f'purnimapathak15/{slug}', 'title': title, 'code_file': slug + '.ipynb', 'language': 'python',
               'kernel_type': 'notebook', 'is_private': True, 'enable_gpu': False, 'enable_tpu': False,
               'enable_internet': True, 'dataset_sources': [], 'competition_sources': [], 'kernel_sources': [],
               'model_sources': []}, open(os.path.join(d, 'kernel-metadata.json'), 'w'), indent=1)
    print(f'{slug:52s} {sl:6s} -> {out}')
