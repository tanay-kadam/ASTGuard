"""Bounded, pretrained, train-only development pilot. Never launches full jobs."""
from __future__ import annotations

import argparse
import csv
import dataclasses
import gc
import heapq
import json
import os
import sys
import time
import uuid
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch
from safetensors.torch import load_model, save_model
from torch.utils.data import DataLoader
from transformers import get_linear_schedule_with_warmup

from astguard.alignment.tokenizer import CanonicalTokenizer
from astguard.config import load_config, dump_config
from astguard.data.audit import LeakageAuditor
from astguard.data.preprocess import preprocess_record
from astguard.data.schema import SampleRecord, read_jsonl, write_jsonl
from astguard.evaluation.metrics import average_precision, evaluate_scores, decode_threshold
from astguard.evaluation.thresholds import ThresholdSelector
from astguard.models.factory import create_model, create_collator
from astguard.training.engine import Trainer, weighted_bce_logits
from astguard.training.optim import build_adamw
from astguard.training.seeds import set_seed
from astguard.utils.atomic_io import atomic_write_json, atomic_write_text, append_jsonl
from astguard.utils.hashing import object_hash, sha256_file
from astguard.utils.provenance import environment_snapshot, source_identity

VARIANTS = ['sequence_only', 'ast_dfg_fixed', 'query_gated_astguard', 'edge_gated_astguard']


def prepare(root, source, counts, max_length):
    # Fixed hash sampling within label and a component audit on the candidate pool.
    # No validation/test release records are eligible, even for calibration.
    heaps = {0: [], 1: []}
    pool_size = max(256, sum(counts.values()) * 2)
    for row in read_jsonl('data/interim/primevul/records.jsonl'):
        if row['original_split'] != 'train':
            continue
        label = int(row['label'])
        key = int(object_hash(['edge-pilot-v1', row['sample_id']]), 16)
        entry = (-key, row['sample_id'], row)
        if len(heaps[label]) < pool_size:
            heapq.heappush(heaps[label], entry)
        elif entry > heaps[label][0]:
            heapq.heapreplace(heaps[label], entry)
    records = [SampleRecord.from_dict(entry[2]) for heap in heaps.values() for entry in heap]
    components, evidence = LeakageAuditor().build_components(records)
    ordered = sorted(records, key=lambda r: object_hash(['edge-pilot-order-v1', r.sample_id]))
    used = set()
    groups = {role: [] for role in counts}
    for role, count in counts.items():
        for label in (0, 1):
            selected = [r for r in ordered if r.label == label and components[r.sample_id] not in used]
            accepted = 0
            for record in selected:
                component = components[record.sample_id]
                if component in used:
                    continue
                used.add(component)
                groups[role].append(record)
                accepted += 1
                if accepted == count // 2:
                    break
            if accepted != count // 2:
                raise RuntimeError('insufficient independent development components')
    tokenizer = CanonicalTokenizer(source['codebert_path'], source['codebert_revision'])
    features = {}
    failures = []
    coverage = {}
    start = time.perf_counter()
    for role, records_for_role in groups.items():
        features[role] = []
        for record in records_for_role:
            feature = dataclasses.asdict(preprocess_record(record, tokenizer, max_length=max_length))
            feature.update(label=record.label, role=role, component_id=components[record.sample_id])
            features[role].append(feature)
            if feature['status_reasons']:
                failures.append(dict(sample_id=record.sample_id, dataset='primevul', role=role,
                                     reasons=feature['status_reasons'], parse_status=feature['parse_status'],
                                     dfg_status=feature['dfg_status']))
        write_jsonl(root/'features'/f'{role}.jsonl', features[role])
        coverage[role] = {name: dict(Counter(row[name] for row in features[role]))
                          for name in ('parse_status', 'ast_status', 'dfg_status', 'alignment_status')}
        coverage[role]['nonempty_ast'] = sum(bool(row['ast_token_edges']) for row in features[role])
        coverage[role]['nonempty_dfg'] = sum(bool(row['dfg_token_edges']) for row in features[role])
    manifest = {'kind': 'balanced_train_only_development_pilot', 'official_test_used': False,
                'natural_distribution': False, 'counts': counts, 'selection': 'edge-pilot-v1',
                'roles': {role: [{'sample_id': r.sample_id, 'component': components[r.sample_id],
                                 'label': r.label, 'source_sha256': r.raw_sha256} for r in rows]
                          for role, rows in groups.items()},
                'candidate_components': len(set(components.values())), 'candidate_link_count': len(evidence),
                'leakage_audit_scope': 'selected candidate pool only; full-release audit remains pending'}
    manifest['hash'] = object_hash(manifest)
    atomic_write_json(root/'split_manifest.json', manifest)
    atomic_write_json(root/'preprocessing.json', {'coverage': coverage, 'seconds': time.perf_counter()-start,
                                               'failure_rows': len(failures), 'excluded_after_preprocessing': 0})
    write_jsonl(root/'preprocessing_failures.jsonl', failures)
    return features, manifest


