from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path

from astguard.config import dump_config, load_config
from astguard.training.checkpoint import save_resume_checkpoint
from astguard.training.engine import Trainer
from astguard.training.optim import build_adamw
from astguard.training.seeds import set_seed
from astguard.utils.atomic_io import atomic_write_json, atomic_write_text,append_jsonl
from astguard.utils.hashing import object_hash,sha256_file
from astguard.utils.provenance import environment_snapshot, source_identity


class _FeatureDataset:
    """Validated random-access JSONL without retaining full graph features in RAM."""
    def __init__(self,path,*,role,manifest_hash,preprocessing_hash,fraction=1.0):
        from astguard.data.splits import component_fraction
        self.path=Path(path);self.offsets=[];self.ids=set();self.components=set()
        self.positives=0;self.max_input_length=0;self._handle=None
        with self.path.open('rb') as handle:
            while True:
                offset=handle.tell();line=handle.readline()
                if not line:break
                if not line.strip():continue
                row=json.loads(line)
                if row.get('role')!=role:raise ValueError(f'{role} feature file contains role {row.get("role")}')
                if row.get('split_hash')!=manifest_hash:raise ValueError('training split manifest hash mismatch')
                if row.get('preprocessing_hash')!=preprocessing_hash:raise ValueError('training preprocessing hash mismatch')
                if 'label' not in row:raise ValueError('joined feature record is missing label')
                if role=='train' and not component_fraction(row['component_id'],fraction):continue
                sample_id=row['sample_id']
                if sample_id in self.ids:raise ValueError(f'duplicate feature sample ID: {sample_id}')
                self.ids.add(sample_id);self.components.add(row['component_id']);self.offsets.append(offset)
                self.positives+=int(row['label']);self.max_input_length=max(self.max_input_length,len(row['input_ids']))
    def __len__(self):return len(self.offsets)
    def __getitem__(self,index):
        if self._handle is None or self._handle.closed:self._handle=self.path.open('rb')
        self._handle.seek(self.offsets[index])
        return json.loads(self._handle.readline())
    def __del__(self):
        if self._handle is not None:self._handle.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--features", required=True, help="JSONL features already joined to training labels")
    parser.add_argument('--tune-features', required=True, help='Component-disjoint V_tune features with labels')
    parser.add_argument("--seed", type=int)
    parser.add_argument("--runs-root", default="runs")
    parser.add_argument("--resume")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    config = load_config(args.config, allow_unresolved=args.dry_run)
    if args.seed is not None:
        config = dataclasses.replace(config, training=dataclasses.replace(config.training, seed=args.seed))
    if args.dry_run:
        print(dump_config(config), end="")
        return 0
    try:
        import torch
        from torch.utils.data import DataLoader
    except ImportError as exc:
        raise RuntimeError("Scientific training requires Python 3.11 and astguard[research]") from exc
    train_dataset=_FeatureDataset(args.features,role='train',manifest_hash=config.dataset.manifest_hash,
                                  preprocessing_hash=config.preprocessing.cache_hash,
                                  fraction=config.dataset.train_fraction)
    tune_dataset=_FeatureDataset(args.tune_features,role='tune',manifest_hash=config.dataset.manifest_hash,
                                 preprocessing_hash=config.preprocessing.cache_hash)
    if train_dataset.ids & tune_dataset.ids:
        raise ValueError('train/tune IDs overlap')
    if train_dataset.components & tune_dataset.components:
        raise ValueError('train/tune components overlap')
    positives = train_dataset.positives
    negatives = len(train_dataset) - positives
    if not positives or not negatives:
        raise ValueError("training set must contain both classes")
    config_hash = object_hash(dataclasses.asdict(config))
    proposed_run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{config_hash[:10]}-{config.training.seed}-{uuid.uuid4().hex[:6]}"
    run_dir = Path(args.resume).resolve().parent.parent if args.resume else Path(args.runs_root) / proposed_run_id
    if not args.resume:
        run_dir.mkdir(parents=True, exist_ok=False)
        run_id = proposed_run_id
    else:
        resume_path = Path(args.resume).resolve()
        if resume_path != (run_dir / "checkpoints" / "last_resume.pt").resolve():
            raise ValueError("--resume must name RUN_DIR/checkpoints/last_resume.pt")
        if not resume_path.is_file():
            raise FileNotFoundError(resume_path)
        status_path = run_dir / "status.json"
        resolved_path = run_dir / "config.resolved.yaml"
        if not status_path.is_file() or not resolved_path.is_file():
            raise ValueError("resume run is missing status or resolved configuration")
        existing_status = json.loads(status_path.read_text(encoding="utf-8"))
        run_id = existing_status.get("run_id")
        if not run_id or run_id != run_dir.name:
            raise ValueError("resume run identity does not match its directory")
        existing_config = load_config(resolved_path)
        if object_hash(dataclasses.asdict(existing_config)) != config_hash:
            raise ValueError("resume configuration differs from the original run")
    set_seed(config.training.seed)
    from astguard.models.factory import create_model,create_collator
    model=create_model(config)
    if config.training.activation_checkpointing:
        if hasattr(model,'gradient_checkpointing'):
            model.gradient_checkpointing = True
        elif hasattr(model,'backbone') and hasattr(model.backbone,'gradient_checkpointing_enable'):
            model.backbone.gradient_checkpointing_enable()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    optimizer = build_adamw(model, pretrained_lr=config.training.pretrained_lr,
                            new_multiplier=config.training.new_module_lr_multiplier,
                            weight_decay=config.training.weight_decay,
                            betas=config.training.adam_betas, epsilon=config.training.adam_epsilon)
    collator=create_collator(config,training=True)
    tune_collator=create_collator(config,training=False)
    loader = DataLoader(train_dataset, batch_size=config.training.microbatch_size,
                        shuffle=True, collate_fn=collator,
                        generator=torch.Generator().manual_seed(config.training.seed))
    class_weights = {0: len(train_dataset)/(2*negatives), 1: len(train_dataset)/(2*positives)}
    if config.training.loss == 'unweighted_bce':
        class_weights = {0:1.,1:1.}
    tune_loader = DataLoader(tune_dataset,batch_size=config.training.microbatch_size,shuffle=False,collate_fn=tune_collator)
    import math
    from transformers import get_linear_schedule_with_warmup
    total_steps = config.training.max_optimizer_steps or math.ceil(len(loader)/config.training.gradient_accumulation)*config.training.epochs
    scheduler = get_linear_schedule_with_warmup(optimizer,int(total_steps*config.training.warmup_fraction),total_steps)
    engine = Trainer(model, optimizer, grad_clip_norm=config.training.grad_clip_norm,
                     accumulation_steps=config.training.gradient_accumulation, device=device, scheduler=scheduler,precision=config.training.precision)
    if not args.resume:
        atomic_write_text(run_dir / "config.resolved.yaml", dump_config(config))
        atomic_write_text(run_dir/'command.txt',' '.join(sys.argv)+'\n')
        if Path('sources.lock.json').exists():
            atomic_write_text(run_dir/'sources.lock.snapshot.json',Path('sources.lock.json').read_text(encoding='utf-8'))
        atomic_write_json(run_dir/'split_manifest.ref',{'hash':config.dataset.manifest_hash,'view':config.dataset.view})
        atomic_write_json(run_dir/'preprocessing_manifest.ref',{'hash':config.preprocessing.cache_hash})
    append_jsonl(run_dir/'events.jsonl',{'status':'running','event':'resume' if args.resume else 'start',
                                        'checkpoint':str(Path(args.resume).resolve()) if args.resume else None,
                                        'utc':datetime.now(timezone.utc).isoformat()})
    atomic_write_json(run_dir/'status.json',{'status':'running','run_id':run_id})
    if device.startswith('cuda'):torch.cuda.reset_peak_memory_stats()
    fit_started=time.perf_counter()
    try:
        fit_result=engine.fit(loader,tune_loader,class_weights,config.training,run_dir,config_hash,resume=args.resume)
    except Exception as exc:
        import traceback
        failure={'status':'failed','reason':str(exc),'traceback':traceback.format_exc(),'utc':datetime.now(timezone.utc).isoformat()}
        append_jsonl(run_dir/'events.jsonl',failure);atomic_write_json(run_dir/'status.json',failure)
        raise
    elapsed=time.perf_counter()-fit_started
    environment=environment_snapshot(["torch","transformers","tree-sitter"])
    atomic_write_json(run_dir / "environment.json", environment)
    precision='fp32' if not engine.use_autocast else 'bf16' if engine.autocast_dtype==torch.bfloat16 else 'fp16'
    hardware={"device":device,"peak_allocated_bytes":torch.cuda.max_memory_allocated() if device.startswith('cuda') else None,
              "peak_reserved_bytes":torch.cuda.max_memory_reserved() if device.startswith('cuda') else None,
              "device_name":torch.cuda.get_device_name(0) if device.startswith('cuda') else None}
    atomic_write_json(run_dir / "provenance.json", {"source": source_identity(), "config_hash": config_hash,
        "class_counts": {"0": negatives, "1": positives},"train_count":len(train_dataset),"tune_count":len(tune_dataset),
        "train_features_sha256":sha256_file(args.features),"tune_features_sha256":sha256_file(args.tune_features),
        "split_hash":config.dataset.manifest_hash,"preprocessing_hash":config.preprocessing.cache_hash,
        "checkpoint_revision":config.model.revision,"seed":config.training.seed,
        "rng_algorithms":{"python":"MT19937","numpy":"MT19937","torch":"default"},
        "input_length_max":max(train_dataset.max_input_length,tune_dataset.max_input_length),
        "class_weights":class_weights,"actual_precision":precision,"backend":"eager",
        "optimizer_steps":engine.optimizer_steps,"elapsed_training_seconds":elapsed,
        "selection":fit_result,"hardware":hardware,"environment_hash":object_hash(environment)})
    append_jsonl(run_dir/'events.jsonl',{'status':'complete','utc':datetime.now(timezone.utc).isoformat()})
    atomic_write_json(run_dir / "status.json", {"status": "complete", "run_id": run_id, "scientific_evaluation": "not_run"})
    checksums={str(path.relative_to(run_dir)).replace('\\','/'):sha256_file(path) for path in sorted(run_dir.rglob('*')) if path.is_file() and path.name!='artifact_checksums.json'}
    atomic_write_json(run_dir/'artifact_checksums.json',checksums)
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
