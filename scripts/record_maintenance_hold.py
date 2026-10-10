"""Preserve interrupted job identity and checkpoint locations; do not resume work."""
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path('artifacts/release_gates/strengthening_20261006')
TAGS=['real_attention_sequence_s456','real_attention_authentic_s42']

def write(path,value):
    temporary=path.with_suffix(path.suffix+'.partial')
    temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)

def main():
    records=[]
    for tag in TAGS:
        job=ROOT/'jobs'/tag
        runs=list((job/'runs').glob('*/config.resolved.yaml'))
        if len(runs)!=1:raise ValueError(f'ambiguous run for {tag}')
        run=runs[0].parent;checkpoint=run/'checkpoints/last_resume.pt'
        if not checkpoint.is_file() or checkpoint.stat().st_size==0:raise ValueError(f'missing checkpoint: {tag}')
        history=[json.loads(line) for line in (run/'train_log.jsonl').read_text().splitlines()]
        last=history[-1]
        old=json.loads((run/'status.json').read_text())
        write(run/'status.json',old|{'status':'interrupted','reason':'user-requested maintenance shutdown',
            'last_completed_epoch':last['epoch'],'last_completed_optimizer_steps':last['optimizer_steps']})
        record={'tag':tag,'status':'interrupted','run_dir':str(run),'resume_checkpoint':str(checkpoint),
            'last_completed_epoch':last['epoch'],'last_completed_optimizer_steps':last['optimizer_steps'],
            'checkpoint_bytes':checkpoint.stat().st_size,'reason':'maintenance; not a completed or failed scientific result'}
        write(job/'status.json',record);records.append(record)
    hold={'status':'maintenance_hold','new_jobs_allowed':False,'utc':datetime.now(timezone.utc).isoformat(),
          'queue_pids_held':[206248,206250],'interrupted_jobs':records,'automatic_resume_allowed':False}
    write(ROOT/'maintenance_hold.json',hold)
    print(json.dumps(hold,indent=2))

if __name__=='__main__':main()
