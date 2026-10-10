"""Build corrected train/tune features only, and an independent synthetic audit set."""
import argparse
import dataclasses
import gzip
import json
import os
import random
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash, sha256_file

CAMPAIGN = Path('artifacts/release_gates/strengthening_20261006')
DATA = Path('data/strengthening_20261006')
REV = '3b0952feddeffad0063f274080e3c23d75e7eb39'
GRAPH_REV = '2b0488a7bb0eefc7041f1bb2cad1ab26b0da269d'
STATE = {}


def init_worker():
    from astguard.alignment.tokenizer import CanonicalTokenizer
    from transformers import AutoTokenizer
    STATE['tokenizer'] = CanonicalTokenizer('microsoft/codebert-base', REV)
    STATE['graph_tokenizer'] = AutoTokenizer.from_pretrained('microsoft/graphcodebert-base', revision=GRAPH_REV)


def build(task):
    from astguard.data.schema import SampleRecord
    from astguard.data.preprocess import preprocess_record
    row, role, component, manifest_hash = task
    value = dataclasses.asdict(preprocess_record(SampleRecord.from_dict(row), STATE['tokenizer']))
    fields = ['sample_id', 'source_sha256', 'preprocessing_hash', 'input_ids', 'attention_mask', 'special_tokens_mask',
              'ast_token_edges', 'dfg_token_edges', 'parse_status', 'ast_status', 'dfg_status', 'status_reasons']
    compact = {k: value[k] for k in fields}
    compact.update(label=row['label'], role=role, component_id=component, split_hash=manifest_hash)
    tok = STATE['graph_tokenizer']
    pieces = tok.tokenize(' '.join(row['source_canonical'].split()))[:398]
    ids = tok.convert_tokens_to_ids([tok.cls_token] + pieces + [tok.sep_token])
    ids += [tok.pad_token_id] * (400 - len(ids))
    external = {k: compact[k] for k in ['sample_id', 'label', 'role', 'component_id', 'source_sha256', 'split_hash']}
    external['input_ids'] = ids
    from astguard.baselines.regvd_audit import native_graph
    external['node_ids'], external['native_edges'] = native_graph(ids)
    return compact, external


def tasks(manifest):
    assignment = {sid: (role, comp) for sid, role, comp in zip(manifest['ordered_sample_ids'], manifest['roles'], manifest['component_ids'])}
    with gzip.open(CAMPAIGN / 'development_records.jsonl.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line); role, comp = assignment[row['sample_id']]
            if role not in {'train', 'tune'}:
                raise ValueError('held-out real source in development transfer')
            yield row, role, comp, manifest['file_hash']


def synthetic():
    from scripts.generate_topology_positive_control import generate_split, validate_rows, _atomic_jsonl, PREPROCESSING_HASH
    directory = DATA / 'synthetic'; directory.mkdir(parents=True, exist_ok=True)
    if (directory / 'manifest.json').exists():
        return
    rng = random.Random(20261007); seen = set()
    groups = {role: generate_split(role, count, rng, seen) for role, count in [('train', 2048), ('tune', 512), ('audit', 512)]}
    validate_rows(groups['train'], groups['tune']); validate_rows(groups['train'], groups['audit'])
    assert not {tuple(r['input_ids']) for r in groups['tune']} & {tuple(r['input_ids']) for r in groups['audit']}
    digest = object_hash({'kind': 'synthetic-three-role-v2', 'generation_seed': 20261007, 'pairs': [2048,512,512]})
    for role, values in groups.items():
        for row in values:
            row['split_hash'] = digest
        _atomic_jsonl(directory / f'{role}.jsonl', values)
    atomic_write_json(directory / 'manifest.json', {'manifest_hash': digest, 'preprocessing_hash': PREPROCESSING_HASH,
        'generation_seed': 20261007, 'official_test_used': False, 'audit_used_for_selection': False,
        'counts': {k:len(v) for k,v in groups.items()}, 'hashes': {k:sha256_file(directory/f'{k}.jsonl') for k in groups}})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--workers', type=int, default=32)
    parser.add_argument('--smoke-only', action='store_true'); args = parser.parse_args()
    manifest = json.loads((CAMPAIGN / 'corrected_manifest.json').read_text())
    columns = ['ordered_sample_ids', 'roles', 'component_ids', 'original_splits']
    assert len({len(manifest[k]) for k in columns}) == 1
    assert object_hash(manifest | {'file_hash':''}) == manifest['file_hash']
    record_report = json.loads((CAMPAIGN / 'split_integrity_correction.json').read_text())
    assert sha256_file(CAMPAIGN / 'development_records.jsonl.gz') == record_report['records_gzip_sha256']
    synthetic()
    directory = DATA / ('smoke' if args.smoke_only else 'real')
    directory.mkdir(parents=True, exist_ok=True)
    complete = directory / 'manifest.json'
    if complete.exists():
        print(complete); return
    source_tasks = tasks(manifest)
    if args.smoke_only:
        selected = []; counts = Counter()
        for task in source_tasks:
            key = (task[1], task[0]['label'])
            if counts[key] < 16:
                selected.append(task); counts[key] += 1
            if all(counts[k] == 16 for k in [('train',0),('train',1),('tune',0),('tune',1)]):
                break
        source_tasks = iter(selected)
    counts = Counter(); positive = Counter(); prep_hashes = set(); start = time.time()
    names = ['train', 'tune', 'regvd_train', 'regvd_tune']
    streams = {name:(directory / f'{name}.jsonl.partial').open('w', encoding='utf-8', newline='\n') for name in names}
    try:
        with Pool(args.workers, initializer=init_worker) as pool:
            for value, external in pool.imap(build, source_tasks, chunksize=2):
                role = value['role']; counts[role] += 1; positive[role] += value['label']; prep_hashes.add(value['preprocessing_hash'])
                streams[role].write(json.dumps(value, sort_keys=True) + '\n')
                streams['regvd_' + role].write(json.dumps(external, sort_keys=True) + '\n')
                if sum(counts.values()) % 5000 == 0:
                    print(json.dumps({'prepared':sum(counts.values()), 'elapsed_seconds':time.time()-start}), flush=True)
    finally:
        for stream in streams.values(): stream.close()
    assert len(prep_hashes) == 1
    expected_counts = {'train':32, 'tune':32} if args.smoke_only else record_report['corrected_counts']
    assert dict(counts) == expected_counts
    if not args.smoke_only:
        assert dict(positive) == record_report['corrected_positives']
    for name in names:
        os.replace(directory / f'{name}.jsonl.partial', directory / f'{name}.jsonl')
    atomic_write_json(complete, {'manifest_hash':manifest['file_hash'], 'preprocessing_hash':next(iter(prep_hashes)),
        'counts':dict(counts), 'positives':dict(positive), 'elapsed_seconds':time.time()-start, 'official_test_used':False,
        'hashes':{name:sha256_file(directory/f'{name}.jsonl') for name in names}, 'compact_graph_fields':True})
    print(complete)


if __name__ == '__main__':
    main()