def loaders_for(groups, config):
    return {role: DataLoader(rows, batch_size=config.training.microbatch_size, shuffle=role == 'train',
                            collate_fn=create_collator(config, training=role == 'train'),
                            generator=torch.Generator().manual_seed(config.training.seed))
            for role, rows in groups.items()}


def sync(device):
    if device == 'cuda':
        torch.cuda.synchronize()


def measured_loss(trainer, loader, weights):
    trainer.model.eval()
    total, count = 0., 0
    with torch.no_grad():
        for batch in loader:
            logits = trainer.forward(batch)['logits']
            loss = weighted_bce_logits(logits, batch['labels'].to(trainer.device), weights)
            total += float(loss) * len(logits)
            count += len(logits)
    return total/count


def benchmark(trainer, loader):
    batch = next(iter(loader))
    trainer.model.eval()
    times = []
    with torch.no_grad():
        for _ in range(3):
            trainer.forward(batch)
        for _ in range(10):
            sync(trainer.device)
            start = time.perf_counter()
            trainer.forward(batch)
            sync(trainer.device)
            times.append(1000*(time.perf_counter()-start))
    return dict(latency_mean_ms=float(np.mean(times)), latency_median_ms=float(np.median(times)),
                latency_p95_ms=float(np.percentile(times, 95)), latency_batch_size=len(batch['labels']),
                latency_sequence_length=batch['input_ids'].shape[1], latency_repeats=10,
                latency_scope='model forward including host-to-device transfer; excludes preprocessing/collation')


def gate_analysis(trainer, loader, run):
    rows = []
    trainer.model.eval()
    with torch.no_grad():
        for batch in loader:
            args = {key: batch[key].to(trainer.device) for key in
                    ('input_ids', 'attention_mask', 'relation_masks', 'special_tokens_mask')}
            trainer.model(**args, output_attentions=True)
            for layer_id, layer in enumerate(trainer.model.layers):
                attention = layer.structural_attention
                if attention is None:
                    continue
                for relation in attention.last_diagnostics['edge_relations']:
                    indices = relation['edge_index'].cpu().tolist()
                    gates, coefficients = relation['gates'].cpu(), relation['coefficients'].cpu()
                    for edge, (b, i, j) in enumerate(indices):
                        for head in range(attention.heads):
                            rows.append(dict(sample_id=batch['sample_ids'][b], layer=layer_id, head=head,
                                             relation=trainer.model.relations[relation['relation']], query=i, key=j,
                                             gate=float(gates[edge, head]), coefficient=float(coefficients[edge, head])))
    write_jsonl(run/'edge_gates.jsonl', rows)
    import pandas as pd
    frame = pd.DataFrame(rows)
    if not frame.empty:
        summary = frame.groupby(['layer', 'head', 'relation']).agg(
            mean=('gate', 'mean'), median=('gate', 'median'), std=('gate', 'std'), count=('gate', 'size'),
            near_zero=('gate', lambda x: float((x < .05).mean())), near_one=('gate', lambda x: float((x > .95).mean())),
            mean_effective_coefficient=('coefficient', 'mean'))
        summary.to_csv(run/'gate_statistics.csv')
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        values = frame.groupby(['layer', 'relation']).gate.mean().unstack()
        fig, ax = plt.subplots(figsize=(5, 3))
        picture = ax.imshow(values.values, vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(len(values.columns)), values.columns)
        ax.set_yticks(range(len(values.index)), values.index)
        ax.set_ylabel('Layer (zero based)')
        ax.set_title('Development pilot: mean edge gate')
        fig.colorbar(picture, ax=ax)
        fig.tight_layout()
        fig.savefig(run/'gate_heatmap.png', dpi=150)
        plt.close(fig)


