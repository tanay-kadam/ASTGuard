"""Finite experiment recipe resolution and dependency-aware execution."""
import dataclasses
import json
from pathlib import Path
from astguard.config import load_config,_construct,_deep_merge,ExperimentConfig
from astguard.utils.hashing import object_hash

CORE={'sequence_only','ast_dfg_fixed','astguard'}
LAYERS={'early':[0,1,2,3],'middle':[4,5,6,7],'late':[8,9,10,11],'distributed':[2,5,8,11],'all':list(range(12))}


def job_overrides(job):
    experiment,model,stage=job['experiment_id'],job['model_id'],job['stage']
    suffix=job['job_id'].split(f'{experiment}-{model}-{job["seed"]}-',1)[1]
    result={'experiment_id':experiment,'training':{'seed':job['seed']}}
    train=result['training']
    if stage.endswith('proxy') or stage=='development_proxy':
        result['dataset']={'train_fraction':.25}
        train.update(epochs=3,min_epochs=3)
    if 'lr' in suffix and '-m' in suffix:
        lr,mult=suffix.split('-m');train.update(pretrained_lr=float(lr[2:].replace('p','.')),new_module_lr_multiplier=int(mult))
    if model=='regvd' and suffix.startswith('ws') and '-lr' in suffix:
        window,lr=suffix.split('-lr');result['model']={'regvd_window_size':int(window[2:])}
        train.update(pretrained_lr=float(lr.replace('p','.')),new_module_lr_multiplier=1)
    if experiment=='A3':result['preprocessing']={'topology':'degree_preserving_rewired'}
    if experiment=='A5':train.update(pretrained_lr=2e-5,new_module_lr_multiplier=1)
    if experiment=='E4':
        fraction=suffix.split('fraction')[1].split('-')[0].replace('p','.')
        result['dataset']={'train_fraction':float(fraction)}
        if suffix.endswith('fixed-steps'):result['requires_full_data_step_budget']=True
    if experiment=='INPUT384':result['preprocessing']={'max_length':384}
    if experiment=='E10b':result['preprocessing']={'structural_context':'visible_prefix'}
    if experiment=='E11':result['dataset']={'view':'P_project'}
    if experiment=='E3' and suffix in LAYERS:result['model']={'structural_layers':LAYERS[suffix]}
    if experiment=='A4':
        changes={'anchored-ast':{'preprocessing':{'ast_relation':'anchored_parent_child'}},
                 'degree-normalized':{'preprocessing':{'degree_normalization':True}},
                 'dfg-symmetric':{'preprocessing':{'dfg_symmetry':True}},
                 'unweighted':{'training':{'loss':'unweighted_bce'}}}
        result=_deep_merge(result,changes[suffix])
    if experiment=='A6':
        result['model']={'freeze_beta':True} if suffix=='frozen-beta' else {'gate_sharing':suffix.split('-')[0]}
    if model=='linevul_function' and stage=='development_hpo_proxy':
        # Four cells represent the LineVul registered recipe candidates, not the
        # controlled-model new-module multiplier grid.
        key=(train['pretrained_lr'],train['new_module_lr_multiplier'])
        recipes={(1e-5,1):(2e-5,'unweighted_bce'),(1e-5,5):(1e-5,'weighted_bce'),
                 (2e-5,1):(2e-5,'weighted_bce'),(2e-5,5):(2e-5,'unweighted_bce')}
        lr,loss=recipes[key];train.update(pretrained_lr=lr,new_module_lr_multiplier=1,loss=loss)
    return result


def dependencies(job,jobs):
    model,stage,experiment=job['model_id'],job['stage'],job['experiment_id']
    if stage=='development_hpo_proxy':return []
    if stage=='development_hpo_full':
        return [x['job_id'] for x in jobs if x['model_id']==model and x['experiment_id']==experiment and x['stage']=='development_hpo_proxy']
    parent=model if model not in {'astguard_ast_only','astguard_dfg_only'} else 'astguard'
    family='A1' if model in {'fixed_adapter','linear_relation','function_gate'} else 'B_REGVD' if model=='regvd' else 'E1'
    if experiment=='A5':return []
    deps=[x['job_id'] for x in jobs if x['model_id']==parent and x['experiment_id']==family and x['stage']=='development_hpo_full']
    if experiment=='E3' and stage=='final_train':
        deps += [x['job_id'] for x in jobs if x['experiment_id']=='E3' and x['stage']=='development_proxy']
    return deps


def selected_recipe(job,jobs,state_dir):
    deps=dependencies(job,jobs)
    results=[]
    for name in deps:
        path=Path(state_dir)/(name+'.json')
        if not path.exists():raise RuntimeError(f'pending dependency: {name}')
        state=json.loads(path.read_text())
        if state['status']!='complete':raise RuntimeError(f'dependency is {state["status"]}: {name}')
        cfg=load_config(Path(state['run_dir'])/'config.resolved.yaml')
        choice=json.loads((Path(state['run_dir'])/'checkpoint_selection.json').read_text())
        results.append((choice['best_value'],cfg,name))
    if not results:return {}
    results.sort(key=lambda item:(-item[0],item[1].training.pretrained_lr,item[1].training.new_module_lr_multiplier,item[2]))
    recipe_results=[row for row in results if row[1].experiment_id!='E3' or job['experiment_id']!='E3']
    if not recipe_results:raise RuntimeError('no completed HPO recipe dependency')
    rank=int(job['job_id'].rsplit('promote',1)[1])-1 if job['stage']=='development_hpo_full' else 0
    if rank>=len(recipe_results):raise RuntimeError('not enough completed HPO candidates')
    chosen=recipe_results[rank][1]
    result={'training':{'pretrained_lr':chosen.training.pretrained_lr,'new_module_lr_multiplier':chosen.training.new_module_lr_multiplier,
                        'loss':chosen.training.loss},'provenance':{'hpo_parent':recipe_results[rank][2]}}
    if chosen.model.variant=='regvd':result['model']={'regvd_window_size':chosen.model.regvd_window_size}
    if job['experiment_id']=='E3' and job['stage']=='final_train':
        choices=[row for row in results if row[1].experiment_id=='E3' and list(row[1].model.structural_layers) not in [LAYERS['distributed'],LAYERS['all']]]
        if not choices:raise RuntimeError('no eligible non-distributed layer screening result')
        result['model']={'structural_layers':list(choices[0][1].model.structural_layers)}
    return result


def resolve_job(job,jobs,context,state_dir):
    base=dataclasses.asdict(load_config(job['config'],allow_unresolved=True))
    base=_deep_merge(base,selected_recipe(job,jobs,state_dir))
    changes=job_overrides(job)
    fixed_steps=changes.pop('requires_full_data_step_budget',False)
    base=_deep_merge(base,changes)
    base['model']['revision']=context['checkpoint_revisions'][base['model']['checkpoint']]
    if fixed_steps:base['training']['max_optimizer_steps']=context['full_data_optimizer_steps']
    fields={key:base['preprocessing'][key] for key in ['max_length','ast_relation','dfg_symmetry','structural_context','topology','annotation_masking']}
    feature_key=object_hash({'view':base['dataset']['view'],**fields})
    artifact=context['feature_registry'].get(feature_key)
    if artifact is None:raise RuntimeError(f'prepare missing feature cohort {feature_key}: {fields}')
    base['dataset']['manifest_hash']=artifact['manifest_hash']
    base['preprocessing']['cache_hash']=artifact['preprocessing_hash']
    base['provenance']['protocol_hash']=context['protocol_hash']
    base['resources']=context['resources']
    config=_construct(ExperimentConfig,base);config.validate()
    return config,artifact
