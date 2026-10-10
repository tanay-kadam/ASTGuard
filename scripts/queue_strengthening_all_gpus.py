"""Distribute only unfinished approved jobs, without occupying busy GPUs.

Attention jobs use GPUs 5/6 exclusively. Adapter workers claim jobs atomically
after their GPU becomes idle. Claims survive disconnects; failed claims are never
silently retried. All workers exit after their pool has been assigned.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astguard.utils.atomic_io import atomic_write_json
from scripts.queue_strengthening import ROOT, run_job, stamp

PLAN = ROOT/'all_gpu_20261007'
BLOCKERS = {5: 'real_attention_authentic_s42', 6: 'real_attention_sequence_s456'}


def status(tag):
    path = ROOT/'jobs'/tag/'status.json'
    return json.loads(path.read_text()).get('status') if path.exists() else 'not_started'


def pool_for(job):
    if job['family'] == 'real' and job['condition'].startswith('attention_'):
        return 'attention'
    if job['family'] == 'real' and job['condition'].startswith('adapter_'):
        return 'adapter'
    raise ValueError(f'Unexpected unfinished family: {job}')


def prepare():
    assert not (PLAN/'plan.json').exists(), 'plan already exists; inspect instead of replacing'
    matrix = json.loads((ROOT/'jobs.json').read_text())
    jobs = matrix['jobs']
    counts = {}
    selected = []
    for job in jobs:
        state = status(job['tag'])
        counts[state] = counts.get(state, 0)+1
        if state == 'not_started':
            config = json.loads(Path(job['config']).read_text())
            pool = pool_for(job)
            assert config['training']['epochs'] == (5 if pool == 'attention' else 3)
            assert config['training']['seed'] == job['seed']
            assert config['training']['max_optimizer_steps'] is None
            assert not (ROOT/'jobs'/job['tag']).exists(), 'refuse stale output directories'
            selected.append(dict(job, pool=pool))
        elif state not in ('complete', 'running'):
            raise ValueError(f'Unresolved job {job["tag"]}: {state}')
    assert counts in ({'complete': 26, 'running': 2, 'not_started': 14},
                      {'complete': 26, 'not_started': 16}), counts
    for name in ('real/train.jsonl', 'real/tune.jsonl', 'real/manifest.json',
                 'smoke/train.jsonl', 'smoke/tune.jsonl'):
        assert (Path('data/strengthening_20261006')/name).is_file()
    atomic_write_json(PLAN/'plan.json', dict(utc=stamp(), jobs=selected, original_counts=counts,
        big_run_gpus=[5, 6], adapter_gpus=[0, 1, 2, 3, 4, 7],
        existing_fresh_runs={gpu: tag for gpu, tag in BLOCKERS.items() if status(tag) == 'running'},
        protocol_sha256=matrix['protocol_sha256'],
        busy_gpu_policy='wait; never kill another process', resume_checkpoints=False))
    # Preserve the old maintenance instruction as history, not an active hold.
    hold = ROOT/'maintenance_hold.json'
    history = PLAN/'maintenance_hold_before_release.json'
    assert not history.exists()
    if hold.exists():
        hold.rename(history)
    atomic_write_json(PLAN/'authorization.json', dict(utc=stamp(),
        instruction='User requested all available GPUs; larger runs on GPUs 5 and 6.',
        general_queue_released=True, unchanged_experiment_matrix=True))
    print(json.dumps({'queued': len(selected), 'counts': counts}), flush=True)


def available(jobs):
    return [job for job in jobs if status(job['tag']) == 'not_started'
            and not (PLAN/'claims'/job['tag']).exists()]


def claim(job, gpu):
    directory = PLAN/'claims'/job['tag']
    directory.parent.mkdir(parents=True, exist_ok=True)
    try:
        directory.mkdir()
    except FileExistsError:
        return False
    atomic_write_json(directory/'owner.json', dict(gpu=gpu, pid=os.getpid(), utc=stamp(), job=job))
    return True


def gpu_idle(gpu):
    used = subprocess.check_output(['nvidia-smi', '--id='+str(gpu),
        '--query-gpu=memory.used', '--format=csv,noheader,nounits'], text=True).strip()
    return int(used) < 1500


def preflight(job, gpu):
    tag = job['tag']+'_allgpu_preflight'
    assert not (ROOT/'jobs'/(tag+'_smoke')).exists()
    config = json.loads(Path(job['config']).read_text())
    config['training'].update(epochs=1, min_epochs=1, patience=1,
        max_optimizer_steps=2, effective_batch_size=4, gradient_accumulation=1)
    base = PLAN/'configs'/f'{tag}.yaml'
    atomic_write_json(str(base).replace('.yaml', '_smoke.yaml'), config)
    run_job(dict(job, tag=tag, config=str(base)), gpu, smoke=True)


def worker(gpu):
    assert not (ROOT/'maintenance_hold.json').exists()
    pool = 'attention' if gpu in BLOCKERS else 'adapter'
    plan = json.loads((PLAN/'plan.json').read_text())
    jobs = [job for job in plan['jobs'] if job['pool'] == pool]
    failures = []
    smoke_passed = set()
    if gpu in BLOCKERS and plan['original_counts'].get('running', 0) > 0 and status(BLOCKERS[gpu]) == 'running':
        tag = BLOCKERS[gpu]
        print(f'Waiting for existing fresh run {tag} on GPU {gpu}', flush=True)
        while status(tag) == 'running':
            if (ROOT/'maintenance_hold.json').exists():
                return
            time.sleep(30)
    while available(jobs):
        if (ROOT/'maintenance_hold.json').exists():
            return
        if not gpu_idle(gpu):
            time.sleep(30)
            continue
        job = next((item for item in available(jobs) if claim(item, gpu)), None)
        if job is None:
            continue
        print(f'GPU {gpu}: claimed {job["tag"]}', flush=True)
        try:
            # New smoke on this GPU before its first job of each condition.
            if job['condition'] not in smoke_passed:
                preflight(job, gpu)
                smoke_passed.add(job['condition'])
            run_job(job, gpu)
        except Exception as exc:
            failures.append(dict(tag=job['tag'], error=str(exc)))
            atomic_write_json(PLAN/'claims'/job['tag']/'failure.json', failures[-1])
            print(f'Failed {job["tag"]}: {exc}', flush=True)
    atomic_write_json(PLAN/f'worker_gpu{gpu}.json', dict(utc=stamp(), gpu=gpu,
        status='failed' if failures else 'pool_assigned_or_complete', failures=failures))


def finalize():
    jobs = json.loads((ROOT/'jobs.json').read_text())['jobs']
    while any(status(job['tag']) not in ('complete', 'failed')
              and not (PLAN/'claims'/job['tag']/'failure.json').exists() for job in jobs):
        time.sleep(30)
    with (PLAN/'summary.log').open('w') as log:
        result = subprocess.run([sys.executable, 'scripts/summarize_strengthening.py'],
                                stdout=log, stderr=subprocess.STDOUT)
    record = dict(utc=stamp(), status='complete' if result.returncode == 0 else 'failed',
                  summary_exit_code=result.returncode, summary_log=str(PLAN/'summary.log'))
    atomic_write_json(PLAN/'completion.json', record)
    atomic_write_json(ROOT/'completion.json', record)
    if result.returncode:
        raise RuntimeError('campaign summary failed; inspect summary.log')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--finalize', action='store_true')
    parser.add_argument('--gpu', type=int, choices=range(8))
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.finalize:
        finalize()
    elif args.launch:
        assert not (ROOT/'maintenance_hold.json').exists()
        assert (PLAN/'authorization.json').is_file()
        commands = []
        for gpu in range(8):
            session = f'astguard_allgpu_20261007_g{gpu}'
            check = subprocess.run(['tmux', 'has-session', '-t', session], capture_output=True)
            assert check.returncode != 0, f'{session} already exists'
            argv = [sys.executable, '-u', str(Path(__file__).resolve()), '--gpu', str(gpu)]
            log = (PLAN/f'gpu{gpu}.log').resolve()
            shell_command = shlex.join(argv)+' > '+shlex.quote(str(log))+' 2>&1'
            subprocess.run(['tmux', 'new-session', '-d', '-s', session,
                            '-c', str(Path.cwd()), shell_command], check=True)
            commands.append(dict(gpu=gpu, session=session, argv=argv, log=str(log)))
        atomic_write_json(PLAN/'launch.json', dict(utc=stamp(), workers=commands))
        print(json.dumps({'workers_launched': len(commands)}), flush=True)
    elif args.gpu is not None:
        worker(args.gpu)
    else:
        parser.error('provide --prepare or --gpu')


if __name__ == '__main__':
    main()
