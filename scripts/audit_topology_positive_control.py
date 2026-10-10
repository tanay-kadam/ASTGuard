"""Recompute downloaded positive-control evidence; no training or metric overrides."""
import hashlib
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

from sklearn.metrics import average_precision_score, roc_auc_score
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    summary = read(ROOT / 'artifacts/audits/topology_positive_control_v1_summary.json')
    remote_hashes = {}
    remote_hash_path = ROOT / 'artifacts/audits/topology_positive_control_remote_checkpoint_sha256.txt'
    if remote_hash_path.exists():
        for line in remote_hash_path.read_text().splitlines():
            value, relative = line.split(maxsplit=1)
            remote_hashes[relative] = value
    split_sequences = []
    dataset_labels = {}
    for role, count in [('train', 4096), ('tune', 1024)]:
        data = rows(ROOT / f'data/positive_control/v1/{role}.jsonl')
        if role == 'tune':
            dataset_labels = {r['sample_id']: r['label'] for r in data}
        assert len(data) == count
        sequences = set()
        for a, b in zip(data[::2], data[1::2]):
            assert a['label'] == 0 and b['label'] == 1
            for field in ['input_ids', 'attention_mask', 'special_tokens_mask', 'component_id']:
                assert a[field] == b[field]
            seq = tuple(a['input_ids'])
            assert seq not in sequences
            sequences.add(seq)
            for row in [a, b]:
                assert row['role'] == role and not row['dfg_token_edges']
                edges = row['ast_token_edges']
                assert Counter(x for x, y in edges) == Counter(range(1, 25))
                assert Counter(y for x, y in edges) == Counter(range(1, 25))
                assert all((row['input_ids'][x] == row['input_ids'][y]) == bool(row['label']) for x, y in edges)
                successor = dict(edges)
                unseen = set(range(1, 25)); lengths = []
                while unseen:
                    start = next(iter(unseen)); node = start; length = 0
                    while node in unseen:
                        unseen.remove(node); length += 1; node = successor[node]
                    assert node == start
                    lengths.append(length)
                assert sorted(lengths) == [6, 6, 6, 6]
        split_sequences.append(sequences)
    assert not split_sequences[0] & split_sequences[1]
    output = {'audit_scope': 'saved_predictions_configs_provenance_and_dataset', 'checkpoint_binary_audit_skipped': '--metadata-only' in sys.argv, 'dataset_checks_passed': True, 'runs': {}, 'interventions': {}, 'warnings': [
        'Tune split used for checkpoint selection and reporting; no independent synthetic test split.',
        'Three seeds; sample SD is descriptive, not a confidence interval.',
        'CuBLAS deterministic-workspace warnings recorded in training logs.',
        'Synthetic AST-channel edges are not parsed program ASTs; DFG is empty.',
    ]}
    for condition, seeds in summary['runs'].items():
        for seed, record in seeds.items():
            run = ROOT / record['run_dir']; provenance = read(run / 'provenance.json')
            assert read(run / 'status.json')['status'] == 'complete'
            assert provenance['optimizer_steps'] == 512
            assert provenance['hardware']['device'] == 'cuda'
            assert provenance['train_count'] == 4096 and provenance['tune_count'] == 1024
            config = yaml.safe_load((run / 'config.resolved.yaml').read_text())
            assert config['training']['seed'] == int(seed)
            assert config['training']['epochs'] == 4
            assert config['training']['effective_batch_size'] == 32
            assert float(config['training']['pretrained_lr']) == 0.00002
            assert config['training']['new_module_lr_multiplier'] == 50
            assert config['model']['variant'] == ('sequence_only' if condition == 'sequence' else 'graph_adapter')
            assert config['model']['shuffle_training_graphs'] == (condition == 'shuffled')
            assert config['model']['revision'] == '3b0952feddeffad0063f274080e3c23d75e7eb39'
            for role in ['train', 'tune']:
                assert provenance[f'{role}_features_sha256'] == digest(ROOT / f'data/positive_control/v1/{role}.jsonl')
            checksums = read(run / 'artifact_checksums.json'); missing = []
            for relative, expected in checksums.items():
                file = run / relative
                if relative.startswith('checkpoints/') and remote_hashes:
                    assert remote_hashes[f"{record['run_dir']}/{relative}"] == expected
                if '--metadata-only' in sys.argv and relative.startswith('checkpoints/'):
                    missing.append(relative)
                    continue
                if file.is_file():
                    assert digest(file) == expected, str(file)
                else:
                    missing.append(relative)
            pred = rows(run / 'selected_tune_predictions.jsonl')
            assert len(pred) == 1024 and len({r['sample_id'] for r in pred}) == 1024
            assert {r['sample_id']: r['label'] for r in pred} == dataset_labels
            ap = float(average_precision_score([r['label'] for r in pred], [r['probability'] for r in pred]))
            assert abs(ap - record['ap']) < 1e-12
            selected = rows(run / f"validation_predictions/epoch_{record['selected_epoch']}.jsonl")
            assert selected == pred
            history = rows(run / 'train_log.jsonl')
            assert len(history) == 4 and history[-1]['optimizer_steps'] == 512
            assert abs(max(r['tune_ap'] for r in history) - record['ap']) < 1e-12
            if condition == 'shuffled':
                from astguard.data.graph_donors import length_matched_donors
                _, donor_stats = length_matched_donors([26] * 4096, int(seed))
                assert donor_stats == read(run / 'graph_donors.json')
            output['runs'][f'{condition}_{seed}'] = dict(ap=ap, roc_auc=float(roc_auc_score([r['label'] for r in pred], [r['probability'] for r in pred])), run_dir=record['run_dir'], optimizer_steps=512, elapsed_training_seconds=provenance['elapsed_training_seconds'], unchecked_artifacts=missing)
    for seed in summary['seeds']:
        report = read(ROOT / f'artifacts/release_gates/positive_control_v1_20261006/interventions/pc_authentic_s{seed}.json')
        assert report['official_test_used'] is False and report['role'] == 'tune'
        run = ROOT / summary['runs']['authentic'][str(seed)]['run_dir']
        assert report['checkpoint_sha256'] == read(run / 'artifact_checksums.json')['checkpoints/best.safetensors']
        assert report['features_sha256'] == digest(ROOT / 'data/positive_control/v1/tune.jsonl')
        pred = report['predictions']; assert len(pred) == 1024
        metrics = {}
        for name in ['normal', 'sequence', 'uncentered', 'null_as_real', 'empty_real']:
            ap = float(average_precision_score([r['label'] for r in pred], [r[f'{name}_logit'] for r in pred]))
            assert abs(ap - report['metrics'][f'{name}_ap']) < 1e-12
            metrics[f'{name}_ap'] = ap
        correction = statistics.mean(abs(r['structural_correction']) for r in pred)
        assert abs(correction - report['metrics']['mean_abs_structural_correction']) < 1e-10
        output['interventions'][str(seed)] = metrics | {'mean_abs_structural_correction': correction}
        assert metrics['normal_ap'] >= 0.9
        assert output['runs'][f'authentic_{seed}']['ap'] - output['runs'][f'sequence_{seed}']['ap'] >= 0.3
        assert output['runs'][f'authentic_{seed}']['ap'] - output['runs'][f'shuffled_{seed}']['ap'] >= 0.3
        assert metrics['normal_ap'] - metrics['empty_real_ap'] >= 0.3
        assert metrics['normal_ap'] - metrics['null_as_real_ap'] >= 0.2
    for condition, aggregate in summary['summary'].items():
        values = [output['runs'][f'{condition}_{seed}']['ap'] for seed in summary['seeds']]
        assert abs(statistics.mean(values) - aggregate['mean_ap']) < 1e-12
        assert abs(statistics.stdev(values) - aggregate['sample_sd_ap']) < 1e-12
    output['audit_passed'] = True
    output['remote_checkpoint_hashes_verified'] = bool(remote_hashes)
    target = ROOT / 'artifacts/audits/topology_positive_control_local_audit.json'
    target.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
