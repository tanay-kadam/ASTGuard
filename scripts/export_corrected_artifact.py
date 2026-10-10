"""Inventory only canonical completed runs and their reproducibility inputs.

Run on the experiment host. No training files are modified. Resume/optimizer
states, smoke jobs, quarantined jobs, and interrupted attempts are excluded.
"""
import argparse
import hashlib
import json
from pathlib import Path

CAMPAIGN = Path('artifacts/release_gates/strengthening_20261006')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def inventory(root):
    root = root.resolve()
    summary = json.loads((root / CAMPAIGN / 'summary.json').read_text())
    plan = json.loads((root / CAMPAIGN / 'jobs.json').read_text())
    if not summary['execution_complete'] or len(summary['jobs']) != 42:
        raise ValueError('Expected 42 completed canonical jobs')
    if set(summary['jobs']) != {j['tag'] for j in plan['jobs']}:
        raise ValueError('Plan/summary job mismatch')
    paths = set()
    for name in ['summary.json', 'jobs.json', 'corrected_manifest.json',
                 'split_integrity_correction.json', 'rebuilt_population_audit.json',
                 'development_records.jsonl.gz', 'cuda_seed_repair_completion.json']:
        p = root / CAMPAIGN / name
        if p.is_file(): paths.add(p)
    for tag, record in summary['jobs'].items():
        run = (root / record['run_dir']).resolve()
        if not run.is_relative_to(root / CAMPAIGN / 'jobs' / tag):
            raise ValueError('Canonical run escapes its job: ' + tag)
        for p in run.rglob('*'):
            if p.is_file() and not p.is_symlink() and p.suffix != '.pt' and 'partial' not in p.name:
                paths.add(p)
        for name in ['status.json', 'interventions.json', 'run.log']:
            p = root / CAMPAIGN / 'jobs' / tag / name
            if p.is_file(): paths.add(p)
    for directory in ['data/strengthening_20261006/real', 'data/strengthening_20261006/synthetic',
                      'data/strengthening_20261006/smoke', 'astguard', 'scripts', 'configs',
                      'tests', 'protocol', 'third_party']:
        for p in (root / directory).rglob('*'):
            if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pt', '.bin'}:
                paths.add(p)
    for name in ['requirements.lock', 'pyproject.toml', 'sources.lock.json', 'LICENSE',
                 'docs/SUBMISSION_STRENGTHENING_PROTOCOL_20261006.md',
                 'artifacts/audits/complete_pipeline_audit_20261006.json']:
        p = root / name
        if p.is_file(): paths.add(p)
    entries = []
    for p in sorted(paths):
        before = p.stat()
        digest = sha(p)
        after = p.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('File changed during inventory: ' + str(p))
        entries.append({'path': p.relative_to(root).as_posix(), 'bytes': after.st_size, 'sha256': digest})
    return {'schema_version': 1, 'source_root': str(root), 'canonical_jobs': 42,
            'excluded': ['optimizer/resume .pt files', 'quarantine', 'interrupted attempts', 'noncanonical runs'],
            'file_count': len(entries), 'total_bytes': sum(e['bytes'] for e in entries), 'files': entries}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    value = inventory(args.root)
    text = json.dumps(value, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text)

if __name__ == '__main__': main()
