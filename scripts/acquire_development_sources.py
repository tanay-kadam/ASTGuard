"""Acquire public training-only fixtures and immutable source/checkpoint revisions."""
import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.hashing import sha256_file


def fetch(url):
    request = urllib.request.Request(url,headers={'User-Agent':'ASTGuard-research-artifact'})
    return urllib.request.urlopen(request,timeout=120).read()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--weights',action='store_true')
    args=parser.parse_args()
    lock_path=Path('sources.lock.json')
    lock=json.loads(lock_path.read_text())
    def register(name,url,data,path,revision,landing):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and path.read_bytes()!=data:
            raise ValueError(f'immutable payload changed: {path}')
        path.write_bytes(data)
        entry={'logical_name':name,'release':'development','official_landing_url':landing,'resolved_download_url':url,
               'upstream_revision':revision,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'bytes':len(data),
               'sha256':sha256_file(path),'license_access_notes':'Upstream terms apply; see pinned LICENSE',
               'local_immutable_path':str(path.resolve())}
        lock['sources']=[e for e in lock['sources'] if e['logical_name']!=name]+[entry]
        atomic_write_json(lock_path,lock)
    repositories={
        'CodeXGLUE':('microsoft/CodeXGLUE','main',['Code-Code/Defect-detection/dataset/train.txt','LICENSE']),
        'CodeBERT':('microsoft/CodeBERT','master',['GraphCodeBERT/codesearch/model.py','GraphCodeBERT/codesearch/run.py','LICENSE']),
        'LineVul':('awsm-research/LineVul','main',['linevul/linevul_model.py','linevul/linevul_main.py','LICENSE']),
        'PrimeVul':('DLVulDet/PrimeVul','main',['calc_vd_score.py','README.md','LICENSE']),
        'ReGVD':('daiquocnguyen/GNN-ReGVD','master',['code/model.py','code/modelGNN_updates.py','code/run.py','code/utils.py','README.md']),
    }
    for name,(repository,branch,files) in repositories.items():
        commit=json.loads(fetch(f'https://api.github.com/repos/{repository}/commits/{branch}'))['sha']
        for file in files:
            url=f'https://raw.githubusercontent.com/{repository}/{commit}/{file}'
            target=Path('data/raw/development')/name/commit/file if file.endswith('.jsonl') else Path('third_party/sources')/name/commit/file
            register(name+'/'+file,url,fetch(url),target,commit,'https://github.com/'+repository)
        print(f'{name}: {commit}',flush=True)
    from huggingface_hub import HfApi, snapshot_download
    patterns=['config.json','tokenizer_config.json','special_tokens_map.json','vocab.json','merges.txt','tokenizer.json']
    if args.weights: patterns += ['pytorch_model.bin','model.safetensors']
    checkpoint_sources={}
    for logical,repo in [('codebert','microsoft/codebert-base'),('graphcodebert','microsoft/graphcodebert-base')]:
        revision=HfApi().model_info(repo).sha
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
