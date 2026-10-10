"""Build compact evidence in Git and large assets for a tagged GitHub release."""
import argparse
import gzip
import hashlib
import json
import shutil
import tarfile
from pathlib import Path

CAMPAIGN=Path('artifacts/release_gates/strengthening_20261006')
TAG='graph-reliance-artifact-20261009-v1'
REPOSITORY='tanay-kadam/ASTGuard'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def package_hashes(out):
    return {p.relative_to(out).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'manifest.json'
        and not {'__pycache__','downloads'}.intersection(p.relative_to(out).parts)}

def compress(source,dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():
        with gzip.open(dest,'rb') as f:
            h=hashlib.sha256()
            for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
        if h.hexdigest()==sha(source):return
        raise FileExistsError('Existing compressed evidence differs: '+str(dest))
    partial=dest.with_name(dest.name+'.partial')
    with source.open('rb') as src,partial.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=6) as dst:
        shutil.copyfileobj(src,dst,8*1024*1024)
    partial.replace(dest)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--import-root',type=Path,default=Path('artifacts/ssh_import_20261009'))
    p.add_argument('--package',type=Path,default=Path('artifact'))
    p.add_argument('--assets',action='store_true')
    p.add_argument('--allow-missing-checkpoints',action='store_true',help='Prepare a draft release while a verified import is still running')
    p.add_argument('--refresh-manifest-only',action='store_true',help='Hash added documentation/validation without rebuilding frozen evidence')
    args=p.parse_args();source=args.import_root/'snapshot';out=args.package
    if args.refresh_manifest_only:
        manifest=read(out/'manifest.json');manifest['package_files']=package_hashes(out);write(out/'manifest.json',manifest)
        print('Refreshed',len(manifest['package_files']),'package file hashes',flush=True);return
    inv=read(args.import_root/'inventory.json');summary=read(source/CAMPAIGN/'summary.json');plan=read(source/CAMPAIGN/'jobs.json')
    files={r['path']:r for r in inv['files']};manifest={'schema_version':1,'release_tag':TAG,'repository':REPOSITORY,
        'scope':'Corrected development-cohort results; synthetic audit is held out. No independent real-data test claim.',
        'jobs':{},'assets':{},'evidence':{},'source_snapshot_inventory_sha256':sha(args.import_root/'inventory.json')}
    for job in plan['jobs']:
        tag=job['tag'];run=Path(summary['jobs'][tag]['run_dir']);external=job['family']=='regvd';target=out/'evidence'/tag
        def copy_evidence(rel,dest):
            sp=source/rel;dp=target/dest
            if dest.endswith('.gz'):compress(sp,dp)
            else:dp.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(sp,dp)
            manifest['evidence'][dp.relative_to(out).as_posix()]={'sha256':sha(dp),'bytes':dp.stat().st_size,'original_sha256':files[rel.as_posix()]['sha256'],'original_path':rel.as_posix()}
        copy_evidence(run/('selected_predictions.jsonl' if external else 'selected_tune_predictions.jsonl'),'selected.jsonl.gz')
        copy_evidence(run/('selection.json' if external else 'checkpoint_selection.json'),'selection.json')
        copy_evidence(run/('history.jsonl' if external else 'train_log.jsonl'),'history.jsonl.gz')
        copy_evidence(run/('config.json' if external else 'config.resolved.yaml'),'config.json')
        for original,destination in [(CAMPAIGN/'jobs'/tag/'run.log','console.log.gz'),
                (CAMPAIGN/'jobs'/tag/'status.json','job_status.json'),(run/'command.txt','command.txt'),
                (run/'status.json','run_status.json')]:
            if (source/original).exists():copy_evidence(original,destination)
        if external:
            copy_evidence(run/'interventions.json','interventions.json')
            for mode in ['native','permuted','empty','self']:copy_evidence(run/('intervention_'+mode+'.jsonl'),mode+'.jsonl.gz')
            copy_evidence(run/'checksums.json','original_checksums.json')
        else:
            copy_evidence(CAMPAIGN/'jobs'/tag/'interventions.json','interventions.json.gz')
            for name in ['provenance.json','environment.json','dataset_views.json','graph_donors.json','matched_null_graphs.json','source.start.json','artifact_checksums.json']:
                if (source/run/name).exists():copy_evidence(run/name,name)
            for epoch in sorted((source/run/'validation_predictions').glob('epoch_*.jsonl')):
                copy_evidence(epoch.relative_to(source),'epochs/'+epoch.name+'.gz')
        checkpoint=run/('best.safetensors' if external else 'checkpoints/best.safetensors');entry=files[checkpoint.as_posix()]
        asset='checkpoint-'+tag+'.safetensors'
        manifest['jobs'][tag]={'family':job['family'],'condition':job['condition'],'seed':job['seed'],
            'selected_tune_ap':summary['jobs'][tag]['selected_tune_ap'],'run_dir':run.as_posix(),'checkpoint_asset':asset}
        manifest['assets'][asset]={'kind':'checkpoint','sha256':entry['sha256'],'bytes':entry['bytes'],
            'original_path':checkpoint.as_posix(),'destination':'checkpoints/'+tag+'.safetensors',
            'url':f'https://github.com/{REPOSITORY}/releases/download/{TAG}/{asset}'}
    for name in ['summary.json','jobs.json','rebuilt_population_audit.json','split_integrity_correction.json']:
        shutil.copy2(source/CAMPAIGN/name,out/name)
    compress(source/CAMPAIGN/'corrected_manifest.json',out/'corrected_manifest.json.gz')
    shutil.copy2(args.import_root/'backbone_configs.json',out/'backbone_configs.json')
    if (args.import_root/'environment-remote-venv.freeze.txt').exists():
        shutil.copy2(args.import_root/'environment-remote-venv.freeze.txt',out/'environment-remote.freeze.txt')
    shutil.copy2(args.import_root/'inventory.json',out/'import_inventory.json')
    for role in ['train','tune','audit']:
        compress(source/'data/strengthening_20261006/synthetic'/(role+'.jsonl'),out/'inputs/synthetic'/(role+'.jsonl.gz'))
    shutil.copy2(source/'data/strengthening_20261006/synthetic/manifest.json',out/'inputs/synthetic/manifest.json')
    shutil.copy2(source/'data/strengthening_20261006/real/manifest.json',out/'real_inputs_manifest.json')
    # Small complete model inputs allow a weights-to-logits smoke without all train data.
    for label,family,role in [('synthetic','synthetic','audit'),('real','real','tune'),('regvd','real','regvd_tune')]:
        feature=source/'data/strengthening_20261006'/family/(role+'.jsonl')
        if feature.exists():
            dest=out/'smoke_inputs'/(label+'.jsonl.gz');dest.parent.mkdir(parents=True,exist_ok=True)
            with feature.open('rb') as src,dest.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as dst:
                for i,line in enumerate(src):
                    if i==8:break
                    dst.write(line)
    source_files={name:r for name,r in files.items() if name.startswith(('astguard/','scripts/','configs/','tests/','third_party/','protocol/')) or name in ['requirements.lock','pyproject.toml','LICENSE','sources.lock.json']}
    archive=out/'runtime_source.tar.gz'
    if not archive.exists() or not (out/'runtime_source_manifest.json').exists() or read(out/'runtime_source_manifest.json')!=source_files:
        with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
            for name in sorted(source_files):tar.add(source/name,arcname=name,recursive=False)
    write(out/'runtime_source_manifest.json',source_files)
    if args.assets:
        asset_dir=Path('output/artifact_release');asset_dir.mkdir(parents=True,exist_ok=True)
        for asset,record in manifest['assets'].items():
            src=source/record['original_path'];dst=asset_dir/asset
            if not src.exists() and args.allow_missing_checkpoints:
                print('Pending import:',asset,flush=True);continue
            if not src.exists() or src.stat().st_size!=record['bytes'] or sha(src)!=record['sha256']:raise ValueError('Unverified checkpoint: '+str(src))
            if not dst.exists():
                try:dst.hardlink_to(src)
                except OSError:shutil.copy2(src,dst)
        input_files=[('real-'+name,'data/strengthening_20261006/real/'+name+'.jsonl') for name in ['train','tune','regvd_train','regvd_tune']]
        input_files.append(('development-records',str(CAMPAIGN/'development_records.jsonl.gz').replace('\\','/')))
        for name,rel in input_files:
            sp=source/rel;asset='inputs-'+name+'.jsonl.gz';dp=asset_dir/asset
            if name=='development-records':
                if not dp.exists():shutil.copy2(sp,dp)
            else:compress(sp,dp)
            if dp.stat().st_size>=2*1024**3:raise ValueError('Release asset exceeds 2 GiB: '+asset)
            if name=='development-records':
                digest=hashlib.sha256()
                with gzip.open(dp,'rb') as f:
                    for b in iter(lambda:f.read(8*1024*1024),b''):digest.update(b)
                expanded_sha=digest.hexdigest()
            else:expanded_sha=files[rel]['sha256']
            manifest['assets'][asset]={'kind':'input','bytes':dp.stat().st_size,'sha256':sha(dp),'original_sha256':files[rel]['sha256'],
                'uncompressed_sha256':expanded_sha,
                'destination':('inputs/development_records.jsonl' if name=='development-records' else 'inputs/real/'+name.removeprefix('real-')+'.jsonl'),
                'url':f'https://github.com/{REPOSITORY}/releases/download/{TAG}/{asset}'}
            print('Prepared',asset,dp.stat().st_size,flush=True)
    # Every packaged evidence/config/source file is covered, including files outside evidence/.
    manifest['package_files']=package_hashes(out)
    write(out/'manifest.json',manifest)
    print(json.dumps({'jobs':len(manifest['jobs']),'package_files':len(manifest['package_files']),
        'package_bytes':sum(r['bytes'] for r in manifest['package_files'].values()),'large_assets_prepared':args.assets}),flush=True)

if __name__=='__main__':main()
