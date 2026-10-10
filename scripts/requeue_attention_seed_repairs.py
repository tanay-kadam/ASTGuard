"""Preserve invalid seed-protocol trials and replace only the six affected jobs."""
import json
import os
import sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astguard.utils.atomic_io import atomic_write_json
from scripts.queue_strengthening import ROOT,run_job


def main():
    gpu=int(sys.argv[1]);root=ROOT.resolve();jobs_root=(ROOT/'jobs').resolve()
    if jobs_root.parent!=root:raise ValueError('unexpected campaign path')
    marker=ROOT/'cuda_seed_repair_started.json'
    if marker.exists():raise FileExistsError('repair already started; preserve evidence and inspect status')
    jobs=json.loads((ROOT/'jobs.json').read_text())['jobs']
    selected=[j for j in jobs if j['family']=='synthetic' and j['condition'] in {'attention_authentic','attention_shuffled'}]
    assert len(selected)==6
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive=(ROOT/'quarantine'/('cuda_seed_bug_'+stamp)).resolve()
    if not archive.is_relative_to(root):raise ValueError('archive path escaped campaign')
    for job in selected:
        source=(jobs_root/job['tag']).resolve()
        if source.parent!=jobs_root:raise ValueError('job path escaped campaign')
        state=json.loads((source/'status.json').read_text())
        if state['status']!='complete':raise ValueError('only finished attention jobs may be quarantined')
    archive.mkdir(parents=True,exist_ok=False)
    atomic_write_json(marker,{'status':'running','jobs':[j['tag'] for j in selected],'gpu':gpu,'archive':str(archive),
        'reason':'constructor overwrote CUDA seed with 100010; CPU initialization and loader seeds still varied',
        'utc':datetime.now(timezone.utc).isoformat()})
    for job in selected:
        source=(jobs_root/job['tag']).resolve();destination=archive/job['tag']
        source.rename(destination)
        atomic_write_json(destination/'invalidation.json',{'valid_for_seed_protocol':False,'original_job_dir':str(source),
            'reason':'CUDA seed changed during model construction; replacement uses requested seed'})
    failed=[]
    for job in selected:
        try:run_job(job,gpu)
        except Exception as exc:failed.append({'tag':job['tag'],'error':str(exc)});print(str(exc),flush=True)
    atomic_write_json(ROOT/'cuda_seed_repair_completion.json',{'status':'failed' if failed else 'complete','failed':failed,
        'jobs':[j['tag'] for j in selected],'gpu':gpu,'utc':datetime.now(timezone.utc).isoformat()})
    if failed:raise RuntimeError('one or more attention replacements failed')


if __name__=='__main__':main()
