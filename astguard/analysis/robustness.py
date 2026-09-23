from __future__ import annotations

import random
import copy

from astguard.utils.hashing import sha256_text


def delete_edge_groups(edges: list[tuple[int,int]], rate: float, *, sample_id: str, relation: str, seed: int) -> list[tuple[int,int]]:
    if not 0 <= rate <= 1:
        raise ValueError("rate must be in [0,1]")
    ranked = sorted(set(edges), key=lambda edge: sha256_text(f"delete-v1|{seed}|{sample_id}|{relation}|{edge[0]}|{edge[1]}"))
    removed = set(ranked[:int(round(rate * len(ranked)))])
    return sorted(edge for edge in set(edges) if edge not in removed)


def swap_directed_edges(edges: list[tuple[int,int]], target_rate: float, *, sample_id: str, relation: str, seed: int, max_attempt_factor: int = 100) -> dict:
    if not 0<=target_rate<=1:raise ValueError('invalid corruption rate')
    original, current = set(edges), set(edges)
    rng = random.Random(int(sha256_text(f"swap-v1|{seed}|{sample_id}|{relation}")[:16],16))
    edge_list, attempts = sorted(original), 0
    while edge_list and len(original-current) < target_rate*len(original) and attempts < max_attempt_factor*len(original):
        attempts += 1
        if len(edge_list) < 2: break
        first, second = rng.sample(edge_list,2)
        a,b=first; c,d=second
        def distance_bin(x,y):
            distance=abs(x-y)
            return 0 if distance<=4 else 1 if distance<=16 else 2 if distance<=64 else 3
        if distance_bin(a,b)!=distance_bin(a,d) or distance_bin(c,d)!=distance_bin(c,b):continue
        proposed={(a,d),(c,b)}
        if a==d or c==b or proposed & current: continue
        current.discard(first); current.discard(second); current |= proposed; edge_list=sorted(current)
    achieved=len(original-current)/len(original) if original else 0.0
    return {"edges":sorted(current),"requested_rate":target_rate,"achieved_rate":achieved,"attempts":attempts,"target_attained":achieved>=target_rate}


def swap_symmetric_edges(edges: list[tuple[int,int]], target_rate: float, *, sample_id: str, relation: str, seed: int, max_attempt_factor: int = 100) -> dict:
    """Degree-preserving double-edge swaps for an undirected token relation."""
    if not 0 <= target_rate <= 1:
        raise ValueError('invalid corruption rate')
    original = {tuple(sorted((a,b))) for a,b in edges if a != b}
    current = set(original)
    rng = random.Random(int(sha256_text(f'symmetric-swap-v1|{seed}|{sample_id}|{relation}')[:16], 16))
    attempts = 0
    while len(current) >= 2 and len(original-current) < target_rate*len(original) and attempts < max_attempt_factor*len(original):
        attempts += 1
        (a,b),(c,d) = rng.sample(sorted(current),2)
        # Only disjoint endpoints can make a nontrivial simple-graph swap.
        if len({a,b,c,d}) != 4:
            continue
        if rng.randrange(2):
            c,d = d,c
        def distance_bin(x, y):
            distance = abs(x-y)
            return 0 if distance <= 4 else 1 if distance <= 16 else 2 if distance <= 64 else 3
        if distance_bin(a,b) != distance_bin(a,d) or distance_bin(c,d) != distance_bin(c,b):
            continue
        proposal = {tuple(sorted((a,d))),tuple(sorted((c,b)))}
        if len(proposal) != 2 or proposal & current:
            continue
        current.difference_update({(a,b),tuple(sorted((c,d)))})
        current.update(proposal)
    directed = sorted({edge for a,b in current for edge in ((a,b),(b,a))})
    achieved = len(original-current)/len(original) if original else 0.0
    return {'edges':directed,'requested_rate':target_rate,'achieved_rate':achieved,
            'attempts':attempts,'target_attained':achieved >= target_rate}


def rewire_directed_edges(edges: list[tuple[int,int]], *, sample_id: str, relation: str, seed: int,
                          successful_swap_factor: int = 10, max_attempt_factor: int = 100) -> dict:
    """A3 fixed mixing budget: 10E successful double swaps or 100E attempts."""
    original=set(edges);current=set(original)
    rng=random.Random(int(sha256_text(f"rewire-v1|{seed}|{sample_id}|{relation}")[:16],16))
    attempts=successes=0;goal=successful_swap_factor*len(original)
    def distance_bin(x,y):
        distance=abs(x-y);return 0 if distance<=4 else 1 if distance<=16 else 2 if distance<=64 else 3
    while len(current)>=2 and successes<goal and attempts<max_attempt_factor*len(original):
        attempts+=1;(a,b),(c,d)=rng.sample(sorted(current),2)
        if distance_bin(a,b)!=distance_bin(a,d) or distance_bin(c,d)!=distance_bin(c,b):continue
        proposed={(a,d),(c,b)}
        if a==d or c==b or len(proposed)!=2 or proposed&current:continue
        current.difference_update({(a,b),(c,d)});current.update(proposed);successes+=1
    achieved=len(original-current)/len(original) if original else 0.
    return {'edges':sorted(current),'achieved_rate':achieved,'attempts':attempts,'successful_swaps':successes,
            'successful_swap_goal':goal,'target_attained':successes>=goal}


