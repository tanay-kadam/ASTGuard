"""Read-only scientific evidence audit; writes a new audit report, never training outputs."""
import collections
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
ARCHIVE=ROOT/'archive/invalid_results_20261007'
from sklearn.metrics import average_precision_score,roc_auc_score
from scipy.stats import t
from astguard.utils.hashing import object_hash
from astguard.utils.atomic_io import atomic_write_json


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def lines(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x]
def historical(relative):
    archived=ARCHIVE/relative
    return archived if archived.exists() else ROOT/relative


def main():
    original=read(ROOT/'artifacts/audits/P_clean.json');old=read(historical('artifacts/audits/P_clean_stage0.json'))
    corrected=read(ROOT/'artifacts/release_gates/strengthening_20261006/corrected_manifest.json')
    orig_roles=dict(zip(original['ordered_sample_ids'],original['roles']))
    orig_comps=dict(zip(original['ordered_sample_ids'],original['component_ids']))
    old_roles=dict(zip(old['ordered_sample_ids'],old['roles']))
    old_comps=dict(zip(old['ordered_sample_ids'],old['component_ids']))
    transitions=collections.Counter((orig_roles[sid],role) for sid,role in old_roles.items() if orig_roles[sid]!=role)
    true_component_roles=collections.defaultdict(set)
    for sid,role in old_roles.items():true_component_roles[orig_comps[sid]].add(role)
    report={'scope':'paper-facing source, metadata, raw predictions, diagnostics, and active campaign implementation',
            'old_split':{'lengths':{k:len(old[k]) for k in ['ordered_sample_ids','roles','component_ids','original_splits']},
            'role_mismatches':sum(transitions.values()),'component_id_mismatches':sum(orig_comps[sid]!=comp for sid,comp in old_comps.items()),
            'transitions':{f'{a}->{b}':n for (a,b),n in transitions.items()},
            'true_components_cross_train_tune':sum({'train','tune'}<=roles for roles in true_component_roles.values()),
            'manifest_identifier_matches_contents':object_hash(old|{'file_hash':''})==old['file_hash']},
            'corrected_split':{'aligned':len({len(corrected[k]) for k in ['ordered_sample_ids','roles','component_ids','original_splits']})==1,
            'identifier_valid':object_hash(corrected|{'file_hash':''})==corrected['file_hash'],
            'roles_preserved':all(orig_roles[sid]==role for sid,role in zip(corrected['ordered_sample_ids'],corrected['roles'])),
            'components_preserved':all(orig_comps[sid]==comp for sid,comp in zip(corrected['ordered_sample_ids'],corrected['component_ids']))},
            'runs':[],'interventions':[],'diagnostics':[],'omitted_runs_without_raw_predictions':[],
            'numerical_errors':[],'normalization':{}}
    expected_old_tune={sid for sid,role in old_roles.items() if role=='tune'}
    run_directories=list((ROOT/'runs').iterdir())
    if (ARCHIVE/'runs').exists():run_directories+=list((ARCHIVE/'runs').iterdir())
    for run in sorted(run_directories):
        if not run.is_dir() or not (run/'checkpoint_selection.json').exists():continue
        if not (run/'selected_tune_predictions.jsonl').exists():
            report['omitted_runs_without_raw_predictions'].append(run.name);continue
        pred=lines(run/'selected_tune_predictions.jsonl');sel=read(run/'checkpoint_selection.json');prov=read(run/'provenance.json')
        ids=[r['sample_id'] for r in pred];labels=[r['label'] for r in pred]
        prob=[r.get('probability',r['logit']) for r in pred];logits=[r['logit'] for r in pred]
        ap=float(average_precision_score(labels,prob));logit_ap=float(average_precision_score(labels,logits))
        item={'run':run.name,'n':len(pred),'positive':sum(labels),'seed':prov['seed'],
              'selected_epoch':sel['epoch'],'selected_ap':sel['best_value'],'sklearn_ap':ap,
              'sklearn_roc_auc':float(roc_auc_score(labels,prob)),'raw_logit_ap':logit_ap,
              'probability_minus_logit_ap':ap-logit_ap,'unique_ids':len(ids)==len(set(ids)),
              'all_finite':all(math.isfinite(x) for x in logits+prob),'optimizer_steps':prov['optimizer_steps']}
        if abs(sel['best_value']-ap)>1e-12:report['numerical_errors'].append({'run':run.name,'type':'selected_AP_mismatch'})
        if prov['split_hash']==old['file_hash']:
            item['matches_historical_executed_tune_ids']=set(ids)==expected_old_tune
            item['original_role_composition']=dict(collections.Counter(orig_roles[sid] for sid in ids))
            item['split_valid_for_intended_claim']=False
        epoch=run/'validation_predictions'/f"epoch_{sel['epoch']}.jsonl"
        item['selected_predictions_equal_selected_epoch']=lines(epoch)==pred if epoch.exists() else None
        history=lines(run/'train_log.jsonl')
        item['selected_is_best_recorded_AP']=abs(max(r['tune_ap'] for r in history)-sel['best_value'])<1e-12
        item['history_epoch_count']=len(history)
        report['runs'].append(item)
    roots=[historical('artifacts/audits/interventions'),ROOT/'artifacts/release_gates/positive_control_v1_20261006/interventions']
    for directory in roots:
        for path in sorted(directory.glob('*.json')):
            document=read(path)
            if 'predictions' not in document:continue
            pred=document['predictions'];labels=[r['label'] for r in pred];computed={};mismatch=[]
            for key in pred[0]:
                if key.endswith('_logit'):
                    name=key[:-6]+'_ap';ap=float(average_precision_score(labels,[r[key] for r in pred]));computed[name]=ap
                    if abs(ap-document['metrics'][name])>1e-12:mismatch.append(name)
            ids=[r['sample_id'] for r in pred]
            report['interventions'].append({'path':str(path.relative_to(ROOT)),'n':len(pred),'positive':sum(labels),
                'unique_ids':len(ids)==len(set(ids)),'sklearn_metrics':computed,'mismatches':mismatch,
                'original_role_composition':dict(collections.Counter(orig_roles[sid] for sid in ids)) if set(ids)<=set(orig_roles) else None})
            report['numerical_errors'].extend({'path':str(path),'type':name} for name in mismatch)
    for path in sorted(historical('artifacts/audits/diagnostics').glob('seedq_pB_*.json')):
        d=read(path);batches=d['empty_graph_sensitivity'];n=sum(r['n'] for r in batches)
        weighted=sum(r['n']*r['mean_abs_logit_delta'] for r in batches)/n
        report['diagnostics'].append({'file':path.name,'n':n,'positive':d['n_positive'],
            'prevalence':d['n_positive']/n,'fraction_of_tune':n/10566,
            'mean_abs_logit_change_example_weighted':weighted,
            'mean_abs_logit_change_batch_mean':statistics.mean(r['mean_abs_logit_delta'] for r in batches),
            'spearman_is_mean_of_batch_correlations':True,'gate_stats_include_padding_and_special_queries':True})
    # Independent upstream train/valid label/source/ID comparison, without opening raw test data.
    upstream={}
    for split in ['train','valid']:
        with (ROOT/f'data/raw/primevul/original/primevul_{split}.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                row=json.loads(line);sid=f"primevul:original:{row['idx']}"
                upstream[sid]=(row['target'],hashlib.sha256(row['func'].encode()).hexdigest(),split)
    checked=0;mismatch=0;lexical_role_sets=collections.defaultdict(set);missing_lexical=0
    corrected_roles=dict(zip(corrected['ordered_sample_ids'],corrected['roles']))
    with (ROOT/'data/interim/primevul/records.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line);sid=row['sample_id']
            if sid in upstream:
                checked+=1
                mismatch+=int((row['label'],row['raw_sha256'],row['original_split'])!=upstream[sid])
            role=corrected_roles.get(sid)
            if role in {'train','tune'}:
                if row['lexical_sha256']:lexical_role_sets[row['lexical_sha256']].add(role)
                else:missing_lexical+=1
    report['normalization']={'upstream_train_valid_records_checked':checked,'label_source_split_mismatches':mismatch,
                            'corrected_records_without_persisted_lexical_hash':missing_lexical,
                            'corrected_exact_lexical_hash_cross_train_tune':None if missing_lexical else sum(len(v)>1 for v in lexical_role_sets.values())}
    report['paired_interval_crosscheck']={}
    for name,values in [('default_auth_minus_shuffle',[.0787660086,.0146200272,-.1421897376]),
                        ('strong_auth_minus_shuffle',[.0968508779,-.0805133677,-.0221761260]),
                        ('centered_minus_sequence',[-.0114673517,-.0891691531,.0168280893])]:
        mean=statistics.mean(values);sd=statistics.stdev(values);half=float(t.ppf(.975,2))*sd/math.sqrt(3)
        report['paired_interval_crosscheck'][name]={'mean':mean,'sample_sd':sd,'95pct_t_interval':[mean-half,mean+half]}
    report['numeric_recomputation_passed']=not report['numerical_errors']
    report['paper_submission_safe']=False
    atomic_write_json(ROOT/'artifacts/audits/complete_pipeline_audit_20261006.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['runs','interventions','diagnostics']},indent=2))
    print('raw_prediction_runs',len(report['runs']),'intervention_reports',len(report['interventions']))


if __name__=='__main__':main()
