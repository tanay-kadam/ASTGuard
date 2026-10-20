"""Verified private mirror of finished campaign; never deletes remote files."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import threading
import time

import paramiko

REPO=Path(__file__).resolve().parents[1]
DEST=REPO/'archive/ssh_campaign_20261020'
REMOTE='/tmp/astguard_seven_day_20261012'
KEY=REPO/'tmp/ssh_task/astguard_gpu_key'
LOCK=threading.Lock()
CONNECT_LOCK=threading.Lock()
STATE={'verified':{},'errors':{},'started':time.time()}

INVENTORY=r'''
import os,json,hashlib,sys
from pathlib import Path
root=Path('/tmp/astguard_seven_day_20261012')
assert root.resolve()==root and root.is_dir() and not root.is_symlink()
sys.path.insert(0,str(root))
from scripts.seven_day_finalize import evaluation_jobs,resolve_run
plan=json.loads((root/'artifacts/seven_day_20261012/plan.json').read_text())
assert len(plan['jobs'])==66
for job in plan['jobs']:
    state=json.loads((root/'artifacts/seven_day_20261012/jobs'/job['tag']/'status.json').read_text())
    assert state['status']=='complete'
for job in evaluation_jobs():
    state=json.loads((root/'artifacts/seven_day_20261012/external_evaluation'/job['tag']/'status.json').read_text())
    assert state['status']=='complete'
selected=set()
for job in plan['jobs']:
    state=json.loads((root/'artifacts/seven_day_20261012/jobs'/job['tag']/'status.json').read_text())
    run=Path(state['run_dir'])
    selected.add(str(run/('best.safetensors' if job['family']=='regvd' else 'checkpoints/best.safetensors')))
extra=[]
for job in evaluation_jobs():
    if job['origin']=='original':
        run=resolve_run(job)
        for p in run.rglob('*'):
            if p.is_file() and (p.name=='best.safetensors' or (p.suffix not in {'.pt','.pth','.safetensors','.bin'} and p.stat().st_size<100_000_000)):
                extra.append((p,'original_regvd/'+job['tag']+'/'+p.relative_to(run).as_posix()))
records=[];omitted=[];links=[]
def add(p,rel):
    before=p.stat();h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    after=p.stat();assert before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns
    records.append({'source':str(p),'relative':rel,'bytes':after.st_size,'sha256':h.hexdigest()})
for parent,dirs,files in os.walk(root,followlinks=False):
    dirs[:]=[d for d in dirs if d not in {'.git','.venv','__pycache__','.pytest_cache'}]
    for name in files:
        p=Path(parent)/name;rel=p.relative_to(root).as_posix()
        if p.is_symlink():links.append({'path':rel,'target':os.readlink(p)});continue
        reason=None
        if p.suffix in {'.pt','.pth','.safetensors','.bin'} and str(p) not in selected:reason='Unselected optimizer/last/smoke checkpoint; selected best is preserved.'
        if '/final_evidence_20261017/' in '/'+rel or name in {'final_evidence_20261017.tar.gz','synthetic_inputs_20261017.tar.gz'}:reason='Duplicate exported evidence already mirrored and verified locally on October17.'
        if reason:omitted.append({'path':rel,'bytes':p.stat().st_size,'reason':reason})
        else:add(p,'campaign/'+rel)
for p,rel in extra:add(p,rel)
assert all(any(r['source']==p for r in records) for p in selected)
report={'root':str(root),'files':records,'omitted':omitted,'symlinks':links,'selected_checkpoints':len(selected),'original_regvd_checkpoints':9,'bytes':sum(r['bytes'] for r in records),'created_unix':__import__('time').time()}
Path('/tmp/astguard_campaign_archive_inventory_20261020.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'files':len(records),'bytes':report['bytes'],'omitted_bytes':sum(r['bytes'] for r in omitted),'links':links}),flush=True)
'''

def connect():
    c=paramiko.SSHClient();c.load_system_host_keys();c.set_missing_host_key_policy(paramiko.RejectPolicy())
    c.connect('seeklab-01.ece.ncsu.edu',username='tkadam',key_filename=str(KEY),allow_agent=False,look_for_keys=False,timeout=20)
    c.get_transport().set_keepalive(20)
    return c

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def save():
    p=DEST/'transfer_state.json';p.write_text(json.dumps(STATE,indent=2)+'\n')

def main():
    policy=REPO/'artifacts/audits/ssh_storage_policy_20261020.json'
    if policy.exists():assert json.loads(policy.read_text()).get('local_large_backup_allowed',False),'Local large backup is disabled by the user storage preference.'
    DEST.mkdir(parents=True,exist_ok=True)
    manifest=DEST/'inventory.json'
    c=connect()
    if not manifest.exists():
        stdin,stdout,stderr=c.exec_command('python3 -',timeout=1200);stdin.write(INVENTORY);stdin.channel.shutdown_write()
        result=stdout.read().decode();err=stderr.read().decode();assert stdout.channel.recv_exit_status()==0,err
        print(result,flush=True)
        s=c.open_sftp();s.get('/tmp/astguard_campaign_archive_inventory_20261020.json',str(manifest));s.close()
    c.close()
    inventory=json.loads(manifest.read_text());records=inventory['files']
    print('Mirror bytes:',inventory['bytes'],'files:',len(records),flush=True)
    local=threading.local()
    def transfer(r):
        p=DEST/r['relative'];assert p.resolve().is_relative_to(DEST.resolve());p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256']:
            with LOCK:STATE['verified'][r['relative']]=r['bytes']
            return
        for attempt in range(4):
            try:
                if not getattr(local,'client',None) or not local.client.get_transport().is_active():
                    with CONNECT_LOCK:local.client=connect()
                    local.sftp=local.client.open_sftp();local.sftp.get_channel().settimeout(120)
                partial=p.with_name(p.name+'.partial')
                offset=partial.stat().st_size if partial.exists() else 0
                if offset>r['bytes']:raise RuntimeError('Oversized partial file')
                with local.sftp.open(r['source'],'rb') as src,partial.open('ab') as dst:
                    src.seek(offset)
                    src.prefetch(file_size=r['bytes'],max_concurrent_requests=64)
                    while True:
                        block=src.read(4*1024*1024)
                        if not block:break
                        dst.write(block)
                assert partial.stat().st_size==r['bytes'] and sha(partial)==r['sha256'],r['relative']
                partial.replace(p)
                with LOCK:STATE['verified'][r['relative']]=r['bytes']
                return
            except Exception as e:
                if getattr(local,'client',None):local.client.close();local.client=None
                if attempt==3:
                    with LOCK:STATE['errors'][r['relative']]=str(e)
                    raise
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
        pending={pool.submit(transfer,r) for r in sorted(records,key=lambda r:r['bytes'])}
        while pending:
            done,pending=concurrent.futures.wait(pending,timeout=30,return_when=concurrent.futures.FIRST_EXCEPTION)
            for f in done:f.result()
            with LOCK:
                STATE['verified_bytes']=sum(STATE['verified'].values());STATE['total_bytes']=inventory['bytes'];save()
                print(json.dumps({'verified_files':len(STATE['verified']),'verified_bytes':STATE['verified_bytes'],'total_bytes':inventory['bytes'],'elapsed_seconds':round(time.time()-STATE['started'])}),flush=True)
    assert len(STATE['verified'])==len(records) and not STATE['errors']
    STATE['status']='passed';save();print('ALL FILES VERIFIED; no remote files deleted by this script.',flush=True)

if __name__=='__main__':main()