def run_variant(root, variant, base, groups, args, device):
    config = dataclasses.replace(base, model=dataclasses.replace(base.model, variant=variant,
        beta_init=.05 if variant == 'ast_dfg_fixed' else .10,
        gate_mode='edge' if variant == 'edge_gated_astguard' else
                  'query_capacity_matched' if variant == 'query_capacity_matched' else 'token'))
    run = root/variant
    run.mkdir()
    atomic_write_text(run/'resolved_config.json', dump_config(config))
    set_seed(config.training.seed)
    model = create_model(config).to(device)
    if device == 'cuda':
        torch.cuda.reset_peak_memory_stats()
    optimizer = build_adamw(model, pretrained_lr=config.training.pretrained_lr, new_multiplier=1., weight_decay=.01)
    loaders = loaders_for(groups, config)
    total_steps = args.epochs*len(loaders['train'])
    scheduler = get_linear_schedule_with_warmup(optimizer, max(1, int(.1*total_steps)), total_steps)
    trainer = Trainer(model, optimizer, scheduler, device=device, precision='fp32')
    labels = [row['label'] for row in groups['train']]
    weights = {label: len(labels)/(2*labels.count(label)) for label in (0, 1)}
    atomic_write_json(run/'class_weights.json', {'source': 'train_only', 'weights': weights})
    train_evaluation = DataLoader(groups['train'], batch_size=args.batch_size, collate_fn=create_collator(config))
    initial_loss = measured_loss(trainer, train_evaluation, weights)
    history, best, selected_epoch = [], -1., None
    start = time.perf_counter()
    for epoch in range(args.epochs):
        log = trainer.train_epoch(loaders['train'], weights)
        predictions = trainer.predict(loaders['tune'])
        ap = average_precision([r['label'] for r in predictions], [r['probability'] for r in predictions])
        row = {'epoch': epoch+1, 'tune_ap': ap, **log}
        history.append(row)
        append_jsonl(run/'train_log.jsonl', row)
        if ap > best:
            best, selected_epoch = ap, epoch+1
            save_model(model, str(run/'best.safetensors'))
        print(f'{variant}: epoch={epoch+1} loss={log["loss"]:.5f} tune_AP={ap:.5f}', flush=True)
    sync(device)
    training_seconds = time.perf_counter()-start
    final_loss = measured_loss(trainer, train_evaluation, weights)
    peak = torch.cuda.max_memory_allocated() if device == 'cuda' else None
    load_model(model, str(run/'best.safetensors'))
    checkpoint_hash = sha256_file(run/'best.safetensors')
    calibration = trainer.predict(loaders['cal'])
    thresholds = ThresholdSelector().fit([r['sample_id'] for r in calibration], [r['label'] for r in calibration],
                 [r['probability'] for r in calibration], role='cal', checkpoint_hash=checkpoint_hash)
    threshold = decode_threshold(thresholds['max_f1'].threshold)
    predictions = trainer.predict(loaders['development_validation'])
    metadata = dict(run_id=str(run), model=variant, seed=args.seed, dataset='primevul',
                    split='development_validation_from_official_train', checkpoint_hash=checkpoint_hash,
                    config_path=str(run/'resolved_config.json'), threshold=threshold)
    atomic_write_json(run/'predictions.json', [row | metadata | {'predicted_label': row['probability'] >= threshold}
                                             for row in predictions])
    atomic_write_json(run/'calibration_predictions.json', calibration)
    atomic_write_json(run/'thresholds.json', {k: dataclasses.asdict(v) for k, v in thresholds.items()})
    metrics = evaluate_scores([r['label'] for r in predictions], [r['probability'] for r in predictions], threshold)
    result = metadata | metrics | benchmark(trainer, loaders['development_validation']) | dict(
        initial_train_eval_loss=initial_loss, final_train_eval_loss=final_loss,
        first_epoch_loss=history[0]['loss'], last_epoch_loss=history[-1]['loss'],
        selected_epoch=selected_epoch, tune_ap=best, optimizer_steps=trainer.optimizer_steps,
        parameters=sum(p.numel() for p in model.parameters()), trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
        peak_gpu_allocated_bytes=peak, device=device, training_seconds=training_seconds,
        model_bytes=(run/'best.safetensors').stat().st_size, kind='balanced_tiny_pretrained_development_pilot')
    atomic_write_json(run/'metrics.json', result)
    if variant == 'edge_gated_astguard':
        gate_analysis(trainer, loaders['development_validation'], run)
        interventions = []
        for mode in ('row_mean', 'within_query_permutation', 'zero'):
            changed = []
            for batch in loaders['development_validation']:
                model.set_edge_intervention(mode, sample_ids=batch['sample_ids'])
                changed.extend(trainer.predict([batch]))
            model.clear_gate_intervention()
            atomic_write_json(run/f'predictions_{mode}.json', changed)
            interventions.append({'mode': mode, 'threshold_frozen': threshold,
                                  **evaluate_scores([r['label'] for r in changed], [r['probability'] for r in changed], threshold)})
        atomic_write_json(run/'interventions.json', interventions)
    del trainer, model, optimizer, scheduler
    gc.collect()
    if device == 'cuda':
        torch.cuda.empty_cache()
    return result


