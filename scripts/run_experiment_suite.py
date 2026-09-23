from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="protocol/experiment_manifest.jsonl")
    parser.add_argument("--stage")
    parser.add_argument("--host")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--features")
    parser.add_argument('--context',help='Resolved checkpoint and feature-registry JSON')
    parser.add_argument('--state-dir',default='artifacts/launcher')
    parser.add_argument('--max-jobs',type=int)
    args = parser.parse_args(argv)
    jobs = [json.loads(line) for line in Path(args.manifest).read_text(encoding="utf-8").splitlines() if line.strip()]
    if len({job["job_id"] for job in jobs}) != len(jobs):
        raise ValueError("manifest contains duplicate job IDs")
    from astguard.experiments import dependencies
    for job in jobs:
        computed=dependencies(job,jobs)
        if job.get("dependencies") != computed:
            raise ValueError(f"stale dependency ledger for {job['job_id']}; run refresh_manifest_dependencies.py")
    selected = [job for job in jobs if args.stage is None or job["stage"] == args.stage]
    summary = {"total_manifest_jobs":len(jobs),"selected_jobs":len(selected),"by_experiment":dict(Counter(job["experiment_id"] for job in selected)),
               "estimated_gpu_hours":sum(job["estimated_hours"] for job in selected)}
    print(json.dumps(summary, indent=2))
    if args.dry_run:
        return 0
    if not args.context:
        raise RuntimeError('execution requires --context with immutable sources and feature cohorts')
    from astguard.experiments import resolve_job
    from astguard.config import dump_config
    from astguard.utils.atomic_io import atomic_write_json,atomic_write_text,append_jsonl
    from astguard.utils.hashing import sha256_file
    from filelock import FileLock,Timeout
    from datetime import datetime,timezone
    context=json.loads(Path(args.context).read_text())
    state_dir=Path(args.state_dir);state_dir.mkdir(parents=True,exist_ok=True)
    completed=0
    for job in selected:
        state_path=state_dir/(job['job_id']+'.json')
        try:
            lock=FileLock(str(state_path)+'.lock',timeout=0)
            lock.acquire()
        except Timeout:continue
        try:
            state=json.loads(state_path.read_text()) if state_path.exists() else {'status':'planned'}
            if state['status']=='complete':continue
            if state['status']=='failed' and not args.resume:continue
            attempts=int(state.get('attempts',0))
            if attempts > int(job['max_retries']):
                outcome={'status':'omitted','reason':'retry budget exhausted','attempts':attempts,'job_id':job['job_id']}
                atomic_write_json(state_path,outcome);append_jsonl(state_dir/'events.jsonl',outcome);continue
            try:
                config,artifact=resolve_job(job,jobs,context,state_dir)
            except RuntimeError as exc:
                atomic_write_json(state_path,{'status':'blocked','reason':str(exc)})
                continue
            for phase in ['queued','running']:
                event={'job_id':job['job_id'],'status':phase,'utc':datetime.now(timezone.utc).isoformat(),'host':args.host}
                append_jsonl(state_dir/'events.jsonl',event);atomic_write_json(state_path,event)
            config_path=state_dir/(job['job_id']+'.resolved.yaml')
            atomic_write_text(config_path,dump_config(config))
            command=[sys.executable,'-m','astguard.train','--config',str(config_path),'--features',artifact['train'],
                     '--tune-features',artifact['tune'],'--runs-root',str(Path('runs')/job['job_id'])]
            checkpoint=state.get('resume_checkpoint')
            if args.resume and checkpoint:command+=['--resume',checkpoint]
            result=subprocess.run(command,text=True,capture_output=True)
            atomic_write_text(state_dir/(job['job_id']+'.stdout.log'),result.stdout)
            atomic_write_text(state_dir/(job['job_id']+'.stderr.log'),result.stderr)
            if result.returncode:
                candidates=sorted((Path('runs')/job['job_id']).glob('*/checkpoints/last_resume.pt'),
                                  key=lambda path:path.stat().st_mtime,reverse=True)
                outcome={'status':'failed','returncode':result.returncode,'job_id':job['job_id'],
                         'attempts':attempts+1,'resume_checkpoint':str(candidates[0]) if candidates else None,
                         'utc':datetime.now(timezone.utc).isoformat()}
            else:
                run_dir=result.stdout.strip().splitlines()[-1]
                outcome={'status':'complete','run_dir':run_dir,'job_id':job['job_id'],
                         'attempts':attempts+1,'utc':datetime.now(timezone.utc).isoformat(),
                         'checkpoint_sha256':sha256_file(Path(run_dir)/'checkpoints/best.safetensors')}
            atomic_write_json(state_path,outcome);append_jsonl(state_dir/'events.jsonl',outcome)
            completed+=1
            if args.max_jobs and completed>=args.max_jobs:break
        finally:
            lock.release()
    return 0


if __name__ == "__main__": raise SystemExit(main())
