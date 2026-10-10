"""Upload SHA256-verified assets to an existing draft GitHub release.

Checkpoint imports may finish while this runs. Existing remote assets are only
accepted when GitHub's SHA256 digest and size match the frozen manifest. This
script never creates/publishes a release, changes tags, or overwrites assets.
"""
import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gh',default=r'C:\Program Files\GitHub CLI\gh.exe')
    p.add_argument('--workers',type=int,default=3)
    p.add_argument('--wait-minutes',type=int,default=120)
    a=p.parse_args();manifest=json.loads(Path('artifact/manifest.json').read_text());repo=manifest['repository'];tag=manifest['release_tag']
    records=manifest['assets'];asset_dir=Path('output/artifact_release');asset_dir.mkdir(parents=True,exist_ok=True)
    snapshot=Path('artifacts/ssh_import_20261009/snapshot')
    # GitHub's /releases/tags endpoint excludes unpublished drafts. Resolve the
    # owner-visible draft once, then use its stable numeric release identifier.
    candidates=json.loads(subprocess.check_output([a.gh,'api',f'repos/{repo}/releases?per_page=100']))
    matching=[r for r in candidates if r['tag_name']==tag]
    if len(matching)!=1:raise ValueError('Expected one existing draft release for '+tag)
    release_id=matching[0]['id']
    def api():return json.loads(subprocess.check_output([a.gh,'api',f'repos/{repo}/releases/{release_id}']))
    release=api()
    if not release['draft']:raise ValueError('Only a draft release may be populated')
    remote={r['name']:r for r in release['assets']};done=set()
    for name,r in records.items():
        if name in remote:
            if remote[name]['size']!=r['bytes'] or remote[name].get('digest')!='sha256:'+r['sha256']:raise ValueError('Remote asset differs: '+name)
            done.add(name)
    def upload(name,r):
        asset=asset_dir/name
        if asset.stat().st_size!=r['bytes'] or sha(asset)!=r['sha256']:raise ValueError('Local asset differs: '+name)
        for attempt in range(3):
            result=subprocess.run([a.gh,'release','upload',tag,str(asset),'--repo',repo],capture_output=True,text=True)
            if result.returncode==0:return name
            # A network failure can occur after GitHub has accepted the complete asset.
            match=next((x for x in api()['assets'] if x['name']==name),None)
            if match and match.get('digest')=='sha256:'+r['sha256'] and match['size']==r['bytes']:return name
            if match:raise ValueError('Incomplete/different remote asset: '+name)
            if attempt==2:raise RuntimeError(result.stderr.strip())
            time.sleep(10*(attempt+1))
    deadline=time.monotonic()+60*a.wait_minutes;active={};submitted=set(done)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        while len(done)<len(records):
            for name,r in records.items():
                if name in submitted or len(active)>=a.workers:continue
                asset=asset_dir/name
                if not asset.exists() and r['kind']=='checkpoint':
                    source=snapshot/r['original_path']
                    if source.exists():
                        if source.stat().st_size!=r['bytes'] or sha(source)!=r['sha256']:raise ValueError('Imported checkpoint differs: '+name)
                        try:asset.hardlink_to(source)
                        except OSError:shutil.copy2(source,asset)
                if asset.exists():submitted.add(name);active[pool.submit(upload,name,r)]=name
            completed,_=concurrent.futures.wait(active,timeout=10,return_when=concurrent.futures.FIRST_COMPLETED) if active else ([],None)
            for future in completed:
                name=future.result();done.add(name);del active[future]
                print(json.dumps({'uploaded_asset':name,'verified_uploaded':len(done),'expected_assets':len(records)}),flush=True)
            if time.monotonic()>deadline:raise TimeoutError('Missing imports or uploads; rerun to resume')
            if not active and len(done)<len(records):time.sleep(10)
    final=api();remote={r['name']:r for r in final['assets']};errors=[]
    for name,r in records.items():
        if name not in remote or remote[name]['size']!=r['bytes'] or remote[name].get('digest')!='sha256:'+r['sha256']:errors.append(name)
    receipt={'passed':not errors,'release_id':final['id'],'release_tag':tag,'assets_checked':len(records),'errors':errors,
             'assets':{name:{'bytes':remote[name]['size'],'sha256':remote[name].get('digest')} for name in records if name in remote}}
    Path('output/artifact_release/github_asset_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['passed','assets_checked','errors']}),flush=True)
    if errors:raise ValueError('GitHub asset verification failed')

if __name__=='__main__':main()
