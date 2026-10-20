"""SSH-side private GitHub archive. Credentials exist only in process memory."""
import base64
import concurrent.futures
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import threading
import time
import traceback

import requests

ROOT=Path('/tmp/astguard_seven_day_20261012')
STAGE=Path('/tmp/astguard_cloud_archive_20261020')
STATE=Path('/tmp/astguard_cloud_archive_status_20261020.json')
RECEIPT=Path('/tmp/astguard_private_release_receipt_20261020.json')
REPOSITORY='tanay-kadam/ASTGuard-campaign-archive-20261020'
TAG='campaign-preservation-20261020-v1'
LOCK=threading.Lock()
PROGRESS={}

def file_digest(f):
    h=hashlib.sha256()
    for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def state(phase,**kw):
    with LOCK:
        PROGRESS.update(phase=phase,updated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw)
        temp=STATE.with_suffix('.partial');temp.write_text(json.dumps(PROGRESS,indent=2)+'\n');temp.replace(STATE)
    print(phase,kw,flush=True)

def package():
    assert ROOT.resolve()==ROOT and ROOT.is_dir() and not ROOT.is_symlink()
    STAGE.mkdir(exist_ok=True)
    source=json.loads(Path('/tmp/astguard_campaign_archive_inventory_20261020.json').read_text())
    records=source['files']
    assert source['selected_checkpoints']==66
    assert sum(r['relative'].startswith('original_regvd/') and r['relative'].endswith('/best.safetensors') for r in records)==9
    shared=Path('/home/tkadam/ASTGuard/data/strengthening_20261006')
    for p in sorted(shared.rglob('*')):
        if p.is_file():
            with p.open('rb') as f:digest=file_digest(f)
            records.append({'source':str(p),'relative':'campaign/data/strengthening_20261006/'+p.relative_to(shared).as_posix(),
                'bytes':p.stat().st_size,'sha256':digest})
    assert shutil.disk_usage('/tmp').free>sum(r['bytes'] for r in records)+2*1024**3
    for r in records:r['mtime_ns']=Path(r['source']).stat().st_mtime_ns
    manifest={'schema':1,'files':records,'omitted':source['omitted'],'selected_campaign_checkpoints':66,
        'reused_regvd_checkpoints':9,'private':True,'storage':'Private GitHub Release; upstream terms remain applicable.',
        'restore':'Concatenate ordered .tar.gz.partNNN files into one .tar.gz, verify part hashes, then extract. Manifest paths are archive-relative; relocate absolute execution paths before reuse.'}
    (STAGE/'ARCHIVE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    state('packaging',archive_files=len(records),uncompressed_bytes=sum(r['bytes'] for r in records))
    proc=subprocess.Popen(['pigz','-1','-p','4'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    failures=[]
    class HashReader:
        def __init__(self,f):self.f=f;self.h=hashlib.sha256()
        def read(self,n=-1):
            b=self.f.read(n);self.h.update(b);return b
    def produce():
        try:
            with tarfile.open(fileobj=proc.stdin,mode='w|') as tar:
                content=(STAGE/'ARCHIVE_MANIFEST.json').read_bytes();info=tarfile.TarInfo('ARCHIVE_MANIFEST.json');info.size=len(content)
                tar.addfile(info,io.BytesIO(content))
                for r in records:
                    p=Path(r['source']);assert p.is_file() and not p.is_symlink() and p.stat().st_size==r['bytes']
                    with p.open('rb') as f:
                        reader=HashReader(f);info=tar.gettarinfo(str(p),arcname=r['relative'])
                        tar.addfile(info,reader);assert reader.h.hexdigest()==r['sha256'],r['relative']
            proc.stdin.close()
        except BaseException as exc:
            failures.append(str(exc));proc.stdin.close()
    thread=threading.Thread(target=produce);thread.start()
    parts=[];number=0;current=None;count=0;digest=None;path=None;limit=1_800_000_000
    while True:
        block=proc.stdout.read(4*1024*1024)
        if not block:break
        while block:
            if current is None:
                path=STAGE/f'campaign.tar.gz.part{number:03d}';current=path.open('wb');count=0;digest=hashlib.sha256()
            chunk=block[:limit-count];current.write(chunk);digest.update(chunk);count+=len(chunk);block=block[len(chunk):]
            if count==limit:
                current.close();parts.append({'name':path.name,'bytes':count,'sha256':digest.hexdigest()});number+=1;current=None
                state('packaging',parts_ready=len(parts),compressed_bytes=sum(p['bytes'] for p in parts))
    if current:
        current.close();parts.append({'name':path.name,'bytes':count,'sha256':digest.hexdigest()})
    thread.join();assert proc.wait()==0 and not failures,failures
    manifest['parts']=parts
    (STAGE/'ARCHIVE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (STAGE/'SHA256SUMS').write_text(''.join(p['sha256']+'  '+p['name']+'\n' for p in parts))
    (STAGE/'RESTORE.md').write_text('''# Private campaign preservation

This is a private backup of selected checkpoint results, inputs, source and logs.
It is not the anonymous conference supplement. Upstream licenses and access terms
remain applicable; private storage does not grant redistribution rights.

Download all campaign.tar.gz.partNNN files, ARCHIVE_MANIFEST.json and SHA256SUMS.
Verify each part SHA256, concatenate parts in numeric filename order, then extract
the resulting gzip tar archive into an empty directory. Verify every extracted
file against the manifest files array. The campaign/ directory restores the
isolated source/input/run tree; original_regvd/ holds nine reused checkpoints.
The linked shared training inputs are materialized inside campaign/data/.
Absolute execution paths and caches must be relocated/restored before rerunning.
Selected weights are preserved; last/optimizer/smoke weights and caches are omitted.
Their omission prevents claiming resumability of every interrupted optimizer state.
''')
    return manifest

def upload(token):
    base='https://api.github.com/repos/'+REPOSITORY
    headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    def call(method,url,**kw):
        r=requests.request(method,url,headers=headers,timeout=1800,**kw)
        if r.status_code>=400:raise RuntimeError('GitHub HTTP '+str(r.status_code)+' '+url.split('?')[0])
        return r.json() if r.content else None
    repository=call('GET',base);assert repository['private'] is True
    manifest=package()
    releases=call('GET',base+'/releases?per_page=100')
    existing=[r for r in releases if r['tag_name']==TAG]
    release=existing[0] if existing else call('POST',base+'/releases',json={'tag_name':TAG,'target_commitish':repository['default_branch'],
        'name':'Verified private campaign preservation — 2026-10-20','draft':True,
        'body':'Private preservation of 66 selected campaign checkpoints, nine reused ReGVD checkpoints, inputs, source, predictions and provenance. Not a public redistribution license or independent retraining claim.'})
    url=release['upload_url'].split('{')[0]
    assets={a['name']:a for a in call('GET',base+'/releases/'+str(release['id'])+'/assets?per_page=100')}
    files=[STAGE/p['name'] for p in manifest['parts']]+[STAGE/n for n in ['ARCHIVE_MANIFEST.json','SHA256SUMS','RESTORE.md']]
    uploaded=[]
    def put(path):
        with path.open('rb') as f:digest=file_digest(f)
        old=assets.get(path.name)
        if old:
            assert old['size']==path.stat().st_size and old.get('digest')=='sha256:'+digest,'Unexpected existing asset: '+path.name
            result=old
        else:
            for attempt in range(4):
                try:
                    with path.open('rb') as f:
                        r=requests.post(url,params={'name':path.name},data=f,
                            headers={**headers,'Content-Type':'application/octet-stream','Content-Length':str(path.stat().st_size)},timeout=1800)
                    if r.status_code!=201:raise RuntimeError('Asset upload HTTP '+str(r.status_code))
                    result=r.json();break
                except Exception:
                    if attempt==3:raise
                    time.sleep(5*(attempt+1))
            assert result['size']==path.stat().st_size and result.get('digest')=='sha256:'+digest,path.name
        # Read back the actual private release asset without writing it to disk.
        h=hashlib.sha256();size=0
        with requests.get(base+'/releases/assets/'+str(result['id']),
                headers={**headers,'Accept':'application/octet-stream'},stream=True,timeout=1800) as r:
            assert r.status_code==200 and r.headers.get('Content-Type','').split(';')[0]!='application/json',path.name
            for chunk in r.iter_content(4*1024*1024):h.update(chunk);size+=len(chunk)
        assert size==path.stat().st_size and h.hexdigest()==digest,path.name
        record={'name':path.name,'bytes':size,'sha256':digest,'asset_id':result['id'],'readback_verified':True}
        with LOCK:uploaded.append(record)
        state('uploading_and_readback_verifying',verified_assets=len(uploaded),total_assets=len(files))
        return record
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(put,files))
    assert len(uploaded)==len(files) and all(x['readback_verified'] for x in uploaded)
    call('PATCH',base+'/releases/'+str(release['id']),json={'draft':False})
    receipt={'status':'cloud_verified','repository':REPOSITORY,'private':True,'tag':TAG,
        'url':release['html_url'],'assets':sorted(uploaded,key=lambda r:r['name']),
        'archive_files':len(manifest['files']),'selected_campaign_checkpoints':66,'reused_regvd_checkpoints':9,
        'large_files_saved_on_pc':False,'remote_campaign_deleted':False}
    RECEIPT.write_text(json.dumps(receipt,indent=2)+'\n')
    state('cloud_verified_preparing_cleanup',release_url=release['html_url'])
    # Destructive step is scoped to the two literal scratch directories only.
    assert ROOT.resolve()==ROOT and str(ROOT)=='/tmp/astguard_seven_day_20261012' and not ROOT.is_symlink()
    assert STAGE.resolve()==STAGE and str(STAGE)=='/tmp/astguard_cloud_archive_20261020' and not STAGE.is_symlink()
    for r in manifest['files']:
        p=Path(r['source']);assert p.stat().st_size==r['bytes'] and p.stat().st_mtime_ns==r['mtime_ns'],'Source changed after packaging: '+str(p)
    known={r['source'] for r in manifest['files']}|{str(ROOT/r['path']) for r in manifest['omitted']}
    for parent,dirs,files in os.walk(ROOT,followlinks=False):
        dirs[:]=[d for d in dirs if d not in {'.git','.venv','__pycache__','.pytest_cache'}]
        for name in dirs:
            p=Path(parent)/name
            if p.is_symlink():assert p==ROOT/'data/strengthening_20261006'
        for name in files:assert str(Path(parent)/name) in known,'Unexpected file since inventory'
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():continue
        try:
            if entry.stat().st_uid!=os.getuid():continue
            cmd=(entry/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if int(entry.name)!=os.getpid():
            assert not any(s in cmd for s in ['scripts/seven_day_campaign.py','scripts/seven_day_finalize.py','scripts/seven_day_evaluate_external.py','scripts/seven_day_holdout.py']),cmd
    assert Path('/home/tkadam/ASTGuard').is_dir()
    shutil.rmtree(ROOT);assert not ROOT.exists()
    receipt.update(status='complete',remote_campaign_deleted=True,original_remote_project_preserved=True)
    RECEIPT.write_text(json.dumps(receipt,indent=2)+'\n')
    content={'message':'Record verified private campaign preservation and cleanup','content':base64.b64encode(RECEIPT.read_bytes()).decode()}
    call('PUT',base+'/contents/VERIFIED_BACKUP_RECEIPT.json',json=content)
    shutil.rmtree(STAGE);assert not STAGE.exists()
    state('complete',release_url=release['html_url'],verified_assets=len(uploaded),remote_campaign_deleted=True,staging_removed=True)

def main():
    payload=json.load(sys.stdin);token=payload['token'];assert token
    if payload.get('detach'):
        pid=os.fork()
        if pid:
            print(json.dumps({'pid':pid,'status':'started','state_file':str(STATE)}),flush=True);return
        os.setsid()
        log=os.open('/tmp/astguard_cloud_archive_20261020.log',os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        os.dup2(log,1);os.dup2(log,2);dev=os.open('/dev/null',os.O_RDONLY);os.dup2(dev,0)
    try:upload(token)
    except BaseException:
        state('failed_remote_preserved_unless_receipt_says_complete',error=traceback.format_exc())
        raise

if __name__=='__main__':main()
