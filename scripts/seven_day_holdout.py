"""Construct a score-blind external cohort using global exact clone components."""
from __future__ import annotations

import argparse
import dataclasses
import gzip
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from astguard.data.audit import _UnionFind, normalize_repository
from astguard.parsing.lexical import _TOKEN, lexical_fingerprint
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash, sha256_file

ROOT = REPO/'artifacts/seven_day_20261012/holdout'


def lexical_job(source):
    fallback = False
    try:
        fingerprint, tokens = lexical_fingerprint(source)
    except ValueError:
        fallback = True
        tokens = []
        for match in _TOKEN.finditer(source):
            kind = match.lastgroup or 'unknown'
            if kind in {'ws', 'line', 'block'}:
                continue
            if kind == 'rawstring':
                kind = 'string'
            tokens.append(kind+':'+match.group())
        fingerprint = hashlib.sha256('\x1f'.join(tokens).encode()).hexdigest()
    shingles = frozenset(hashlib.sha256('\x1e'.join(tokens[i:i+5]).encode()).digest()
                         for i in range(max(0, len(tokens)-4)))
    return fingerprint, len(tokens), shingles, fallback


def near_clone_join(info, uf, threshold=.90, ratio=.80, progress=None):
    """Complete global prefix candidate join followed by exact verification.

    The total order is global (frequency, digest). Jaccard>=t implies the two
    prefixes of lengths n-ceil(t*n)+1 intersect. Each unordered candidate pair
    is verified once; size and token-count filters are necessary conditions.
    """
    frequency = Counter(s for _, shingles in info.values() for s in shingles)
    inverted = defaultdict(list)
    checked = linked = 0
    ordered = sorted(info, key=lambda sid: (len(info[sid][1]), sid))
    for index, sid in enumerate(ordered):
        length, shingles = info[sid]
        if length < 5 or not shingles:
            continue
        prefix_n = len(shingles)-math.ceil(threshold*len(shingles))+1
        prefix = sorted(shingles, key=lambda s: (frequency[s], s))[:prefix_n]
        candidates = set(other for s in prefix for other in inverted[s])
        for other in sorted(candidates):
            if uf.find(sid) == uf.find(other):
                continue
            other_length, other_set = info[other]
            if len(other_set) < math.ceil(threshold*len(shingles)):
                continue
            if min(length, other_length)/max(length, other_length) < ratio:
                continue
            checked += 1
            intersection = len(shingles & other_set)
            union = len(shingles)+len(other_set)-intersection
            if intersection/union >= threshold:
                uf.union(sid, other)
                linked += 1
        for s in prefix:
            inverted[s].append(sid)
        if progress and index % 10000 == 0:
            progress({'phase': 'near_clone_join', 'processed': index, 'total': len(ordered),
                      'verified_candidates': checked, 'new_links': linked})
    return {'verified_candidates': checked, 'near_clone_links': linked}


