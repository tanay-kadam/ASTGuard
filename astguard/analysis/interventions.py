"""Registered intervention identifiers and validation."""

VALID_INTERVENTIONS = {"original", "training_mean", "function_mean", "degree_bin_permutation", "zero_ast", "zero_dfg"}


def validate_intervention(name: str) -> str:
    if name not in VALID_INTERVENTIONS:
        raise ValueError(f"unknown intervention {name}")
    return name


def intervene_gates(gates,relation_masks,mode,*,sample_ids,layer,seed=1001,training_mean=None):
    import torch
    from astguard.utils.hashing import sha256_text
    validate_intervention(mode)
    degrees=relation_masks.sum(-1).permute(0,2,1)
    eligible=degrees>0
    if mode=='original':return gates
    result=gates.clone()
    if mode=='training_mean':
        if training_mean is None:raise ValueError('training-fitted gate means required')
        return training_mean.to(gates.device)[None,:,None,:].expand_as(gates)
    if mode=='function_mean':
        weights=eligible[:,None].to(gates.dtype)
        means=(gates*weights).sum(2,keepdim=True)/weights.sum(2,keepdim=True).clamp_min(1)
        return means.expand_as(gates)
    if mode in {'zero_ast','zero_dfg'}:
        result[...,0 if mode=='zero_ast' else 1]=0
        return result
    boundaries=[(1,1),(2,4),(5,16),(17,float('inf'))]
    for batch,sample in enumerate(sample_ids):
        for head in range(gates.shape[1]):
            for relation in range(gates.shape[-1]):
                generator=torch.Generator(device='cpu')
                generator.manual_seed(int(sha256_text(f'{seed}|{sample}|{layer}|{head}|{relation}')[:16],16))
                for low,high in boundaries:
                    indices=torch.where((degrees[batch,:,relation]>=low)&(degrees[batch,:,relation]<=high))[0]
                    order=torch.randperm(len(indices),generator=generator).to(indices.device)
                    result[batch,head,indices,relation]=gates[batch,head,indices[order],relation]
    return result
