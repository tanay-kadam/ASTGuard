"""Detached, failure-isolated queues for the frozen strengthening matrix."""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astguard.utils.atomic_io import atomic_write_json
from astguard.config import load_config

ROOT=Path('artifacts/release_gates/strengthening_20261006')


def stamp():return datetime.now(timezone.utc).isoformat()


def wait_gpu(gpu):
    while True:
        value=subprocess.check_output(['nvidia-smi','--id='+str(gpu),'--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True).strip()
        if int(value)<1500:return
        time.sleep(60)


def command(argv,log,env):
    with Path(log).open('a') as stream:
        stream.write(json.dumps({'command':argv,'utc':stamp()})+'\n');stream.flush()
        result=subprocess.run(argv,stdout=stream,stderr=subprocess.STDOUT,env=env)
    if result.returncode:raise RuntimeError(f'command failed exit={result.returncode}; log={log}')


def run_job(job,gpu,smoke=False,maintenance_rerun_tag=None):
    if (ROOT/'maintenance_hold.json').exists():
        permitted=False
        authorization=ROOT/'fresh_rerun_authorization.json'
        if maintenance_rerun_tag is not None and authorization.exists():
            record=json.loads(authorization.read_text())
            permitted=(record.get('fresh_only') is True
                       and maintenance_rerun_tag in record.get('tags',[])
                       and job['tag'] in (maintenance_rerun_tag,maintenance_rerun_tag+'_fresh_preflight'))
        if not permitted:
            raise RuntimeError('user maintenance hold: new jobs are disabled')
    env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=str(gpu);env['PYTHONPATH']=str(Path.cwd());env['TOKENIZERS_PARALLELISM']='false'
    env['CUBLAS_WORKSPACE_CONFIG']=':4096:8';env['OMP_NUM_THREADS']='1';env['MKL_NUM_THREADS']='1'
    name=job['tag']+('_smoke' if smoke else '')
    target=ROOT/'jobs'/name;target.mkdir(parents=True,exist_ok=True)
    state=target/'status.json'
    if state.exists() and json.loads(state.read_text()).get('status')=='complete':return
    log=target/'run.log';atomic_write_json(state,{'status':'running','gpu':gpu,'job':job,'utc':stamp()})
    try:
        wait_gpu(gpu)
        data=Path('data/strengthening_20261006')/('smoke' if smoke else 'real')
        if job['family']=='synthetic':data=Path('data/strengthening_20261006/synthetic')
        if job['family']=='regvd':
            output=target/'run'
            if output.exists():
                output=target/f'run_attempt_{time.time_ns()}'
            argv=[sys.executable,'scripts/run_regvd_strengthening.py','--train',str(data/'regvd_train.jsonl'),
                '--tune',str(data/'regvd_tune.jsonl'),'--condition',job['condition'],'--seed',str(job['seed']),'--output',str(output)]
            if smoke:argv+=['--smoke']
            command(argv,log,env)
            complete=json.loads((output/'status.json').read_text());assert complete['status']=='complete'
            atomic_write_json(state,{'status':'complete','gpu':gpu,'run_dir':str(output),'utc':stamp(),'optimizer_steps':complete['optimizer_steps']})
            return
        config=job['config'].replace('.yaml','_smoke.yaml') if smoke else job['config']
        resolved=load_config(config)
        argv=[sys.executable,'-m','astguard.train','--config',config,'--features',str(data/'train.jsonl'),
             '--tune-features',str(data/'tune.jsonl'),'--seed',str(job['seed']),'--runs-root',str(target/'runs'),'--require-cuda']
        command(argv,log,env)
        candidates=list((target/'runs').glob('*/provenance.json'))
        if len(candidates)!=1:raise ValueError('ambiguous run identity; manual recovery required')
        run=candidates[0].parent;provenance=json.loads(candidates[0].read_text())
        assert provenance['hardware']['device']=='cuda'
        expected=2 if smoke else 1536 if job['family']=='synthetic' else 4424*resolved.training.epochs
        assert provenance['optimizer_steps']==expected,(provenance['optimizer_steps'],expected)
        role='audit' if job['family']=='synthetic' and not smoke else 'tune'
        argv=[sys.executable,'scripts/evaluate_strengthening_checkpoint.py','--run',str(run),'--features',str(data/f'{role}.jsonl'),
            '--role',role,'--output',str(target/'interventions.json')]
        if smoke:argv+=['--max-examples','16']
        command(argv,log,env)
        atomic_write_json(state,{'status':'complete','gpu':gpu,'run_dir':str(run),'optimizer_steps':expected,'utc':stamp()})
    except Exception as exc:
        atomic_write_json(state,{'status':'failed','gpu':gpu,'error':str(exc),'utc':stamp()});raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--gpu',type=int,required=True);p.add_argument('--partition',type=int,default=0)
    p.add_argument('--smoke',action='store_true');args=p.parse_args()
    document=json.loads((ROOT/'jobs.json').read_text());jobs=document['jobs']
    if args.smoke:
        selected=[];seen=set()
        for job in jobs:
            key=(job['family'],job['condition'])
            if key not in seen:selected.append(job);seen.add(key)
        for job in selected:run_job(job,args.gpu,True)
        atomic_write_json(ROOT/'smoke_gate.json',{'status':'passed','families_conditions':len(selected),'device':'cuda','utc':stamp()})
        return
    failed=0
    for i,job in enumerate(jobs):
        if (ROOT/'maintenance_hold.json').exists():
            print('Maintenance hold: stopping scheduling without starting another job',flush=True)
            return
        if i%2!=args.partition:continue
        if job['family']!='synthetic':
            while not Path('data/strengthening_20261006/real/manifest.json').exists():
                if (ROOT/'preparation_failed.json').exists():raise RuntimeError('real-data preparation failed; no full real runs launched')
                time.sleep(30)
        try:run_job(job,args.gpu)
        except Exception as exc:failed+=1;print(str(exc),flush=True)
    atomic_write_json(ROOT/f'worker_{args.partition}_completion.json',{'status':'failed' if failed else 'complete','failed_jobs':failed,'utc':stamp()})


if __name__=='__main__':main()
