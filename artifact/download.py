"""Download selected large release assets and verify SHA256 before use."""
import argparse
import gzip
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',action='store_true')
    p.add_argument('--all-checkpoints',action='store_true');p.add_argument('--checkpoints',nargs='*',default=[])
    p.add_argument('--destination',type=Path,default=Path('artifact/downloads'));p.add_argument('--local-assets',type=Path)
    a=p.parse_args();root=Path(__file__).resolve().parent;manifest=json.loads((root/'manifest.json').read_text())
    selected=[(name,r) for name,r in manifest['assets'].items() if (a.data and r['kind']=='input') or
        (r['kind']=='checkpoint' and (a.all_checkpoints or name.removeprefix('checkpoint-').removesuffix('.safetensors') in a.checkpoints))]
    if not selected:p.error('Choose --data, --all-checkpoints, or --checkpoints JOB_TAG ...')
    known=set(manifest['jobs']);unknown=set(a.checkpoints)-known
    if unknown:p.error('Unknown job tags: '+', '.join(sorted(unknown)))
    cache=a.destination/'asset_cache';cache.mkdir(parents=True,exist_ok=True)
    for name,r in selected:
        asset=(a.local_assets/name) if a.local_assets else cache/name
        if not asset.exists():
            if a.local_assets:raise FileNotFoundError(asset)
            temp=asset.with_name(asset.name+'.partial')
            request=urllib.request.Request(r['url'],headers={'User-Agent':'ASTGuard-artifact-downloader'})
            with urllib.request.urlopen(request,timeout=60) as source,temp.open('wb') as target:shutil.copyfileobj(source,target,8*1024*1024)
            if temp.stat().st_size!=r['bytes'] or sha(temp)!=r['sha256']:raise ValueError('Asset checksum mismatch: '+name)
            temp.replace(asset)
        if asset.stat().st_size!=r['bytes'] or sha(asset)!=r['sha256']:raise ValueError('Asset checksum mismatch: '+name)
        dest=a.destination/r['destination'];dest.parent.mkdir(parents=True,exist_ok=True)
        if r['kind']=='checkpoint':
            if dest.exists():
                if sha(dest)!=r['sha256']:raise FileExistsError('Different existing checkpoint '+str(dest))
            else:
                try:dest.hardlink_to(asset)
                except OSError:shutil.copy2(asset,dest)
        else:
            expected=r.get('uncompressed_sha256')
            if dest.exists() and expected and sha(dest)==expected:continue
            if dest.exists():raise FileExistsError('Refusing to replace '+str(dest))
            temp=dest.with_name(dest.name+'.partial')
            with gzip.open(asset,'rb') as source,temp.open('wb') as target:shutil.copyfileobj(source,target,8*1024*1024)
            if expected and sha(temp)!=expected:raise ValueError('Decompressed input checksum mismatch '+name)
            temp.replace(dest)
        print('Verified',name,'->',dest,flush=True)

if __name__=='__main__':main()