def seal_components():
    ROOT.mkdir(parents=True, exist_ok=True)
    if (ROOT/'components.json').exists():
        raise FileExistsError('Never overwrite a frozen component audit')
    start = time.time()
    def progress(record):
        record['elapsed_seconds'] = time.time()-start
        print(json.dumps(record), flush=True)
        atomic_write_json(ROOT/'progress.json', record)
    records = []
    sources = [REPO/'data/interim'/name/'records.jsonl' for name in ['primevul', 'diversevul']]
    for path in sources:
        with path.open() as f:
            records.extend(json.loads(line) for line in f if line.strip())
    ids = [r['sample_id'] for r in records]
    assert len(set(ids)) == len(ids) == 566260
    uf = _UnionFind(ids)
    evidence_counts = Counter()
    def link(kind, entries):
        seen = {}
        for value, sid in entries:
            if not value:
                continue
            if value in seen:
                if uf.find(sid) != uf.find(seen[value]):
                    uf.union(sid, seen[value]); evidence_counts[kind] += 1
            else:
                seen[value] = sid
    link('raw', ((r['raw_sha256'], r['sample_id']) for r in records))
    link('normalized', ((r['upstream_normalized_hash'], r['sample_id']) for r in records))
    link('repository_commit', (((normalize_repository(r.get('repository_url')) or (r.get('project_id') or '').lower())+'@'+r['commit_id'].lower(), r['sample_id'])
        for r in records if (r.get('repository_url') or r.get('project_id')) and r.get('commit_id')))
    link('cve', ((cve, r['sample_id']) for r in records for cve in r.get('cve_ids', [])))
    link('pair', ((pair, r['sample_id']) for r in records for pair in r.get('pair_ids', [])))
    info = {}; fingerprints = {}; fallbacks = Counter()
    with Pool(24) as pool:
        results = pool.imap(lexical_job, (r['source_canonical'] for r in records), chunksize=32)
        for index, (row, result) in enumerate(zip(records, results)):
            fp, length, shingles, fallback = result
            sid = row['sample_id']
            info[sid] = (length, shingles)
            if fp in fingerprints:
                uf.union(sid, fingerprints[fp])
            else:
                fingerprints[fp] = sid
            fallbacks[row['dataset']] += int(fallback)
            if index % 10000 == 0:
                progress({'phase': 'lexical', 'processed': index, 'total': len(records)})
    # Exact lexical duplicates have identical shingle sets and token counts;
    # indexing one representative is sufficient for all their near-clone links.
    representatives = set(fingerprints.values())
    info = {sid: item for sid, item in info.items() if sid in representatives}
    near = near_clone_join(info, uf, progress=progress)
    members = defaultdict(list)
    for sid in ids:
        members[uf.find(sid)].append(sid)
    component = {}
    for values in members.values():
        digest = hashlib.sha256('\n'.join(sorted(values)).encode()).hexdigest()
        for sid in values:
            component[sid] = digest
    prime = {component[r['sample_id']] for r in records if r['dataset'] == 'primevul'}
    candidate = [r for r in records if r['dataset'] == 'diversevul' and component[r['sample_id']] not in prime]
    with gzip.open(ROOT/'candidate_records.jsonl.gz', 'wt', encoding='utf-8', compresslevel=1) as f:
        for row in candidate:
            f.write(json.dumps(row | {'component_id': component[row['sample_id']]}, sort_keys=True)+'\n')
    atomic_write_json(ROOT/'components.json', {'components': component})
    protocol = REPO/'docs/SEVEN_DAY_HOLDOUT_PROTOCOL_20261012.md'
    report = {'phase': 'component_audit_complete', 'protocol_sha256': sha256_file(protocol),
        'script_sha256': sha256_file(Path(__file__)), 'source_sha256': {str(p): sha256_file(p) for p in sources},
        'reference_primevul_count': 235768, 'candidate_source_diversevul_count': 330492,
        'component_filtered_candidates': len(candidate), 'candidate_positive': sum(r['label'] for r in candidate),
        'candidate_components': len({component[r['sample_id']] for r in candidate}),
        'metadata_union_counts': dict(evidence_counts), 'lexical_fallback_counts': dict(fallbacks), **near,
        'candidate_records_sha256': sha256_file(ROOT/'candidate_records.jsonl.gz'),
        'elapsed_seconds': time.time()-start, 'model_input_collision_audit': 'pending',
        'independence_scope': 'specified linkage rules; missing metadata and pretraining exposure unverified'}
    atomic_write_json(ROOT/'component_report.json', report)
    print(json.dumps(report), flush=True)


TOKENIZERS = {}


def init_tokenizers():
    from astguard.alignment.tokenizer import CanonicalTokenizer
    from transformers import AutoTokenizer
    TOKENIZERS['code'] = CanonicalTokenizer('microsoft/codebert-base', '3b0952feddeffad0063f274080e3c23d75e7eb39')
    TOKENIZERS['graph'] = AutoTokenizer.from_pretrained('microsoft/graphcodebert-base', revision='2b0488a7bb0eefc7041f1bb2cad1ab26b0da269d')


def input_keys(source):
    ids = TOKENIZERS['code'].encode(source, max_length=512).input_ids
    tok = TOKENIZERS['graph']
    pieces = tok.tokenize(' '.join(source.split()))[:398]
    graph_ids = tok.convert_tokens_to_ids([tok.cls_token]+pieces+[tok.sep_token])
    graph_ids += [tok.pad_token_id]*(400-len(graph_ids))
    return object_hash(ids), object_hash(graph_ids)


