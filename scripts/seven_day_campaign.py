"""Isolated, atomic eight-GPU queue for the frozen 2026-10-12 protocol.

Run --prepare once inside the source snapshot, then --launch. Full jobs are cold
starts. Failed claims are preserved and never retried without inspection.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import shlex
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from astguard.config import dump_config, load_config
from astguard.utils.atomic_io import atomic_write_json, atomic_write_text
from astguard.utils.hashing import object_hash, sha256_file

OLD = Path('/home/tkadam/ASTGuard')
ROOT = REPO/'artifacts/seven_day_20261012'
SEEDS = [42, 123, 456, 789, 2026]
PROTOCOL = REPO/'docs/SEVEN_DAY_STRENGTHENING_PROTOCOL_20261012.md'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def prepare():
    if (ROOT/'plan.json').exists():
        raise FileExistsError('Plan already frozen; inspect instead of replacing')
    assert shutil.disk_usage(REPO).free > 200 * 1024**3
    import torch
    assert torch.cuda.device_count() == 8
    original = OLD/'data/strengthening_20261006'
    (REPO/'data').mkdir(exist_ok=True)
    (REPO/'data/strengthening_20261006').symlink_to(original, target_is_directory=True)
    real = json.loads((original/'real/manifest.json').read_text())
    assert real['counts'] == {'train': 141560, 'tune': 10566}
    assert real['positives'] == {'train': 4302, 'tune': 330}
    for name, expected in real['hashes'].items():
        assert sha256_file(original/'real'/f'{name}.jsonl') == expected
    old_matrix = json.loads((OLD/'artifacts/release_gates/strengthening_20261006/jobs.json').read_text())
    reference = {j['tag']: j for j in old_matrix['jobs']}
    source = {str(p.relative_to(REPO)): sha256_file(p)
              for directory in ['astguard', 'scripts', 'configs', 'third_party']
              for p in (REPO/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    atomic_write_json(ROOT/'source_files.json', source)
    protocol_hash = sha256_file(PROTOCOL)
    source_hash = object_hash(source)
    # Generate a new sequence-disjoint synthetic cohort before any training.
    from scripts.generate_topology_positive_control import generate_split, validate_rows, _atomic_jsonl, PREPROCESSING_HASH
    seen = set()
    for role in ['train', 'tune', 'audit']:
        with (original/'synthetic'/f'{role}.jsonl').open() as f:
            seen.update(tuple(json.loads(line)['input_ids'][1:-1]) for line in f if line.strip())
    rng = random.Random(20261012)
    groups = {role: generate_split(role, count, rng, seen)
              for role, count in [('train', 2048), ('tune', 512), ('audit', 512)]}
    validate_rows(groups['train'], groups['tune'])
    validate_rows(groups['train'], groups['audit'])
    validate_rows(groups['tune'], groups['audit'])
    synth_hash = object_hash({'kind': 'seven-day-synthetic', 'seed': 20261012, 'pairs': [2048, 512, 512]})
    syn = REPO/'data/seven_day_20261012/synthetic'
    for role, rows in groups.items():
        for row in rows:
            row.update(sample_id='sd-20261012-'+row['sample_id'],
                       component_id='sd-20261012-'+row['component_id'], split_hash=synth_hash)
        _atomic_jsonl(syn/f'{role}.jsonl', rows)
    from astguard.data.graph_donors import length_matched_donors, transplant_graph
    donor_audit = {}
    for seed in SEEDS:
        rows = groups['tune']
        donors, stats = length_matched_donors([len(r['input_ids']) for r in rows], seed)
        donor_rows = [transplant_graph(row, rows[donors[i]]) for i, row in enumerate(rows)]
        _atomic_jsonl(syn/f'donor_tune_s{seed}.jsonl', donor_rows)
        table = Counter((r['label'], rows[donors[i]]['label']) for i, r in enumerate(rows))
        donor_audit[str(seed)] = {'stats': stats, 'recipient_donor_label_counts': {str(k): v for k, v in table.items()},
            'same_component_donors': sum(r['component_id'] == rows[donors[i]]['component_id'] for i, r in enumerate(rows))}
    atomic_write_json(ROOT/'synthetic_integrity.json', {'generation_seed': 20261012,
        'excluded_original_sequences': True, 'sequence_component_disjoint': True,
        'counts': {role: len(rows) for role, rows in groups.items()}, 'donor_tune': donor_audit,
        'hashes': {p.name: sha256_file(p) for p in syn.glob('*.jsonl')}})
    jobs = []
    specs = [(family, condition) for family, conditions in [
        ('real', ['attention_sequence', 'attention_authentic', 'attention_shuffled',
                  'adapter_sequence', 'adapter_uncentered', 'adapter_centered']),
        ('synthetic', ['sequence', 'attention_authentic', 'attention_shuffled',
                       'centered_authentic', 'centered_shuffled', 'centered_shuffled_donor_tune'])]
             for condition in conditions]
    for family, condition in specs:
        parent_condition = condition.replace('_donor_tune', '')
        old_job = reference[f'{family}_{parent_condition}_s42']
        old_config = load_config(OLD/old_job['config'])
        for seed in SEEDS:
            epochs = (10 if condition.startswith('attention_') else 6) if family == 'real' else 12
            tag = f'{family}_{condition}_s{seed}'
            config = dataclasses.replace(old_config, experiment_id='SEVEN_DAY_'+tag,
                dataset=dataclasses.replace(old_config.dataset, manifest_hash=synth_hash if family == 'synthetic' else old_config.dataset.manifest_hash),
                training=dataclasses.replace(old_config.training, seed=seed, epochs=epochs,
                    min_epochs=epochs, patience=epochs, max_optimizer_steps=1536 if family == 'synthetic' else None),
                provenance=dataclasses.replace(old_config.provenance, protocol_hash=protocol_hash))
            path = ROOT/'configs'/f'{tag}.yaml'
            atomic_write_text(path, dump_config(config))
            smoke = dataclasses.replace(config, training=dataclasses.replace(config.training,
                epochs=1, min_epochs=1, patience=1, max_optimizer_steps=2,
                microbatch_size=4, gradient_accumulation=1, effective_batch_size=4))
            smoke_path = path.with_name(tag+'_smoke.yaml')
            atomic_write_text(smoke_path, dump_config(smoke))
            cost = {'adapter_centered': 44, 'adapter_uncentered': 13.3,
                    'adapter_sequence': 8, 'attention_sequence': 12.6}.get(condition, 24)
            jobs.append({'tag': tag, 'family': family, 'condition': condition, 'seed': seed,
                         'config': str(path), 'smoke_config': str(smoke_path), 'epochs': epochs,
                         'estimated_hours': cost if family == 'real' else 0.2})
    for seed in [789, 2026]:
        for mode in ['native', 'permuted', 'self']:
            jobs.append({'tag': f'regvd_{mode}_s{seed}', 'family': 'regvd', 'condition': mode,
                         'seed': seed, 'estimated_hours': 3})
    jobs.sort(key=lambda j: (-j['estimated_hours'], j['tag']))
    assert len(jobs) == 66 and len({j['tag'] for j in jobs}) == 66
    atomic_write_json(ROOT/'plan.json', {'created_utc': stamp(), 'protocol_sha256': protocol_hash,
        'source_sha256': source_hash, 'jobs': jobs, 'gpus': list(range(8)),
        'stop_starting_after_utc': '2026-10-17T05:30:00+00:00',
        'existing_results_unchanged': True, 'independent_real_evaluation': 'gated_pending_exposure_clone_audit'})
    atomic_write_json(ROOT/'authorization.json', {'utc': stamp(),
        'instruction': 'User requested seven days and all eight GPUs; no guaranteed paper rating.',
        'public_posting_authorized': False})
    print(json.dumps({'jobs': len(jobs), 'root': str(ROOT), 'protocol_sha256': protocol_hash}), flush=True)


def command(argv, log, env):
    with log.open('a') as f:
        f.write(json.dumps({'utc': stamp(), 'argv': argv, 'cuda_visible_devices': env['CUDA_VISIBLE_DEVICES']})+'\n')
        f.flush()
        result = subprocess.run(argv, stdout=f, stderr=subprocess.STDOUT, env=env)
    if result.returncode:
        raise RuntimeError(f'exit {result.returncode}: {log}')


def execute(job, gpu, smoke=False):
    import torch
    assert torch.cuda.is_available()
    target = ROOT/('smokes' if smoke else 'jobs')/job['tag']
    target.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES=str(gpu), PYTHONPATH=str(REPO),
               TOKENIZERS_PARALLELISM='false', CUBLAS_WORKSPACE_CONFIG=':4096:8',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    status = target/'status.json'
    atomic_write_json(status, {'status': 'running', 'utc': stamp(), 'gpu': gpu, 'job': job})
    start = time.time()
    try:
        if shutil.disk_usage(REPO).free < 30*1024**3:
            raise RuntimeError('disk reserve below 30 GiB')
        if job['family'] == 'regvd':
            data = REPO/'data/strengthening_20261006'/('smoke' if smoke else 'real')
            run = target/'run'
            argv = [sys.executable, 'scripts/run_regvd_strengthening.py', '--train', str(data/'regvd_train.jsonl'),
                    '--tune', str(data/'regvd_tune.jsonl'), '--condition', job['condition'],
                    '--seed', str(job['seed']), '--output', str(run)]
            if smoke:
                argv.append('--smoke')
            command(argv, target/'run.log', env)
            record = json.loads((run/'status.json').read_text())
            assert record['status'] == 'complete'
        else:
            syn = job['family'] == 'synthetic'
            data = REPO/'data/seven_day_20261012/synthetic' if syn else REPO/'data/strengthening_20261006'/('smoke' if smoke else 'real')
            tune = data/(f'donor_tune_s{job["seed"]}.jsonl' if job['condition'].endswith('_donor_tune') else 'tune.jsonl')
            argv = [sys.executable, '-m', 'astguard.train', '--config', job['smoke_config'] if smoke else job['config'],
                    '--features', str(data/'train.jsonl'), '--tune-features', str(tune), '--seed', str(job['seed']),
                    '--runs-root', str(target/'runs'), '--require-cuda']
            command(argv, target/'run.log', env)
            runs = list((target/'runs').glob('*/provenance.json'))
            assert len(runs) == 1
            run = runs[0].parent
            record = json.loads(runs[0].read_text())
            assert record['hardware']['device'] == 'cuda'
            expected = 2 if smoke else 1536 if syn else 4424*job['epochs']
            assert record['optimizer_steps'] == expected, (record['optimizer_steps'], expected)
            role = 'audit' if syn else 'tune'
            argv = [sys.executable, 'scripts/evaluate_strengthening_checkpoint.py', '--run', str(run),
                    '--features', str(data/f'{role}.jsonl'), '--role', role, '--output', str(target/'interventions.json')]
            if smoke:
                argv += ['--max-examples', '16']
            command(argv, target/'run.log', env)
        atomic_write_json(status, {'status': 'complete', 'utc': stamp(), 'gpu': gpu,
            'run_dir': str(run), 'elapsed_seconds': time.time()-start, 'job': job})
    except Exception as exc:
        atomic_write_json(status, {'status': 'failed', 'utc': stamp(), 'gpu': gpu, 'job': job, 'error': repr(exc)})
        raise


def worker(gpu):
    plan = json.loads((ROOT/'plan.json').read_text())
    assert sha256_file(PROTOCOL) == plan['protocol_sha256']
    print(json.dumps({'worker_gpu': gpu, 'pid': os.getpid(), 'utc': stamp()}), flush=True)
    for job in plan['jobs']:
        if (ROOT/'STOP_STARTING').exists() or datetime.now(timezone.utc) >= datetime.fromisoformat(plan['stop_starting_after_utc']):
            break
        while True:
            values = subprocess.check_output(['nvidia-smi', '--id='+str(gpu), '--query-gpu=memory.used,utilization.gpu',
                                             '--format=csv,noheader,nounits'], text=True).strip().split(',')
            if int(values[0]) < 1000 and int(values[1]) < 5:
                break
            if (ROOT/'STOP_STARTING').exists():
                return
            time.sleep(30)
        claim = ROOT/'claims'/job['tag']
        claim.parent.mkdir(parents=True, exist_ok=True)
        try:
            claim.mkdir()
        except FileExistsError:
            continue
        atomic_write_json(claim/'owner.json', {'gpu': gpu, 'pid': os.getpid(), 'utc': stamp(), 'job': job})
        key = job['family']+'_'+job['condition']
        gate = ROOT/'gates'/key
        gate.parent.mkdir(parents=True, exist_ok=True)
        try:
            try:
                gate.mkdir()
                gate_owner = True
            except FileExistsError:
                gate_owner = False
            if gate_owner:
                try:
                    execute(job, gpu, smoke=True)
                    atomic_write_json(gate/'status.json', {'status': 'passed', 'utc': stamp(), 'smoke_job': job['tag']})
                except Exception as exc:
                    atomic_write_json(gate/'status.json', {'status': 'failed', 'utc': stamp(), 'error': repr(exc)})
                    raise
            else:
                while not (gate/'status.json').exists():
                    time.sleep(5)
                assert json.loads((gate/'status.json').read_text())['status'] == 'passed', 'condition smoke failed'
            execute(job, gpu)
        except Exception as exc:
            atomic_write_json(claim/'failure.json', {'utc': stamp(), 'error': repr(exc)})
            print(json.dumps({'tag': job['tag'], 'failure': repr(exc)}), flush=True)
    atomic_write_json(ROOT/f'worker_gpu{gpu}.json', {'utc': stamp(), 'status': 'queue_scan_finished', 'gpu': gpu})


def launch():
    plan = json.loads((ROOT/'plan.json').read_text())
    assert sha256_file(PROTOCOL) == plan['protocol_sha256']
    assert not (ROOT/'launch.json').exists()
    commands = []
    for gpu in range(8):
        name = f'astguard_7day_20261012_g{gpu}'
        assert subprocess.run(['tmux', 'has-session', '-t', name], capture_output=True).returncode != 0
        argv = [sys.executable, '-u', str(Path(__file__).resolve()), '--gpu', str(gpu)]
        log = ROOT/f'gpu{gpu}.log'
        shell = shlex.join(argv)+' > '+shlex.quote(str(log))+' 2>&1'
        subprocess.run(['tmux', 'new-session', '-d', '-s', name, '-c', str(REPO), shell], check=True)
        commands.append({'gpu': gpu, 'session': name, 'argv': argv, 'log': str(log)})
    atomic_write_json(ROOT/'launch.json', {'utc': stamp(), 'workers': commands})
    print(json.dumps({'launched': len(commands), 'root': str(ROOT)}), flush=True)


def status():
    plan = json.loads((ROOT/'plan.json').read_text())
    counts = Counter()
    details = []
    for job in plan['jobs']:
        path = ROOT/'jobs'/job['tag']/'status.json'
        failure = ROOT/'claims'/job['tag']/'failure.json'
        state = json.loads(path.read_text()) if path.exists() else {'status': 'blocked_or_failed' if failure.exists() else 'claimed' if failure.parent.exists() else 'queued'}
        counts[state['status']] += 1
        if state['status'] != 'queued':
            details.append({'tag': job['tag'], **state})
    report = {'utc': stamp(), 'counts': dict(counts), 'jobs': details}
    print(json.dumps(report, indent=2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prepare', action='store_true'); p.add_argument('--launch', action='store_true')
    p.add_argument('--status', action='store_true'); p.add_argument('--gpu', type=int, choices=range(8))
    args = p.parse_args()
    os.chdir(REPO)
    if args.prepare: prepare()
    elif args.launch: launch()
    elif args.status: status()
    elif args.gpu is not None: worker(args.gpu)
    else: p.error('choose --prepare, --launch, --status or --gpu')


if __name__ == '__main__':
    main()
