"""Preserve linked training inputs from existing local release assets, hash checked."""
import gzip
import hashlib
import json
import shutil
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
DEST=REPO/'archive/ssh_campaign_20261020'

def main():
    blob=(REPO/'tmp/shared_training_hashes_20261020.txt').read_bytes()
    text=blob.decode('utf-16' if blob.startswith(b'\xff\xfe') else 'utf-8-sig')
    remote={Path(line.split()[-1]).name:line.split()[0] for line in text.splitlines() if len(line.split())==2}
    assert len(remote)==4
    records=[]
    for name,expected in remote.items():
        source=REPO/'output/artifact_release'/('inputs-real-'+name+'.gz')
        h=hashlib.sha256();size=0
        with gzip.open(source,'rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block);size+=len(block)
        assert h.hexdigest()==expected,name
        target=DEST/'shared_inputs'/source.name;target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source,target)
        compressed=hashlib.sha256(target.read_bytes()).hexdigest()
        records.append({'file':str(target.relative_to(DEST)),'original_name':name,'uncompressed_sha256':expected,'uncompressed_bytes':size,'compressed_sha256':compressed})
        print('Verified linked input:',name,size,flush=True)
    report={'status':'passed','remote_link':'campaign/data/strengthening_20261006 -> /home/tkadam/ASTGuard/data/strengthening_20261006','files':records,'note':'Compressed copies are byte-equivalent after decompression to the four shared real training/TUNE inputs; no redownload or redistribution.'}
    (DEST/'shared_inputs_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    inventory=json.loads((DEST/'inventory.json').read_text())
    for r in inventory['files']:
        if not r['relative'].startswith('campaign/data/interim/'):continue
        source=REPO/r['relative'].removeprefix('campaign/')
        if not source.exists():continue
        with source.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        if h!=r['sha256']:continue
        target=DEST/r['relative'];target.parent.mkdir(exist_ok=True,parents=True)
        if target.exists():continue
        temporary=target.with_name(target.name+'.reuse');shutil.copyfile(source,temporary);temporary.replace(target)
        print('Reused exact normalized input:',r['relative'],flush=True)

if __name__=='__main__':main()
