"""Materialize frozen feature cohorts and the experiment-launcher context."""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

from astguard.alignment.tokenizer import CanonicalTokenizer
from astguard.data.join import join_features
from astguard.data.preprocess import preprocess_record,_preprocessing_hash
from astguard.data.cache import FeatureCache
from astguard.data.schema import SampleRecord,read_jsonl,write_jsonl
from astguard.utils.atomic_io import atomic_write_json,atomic_write_text,append_jsonl
from astguard.utils.hashing import object_hash,sha256_file


DEFAULT_VARIANTS=tuple({**variant,'annotation_masking':'a_priori_v1'} for variant in (
    {'max_length':512,'ast_relation':'leaf_path_radius4','dfg_symmetry':False,'structural_context':'full_function','topology':'clean'},
    {'max_length':384,'ast_relation':'leaf_path_radius4','dfg_symmetry':False,'structural_context':'full_function','topology':'clean'},
    {'max_length':512,'ast_relation':'anchored_parent_child','dfg_symmetry':False,'structural_context':'full_function','topology':'clean'},
    {'max_length':512,'ast_relation':'leaf_path_radius4','dfg_symmetry':True,'structural_context':'full_function','topology':'clean'},
    {'max_length':512,'ast_relation':'leaf_path_radius4','dfg_symmetry':False,'structural_context':'visible_prefix','topology':'clean'},
    {'max_length':512,'ast_relation':'leaf_path_radius4','dfg_symmetry':False,'structural_context':'full_function','topology':'degree_preserving_rewired'},
))


def prepare(plan_path: Path,output_root: Path,context_path: Path):
    plan=json.loads(plan_path.read_text(encoding='utf-8'))
    checkpoint=plan['checkpoint'];revision=plan['checkpoint_revision']
    tokenizer=CanonicalTokenizer(checkpoint,revision)
    cache_root=Path(plan.get('cache_root','data/cache/features'))
    variants=plan.get('variants') or list(DEFAULT_VARIANTS)
    registry={};preprocessing=[]
    for view,cohort in sorted(plan['cohorts'].items()):
        manifest_path=Path(cohort['manifest']);manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        if manifest['view']!=view:raise ValueError(f'cohort name/manifest view mismatch: {view}')
        wanted=set(manifest['ordered_sample_ids'])
        for fields in variants:
            fields={'annotation_masking':'a_priori_v1',**fields}
            key=object_hash({'view':view,**fields})
            directory=output_root/view/key;directory.mkdir(parents=True,exist_ok=True)
            feature_path=directory/'features.jsonl';partial=directory/'features.jsonl.partial'
            expected_hash=_preprocessing_hash(tokenizer.identity_hash,fields['max_length'],False,
                fields['ast_relation'],fields['dfg_symmetry'],fields['structural_context'],fields['topology'],
                fields['annotation_masking'])
            cache=FeatureCache(cache_root/expected_hash,expected_hash)
            failure_path=directory/'preprocessing_failures.jsonl';atomic_write_text(failure_path,'')
            hashes=set();seen=set();failures=[0]
            def features():
                for record_path in cohort['records']:
                    for row in read_jsonl(record_path):
                        if row['sample_id'] not in wanted:continue
                        record=SampleRecord.from_dict(row)
                        try:
                            feature=cache.get_or_build(record.raw_sha256,lambda:dataclasses.asdict(
                                preprocess_record(record,tokenizer,**fields)),sample_id=record.sample_id)
                            hashes.add(feature['preprocessing_hash']);seen.add(feature['sample_id'])
                            yield feature
                        except Exception as exc:
                            failures[0]+=1
                            append_jsonl(failure_path,{'sample_id':record.sample_id,'dataset':record.dataset,
                                'stage':'preprocess','exception':type(exc).__name__,'reason':str(exc),
                                'source_length':len(record.source_canonical),'language':record.language_metadata,
                                'cache_version':expected_hash})
            write_jsonl(partial,features())
            if failures[0]:raise RuntimeError(f'{view}/{key} had {failures[0]} preprocessing failures; see {failure_path}')
            if seen!=wanted:raise ValueError(f'{view}/{key} missing {len(wanted-seen)} records')
            if len(hashes)!=1:raise ValueError('feature cohort has inconsistent preprocessing hashes')
            os.replace(partial,feature_path)
            role_paths=join_features(cohort['records'],feature_path,manifest_path,directory/'joined')
            artifact={'view':view,'manifest':str(manifest_path),'manifest_hash':manifest['file_hash'],
                      'preprocessing_hash':next(iter(hashes)),'features':str(feature_path),**role_paths}
            registry[key]=artifact
            preprocessing.append({'feature_key':key,'fields':fields,**artifact,'feature_sha256':sha256_file(feature_path)})
    context={'protocol_hash':plan['protocol_hash'],'checkpoint_revisions':plan['checkpoint_revisions'],
             'resources':plan['resources'],'full_data_optimizer_steps':plan.get('full_data_optimizer_steps'),
             'feature_registry':registry}
    if context['full_data_optimizer_steps'] is None:
        clean=next((row for row in preprocessing if row['view']=='P_clean' and row['fields']==DEFAULT_VARIANTS[0]),None)
        if clean:
            count=sum(1 for _ in read_jsonl(clean['train']))
            import math
            context['full_data_optimizer_steps']=math.ceil(math.ceil(count/4)/8)*5
    atomic_write_json(output_root/'preprocessing_manifest.json',{'schema_version':1,'entries':preprocessing})
    atomic_write_json(context_path,context)
    return context


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',required=True,help='JSON plan containing checkpoint, cohorts, hashes, and resources')
    parser.add_argument('--output-root',default='data/processed/cohorts')
    parser.add_argument('--context',default='artifacts/launcher/context.json')
    args=parser.parse_args(argv)
    prepare(Path(args.plan),Path(args.output_root),Path(args.context))
    print(args.context)
    return 0


if __name__=='__main__':raise SystemExit(main())