def seal_features():
    if (ROOT/'manifest.json').exists():
        raise FileExistsError('Never overwrite a frozen holdout')
    component_report = json.loads((ROOT/'component_report.json').read_text())
    assert sha256_file(ROOT/'candidate_records.jsonl.gz') == component_report['candidate_records_sha256']
    report = {'phase': 'model_input_collision_audit', 'started': time.time()}
    from astguard.data.schema import read_jsonl
    references = list(read_jsonl(REPO/'data/interim/primevul/records.jsonl'))
    with gzip.open(ROOT/'candidate_records.jsonl.gz', 'rt', encoding='utf-8') as f:
        candidates = [json.loads(line) for line in f if line.strip()]
    code_keys = set(); graph_keys = set(); bad_components = set(); collisions = Counter()
    with Pool(24, initializer=init_tokenizers) as pool:
        for index, (code, graph) in enumerate(pool.imap(input_keys, (r['source_canonical'] for r in references), chunksize=16)):
            code_keys.add(code); graph_keys.add(graph)
            if index % 10000 == 0:
                print(json.dumps({'phase': 'reference_tokenization', 'processed': index}), flush=True)
        for index, (row, (code, graph)) in enumerate(zip(candidates, pool.imap(input_keys, (r['source_canonical'] for r in candidates), chunksize=16))):
            code_hit, graph_hit = code in code_keys, graph in graph_keys
            if code_hit or graph_hit:
                bad_components.add(row['component_id'])
                collisions['codebert'] += int(code_hit); collisions['regvd'] += int(graph_hit)
            if index % 10000 == 0:
                print(json.dumps({'phase': 'candidate_tokenization', 'processed': index}), flush=True)
    rows = [r for r in candidates if r['component_id'] not in bad_components]
    labels = Counter(r['label'] for r in rows)
    clusters = len({r['component_id'] for r in rows})
    membership = sorted((r['sample_id'], r['label'], r['component_id'], r['raw_sha256']) for r in rows)
    manifest_hash = object_hash({'protocol': sha256_file(REPO/'docs/SEVEN_DAY_HOLDOUT_PROTOCOL_20261012.md'),
                                 'membership': membership})
    feasible = len(rows) >= 1000 and labels[1] >= 100 and labels[0] >= 100 and clusters >= 20
    report.update({'n': len(rows), 'positive': labels[1], 'negative': labels[0], 'components': clusters,
        'collision_rows': dict(collisions), 'purged_components': len(bad_components),
        'feasibility_passed': feasible, 'membership_hash': manifest_hash,
        'reference_population': 'all_primevul_source_roles', 'model_scores_inspected': False})
    atomic_write_json(ROOT/'membership.json', {'manifest_hash': manifest_hash, 'rows': membership})
    atomic_write_json(ROOT/'collision_report.json', report)
    if not feasible:
        atomic_write_json(ROOT/'inadequate_cohort.json', report)
        print(json.dumps(report), flush=True)
        return
    extract_features(rows, manifest_hash)


def init_feature_worker():
    # The existing recursive AST traversal can exceed Python's default depth on
    # long functions. Increase runtime stack/depth limits without changing the
    # parser, graph construction, tokenizer, or retained population.
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    desired = max(soft, 256*1024**2)
    if hard != resource.RLIM_INFINITY: desired = min(desired, hard)
    resource.setrlimit(resource.RLIMIT_STACK, (desired, hard))
    sys.setrecursionlimit(10000)
    from scripts.prepare_strengthening_data import init_worker
    init_worker()


def build_with_progress(task):
    from scripts.prepare_strengthening_data import build
    row = task[0]
    path = ROOT/'worker_progress'/f'{os.getpid()}.json'
    atomic_write_json(path, {'phase': 'building', 'sample_id': row['sample_id'],
        'source_characters': len(row['source_canonical']), 'started_unix': time.time()})
    value = build(task)
    atomic_write_json(path, {'phase': 'finished', 'sample_id': row['sample_id'], 'finished_unix': time.time()})
    return value


