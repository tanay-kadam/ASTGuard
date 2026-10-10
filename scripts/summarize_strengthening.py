"""Validate every completed job and recompute raw-prediction metrics."""
import json
import statistics
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astguard.evaluation.metrics import average_precision
from astguard.utils.atomic_io import atomic_write_json

ROOT=Path('artifacts/release_gates/strengthening_20261006')


def read(p):return json.loads(p.read_text())


def main():
    if (ROOT/'cuda_seed_repair_started.json').exists():
        while not (ROOT/'cuda_seed_repair_completion.json').exists():
            time.sleep(30)
    jobs=read(ROOT/'jobs.json')['jobs'];report={};failed=[];groups={};interventions_by_tag={}
    if len(jobs)!=42 or len({j['tag'] for j in jobs})!=42:raise ValueError('frozen matrix is incomplete or contains duplicate tags')
    for job in jobs:
        target=ROOT/'jobs'/job['tag'];status=read(target/'status.json') if (target/'status.json').exists() else {'status':'missing'}
        if status['status']!='complete':failed.append(job['tag']);report[job['tag']]=status;continue
        run=Path(status['run_dir'])
        if job['family']=='regvd':
            predictions=[json.loads(line) for line in (run/'selected_predictions.jsonl').read_text().splitlines()]
            selected=read(run/'selection.json');expected=selected['tune_ap'];key='logit'
        else:
            predictions=[json.loads(line) for line in (run/'selected_tune_predictions.jsonl').read_text().splitlines()]
            expected=read(run/'checkpoint_selection.json')['best_value'];key='probability'
        ap=average_precision([r['label'] for r in predictions],[r[key] for r in predictions]);assert abs(ap-expected)<1e-12
        if job['family']=='regvd':
            intervention=read(run/'interventions.json')
            for mode in intervention:
                pred=[json.loads(line) for line in (run/f'intervention_{mode}.jsonl').read_text().splitlines()]
                actual=average_precision([r['label'] for r in pred],[r['logit'] for r in pred])
                assert abs(actual-intervention[mode]['ap'])<1e-12
        else:
            intervention=read(target/'interventions.json')
            assert intervention['official_test_used'] is False
            for mode,value in intervention['metrics'].items():
                actual=average_precision([r['label'] for r in intervention['predictions']],[r[mode] for r in intervention['predictions']])
                assert abs(actual-value['ap'])<1e-12
        report[job['tag']]={'status':'complete','selected_tune_ap':ap,'run_dir':str(run),'interventions_verified':True}
        interventions_by_tag[job['tag']]=intervention
        group=job['family']+'_'+job['condition'];groups.setdefault(group,[]).append(ap)
    aggregates={group:{'n':len(values),'mean_ap':statistics.mean(values),'sample_sd_ap':statistics.stdev(values) if len(values)>1 else None} for group,values in groups.items()}
    rules={}
    if not failed:
        for seed in [42,123,456]:
            for name in ['attention','centered']:
                authentic=interventions_by_tag[f'synthetic_{name}_authentic_s{seed}']['metrics']
                shuffled=interventions_by_tag[f'synthetic_{name}_shuffled_s{seed}']['metrics']
                sequence=interventions_by_tag[f'synthetic_sequence_s{seed}']['metrics']
                rules[f'synthetic_{name}_s{seed}']={
                    'authentic_audit_ap_ge_0_90':authentic['normal']['ap']>=.9,
                    'authentic_minus_sequence_ge_0_30':authentic['normal']['ap']-sequence['normal']['ap']>=.3,
                    'authentic_minus_shuffled_ge_0_30':authentic['normal']['ap']-shuffled['normal']['ap']>=.3,
                    'normal_minus_empty_ge_0_30':authentic['normal']['ap']-authentic['empty']['ap']>=.3,
                    'normal_minus_null_ge_0_20':authentic['normal']['ap']-authentic['null']['ap']>=.2}
    paired={}
    if not failed:
        for name,left,right in [('attention_authentic_minus_shuffled','real_attention_authentic','real_attention_shuffled'),
                                ('attention_authentic_minus_sequence','real_attention_authentic','real_attention_sequence'),
                                ('centered_minus_sequence','real_adapter_centered','real_adapter_sequence'),
                                ('regvd_native_minus_permuted','regvd_native','regvd_permuted'),
                                ('regvd_native_minus_self','regvd_native','regvd_self')]:
            deltas=[report[f'{left}_s{s}']['selected_tune_ap']-report[f'{right}_s{s}']['selected_tune_ap'] for s in [42,123,456]]
            paired[name]={'seeds':[42,123,456],'deltas':deltas,'mean':statistics.mean(deltas),
                'sample_sd':statistics.stdev(deltas),'all_positive_and_mean_ge_0_02':all(d>0 for d in deltas) and statistics.mean(deltas)>=.02}
    atomic_write_json(ROOT/'summary.json',{'execution_complete':not failed,'failed_or_missing_jobs':failed,'jobs':report,
        'tune_summaries':aggregates,'official_test_used':False,'historical_results_submission_safe':False,
        'paired_comparisons':paired,'synthetic_audit_success_rules':rules,
        'hypothesis_outcomes_require_review':True})
    if failed:raise RuntimeError(f'{len(failed)} failed/missing jobs')
    print(json.dumps({'completed':len(report),'tune_summaries':aggregates},indent=2))


if __name__=='__main__':main()
