"""Read-only extraction for a preliminary result/claim review, not a weight rerun."""
import json
import statistics
from pathlib import Path
from sklearn.metrics import average_precision_score

root = Path('/home/tkadam/ASTGuard/artifacts/release_gates/strengthening_20261006')
summary = json.loads((root/'summary.json').read_text())
out = []
checks = []
for tag, record in summary['jobs'].items():
    run = Path('/home/tkadam/ASTGuard')/record['run_dir']
    row = dict(tag=tag, selected_tune_ap=record['selected_tune_ap'])
    prediction_path = run/('selected_predictions.jsonl' if tag.startswith('regvd_') else 'selected_tune_predictions.jsonl')
    predictions = [json.loads(line) for line in prediction_path.read_text().splitlines()]
    score = 'logit' if tag.startswith('regvd_') else 'probability'
    recomputed = float(average_precision_score([r['label'] for r in predictions], [r[score] for r in predictions]))
    assert abs(recomputed-record['selected_tune_ap']) < 1e-12, tag
    checks.append(tag)
    if tag.startswith('regvd_'):
        row['selection'] = json.loads((run/'selection.json').read_text())
        row['interventions'] = json.loads((run/'interventions.json').read_text())
    else:
        intervention = json.loads((root/'jobs'/tag/'interventions.json').read_text())
        row.update(role=intervention['role'], n=intervention['n'], variant=intervention['variant'],
                   metrics=intervention['metrics'], edge_change=intervention['mean_edge_change_fraction'])
        config = json.loads((run/'config.resolved.yaml').read_text())
        provenance = json.loads((run/'provenance.json').read_text())
        row.update(selection=json.loads((run/'checkpoint_selection.json').read_text()),
                   epochs=config['training']['epochs'], seed=config['training']['seed'],
                   model=config['model']['variant'], shuffle=config['model']['shuffle_training_graphs'],
                   optimizer_steps=provenance['optimizer_steps'], device=provenance['hardware']['device'])
        view = run/'dataset_views.json'
        if view.exists() and tag.startswith('synthetic_centered_shuffled'):
            row['dataset_views'] = json.loads(view.read_text())
    # Compact the output to avoid losing middle rows to tool truncation.
    if tag.startswith('regvd_native'):
        out.append(row)
    elif tag.startswith('real_') and 'sequence' not in tag and 'shuffled' not in tag:
        out.append(dict(tag=tag, selected_tune_ap=row['selected_tune_ap'], selected_epoch=row['selection']['epoch'],
            intervention_ap={name: value['ap'] for name, value in row['metrics'].items()},
            mean_abs_change={name: value['mean_abs_logit_change'] for name, value in row['metrics'].items()},
            edge_change=row['edge_change']))
    elif tag.startswith('synthetic_'):
        out.append(dict(tag=tag, audit_ap=row['metrics']['normal']['ap'],
            empty_ap=row['metrics']['empty']['ap'], null_ap=row['metrics']['null']['ap'],
            dataset_views=row.get('dataset_views')))
print(json.dumps({'selected_AP_independent_sklearn_checks': len(checks), 'details': out}, indent=2))
