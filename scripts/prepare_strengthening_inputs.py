"""Preserve historical manifests; produce a corrected development-only transfer."""
import collections
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from astguard.utils.hashing import object_hash, sha256_file
from astguard.utils.atomic_io import atomic_write_json

COLS = ('ordered_sample_ids', 'roles', 'component_ids', 'original_splits')


def corrected_manifest(original, excluded):
    n = len(original['ordered_sample_ids'])
    if any(len(original[k]) != n for k in COLS):
        raise ValueError('original manifest is not aligned')
    keep = [i for i, sid in enumerate(original['ordered_sample_ids']) if sid not in excluded]
    value = dict(original)
    for k in COLS:
        value[k] = [original[k][i] for i in keep]
    value['counts'] = dict(collections.Counter(value['roles']))
    value['version'] = '1.1-corrected-outlier-filter'
    value['exclusion_reasons'] = original['exclusion_reasons'] | {sid: 'predeclared extraction-size outlier' for sid in excluded}
    value['rule_hash'] = object_hash({'parent': original['file_hash'], 'excluded': sorted(excluded), 'column_filter': 'aligned-v1'})
    value['file_hash'] = object_hash(value | {'file_hash': ''})
    return value


def main():
    original = json.loads((ROOT / 'artifacts/audits/P_clean.json').read_text())
    archived = ROOT / 'archive/invalid_results_20261007/artifacts/audits/P_clean_stage0.json'
    bad_path = archived if archived.exists() else ROOT / 'artifacts/audits/P_clean_stage0.json'
    bad = json.loads(bad_path.read_text())
    original_roles = dict(zip(original['ordered_sample_ids'], original['roles']))
    bad_roles = dict(zip(bad['ordered_sample_ids'], bad['roles']))
    changed = [(sid, original_roles[sid], role) for sid, role in bad_roles.items() if original_roles[sid] != role]
    fixed = corrected_manifest(original, set(bad['stage0_excluded_outliers']))
    target = ROOT / 'artifacts/release_gates/strengthening_20261006'
    target.mkdir(parents=True, exist_ok=True)
    atomic_write_json(target / 'corrected_manifest.json', fixed)
    assignment = {sid: (role, component, source_split) for sid, role, component, source_split in zip(*(fixed[k] for k in COLS))}
    components = {}; hashes = {}; counts = collections.Counter(); positives = collections.Counter(); seen = set()
    path = target / 'development_records.jsonl.gz'
    if path.exists():
        raise FileExistsError(path)
    with gzip.open(path, 'wt', encoding='utf-8', newline='\n', compresslevel=1) as out:
        with (ROOT / 'data/interim/primevul/records.jsonl').open(encoding='utf-8') as source:
            for line in source:
                row = json.loads(line)
                sid = row['sample_id']
                if sid not in assignment or assignment[sid][0] not in {'train', 'tune'}:
                    continue
                role, component, original_split = assignment[sid]
                assert row['original_split'] == original_split
                assert (role == 'train' and original_split == 'train') or (role == 'tune' and original_split in {'valid', 'validation', 'val'})
                assert sid not in seen; seen.add(sid)
                for registry, key in [(components, component), (hashes, row['raw_sha256'])]:
                    if key in registry and registry[key] != role:
                        raise ValueError('source/component cross-split contamination')
                    registry[key] = role
                row['component_id'] = component
                out.write(json.dumps(row, sort_keys=True) + '\n')
                counts[role] += 1; positives[role] += int(row['label'])
    assert seen == {sid for sid, (role, _, _) in assignment.items() if role in {'train', 'tune'}}
    report = {'historical_manifest_columns': {k: len(bad[k]) for k in COLS},
              'historical_role_mismatches': len(changed),
              'historical_transition_counts': {f'{a}->{b}': count for (a,b), count in collections.Counter((a,b) for _,a,b in changed).items()},
              'corrected_counts': dict(counts), 'corrected_positives': dict(positives),
              'corrected_manifest_hash': fixed['file_hash'], 'records_gzip_sha256': sha256_file(path),
              'original_test_transferred': False, 'historical_results_submission_safe': False}
    atomic_write_json(target / 'split_integrity_correction.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
