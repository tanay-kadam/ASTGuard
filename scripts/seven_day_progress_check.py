"""Read-only campaign inspection; independently check sealed feature files."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import object_hash, sha256_file

ROOT = REPO/'artifacts/seven_day_20261012'


def check_features():
    folder = ROOT/'holdout'
    manifest = json.loads((folder/'manifest.json').read_text())
    membership = json.loads((folder/'membership.json').read_text())
    protocol = sha256_file(REPO/'docs/SEVEN_DAY_HOLDOUT_PROTOCOL_20261012.md')
    assert object_hash({'protocol': protocol, 'membership': membership['rows']}) == manifest['manifest_hash']
    assert membership['manifest_hash'] == manifest['manifest_hash']
    expected = {sid: (label, component, raw_hash) for sid, label, component, raw_hash in membership['rows']}
    assert len(expected) == len(membership['rows']) == manifest['n']
    original = json.loads((REPO/'data/strengthening_20261006/real/manifest.json').read_text())
    assert manifest['preprocessing_hash'] == original['preprocessing_hash']
    assert manifest['feasibility_passed'] and not manifest['selection_allowed']
    checked = {}
    for name in ['audit', 'regvd_audit']:
        path = Path(manifest['features_directory'])/f'{name}.jsonl'
        digest = sha256_file(path)
        assert digest == manifest['hashes'][name], name
        seen = set(); positives = 0
        with path.open() as stream:
            for line in stream:
                row = json.loads(line)
                sid = row['sample_id']
                assert sid not in seen and sid in expected, sid
                assert (row['label'], row['component_id'], row['source_sha256']) == expected[sid], sid
                assert row['role'] == 'audit' and row['split_hash'] == manifest['manifest_hash'], sid
                if name == 'audit':
                    assert row['preprocessing_hash'] == manifest['preprocessing_hash'], sid
                    assert len(row['input_ids']) == len(row['attention_mask']) == len(row['special_tokens_mask']) <= 512, sid
                else:
                    assert len(row['input_ids']) == 400, sid
                seen.add(sid); positives += row['label']
        assert seen == set(expected) and positives == manifest['positive'], name
        checked[name] = {'n': len(seen), 'positive': positives, 'sha256': digest}
    record = {'status': 'passed', 'utc': datetime.now(timezone.utc).isoformat(),
        'membership_hash': manifest['manifest_hash'], 'files': checked,
        'preprocessing_matches_training': True, 'verification_script_sha256': sha256_file(Path(__file__)),
        'scope': 'Saved features, IDs, labels, components, raw hashes and roles; no model predictions verified.'}
    atomic_write_json(folder/'feature_integrity_check.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check-features', action='store_true')
    args = parser.parse_args()
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'epochs': {}}
    for log in sorted((ROOT/'jobs').glob('*/runs/*/train_log.jsonl')):
        rows = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        if rows:
            last = rows[-1]
            report['epochs'][log.parents[2].name] = {'last_completed_epoch': last['epoch'],
                'optimizer_steps': last['optimizer_steps'], 'log': str(log)}
    if args.check_features: report['features'] = check_features()
    atomic_write_json(ROOT/'progress_check.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
