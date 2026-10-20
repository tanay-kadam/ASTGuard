"""Verify normalized source/label/identity rows against pinned raw releases."""
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from astguard.data.schema import read_jsonl
from astguard.utils.hashing import sha256_file
from astguard.utils.atomic_io import atomic_write_json


def main():
    registry = json.loads((REPO/'sources.lock.json').read_text())['sources']
    selected = [r for r in registry if r['logical_name'] == 'diversevul/standalone'
                or r['logical_name'] in {f'primevul/primevul_{split}.jsonl' for split in ['train', 'valid', 'test']}]
    assert len(selected) == 4
    hashes = {}
    for record in selected:
        path = (REPO/'data/raw/diversevul/original/payload.jsonl' if record['logical_name'] == 'diversevul/standalone'
                else REPO/'data/raw/primevul/original'/record['logical_name'].split('/')[-1])
        assert path.is_file() and sha256_file(path) == record['sha256']
        hashes[record['logical_name']] = record['sha256']
    def raw_prime():
        for split in ['train', 'valid', 'test']:
            for index, row in enumerate(read_jsonl(REPO/f'data/raw/primevul/original/primevul_{split}.jsonl')):
                yield split, index, row
    def raw_diverse():
        for index, row in enumerate(read_jsonl(REPO/'data/raw/diversevul/original/payload.jsonl')):
            yield 'transfer', index, row
    report = {'raw_release_hashes': hashes, 'datasets': {}, 'status': 'passed',
              'verification_script_sha256': sha256_file(Path(__file__))}
    for name, raw in [('primevul', raw_prime()), ('diversevul', raw_diverse())]:
        counts = Counter()
        normpath = REPO/f'data/interim/{name}/records.jsonl'
        for a, b in itertools.zip_longest(raw, read_jsonl(normpath)):
            assert a is not None and b is not None, 'Raw and normalized row populations differ'
            split, index, row = a
            expected_id = f'primevul:original:{row["idx"]}' if name == 'primevul' else f'diversevul:standalone:{index}'
            assert b['sample_id'] == expected_id and b['label'] == row['target']
            assert b['source_raw'] == row['func'] and b['source_canonical'] == row['func'].replace('\r\n', '\n')
            assert b['raw_sha256'] == hashlib.sha256(row['func'].encode()).hexdigest()
            assert b['upstream_normalized_hash'] == hashlib.sha256(''.join(b['source_canonical'].split()).encode()).hexdigest()
            assert b['original_row_index'] == index and b['original_split'] == split
            assert b['project_id'] == row.get('project') and b['commit_id'] == row.get('commit_id')
            counts['n'] += 1; counts['positive'] += b['label']
        report['datasets'][name] = dict(counts) | {'normalized_sha256': sha256_file(normpath)}
    target = REPO/'artifacts/seven_day_20261012/dataset_provenance.json'
    atomic_write_json(target, report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