def overfit(root, base, groups, args, device):
    run = root/'edge_overfit'
    run.mkdir()
    selected = [row for label in (0, 1) for row in groups['train'] if row['label'] == label]
    selected = [row for label in (0, 1) for row in [x for x in selected if x['label'] == label][:4]]
    config = dataclasses.replace(base,
        model=dataclasses.replace(base.model, variant='edge_gated_astguard', gate_mode='edge', head_dropout=0.),
        training=dataclasses.replace(base.training, pretrained_lr=1e-4, weight_decay=0.,
                                     max_optimizer_steps=args.overfit_steps))
    atomic_write_text(run/'resolved_config.json', dump_config(config))
    set_seed(args.seed)
    atomic_write_json(run/'diagnostic_overrides.json', {'learning_rate': config.training.pretrained_lr,
        'weight_decay': config.training.weight_decay, 'scheduler': None, 'accumulation_steps': 1,
        'selection': 'stop at loss ratio <= .25 and accuracy >= .95, or the step limit',
        'max_optimizer_steps': args.overfit_steps, 'class_weights': {0: 1., 1: 1.}})
    model = create_model(config).to(device)
    # Diagnostic-only learning rate; not the controlled pilot recipe.
    optimizer = build_adamw(model, pretrained_lr=config.training.pretrained_lr,
                            new_multiplier=1., weight_decay=config.training.weight_decay)
    trainer = Trainer(model, optimizer, device=device)
    loader = DataLoader(selected, batch_size=args.batch_size, collate_fn=create_collator(config))
    initial = measured_loss(trainer, loader, {0: 1., 1: 1.})
    history = []
    while trainer.optimizer_steps < args.overfit_steps:
        log = trainer.train_epoch(loader, {0: 1., 1: 1.}, max_optimizer_steps=args.overfit_steps)
        loss = measured_loss(trainer, loader, {0: 1., 1: 1.})
        predictions = trainer.predict(loader)
        accuracy = sum((p['probability'] >= .5) == p['label'] for p in predictions)/len(predictions)
        history.append(dict(steps=trainer.optimizer_steps, eval_loss=loss, accuracy=accuracy, **log))
        append_jsonl(run/'history.jsonl', history[-1])
        print(f'overfit: steps={trainer.optimizer_steps} eval_loss={loss:.5f} accuracy={accuracy:.3f}', flush=True)
        if loss <= initial*.25 and accuracy >= .95:
            break
    passed = loss <= initial*.25 and accuracy >= .95
    save_model(model, str(run/'final.safetensors'))
    result = dict(status='passed' if passed else 'failed', initial_loss=initial, final_loss=loss,
                  accuracy=accuracy, steps=trainer.optimizer_steps, maximum_steps=args.overfit_steps,
                  required_loss_ratio=.25, required_accuracy=.95, seed=args.seed, device=device,
                  learning_rate=1e-4, weight_decay=0., sample_ids=[row['sample_id'] for row in selected],
                  checkpoint_sha256=sha256_file(run/'final.safetensors'), scientific_status='memorization_diagnostic_only')
    atomic_write_json(run/'result.json', result)
    atomic_write_json(run/'predictions.json', predictions)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='new directory only')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--max-length', type=int, default=64)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--overfit-steps', type=int, default=80)
    parser.add_argument('--include-capacity-control', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.epochs <= 5 or not 1 <= args.overfit_steps <= 150 or not 8 <= args.max_length <= 128:
        parser.error('this runner is limited to a small development pilot')
    if not 1 <= args.batch_size <= 8:
        parser.error('batch size must be between 1 and 8')
    torch.set_num_threads(2)
    root = Path(args.output) if args.output else Path('runs')/('edge-pilot-'+uuid.uuid4().hex[:12])
    root.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault('MPLCONFIGDIR', str((root/'matplotlib_cache').resolve()))
    atomic_write_json(root/'status.json', {'status': 'running', 'official_test_used': False})
    print(f'Pilot directory: {root}', flush=True)
    source = json.loads(Path('artifacts/environment/development_sources.json').read_text())
    groups, manifest = prepare(root, source, {'train': 32, 'tune': 16, 'cal': 16, 'development_validation': 32}, args.max_length)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    base = load_config('configs/models/astguard.yaml', allow_unresolved=True)
    base = dataclasses.replace(base, experiment_id='edge_development_pilot',
        dataset=dataclasses.replace(base.dataset, view='train_only_balanced_pilot', manifest_hash=manifest['hash']),
        preprocessing=dataclasses.replace(base.preprocessing, max_length=args.max_length,
            cache_hash=object_hash([row['preprocessing_hash'] for rows in groups.values() for row in rows])),
        model=dataclasses.replace(base.model, checkpoint=source['codebert_path'], revision=source['codebert_revision']),
        training=dataclasses.replace(base.training, seed=args.seed, epochs=args.epochs, min_epochs=args.epochs,
            microbatch_size=args.batch_size, gradient_accumulation=1, effective_batch_size=args.batch_size,
            precision='fp32', activation_checkpointing=False),
        provenance=dataclasses.replace(base.provenance, protocol_hash=object_hash({'pilot': vars(args), 'split': manifest['hash']})))
    environment = environment_snapshot(['torch', 'transformers', 'tree-sitter', 'tokenizers'])
    environment.update(device=device, cuda=torch.version.cuda, gpu=torch.cuda.get_device_name() if device == 'cuda' else None,
                       source_identity=source_identity(), codebert_revision=source['codebert_revision'], arguments=vars(args),
                       implementation_hashes={str(path): sha256_file(path) for directory in ('astguard', 'scripts')
                                              for path in sorted(Path(directory).rglob('*.py'))})
    atomic_write_json(root/'environment.json', environment)
    # Run the memorization gate before the controlled pilot; failed runs stay intact.
    overfit_result = overfit(root, base, groups, args, device)
    gc.collect()
    variants = VARIANTS + (['query_capacity_matched'] if args.include_capacity_control else [])
    results = [run_variant(root, variant, base, groups, args, device) for variant in variants]
    atomic_write_json(root/'pilot_results.json', results)
    with (root/'pilot_results.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    atomic_write_json(root/'status.json', {'status': 'complete', 'official_test_used': False,
        'scientific_status': 'balanced_train_only_short_pretrained_pilot_not_main_results',
        'overfit_status': overfit_result['status'], 'full_suite_launched': False})
    print(f'Completed bounded pilot: {root}', flush=True)


if __name__ == '__main__':
    main()
