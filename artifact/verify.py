"""Independently recompute the paper's metrics from the compact saved evidence."""
import argparse
import gzip
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from sklearn.metrics import average_precision_score, roc_auc_score

def read(p):
    opener=gzip.open if p.suffix=='.gz' else open
    with opener(p,'rt',encoding='utf-8-sig') as f:return json.load(f)
def rows(p):
    opener=gzip.open if p.suffix=='.gz' else open
    with opener(p,'rt',encoding='utf-8') as f:return [json.loads(line) for line in f if line.strip()]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def verify(root,checkpoint_dir=None):
    manifest=read(root/'manifest.json');errors=[];reports={};count=0;real_population=None;synthetic_tune=None;audit_population=None
    def check(ok,message):
        if not ok:errors.append(message)
    def close(a,b):return a is not None and b is not None and abs(a-b)<1e-12
    for name,record in manifest['package_files'].items():check((root/name).is_file() and sha(root/name)==record['sha256'],'package SHA256 '+name)
    for name,record in manifest['evidence'].items():
        with (gzip.open(root/name,'rb') if name.endswith('.gz') else (root/name).open('rb')) as f:
            h=hashlib.sha256()
            for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
        check(h.hexdigest()==record['original_sha256'],'uncompressed original SHA256 '+name)
    parts={role:rows(root/'inputs/synthetic'/(role+'.jsonl.gz')) for role in ['train','tune','audit']}
    for role,rr in parts.items():
        groups=defaultdict(list)
        for row in rr:groups[row['component_id']].append(row)
        check(len({r['sample_id'] for r in rr})==len(rr),'synthetic unique IDs '+role)
        check(len(rr)==(4096 if role=='train' else 1024) and sum(r['label'] for r in rr)==len(rr)//2,'synthetic counts '+role)
        check(all(len(pair)==2 and {r['label'] for r in pair}=={0,1} and pair[0]['input_ids']==pair[1]['input_ids'] for pair in groups.values()),'opposite-label identical sequences '+role)
        check(all(all((r['input_ids'][a]==r['input_ids'][b])==bool(r['label']) for a,b in r['ast_token_edges']) for r in rr),'synthetic target graph alignment '+role)
    for left,right in [('train','tune'),('train','audit'),('tune','audit')]:
        for field in ['sample_id','component_id']:
            check(not {r[field] for r in parts[left]}&{r[field] for r in parts[right]},'synthetic disjoint '+field+' '+left+'/'+right)
        check(not {tuple(r['input_ids']) for r in parts[left]}&{tuple(r['input_ids']) for r in parts[right]},'synthetic disjoint sequences '+left+'/'+right)
    expected_synthetic={role:{r['sample_id']:r['label'] for r in rr} for role,rr in parts.items()}
    check(len(manifest['jobs'])==42,'expected 42 unique jobs')
    for tag,record in manifest['jobs'].items():
        d=root/'evidence'/tag;external=record['family']=='regvd';pred=rows(d/'selected.jsonl.gz');selection=read(d/'selection.json')
        labels=[r['label'] for r in pred];scores=[r['logit' if external else 'probability'] for r in pred]
        check(all(math.isfinite(s) for s in scores),'nonfinite selected scores '+tag)
        ap=float(average_precision_score(labels,scores));check(close(ap,record['selected_tune_ap']),'selected AP '+tag)
        check(close(ap,selection['tune_ap' if external else 'best_value']),'selection metadata '+tag)
        pop={r['sample_id']:r['label'] for r in pred};check(len(pop)==len(pred),'selected duplicate IDs '+tag)
        if record['family']=='synthetic':
            if synthetic_tune is None:synthetic_tune=pop
            check(pop==synthetic_tune and len(pop)==1024 and sum(pop.values())==512,'synthetic tune population '+tag)
            check(pop==expected_synthetic['tune'],'synthetic tune inputs '+tag)
        else:
            if real_population is None:real_population=pop
            check(pop==real_population and len(pop)==10566 and sum(pop.values())==330,'real tune population '+tag)
        hist=rows(d/'history.jsonl.gz');check(close(max(r['tune_ap'] for r in hist),ap),'best history AP '+tag)
        if not external:check(rows(d/'epochs'/('epoch_'+str(selection['epoch'])+'.jsonl.gz'))==pred,'selected epoch '+tag)
        if external:
            metrics=read(d/'interventions.json');modes={m:rows(d/(m+'.jsonl.gz')) for m in metrics};normal=modes['native']
            check(read(d/'original_checksums.json')['best.safetensors']==manifest['assets'][record['checkpoint_asset']]['sha256'],'ReGVD checkpoint report hash '+tag)
        else:
            inter=read(d/'interventions.json.gz');metrics=inter['metrics'];normal=[{'sample_id':r['sample_id'],'label':r['label'],'logit':r['normal']} for r in inter['predictions']]
            modes={m:[{'sample_id':r['sample_id'],'label':r['label'],'logit':r[m]} for r in inter['predictions']] for m in metrics}
            check(inter['checkpoint_sha256']==manifest['assets'][record['checkpoint_asset']]['sha256'],'checkpoint-report hash '+tag)
        ii={}
        for mode,pp in modes.items():
            count+=1;population={r['sample_id']:r['label'] for r in pp}
            check(len(population)==len(pp),'intervention duplicate IDs '+tag+' '+mode)
            if record['family']=='synthetic':
                if audit_population is None:audit_population=population
                expected=audit_population;check(len(population)==1024 and sum(population.values())==512,'audit class counts '+tag)
                check(population==expected_synthetic['audit'],'synthetic audit inputs '+tag)
            else:expected=real_population
            check(population==expected,'intervention population '+tag+' '+mode)
            check([(r['sample_id'],r['label']) for r in pp]==[(r['sample_id'],r['label']) for r in normal],'paired row order '+tag+' '+mode)
            ll=[r['label'] for r in pp];ss=[r['logit'] for r in pp]
            check(all(math.isfinite(s) for s in ss),'finite logits '+tag+' '+mode)
            actual=float(average_precision_score(ll,ss));auc=float(roc_auc_score(ll,ss));delta=statistics.mean(abs(a['logit']-b['logit']) for a,b in zip(pp,normal))
            check(close(actual,metrics[mode]['ap']),'intervention AP '+tag+' '+mode)
            check(close(auc,metrics[mode]['roc_auc']),'intervention ROC-AUC '+tag+' '+mode)
            check(close(delta,metrics[mode]['mean_abs_logit_change']),'intervention logit difference '+tag+' '+mode)
            ii[mode]={'ap':actual,'roc_auc':auc,'mean_abs_logit_change':delta}
        if checkpoint_dir:
            cp=checkpoint_dir/(tag+'.safetensors');check(cp.is_file() and sha(cp)==manifest['assets'][record['checkpoint_asset']]['sha256'],'downloaded checkpoint hash '+tag)
        reports[tag]={'selected_tune_ap':ap,'interventions':ii}
    check(count==156,'expected 156 intervention conditions')
    paired={}
    for name,left,right in [('attention_authentic_minus_shuffled','real_attention_authentic','real_attention_shuffled'),('attention_authentic_minus_sequence','real_attention_authentic','real_attention_sequence'),('centered_minus_sequence','real_adapter_centered','real_adapter_sequence'),('regvd_native_minus_permuted','regvd_native','regvd_permuted'),('regvd_native_minus_self','regvd_native','regvd_self')]:
        ds=[reports[left+'_s'+str(s)]['selected_tune_ap']-reports[right+'_s'+str(s)]['selected_tune_ap'] for s in [42,123,456]]
        paired[name]={'deltas':ds,'mean':statistics.mean(ds),'sample_sd':statistics.stdev(ds),'passes_all_positive_and_mean_ge_0_02':all(d>0 for d in ds) and statistics.mean(ds)>=.02}
    rules={}
    for family in ['attention','centered']:
        for seed in [42,123,456]:
            a=reports[f'synthetic_{family}_authentic_s{seed}']['interventions'];sh=reports[f'synthetic_{family}_shuffled_s{seed}']['interventions'];seq=reports[f'synthetic_sequence_s{seed}']['interventions']
            rules[family+'_s'+str(seed)]={'authentic_ap_ge_0_90':a['normal']['ap']>=.9,'authentic_minus_sequence_ge_0_30':a['normal']['ap']-seq['normal']['ap']>=.3,
                'authentic_minus_shuffled_ge_0_30':a['normal']['ap']-sh['normal']['ap']>=.3,'normal_minus_empty_ge_0_30':a['normal']['ap']-a['empty']['ap']>=.3,'normal_minus_null_ge_0_20':a['normal']['ap']-a['null']['ap']>=.2}
    return {'passed':not errors,'errors':errors,'selected_jobs_checked':len(reports),'intervention_conditions_checked':count,
            'checkpoint_bytes_checked':checkpoint_dir is not None,'paired_comparisons':paired,'synthetic_success_rules':rules,'jobs':reports}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--checkpoints',type=Path);p.add_argument('--output',type=Path,default=Path('results/artifact_verification.json'));a=p.parse_args()
    result=verify(a.root,a.checkpoints);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','errors','selected_jobs_checked','intervention_conditions_checked','checkpoint_bytes_checked']},indent=2))
    raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