def rewire_symmetric_edges(edges: list[tuple[int,int]], *, sample_id: str, relation: str, seed: int,
                           successful_swap_factor: int = 10, max_attempt_factor: int = 100) -> dict:
    original={tuple(sorted(edge)) for edge in edges if edge[0]!=edge[1]};current=set(original)
    rng=random.Random(int(sha256_text(f"symmetric-rewire-v1|{seed}|{sample_id}|{relation}")[:16],16))
    attempts=successes=0;goal=successful_swap_factor*len(original)
    def distance_bin(x,y):
        distance=abs(x-y);return 0 if distance<=4 else 1 if distance<=16 else 2 if distance<=64 else 3
    while len(current)>=2 and successes<goal and attempts<max_attempt_factor*len(original):
        attempts+=1;(a,b),(c,d)=rng.sample(sorted(current),2)
        if len({a,b,c,d})!=4:continue
        if rng.randrange(2):c,d=d,c
        if distance_bin(a,b)!=distance_bin(a,d) or distance_bin(c,d)!=distance_bin(c,b):continue
        proposed={tuple(sorted((a,d))),tuple(sorted((c,b)))}
        if len(proposed)!=2 or proposed&current:continue
        current.difference_update({tuple(sorted((a,b))),tuple(sorted((c,d)))})
        current.update(proposed);successes+=1
    achieved=len(original-current)/len(original) if original else 0.
    directed=sorted({edge for a,b in current for edge in ((a,b),(b,a))})
    return {'edges':directed,'achieved_rate':achieved,'attempts':attempts,'successful_swaps':successes,
            'successful_swap_goal':goal,'target_attained':successes>=goal}


def corrupt_feature(feature: dict, *, operation: str, relation: str, rate: float, seed: int) -> tuple[dict,dict]:
    """Apply an E7 corruption to frozen lexical edges and reproject it."""
    if operation not in {'delete','swap'} or relation not in {'ast','dfg','both'}:
        raise ValueError('unknown robustness condition')
    from astguard.alignment.projection import RelationProjector
    result=copy.deepcopy(feature);diagnostics={}
    for name in ('ast','dfg'):
        if relation not in {name,'both'}:continue
        field='lexical_ast_edges' if name=='ast' else 'lexical_dfg_edges'
        edges=[tuple(edge) for edge in feature.get(field,[])]
        if operation=='delete':
            if name=='ast':
                groups=sorted({tuple(sorted(edge)) for edge in edges if edge[0]!=edge[1]})
                retained=delete_edge_groups(groups,rate,sample_id=feature['sample_id'],relation=name,seed=seed)
                changed=sorted({directed for left,right in retained for directed in ((left,right),(right,left))})
                achieved=1-len(retained)/len(groups) if groups else 0.
            else:
                changed=delete_edge_groups(edges,rate,sample_id=feature['sample_id'],relation=name,seed=seed)
                achieved=1-len(changed)/len(set(edges)) if edges else 0.
            detail={'requested_rate':rate,'achieved_rate':achieved,'attempts':0,'target_attained':True}
        elif name=='ast':
            detail=swap_symmetric_edges(edges,rate,sample_id=feature['sample_id'],relation=name,seed=seed);changed=detail['edges']
        else:
            detail=swap_directed_edges(edges,rate,sample_id=feature['sample_id'],relation=name,seed=seed);changed=detail['edges']
        mapping=feature.get('ast_leaf_to_bpe',{}) if name=='ast' else feature.get('leaf_to_bpe',{})
        mapping={int(key):value for key,value in mapping.items()}
        projected,groups=RelationProjector().project(changed,mapping,symmetric=name=='ast')
        for group in groups:group['relation']=name
        result[field]=changed;result[name+'_token_edges']=projected
        result['edge_projection_groups']=[g for g in result.get('edge_projection_groups',[]) if g.get('relation')!=name]+groups
        detail['original_edge_count']=len({tuple(sorted(edge)) for edge in edges}) if name=='ast' else len(set(edges))
        diagnostics[name]=detail
    return result,diagnostics
