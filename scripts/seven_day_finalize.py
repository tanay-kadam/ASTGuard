"""Detached evidence checks and sealed-cohort inference after training queues.

CPU monitor records partial/failed work honestly. GPU evaluators start only after
their corresponding training worker finishes and wait for idle devices. No
process belonging to another user is terminated or signaled.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file

ROOT = REPO/'artifacts/seven_day_20261012'
OLD = Path('/home/tkadam/ASTGuard')


def stamp(): return datetime.now(timezone.utc).isoformat()


def evaluation_jobs():
    plan = json.loads((ROOT/'plan.json').read_text())
    jobs = [dict(j, status_path=str(ROOT/'jobs'/j['tag']/'status.json'), origin='new')
            for j in plan['jobs'] if j['family'] in {'real', 'regvd'}]
    for condition in ['native', 'permuted', 'self']:
        for seed in [42, 123, 456]:
            tag = f'regvd_{condition}_s{seed}'
            jobs.append({'tag': 'original_'+tag, 'family': 'regvd', 'condition': condition,
                'seed': seed, 'origin': 'original',
                'status_path': str(OLD/'artifacts/release_gates/strengthening_20261006/jobs'/tag/'status.json')})
    assert len(jobs) == 45
    return jobs


def resolve_run(job):
    path = Path(job['status_path'])
    if not path.exists(): return None
    state = json.loads(path.read_text())
    if state.get('status') != 'complete': return None
    run = Path(state['run_dir'])
    if not run.is_absolute(): run = (OLD if job['origin'] == 'original' else REPO)/run
    return run


def gpu_evaluator(gpu):
    target = ROOT/'external_evaluation'
    target.mkdir(exist_ok=True)
    jobs = evaluation_jobs()
    atomic_write_json(target/f'worker_gpu{gpu}.json', {'status': 'waiting_for_training_queue', 'utc': stamp()})
    deadline = datetime.fromisoformat('2026-10-19T05:30:00+00:00')
    while not (ROOT/f'worker_gpu{gpu}.json').exists():
        if datetime.now(timezone.utc) >= deadline: return
        time.sleep(30)
    while not (ROOT/'holdout/manifest.json').exists():
        if (ROOT/'holdout/failure.json').exists() or (ROOT/'holdout/inadequate_cohort.json').exists():
            atomic_write_json(target/f'worker_gpu{gpu}.json', {'status': 'blocked_by_holdout_gate', 'utc': stamp()})
            return
        if datetime.now(timezone.utc) >= deadline: return
        time.sleep(30)
    env = os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES=str(gpu), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', TOKENIZERS_PARALLELISM='false',
        CUBLAS_WORKSPACE_CONFIG=':4096:8', PYTHONPATH=str(REPO))
    for job in jobs:
        while True:
            if datetime.now(timezone.utc) >= deadline: return
            idle = subprocess.check_output(['nvidia-smi', '--id='+str(gpu),
                '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True).split(',')
            if int(idle[0]) < 1000 and int(idle[1]) < 5: break
            time.sleep(30)
        run = resolve_run(job)
        if run is None: continue
        directory = target/job['tag']
        try: directory.mkdir()
        except FileExistsError: continue
        atomic_write_json(directory/'status.json', {'status': 'running', 'utc': stamp(), 'gpu': gpu, 'job': job})
        argv = [sys.executable, 'scripts/seven_day_evaluate_external.py', '--run', str(run),
            '--family', job['family'], '--condition', job['condition'], '--seed', str(job['seed'])]
        try:
            with (directory/'run.log').open('w') as f:
                # A new-model/data smoke is separate from full predictions.
                for name, extra in [('smoke.json', ['--max-examples', '16']), ('predictions.json', [])]:
                    command = argv+['--output', str(directory/name)]+extra
                    f.write(json.dumps({'utc': stamp(), 'argv': command})+'\n'); f.flush()
                    completed = subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT)
                    if completed.returncode: raise RuntimeError(f'{name}: exit {completed.returncode}')
            data = json.loads((directory/'predictions.json').read_text())
            assert data['status'] == 'complete'
            atomic_write_json(directory/'status.json', {'status': 'complete', 'utc': stamp(), 'gpu': gpu,
                'job': job, 'predictions_sha256': sha256_file(directory/'predictions.json')})
        except Exception as exc:
            atomic_write_json(directory/'status.json', {'status': 'failed', 'utc': stamp(), 'gpu': gpu,
                'job': job, 'error': repr(exc)})
    atomic_write_json(target/f'worker_gpu{gpu}.json', {'status': 'queue_scan_finished', 'utc': stamp()})


def verify_job(job):
    from sklearn.metrics import average_precision_score, roc_auc_score
    run_state = json.loads((ROOT/'jobs'/job['tag']/'status.json').read_text())
    run = Path(run_state['run_dir'])
    if job['family'] == 'regvd':
        selection = json.loads((run/'selection.json').read_text())
        selected = [json.loads(line) for line in (run/'selected_predictions.jsonl').read_text().splitlines() if line.strip()]
        expected = selection['tune_ap']; key = 'logit'
        streams = {p.stem: [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
                   for p in run.glob('intervention_*.jsonl')}
        claimed = json.loads((run/'interventions.json').read_text())
        metrics = {name: {'ap': average_precision_score([r['label'] for r in rows], [r['logit'] for r in rows]),
                         'roc_auc': roc_auc_score([r['label'] for r in rows], [r['logit'] for r in rows])}
                   for name, rows in streams.items()}
        for name, values in metrics.items():
            for metric in ['ap', 'roc_auc']:
                assert abs(values[metric]-claimed[name.replace('intervention_', '')][metric]) < 1e-12
        checkpoint = run/'best.safetensors'
    else:
        selection = json.loads((run/'checkpoint_selection.json').read_text())
        selected = [json.loads(line) for line in (run/'selected_tune_predictions.jsonl').read_text().splitlines() if line.strip()]
        expected = selection['best_value']; key = 'probability'
        intervention = json.loads((ROOT/'jobs'/job['tag']/'interventions.json').read_text())
        rows = intervention['predictions']; metrics = {}
        for mode, claimed in intervention['metrics'].items():
            ap = average_precision_score([r['label'] for r in rows], [r[mode] for r in rows])
            auc = roc_auc_score([r['label'] for r in rows], [r[mode] for r in rows])
            change = sum(abs(r[mode]-r['normal']) for r in rows)/len(rows)
            assert abs(ap-claimed['ap']) < 1e-12 and abs(auc-claimed['roc_auc']) < 1e-12
            assert abs(change-claimed['mean_abs_logit_change']) < 1e-12
            metrics[mode] = dict(claimed)
        checkpoint = run/'checkpoints/best.safetensors'
        assert sha256_file(checkpoint) == intervention['checkpoint_sha256']
    ap = average_precision_score([r['label'] for r in selected], [r[key] for r in selected])
    assert abs(ap-expected) < 1e-12
    assert len({r['sample_id'] for r in selected}) == len(selected)
    assert len(selected) == (1024 if job['family'] == 'synthetic' else 10566)
    return {'tag': job['tag'], 'family': job['family'], 'condition': job['condition'], 'seed': job['seed'],
        'selected_tune_ap': ap, 'selection': selection, 'interventions': metrics,
        'checkpoint_sha256': sha256_file(checkpoint), 'run_dir': str(run), 'independent_metric_check': 'passed'}


def external_analysis():
    from scripts.seven_day_analysis import paired_analysis
    manifest = json.loads((ROOT/'holdout/manifest.json').read_text())
    membership = json.loads((ROOT/'holdout/membership.json').read_text())
    component = {r[0]: r[2] for r in membership['rows']}
    predictions = {}; labels = None; ids = None
    for job in evaluation_jobs():
        path = ROOT/'external_evaluation'/job['tag']/'predictions.json'
        if not path.exists(): return False
        doc = json.loads(path.read_text()); rows = doc['predictions']
        if ids is None:
            ids = [r['sample_id'] for r in rows]; labels = [r['label'] for r in rows]
        assert [r['sample_id'] for r in rows] == ids and [r['label'] for r in rows] == labels
        assert len(rows) == manifest['n']
        predictions[(job['family'], job['condition'], job['seed'])] = [r['normal'] for r in rows]
    contrasts = [('attention_authentic', 'attention_shuffled'), ('attention_authentic', 'attention_sequence'),
                 ('adapter_centered', 'adapter_sequence'), ('native', 'permuted'), ('native', 'self')]
    results = {}
    for left, right in contrasts:
        family = 'regvd' if left == 'native' else 'real'
        a = {s: predictions[(family, left, s)] for s in [42, 123, 456, 789, 2026]}
        b = {s: predictions[(family, right, s)] for s in [42, 123, 456, 789, 2026]}
        results[left+'-minus-'+right] = paired_analysis(labels, a, b, [component[sid] for sid in ids])
        atomic_write_json(ROOT/'external_analysis_progress.json', results)
    atomic_write_json(ROOT/'external_analysis.json', {'status': 'complete', 'contrasts': results,
        'manifest_sha256': sha256_file(ROOT/'holdout/manifest.json'), 'n': manifest['n'],
        'analysis_script_sha256': sha256_file(REPO/'scripts/seven_day_analysis.py')})
    return True


def selection_diagnostic(checks):
    results = {}
    for seed in [42, 123, 456, 789, 2026]:
        left_tag = f'synthetic_centered_shuffled_s{seed}'
        right_tag = f'synthetic_centered_shuffled_donor_tune_s{seed}'
        if left_tag not in checks or right_tag not in checks: continue
        a, b = checks[left_tag], checks[right_tag]
        def history(record):
            return [json.loads(line) for line in (Path(record['run_dir'])/'train_log.jsonl').read_text().splitlines() if line.strip()]
        ah, bh = history(a), history(b)
        same = len(ah) == len(bh) and all(x['optimizer_steps'] == y['optimizer_steps'] and abs(x['loss']-y['loss']) < 1e-12
                                                    for x, y in zip(ah, bh))
        results[str(seed)] = {'training_loss_trajectories_match': same,
            'authentic_tune_selected_epoch': a['selection']['epoch'],
            'donor_tune_selected_epoch': b['selection']['epoch'],
            'authentic_tune_checkpoint_audit_ap': a['interventions']['normal']['ap'],
            'donor_tune_checkpoint_audit_ap': b['interventions']['normal']['ap'],
            'interpretation': 'Selection-only interpretation requires matching training trajectories; inspect before claiming a mechanism.'}
    atomic_write_json(ROOT/'selection_diagnostic.json', {'seeds': results, 'complete': len(results) == 5})


def synthetic_checks(checks):
    results = {}
    for seed in [42, 123, 456, 789, 2026]:
        prefix = 'synthetic_'
        names = ['sequence', 'attention_authentic', 'attention_shuffled', 'centered_authentic', 'centered_shuffled']
        tags = {name: f'{prefix}{name}_s{seed}' for name in names}
        if any(tag not in checks for tag in tags.values()): continue
        values = {name: checks[tag]['interventions'] for name, tag in tags.items()}
        per_family = {}
        for family in ['attention', 'centered']:
            authentic, shuffled = values[family+'_authentic'], values[family+'_shuffled']
            ap = authentic['normal']['ap']
            rule = {'authentic_ap_at_least_0_90': ap >= .90,
                'authentic_minus_sequence_at_least_0_30': ap-values['sequence']['normal']['ap'] >= .30,
                'authentic_minus_shuffled_at_least_0_30': ap-shuffled['normal']['ap'] >= .30,
                'normal_minus_empty_at_least_0_30': ap-authentic['empty']['ap'] >= .30,
                'normal_minus_null_at_least_0_20': ap-authentic['null']['ap'] >= .20}
            per_family[family] = {'criteria': rule, 'all_pass': all(rule.values()),
                'authentic_audit_ap': ap, 'shuffled_audit_ap': shuffled['normal']['ap']}
        results[str(seed)] = per_family
    atomic_write_json(ROOT/'synthetic_control_checks.json', {'seeds': results, 'complete': len(results) == 5,
        'thresholds_frozen_before_new_runs': True, 'failed_controls_retained': True})


def monitor():
    plan = json.loads((ROOT/'plan.json').read_text())
    checks = {}; failures = {}
    while True:
        now = datetime.now(timezone.utc)
        if now >= datetime.fromisoformat(plan['stop_starting_after_utc']):
            (ROOT/'STOP_STARTING').touch(exist_ok=True)
        states = Counter()
        for job in plan['jobs']:
            state_path = ROOT/'jobs'/job['tag']/'status.json'
            failure = ROOT/'claims'/job['tag']/'failure.json'
            state = json.loads(state_path.read_text())['status'] if state_path.exists() else 'failed_or_blocked' if failure.exists() else 'queued'
            states[state] += 1
            if state == 'complete' and job['tag'] not in checks and job['tag'] not in failures:
                try: checks[job['tag']] = verify_job(job)
                except Exception as exc: failures[job['tag']] = repr(exc)
        atomic_write_json(ROOT/'verified_metrics.json', {'utc': stamp(), 'jobs': checks, 'verification_failures': failures})
        selection_diagnostic(checks)
        report = {'utc': stamp(), 'training_counts': dict(states), 'verified_jobs': len(checks),
            'verification_failures': failures, 'complete': len(checks) == len(plan['jobs']) and not failures,
            'holdout_ready': (ROOT/'holdout/manifest.json').exists(),
            'external_analysis_ready': (ROOT/'external_analysis.json').exists()}
        resource = ROOT/'resource_wait_status.json'
        if resource.exists(): report['resource_wait'] = json.loads(resource.read_text())
        atomic_write_json(ROOT/'campaign_status.json', report)
        if report['holdout_ready'] and not report['external_analysis_ready']:
            try: external_analysis()
            except Exception as exc: atomic_write_json(ROOT/'external_analysis_failure.json', {'error': repr(exc), 'utc': stamp()})
        if now >= datetime.fromisoformat('2026-10-19T05:30:00+00:00'):
            atomic_write_json(ROOT/'deadline_status.json', report)
            return
        if report['complete'] and (ROOT/'external_analysis.json').exists(): return
        time.sleep(60)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--monitor', action='store_true')
    p.add_argument('--gpu', type=int, choices=range(8)); args = p.parse_args()
    os.chdir(REPO)
    if args.monitor: monitor()
    elif args.gpu is not None: gpu_evaluator(args.gpu)
    else: p.error('choose --monitor or --gpu')


if __name__ == '__main__': main()
