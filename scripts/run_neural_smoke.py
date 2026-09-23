"""Actual Tree-sitter/tokenizer/Transformer/trainer smoke on public train-only data."""
import dataclasses
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from torch.utils.data import DataLoader
from transformers import RobertaConfig, RobertaModel, get_linear_schedule_with_warmup
from astguard.alignment.tokenizer import CanonicalTokenizer
from astguard.data.schema import make_sample
from astguard.data.preprocess import preprocess_record
from astguard.data.collate import StructuralCollator
from astguard.data.audit import LeakageAuditor
from astguard.models.codebert import ASTGuardClassifier
from astguard.training.engine import Trainer
from astguard.training.optim import build_adamw
from astguard.config import TrainingConfig
from astguard.evaluation.thresholds import ThresholdSelector
from astguard.evaluation.metrics import evaluate_scores, decode_threshold
from astguard.utils.hashing import hash_uniform, object_hash, sha256_file
from astguard.utils.atomic_io import atomic_write_json
from astguard.utils.provenance import environment_snapshot


def main():
    torch.set_num_threads(2)
    source=json.loads(Path('artifacts/environment/development_sources.json').read_text())
    tokenizer=CanonicalTokenizer(source['codebert_path'],source['codebert_revision'])
    index_file=next(Path('third_party/sources/CodeXGLUE').glob('*/Code-Code/Defect-detection/dataset/train.txt'))
    train_ids={int(x) for x in index_file.read_text().splitlines()}
    raw=json.loads(Path('data/raw/development/function.json').read_text())
    indices=sorted(train_ids,key=lambda i:hash_uniform('smoke-public-v1',str(i)))[:96]
    records=[make_sample(dataset='codexglue',release='official-training-development',original_split='train',
                         original_id=str(i),original_row_index=i,source=raw[i]['func'],label=int(raw[i]['target'])) for i in indices]
    components,_=LeakageAuditor().build_components(records)
    groups={role:[] for role in ['train','tune','cal','test']}
    for record in records:
        value=hash_uniform('smoke-roles-v1',components[record.sample_id])
        role='train' if value<.55 else 'tune' if value<.70 else 'cal' if value<.85 else 'test'
        feature=dataclasses.asdict(preprocess_record(record,tokenizer,max_length=64))
        groups[role].append(feature|{'label':record.label,'role':role,'component_id':components[record.sample_id]})
    for role,rows in groups.items():
        if {x['label'] for x in rows}!={0,1}:
            raise RuntimeError(f'predeclared smoke split {role} has a missing class')
    root=Path('runs')/('neural-smoke-'+uuid.uuid4().hex[:12]);root.mkdir()
    smoke_split={role:[x['sample_id'] for x in rows] for role,rows in groups.items()}
    smoke_split_hash=object_hash(smoke_split)
    smoke_feature_hash=object_hash(sorted({row['preprocessing_hash'] for rows in groups.values() for row in rows}))
    atomic_write_json(root/'split_manifest.json',smoke_split|{'file_hash':smoke_split_hash})
    summaries=[]
    for variant in ['sequence_only','ast_dfg_fixed','astguard']:
        torch.manual_seed(42)
        config=RobertaConfig(vocab_size=tokenizer.tokenizer.vocab_size,hidden_size=32,num_hidden_layers=2,
            num_attention_heads=4,intermediate_size=64,max_position_embeddings=80,hidden_dropout_prob=.1,attention_probs_dropout_prob=.1)
        config._attn_implementation='eager'
        model=ASTGuardClassifier(RobertaModel(config,add_pooling_layer=False),variant=variant,structural_layers=(0,1),plumbing_only=True)
        optimizer=build_adamw(model,pretrained_lr=1e-3,new_multiplier=1,weight_decay=.01)
        loaders={role:DataLoader(rows,batch_size=4,shuffle=role=='train',collate_fn=StructuralCollator(),
                                 generator=torch.Generator().manual_seed(42)) for role,rows in groups.items()}
        recipe=TrainingConfig(epochs=2,min_epochs=2,microbatch_size=4,gradient_accumulation=2,effective_batch_size=8,precision='fp32')
        scheduler=get_linear_schedule_with_warmup(optimizer,1,2*((len(loaders['train'])+1)//2))
        trainer=Trainer(model,optimizer,scheduler,accumulation_steps=2)
        labels=[x['label'] for x in groups['train']];n=len(labels);weights={0:n/(2*(n-sum(labels))),1:n/(2*sum(labels))}
        run=root/variant;run.mkdir()
        trainer.fit(loaders['train'],loaders['tune'],weights,recipe,run,object_hash(dataclasses.asdict(recipe)))
        calibration=trainer.predict(loaders['cal'])
        checkpoint_hash=sha256_file(run/'checkpoints/best.safetensors')
        thresholds=ThresholdSelector().fit([r['sample_id'] for r in calibration],[r['label'] for r in calibration],
             [r['probability'] for r in calibration],role='cal',checkpoint_hash=checkpoint_hash)
        predictions=trainer.predict(loaders['test'])
        prediction_rows=[r|{'model_id':variant,'seed':42,'run_id':str(run),'checkpoint_hash':checkpoint_hash,
                            'dataset':'codexglue','view':'training_only_smoke','split_hash':smoke_split_hash,
                            'config_hash':object_hash({'model_id':variant,'kind':'tiny_random_neural_smoke'}),
                            'feature_hash':smoke_feature_hash,'metric_version':'1.0',
                            'threshold_ids':{'max_f1':thresholds['max_f1'].threshold_id},
                            'decisions':{'max_f1':r['probability']>=decode_threshold(thresholds['max_f1'].threshold)},
                            'role':'development_test_from_official_train'} for r in predictions]
        atomic_write_json(run/'predictions.json',prediction_rows)
        atomic_write_json(run/'calibration_predictions.json',calibration)
        atomic_write_json(run/'thresholds.json',{k:dataclasses.asdict(v) for k,v in thresholds.items()})
        metric=evaluate_scores([r['label'] for r in predictions],[r['probability'] for r in predictions],decode_threshold(thresholds['max_f1'].threshold))
        atomic_write_json(run/'metrics.json',metric)
        import pyarrow as pa
        import pyarrow.parquet as pq
        pq.write_table(pa.Table.from_pylist(prediction_rows),run/'predictions.parquet')
        summaries.append({'model_id':variant,'seed':42,**metric})
    from astguard.analysis.aggregate import ResultAggregator
    from astguard.analysis.plots import write_metric_svg
    ResultAggregator().build_markdown_table(summaries,root/'table.md')
    write_metric_svg(summaries,root/'figure.svg')
    atomic_write_json(root/'environment.json',environment_snapshot(['torch','transformers','tree-sitter','pyarrow']))
    atomic_write_json(root/'status.json',{'status':'complete','scientific_status':'plumbing_only_random_tiny_encoder',
        'official_test_used':False,'data_source_sha256':sha256_file('data/raw/development/function.json'),
        'counts':{role:len(rows) for role,rows in groups.items()},'codebert_revision':source['codebert_revision']})
    print(root)


if __name__=='__main__':main()
