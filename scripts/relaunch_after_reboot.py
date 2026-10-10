"""Archive stale reboot-interrupted attempts, then prepare a fresh 16-job queue."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astguard.utils.atomic_io import atomic_write_json
from scripts.queue_strengthening_all_gpus import ROOT, PLAN, prepare
from scripts.queue_strengthening import stamp


def main():
    processes = subprocess.check_output(['ps', '-u', str(os.getuid()), '-o', 'args='], text=True)
    for marker in (' -m astguard.train ', 'queue_strengthening_all_gpus.py --gpu',
                   'rerun_maintenance_jobs.py --tag'):
        assert marker not in processes, 'owned training/scheduler already running'
    archive = ROOT/'reboot_interrupted_20261007T213025Z'
    assert not archive.exists(), 'recovery already performed; inspect instead of repeating'
    jobs = json.loads((ROOT/'jobs.json').read_text())['jobs']
    counts = {}
    running = []
    unfinished = []
    for job in jobs:
        path = ROOT/'jobs'/job['tag']
        state = json.loads((path/'status.json').read_text()) if (path/'status.json').exists() else {'status': 'not_started'}
        counts[state['status']] = counts.get(state['status'], 0)+1
        if state['status'] == 'running':
            running.append((path, state))
        if state['status'] != 'complete':
            unfinished.append(job)
    assert counts == {'complete': 26, 'running': 4, 'not_started': 12}, counts
    assert PLAN.is_dir()
    for name in ('real/train.jsonl', 'real/tune.jsonl', 'real/manifest.json'):
        assert (Path('data/strengthening_20261006')/name).is_file()
    archive.mkdir()
    moved = []
    for path, state in running:
        state.update(status='interrupted', reason='server reboot at 2026-10-07 17:30:25 EDT',
                     observed_utc=stamp(), replacement_mode='fresh; no resume')
        atomic_write_json(path/'status.json', state)
        destination = archive/'jobs'/path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        path.rename(destination)
        moved.append(str(destination))
    for job in unfinished:
        for suffix in ('_allgpu_preflight_smoke', '_fresh_preflight_smoke'):
            path = ROOT/'jobs'/(job['tag']+suffix)
            if path.exists():
                destination = archive/'preflights'/path.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.rename(destination)
                moved.append(str(destination))
    PLAN.rename(archive/'all_gpu_20261007')
    atomic_write_json(archive/'relaunch_record.json', dict(utc=stamp(), previous_counts=counts,
        preserved_paths=moved, completed_runs_untouched=26,
        fresh_rerun_tags=[path.name for path, _ in running], resume_checkpoints=False))
    prepare()
    print(json.dumps({'archived_interrupted_attempts': len(running), 'fresh_queue_jobs': len(unfinished)}))


if __name__ == '__main__':
    main()
