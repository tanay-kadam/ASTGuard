"""Content-addressed, fail-closed test access."""
import json
from pathlib import Path
from astguard.utils.hashing import sha256_file


def verify_test_lock(path='protocol/test_unlock.json', run_config=None):
    lock=json.loads(Path(path).read_text(encoding='utf-8'))
    if lock.get('status')!='unlocked':
        raise RuntimeError('test access remains locked')
    if not lock.get('artifacts'):
        raise RuntimeError('test lock has no registered artifact hashes')
    for artifact,expected in lock['artifacts'].items():
        if sha256_file(artifact)!=expected:
            raise RuntimeError(f'protocol artifact changed: {artifact}')
    if run_config is not None and run_config not in lock['selected_config_hashes']:
        raise RuntimeError('run configuration was not selected before test unlock')
    return lock
