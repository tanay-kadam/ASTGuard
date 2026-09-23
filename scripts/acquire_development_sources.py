"""Acquire public training-only fixtures and immutable source/checkpoint revisions."""
import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file

CODEXGLUE_FUNCTION_ID='1x6hoF7G-tSYxg8AFybggypLZgMGDNHfF'


def fetch(url):
    request = urllib.request.Request(url,headers={'User-Agent':'ASTGuard-research-artifact'})
    return urllib.request.urlopen(request,timeout=120).read()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--weights',action='store_true')
    args=parser.parse_args()
    lock_path=Path('sources.lock.json')
    lock=json.loads(lock_path.read_text())
    def registered(name):
        return next((entry for entry in lock['sources'] if entry['logical_name']==name),None)
    def pinned_revision(prefix):
        revisions={entry['upstream_revision'] for entry in lock['sources']
                   if entry['logical_name'].startswith(prefix+'/') and entry.get('upstream_revision')}
        if len(revisions)!=1:
            raise ValueError(f'expected one locked revision for {prefix}, found {sorted(revisions)}')
        return revisions.pop()
    def register(name,url,data,path,revision,landing):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()!=data:
            raise ValueError(f'immutable payload changed: {path}')
        prior=registered(name)
        digest=sha256_file(path) if path.exists() else hashlib.sha256(data).hexdigest()
        if prior and (digest!=prior['sha256'] or len(data)!=prior['bytes']):
            raise ValueError(f'locked payload changed upstream: {name}')
        path.write_bytes(data)
        if prior:
            return
        entry={'logical_name':name,'release':'development','official_landing_url':landing,'resolved_download_url':url,
               'upstream_revision':revision,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'bytes':len(data),
               'sha256':sha256_file(path),'license_access_notes':'Upstream terms apply; see pinned LICENSE',
               'local_immutable_path':str(path.resolve())}
        lock['sources']=[e for e in lock['sources'] if e['logical_name']!=name]+[entry]
        atomic_write_json(lock_path,lock)
    repositories={
        'CodeXGLUE':('microsoft/CodeXGLUE',['Code-Code/Defect-detection/dataset/train.txt','LICENSE']),
        'CodeBERT':('microsoft/CodeBERT',['GraphCodeBERT/codesearch/model.py','GraphCodeBERT/codesearch/run.py','LICENSE']),
        'LineVul':('awsm-research/LineVul',['linevul/linevul_model.py','linevul/linevul_main.py','LICENSE']),
        'PrimeVul':('DLVulDet/PrimeVul',['calc_vd_score.py','README.md','LICENSE']),
        'ReGVD':('daiquocnguyen/GNN-ReGVD',['code/model.py','code/modelGNN_updates.py','code/run.py','code/utils.py','README.md']),
    }
    for name,(repository,files) in repositories.items():
        commit=pinned_revision(name)
        for file in files:
            url=f'https://raw.githubusercontent.com/{repository}/{commit}/{file}'
            target=Path('data/raw/development')/name/commit/file if file.endswith('.jsonl') else Path('third_party/sources')/name/commit/file
            prior=registered(name+'/'+file)
            if prior and target.is_file() and target.stat().st_size==prior['bytes'] and sha256_file(target)==prior['sha256']:
                continue
            register(name+'/'+file,url,fetch(url),target,commit,'https://github.com/'+repository)
        print(f'{name}: {commit}',flush=True)
    import gdown
    function_name='CodeXGLUE/function.json'
    function_entry=registered(function_name)
    if not function_entry:
        raise ValueError(f'{function_name} is not registered in {lock_path}')
    function_path=Path('data/raw/development/function.json')
    if function_path.exists():
        if sha256_file(function_path)!=function_entry['sha256']:
            raise ValueError(f'immutable payload changed: {function_path}')
    else:
        function_path.parent.mkdir(parents=True,exist_ok=True)
        partial=function_path.with_suffix('.partial')
        gdown.download('https://drive.google.com/uc?id='+CODEXGLUE_FUNCTION_ID,str(partial),quiet=False)
        if sha256_file(partial)!=function_entry['sha256']:
            partial.unlink(missing_ok=True)
            raise ValueError(f'locked payload changed upstream: {function_name}')
        rows=json.loads(partial.read_text(encoding='utf-8'))
        if len(rows)!=function_entry['rows']:
            partial.unlink(missing_ok=True)
            raise ValueError(f'locked payload row count changed: {function_name}')
        partial.replace(function_path)
    print(f'{function_name}: {function_entry["sha256"]}',flush=True)
    from huggingface_hub import snapshot_download
    patterns=['config.json','tokenizer_config.json','special_tokens_map.json','vocab.json','merges.txt','tokenizer.json']
    if args.weights: patterns += ['pytorch_model.bin','model.safetensors']
    checkpoint_sources={}
    for logical,repo in [('codebert','microsoft/codebert-base'),('graphcodebert','microsoft/graphcodebert-base')]:
        revision=pinned_revision(logical)
        directory=Path('data/raw/checkpoints')/logical/revision
        snapshot_download(repo,revision=revision,allow_patterns=patterns,local_dir=directory)
        for path in directory.iterdir():
            if path.is_file():
                register(logical+'/'+path.name,f'https://huggingface.co/{repo}/resolve/{revision}/{path.name}',
                         path.read_bytes(),path,revision,f'https://huggingface.co/{repo}')
        checkpoint_sources[logical+'_path']=str(directory)
        checkpoint_sources[logical+'_revision']=revision
        print(f'{repo}: {revision}',flush=True)
    atomic_write_json('artifacts/environment/development_sources.json',checkpoint_sources)


if __name__=='__main__': main()
