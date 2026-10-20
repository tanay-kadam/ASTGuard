"""Verify frozen execution sources and record post-launch audit additions."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from astguard.utils.hashing import sha256_file
from astguard.utils.atomic_io import atomic_write_json

ROOT = REPO/'artifacts/seven_day_20261012'
frozen = json.loads((ROOT/'source_files.json').read_text())
changed = {name: {'frozen': digest, 'current': sha256_file(REPO/name)}
           for name, digest in frozen.items() if sha256_file(REPO/name) != digest}
added = {str(p.relative_to(REPO)): sha256_file(p)
         for directory in ['scripts', 'docs', 'protocol', 'tests']
         for p in (REPO/directory).rglob('*')
         if p.is_file() and '__pycache__' not in p.parts and str(p.relative_to(REPO)) not in frozen}
report = {'frozen_sources_unchanged': not changed, 'changes': changed, 'additions': added,
          'scope': 'Holdout/analysis/operational additions do not change frozen model/training code.'}
atomic_write_json(ROOT/'source_additions_check.json', report)
assert not changed, changed
print(json.dumps({'frozen_sources_unchanged': True, 'added_files': len(added)}))
