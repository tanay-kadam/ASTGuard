from __future__ import annotations

import math
from itertools import islice


def weighted_bce_logits(logits, labels, class_weights):
    import torch.nn.functional as F
    positive = class_weights[1] * labels * F.softplus(-logits)
    negative = class_weights[0] * (1 - labels) * F.softplus(logits)
    return (positive + negative).mean()


class Trainer:
    def __init__(self, model, optimizer, scheduler=None, grad_clip_norm=1.0, accumulation_steps=1, device="cpu", precision='fp32'):
        self.model, self.optimizer, self.scheduler = model, optimizer, scheduler
        self.grad_clip_norm, self.accumulation_steps, self.device = grad_clip_norm, accumulation_steps, device
        import torch
        self.autocast_dtype = torch.bfloat16 if precision in {'bf16','bf16_if_supported'} and device.startswith('cuda') and torch.cuda.is_bf16_supported() else torch.float16
        self.use_autocast = device.startswith('cuda') and precision != 'fp32'
        self.scaler = torch.amp.GradScaler('cuda', enabled=self.use_autocast and self.autocast_dtype == torch.float16)
        self.optimizer_steps = 0

    def forward(self, batch):
        if 'graph_attention_mask' in batch:
            return self.model(**{key:batch[key].to(self.device) for key in ('input_ids','position_ids','graph_attention_mask')})
        if 'relation_masks' not in batch:
            return self.model(batch['input_ids'].to(self.device),batch['attention_mask'].to(self.device))
        return self.model(batch['input_ids'].to(self.device),batch['attention_mask'].to(self.device),
                          batch['relation_masks'].to(self.device),
                          special_tokens_mask=batch['special_tokens_mask'].to(self.device))

    def train_epoch(self, loader, class_weights: dict[int, float], max_optimizer_steps: int | None = None) -> dict:
        import torch
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        total_loss, examples, steps = 0.0, 0, 0
        gradient_totals: dict[str, float] = {}
        optimizer_steps_this_epoch = 0
        iterator = iter(loader)
        while group := list(islice(iterator, self.accumulation_steps)):
            if max_optimizer_steps is not None and self.optimizer_steps >= max_optimizer_steps:
                break
            group_size = sum(len(batch['labels']) for batch in group)
            for batch in group:
                size = len(batch['labels'])
                with torch.autocast(device_type=str(self.device).split(':')[0], dtype=self.autocast_dtype, enabled=self.use_autocast):
                    outputs = self.forward(batch)
                    loss = weighted_bce_logits(outputs['logits'].float(),batch['labels'].to(self.device),class_weights)
                if not torch.isfinite(loss):
                    raise FloatingPointError('nonfinite training loss')
                self.scaler.scale(loss * size / group_size).backward()
                total_loss += float(loss.detach()) * size
                examples += size
                steps += 1
            self.scaler.unscale_(self.optimizer)
            total_gradient_norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip_norm, error_if_nonfinite=True)
            gradient_totals["all_parameters"] = gradient_totals.get("all_parameters", 0.0) + float(total_gradient_norm)
            for name, parameter in self.model.named_parameters():
                if parameter.grad is not None and (".gate." in name or name.endswith(".beta")):
                    gradient_totals[name] = gradient_totals.get(name, 0.0) + float(parameter.grad.detach().float().norm())
            old_scale = self.scaler.get_scale()
            self.scaler.step(self.optimizer)
            self.scaler.update()
            if self.scheduler is not None and self.scaler.get_scale() >= old_scale:
                self.scheduler.step()
            self.optimizer.zero_grad(set_to_none=True)
            self.optimizer_steps += 1
            optimizer_steps_this_epoch += 1
        gradient_norms = {name: value/max(1,optimizer_steps_this_epoch) for name,value in gradient_totals.items()}
        return {'loss': total_loss/max(1,examples), 'examples':examples, 'microbatches':steps,
                'optimizer_steps':self.optimizer_steps, 'gradient_norms':gradient_norms}

    def predict(self, loader):
        import torch
        self.model.eval()
        result = []
        with torch.no_grad():
            for batch in loader:
                logits = self.forward(batch)['logits'].float().cpu()
                if not torch.isfinite(logits).all():
                    raise FloatingPointError('nonfinite inference logits')
                for sample_id, label, logit, probability in zip(batch['sample_ids'],batch['labels'],logits,logits.sigmoid()):
                    result.append({'sample_id':sample_id,'label':int(label),'logit':float(logit),'probability':float(probability)})
        return result

    def fit(self, train_loader, tune_loader, class_weights, config, run_dir, config_hash, resume=None):
        from pathlib import Path
        from safetensors.torch import save_model, load_model
        from astguard.evaluation.metrics import average_precision
        from astguard.training.checkpoint import save_resume_checkpoint, load_resume_checkpoint
        from astguard.utils.atomic_io import atomic_write_json, append_jsonl
        run_dir = Path(run_dir)
        checkpoints = run_dir/'checkpoints'
        checkpoints.mkdir(parents=True,exist_ok=True)
        start, best, stale, selected_epoch = 0, -1., 0, None
        if resume:
            state = load_resume_checkpoint(resume,model=self.model,optimizer=self.optimizer,scheduler=self.scheduler,
                                           scaler=self.scaler,expected_config_hash=config_hash)
            start,best = state['epoch'],state['best_metric']
            self.optimizer_steps = state['step']
            extra = state.get('extra',{})
            stale,selected_epoch = extra.get('patience',0),extra.get('selected_epoch')
            if extra.get('loader_rng') is not None:
                train_loader.generator.set_state(extra['loader_rng'])
            if hasattr(train_loader.collate_fn,'presentation_counts'):
                train_loader.collate_fn.presentation_counts = extra.get('augmentation_counts',{})
        steps_per_epoch=math.ceil(len(train_loader)/self.accumulation_steps)
        final_epoch=config.epochs if config.max_optimizer_steps is None else max(config.epochs,math.ceil(config.max_optimizer_steps/max(1,steps_per_epoch)))
        history=[]
        history_path=run_dir/'validation_history.parquet'
        if resume and history_path.exists():
            import pyarrow.parquet as pq
            history=pq.read_table(history_path).to_pylist()
        for epoch in range(start,final_epoch):
            train_loader.collate_fn.epoch = epoch
            log = self.train_epoch(train_loader,class_weights,max_optimizer_steps=config.max_optimizer_steps)
            predictions = self.predict(tune_loader)
            ap = average_precision([x['label'] for x in predictions],[x['probability'] for x in predictions])
            if ap is None:
                raise ValueError('V_tune must contain both classes')
            significant = ap > best + config.min_delta
            if ap > best:
                best,selected_epoch = ap,epoch+1
                temporary=checkpoints/'best.safetensors.partial'
                save_model(self.model,str(temporary))
                temporary.replace(checkpoints/'best.safetensors')
            stale = 0 if significant else stale+1
            history_row={'epoch':epoch+1,'tune_ap':ap,**log};history.append(history_row)
            append_jsonl(run_dir/'train_log.jsonl',history_row)
            save_resume_checkpoint(checkpoints/'last_resume.pt', model=self.model,optimizer=self.optimizer,
                scheduler=self.scheduler,scaler=self.scaler,epoch=epoch+1,step=self.optimizer_steps,
                best_metric=best,config_hash=config_hash,extra={'patience':stale,'selected_epoch':selected_epoch,
                    'loader_rng':train_loader.generator.get_state(),'augmentation_counts':getattr(train_loader.collate_fn,'presentation_counts',{})})
            if config.max_optimizer_steps is not None and self.optimizer_steps>=config.max_optimizer_steps:
                break
            if config.max_optimizer_steps is None and epoch+1 >= config.min_epochs and stale >= config.patience:
                break
        load_model(self.model,str(checkpoints/'best.safetensors'))
        if history:
            import pyarrow as pa
            import pyarrow.parquet as pq
            temporary=history_path.with_suffix('.parquet.partial')
            pq.write_table(pa.Table.from_pylist(history),temporary)
            temporary.replace(history_path)
        atomic_write_json(run_dir/'checkpoint_selection.json',{'role':'tune','metric':'average_precision','best_value':best,'epoch':selected_epoch})
        return {'best_tune_ap':best,'selected_epoch':selected_epoch}
