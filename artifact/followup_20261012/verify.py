"""Verify anonymous saved scores, paired contrasts and optional bootstrap."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import t
from sklearn.metrics import average_precision_score,roc_auc_score

def read_csv(path):
    with gzip.open(path,'rt',encoding='utf-8',newline='') as f:
        return [{k:(int(v) if k in {'id','label','component'} else float(v)) for k,v in row.items()} for row in csv.DictReader(f)]

def near(a,b):
    assert np.isfinite(a) and np.isfinite(b) and abs(a-b)<1e-12,(a,b)

def verify(root,bootstrap=False):
    study=json.loads((root/'study.json').read_text());checks=json.loads((root/'checksums.json').read_text())
    for name,expected in checks.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
    population=read_csv(root/'predictions/external_population.csv.gz')
    ids=[r['id'] for r in population];labels=[r['label'] for r in population];components=[r['component'] for r in population]
    assert len(ids)==56571 and len(set(ids))==56571 and sum(labels)==4135 and len(set(components))==881
    external={};streams=0
    for name,record in study['external'].items():
        rows=read_csv(root/'predictions/external'/f'{name}.csv.gz')
        assert [r['id'] for r in rows]==ids and [r['label'] for r in rows]==labels
        for mode,claimed in record['metrics'].items():
            scores=np.array([r[mode] for r in rows]);assert np.isfinite(scores).all()
            near(float(average_precision_score(labels,scores)),claimed['ap'])
            near(float(roc_auc_score(labels,scores)),claimed['roc_auc'])
            change=np.abs(scores-np.array([r['normal'] for r in rows]))
            near(float(change.mean()),claimed['mean_abs_logit_change']);near(float(change.max()),claimed['max_abs_logit_change'])
            streams+=1
        external[(record['family'],record['condition'],record['seed'])]=[r['normal'] for r in rows]
    assert len(external)==45
    for name,record in study['jobs'].items():
        selected=read_csv(root/'predictions/selected'/f'{name}.csv.gz')
        expected=1024 if record['family']=='synthetic' else 10566
        assert len(selected)==len({r['id'] for r in selected})==expected
        near(float(average_precision_score([r['label'] for r in selected],[r['score'] for r in selected])),record['selected_tune_ap'])
        rows=read_csv(root/'predictions/development'/f'{name}.csv.gz');assert len(rows)==expected
        assert len({r['id'] for r in rows})==expected
        for mode,claimed in record['metrics'].items():
            scores=np.array([r[mode] for r in rows]);assert np.isfinite(scores).all()
            y=[r['label'] for r in rows]
            near(float(average_precision_score(y,scores)),claimed['ap']);near(float(roc_auc_score(y,scores)),claimed['roc_auc'])
            if 'mean_abs_logit_change' in claimed:
                near(float(np.abs(scores-np.array([r['normal'] for r in rows])).mean()),claimed['mean_abs_logit_change'])
            streams+=1
    assert len(study['jobs'])==66
    seeds=[42,123,456,789,2026]
    pairs=[('real','attention_authentic','attention_shuffled'),('real','attention_authentic','attention_sequence'),
           ('real','adapter_centered','adapter_sequence'),('regvd','native','permuted'),('regvd','native','self')]
    for family,a,b in pairs:
        key=a+'-minus-'+b;record=study['contrasts'][key]
        differences=np.array([average_precision_score(labels,external[(family,a,s)])-average_precision_score(labels,external[(family,b,s)]) for s in seeds])
        for x,y in zip(differences,record['paired_seed_differences']):near(float(x),y)
        near(float(differences.mean()),record['mean_difference'])
        sd=float(differences.std(ddof=1));near(sd,record['sample_sd'])
        half=t.ppf(.975,4)*sd/5**.5
        for x,y in zip([differences.mean()-half,differences.mean()+half],record['seed_t_interval_95']):near(float(x),y)
        if bootstrap:
            from analysis import paired_analysis
            fresh=paired_analysis(labels,{s:external[(family,a,s)] for s in seeds},{s:external[(family,b,s)] for s in seeds},components)
            for field in ['component_interval_95','hierarchical_interval_95']:
                for x,y in zip(fresh[field],record[field]):near(x,y)
            print('Bootstrap reproduced:',key,flush=True)
    report={'status':'passed','selected_prediction_streams':66,'external_evaluations':45,
        'intervention_score_streams':streams,'contrasts':5,'n_external':56571,
        'bootstrap_reproduced':bootstrap,'scope':'Saved-score reproduction; no training or inference rerun.'}
    (root/'verification_result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--bootstrap',action='store_true');a=p.parse_args();verify(a.root,a.bootstrap)