def extract_features(rows, manifest_hash):
    # Feature exceptions block completion; they never silently remove rows.
    from scripts.prepare_strengthening_data import build
    labels = Counter(r['label'] for r in rows)
    clusters = len({r['component_id'] for r in rows})
    component_report = json.loads((ROOT/'component_report.json').read_text())
    target = REPO/'data/seven_day_20261012/external'
    target.mkdir(parents=True, exist_ok=False)
    prep_hashes = set(); statuses = Counter()
    with (target/'audit.jsonl.partial').open('w') as local, (target/'regvd_audit.jsonl.partial').open('w') as external:
        with Pool(24, initializer=init_feature_worker) as pool:
            tasks = ((row, 'audit', row['component_id'], manifest_hash) for row in rows)
            for index, (value, graph) in enumerate(pool.imap(build_with_progress, tasks, chunksize=2)):
                prep_hashes.add(value['preprocessing_hash'])
                statuses[(value['ast_status'], value['dfg_status'])] += 1
                local.write(json.dumps(value, sort_keys=True)+'\n')
                external.write(json.dumps(graph, sort_keys=True)+'\n')
                if index % 5000 == 0:
                    print(json.dumps({'phase': 'feature_extraction', 'processed': index, 'total': len(rows)}), flush=True)
    assert len(prep_hashes) == 1
    expected = json.loads((REPO/'data/strengthening_20261006/real/manifest.json').read_text())['preprocessing_hash']
    assert next(iter(prep_hashes)) == expected, 'External preprocessing differs from frozen training recipe'
    for name in ['audit', 'regvd_audit']:
        (target/f'{name}.jsonl.partial').replace(target/f'{name}.jsonl')
    manifest = {'manifest_hash': manifest_hash, 'preprocessing_hash': expected,
        'n': len(rows), 'positive': labels[1], 'negative': labels[0], 'components': clusters,
        'hashes': {name: sha256_file(target/f'{name}.jsonl') for name in ['audit', 'regvd_audit']},
        'features_directory': str(target), 'selection_allowed': False,
        'source': 'diversevul', 'official_primevul_test_evaluated': False,
        'runtime_recursion_limit': 10000, 'worker_stack_limit_requested_bytes': 256*1024**2,
        'feasibility_passed': True, 'extraction_statuses': {str(k): v for k, v in statuses.items()},
        'independence_scope': component_report['independence_scope']}
    atomic_write_json(ROOT/'manifest.json', manifest)
    print(json.dumps(manifest), flush=True)


def retry_extraction():
    assert not (ROOT/'manifest.json').exists()
    membership = json.loads((ROOT/'membership.json').read_text())
    collision = json.loads((ROOT/'collision_report.json').read_text())
    assert collision['feasibility_passed']
    wanted = {row[0] for row in membership['rows']}
    with gzip.open(ROOT/'candidate_records.jsonl.gz', 'rt', encoding='utf-8') as f:
        rows = [row for line in f if (row := json.loads(line))['sample_id'] in wanted]
    actual = sorted((r['sample_id'], r['label'], r['component_id'], r['raw_sha256']) for r in rows)
    assert actual == [tuple(row) for row in membership['rows']]
    target = REPO/'data/seven_day_20261012/external'
    attempt = 1
    while target.with_name(f'external_failed_attempt{attempt}').exists(): attempt += 1
    archive = target.with_name(f'external_failed_attempt{attempt}')
    assert target.resolve() == Path('/tmp/astguard_seven_day_20261012/data/seven_day_20261012/external')
    assert not archive.exists()
    target.rename(archive)
    failure = ROOT/'failure.json'
    if failure.exists(): failure.rename(ROOT/f'failure_attempt{attempt}.json')
    atomic_write_json(ROOT/f'extraction_retry{attempt}.json', {'reason': 'runtime recovery; original recursion failure and subsequent retry without thread limits retained',
        'membership_unchanged': True, 'manifest_hash': membership['manifest_hash'],
        'failed_features_preserved': str(archive), 'model_scores_inspected': False})
    extract_features(rows, membership['manifest_hash'])


def main():
    p = argparse.ArgumentParser(); p.add_argument('--components', action='store_true')
    p.add_argument('--features', action='store_true')
    p.add_argument('--retry-extraction', action='store_true')
    args = p.parse_args(); os.chdir(REPO)
    if args.components or args.features or args.retry_extraction:
        try:
            if args.components: seal_components()
            elif args.features: seal_features()
            else: retry_extraction()
        except Exception as exc:
            atomic_write_json(ROOT/'failure.json', {'error': repr(exc), 'scores_computed': False})
            raise
    else: p.error('choose --components or --features')


if __name__ == '__main__':
    main()
