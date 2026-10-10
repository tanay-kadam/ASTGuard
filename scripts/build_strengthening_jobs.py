"""Materialize the frozen matrix with runtime-identified preprocessing hashes."""
import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astguard.config import load_config,dump_config
from astguard.utils.atomic_io import atomic_write_json,atomic_write_text
from astguard.utils.hashing import sha256_file

ROOT=Path('artifacts/release_gates/strengthening_20261006')


def main():
    smoke=json.loads(Path('data/strengthening_20261006/smoke/manifest.json').read_text())
    synthetic=json.loads(Path('data/strengthening_20261006/synthetic/manifest.json').read_text())
    configs=ROOT/'configs';configs.mkdir(parents=True,exist_ok=True)
    jobs=[];protocol_hash=sha256_file('docs/SUBMISSION_STRENGTHENING_PROTOCOL_20261006.md')
    groups=[('synthetic', 'sequence', 'configs/positive_control/sequence_only.yaml',12),
            ('synthetic', 'attention_authentic','configs/structure_usage/astguard_strong_stage0fullprobe.yaml',12),
            ('synthetic', 'attention_shuffled','configs/structure_usage/astguard_strong_shuffled_stage0fullprobe.yaml',12),
            ('synthetic', 'centered_authentic','configs/positive_control/graph_adapter.yaml',12),
            ('synthetic', 'centered_shuffled','configs/positive_control/graph_adapter_shuffled.yaml',12),
            ('real','attention_sequence','configs/structure_usage/sequence_only_strong_stage0fullprobe.yaml',5),
            ('real','attention_authentic','configs/structure_usage/astguard_strong_stage0fullprobe.yaml',5),
            ('real','attention_shuffled','configs/structure_usage/astguard_strong_shuffled_stage0fullprobe.yaml',5),
            ('real','adapter_sequence','configs/structure_usage/sequence_only_adapterlr10_stage0fullprobe.yaml',3),
            ('real','adapter_uncentered','configs/structure_usage/graph_adapter_stage0fullprobe.yaml',3),
            ('real','adapter_centered','configs/structure_usage/null_centered_graph_adapter_stage0fullprobe.yaml',3)]
    for family,name,parent,epochs in groups:
        for seed in [42,123,456]:
            config=load_config(parent)
            manifest=synthetic if family=='synthetic' else smoke
            model=config.model
            if name.startswith('centered_'):
                model=dataclasses.replace(model,variant='null_centered_graph_adapter',null_graph_samples=8,null_position_blocks=1)
            if family=='synthetic':
                model=dataclasses.replace(model,relations=('ast',),beta_init=1.0,structural_layers=(2,5,8,10))
            config=dataclasses.replace(config,experiment_id='STRENGTHEN_'+family+'_'+name,
                dataset=dataclasses.replace(config.dataset,name='topology_positive_control' if family=='synthetic' else 'primevul',manifest_hash=manifest['manifest_hash']),
                preprocessing=dataclasses.replace(config.preprocessing,max_length=26 if family=='synthetic' else 512,cache_hash=manifest['preprocessing_hash']),
                model=model,training=dataclasses.replace(config.training,seed=seed,epochs=epochs,min_epochs=epochs,patience=epochs,
                    max_optimizer_steps=1536 if family=='synthetic' else None,
                    microbatch_size=32 if family=='synthetic' else 4,gradient_accumulation=1 if family=='synthetic' else 8,
                    effective_batch_size=32,loss='unweighted_bce' if family=='synthetic' else 'weighted_bce',
                    activation_checkpointing=False if family=='synthetic' else True),
                provenance=dataclasses.replace(config.provenance,protocol_hash=protocol_hash))
            if family=='synthetic':config=dataclasses.replace(config,training=dataclasses.replace(config.training,new_module_lr_multiplier=50))
            tag=f'{family}_{name}_s{seed}'
            target=configs/f'{tag}.yaml';atomic_write_text(target,dump_config(config))
            mini=dataclasses.replace(config,training=dataclasses.replace(config.training,epochs=1,min_epochs=1,patience=1,max_optimizer_steps=2,microbatch_size=4,gradient_accumulation=1,effective_batch_size=4))
            atomic_write_text(configs/f'{tag}_smoke.yaml',dump_config(mini))
            jobs.append({'tag':tag,'family':family,'condition':name,'seed':seed,'config':str(target)})
    # External jobs are prioritized before the long corrected local-model queues.
    external=[{'tag':f'regvd_{mode}_s{seed}','family':'regvd','condition':mode,'seed':seed}
              for mode in ['native','permuted','self'] for seed in [42,123,456]]
    jobs=[j for j in jobs if j['family']=='synthetic']+external+[j for j in jobs if j['family']=='real']
    assert len(jobs)==42
    atomic_write_json(ROOT/'jobs.json',{'protocol_sha256':protocol_hash,'jobs':jobs,'gpus':[5,6],'official_test_used':False})
    print('frozen jobs',len(jobs))


if __name__=='__main__':main()
