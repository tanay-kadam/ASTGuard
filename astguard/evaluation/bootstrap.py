from __future__ import annotations

import random
from collections import defaultdict
from typing import Callable, Sequence


class ClusterBootstrap:
    def hierarchical(self, labels, left_by_seed, right_by_seed, components, *, replicates=10000, seed=20260921, confidence=.975):
        import numpy as np
        from scipy.stats import t
        from astguard.evaluation.metrics import average_precision
        seeds=sorted(set(left_by_seed)&set(right_by_seed))
        if len(seeds)<2:raise ValueError('at least two paired training seeds are required')
        labels=np.asarray(labels,dtype=int)
        groups=defaultdict(list)
        for index,component in enumerate(components):groups[component].append(index)
        keys=sorted(groups)
        if any(len(left_by_seed[s])!=len(labels) or len(right_by_seed[s])!=len(labels) for s in seeds):
            raise ValueError('predictions do not align with label population')
        def difference(s,indices):
            y=labels[indices].tolist()
            a=average_precision(y,np.asarray(left_by_seed[s])[indices].tolist())
            b=average_precision(y,np.asarray(right_by_seed[s])[indices].tolist())
            return None if a is None or b is None else a-b
        all_indices=np.arange(len(labels))
        seed_effects=[difference(s,all_indices) for s in seeds]
        if any(x is None for x in seed_effects):raise ValueError('population missing a class')
        rng=np.random.default_rng(seed)
        hierarchical,conditional=[],[]
        invalid=0
        for _ in range(replicates):
            draws=rng.integers(0,len(keys),len(keys))
            indices=np.array([i for draw in draws for i in groups[keys[draw]]])
            effects=[difference(s,indices) for s in seeds]
            if any(x is None for x in effects):invalid+=1;continue
            conditional.append(float(np.mean(effects)))
            sampled_seeds=rng.integers(0,len(seeds),len(seeds))
            hierarchical.append(float(np.mean(np.asarray(effects)[sampled_seeds])))
        alpha=1-confidence
        def interval(values,level=confidence):
            return np.quantile(values,[(1-level)/2,1-(1-level)/2]).tolist() if values else None
        mean=float(np.mean(seed_effects));sd=float(np.std(seed_effects,ddof=1))
        half=float(t.ppf(1-alpha/2,len(seeds)-1)*sd/len(seeds)**.5)
        t_interval=[mean-half,mean+half]
        allowed=len(keys)>=20 and invalid/replicates<=.01
        ci=interval(hierarchical)
        return {'paired_seeds':seeds,'seed_effects':seed_effects,'mean_difference':mean,'sample_sd':sd,
            'hierarchical_interval':ci,'component_only_interval':interval(conditional),'seed_t_interval':t_interval,
            'equivalence_interval_90':interval(hierarchical,.90),'confidence':confidence,'cluster_count':len(keys),
            'invalid_replicates':invalid,'replicates':replicates,'confirmatory_eligible':allowed,
            'strong_positive':bool(allowed and mean>=.01 and ci and ci[0]>0 and t_interval[0]>0),
            'bootstrap_effects':hierarchical,'component_only_effects':conditional}

    def compare(
        self, labels: Sequence[int], left: Sequence[float], right: Sequence[float],
        components: Sequence[str], metric: Callable[[Sequence[int], Sequence[float]], float | None],
        replicates: int = 10000, seed: int = 20260921,
    ) -> dict:
        if not (len(labels) == len(left) == len(right) == len(components)):
            raise ValueError("paired bootstrap arrays must align")
        groups: dict[str, list[int]] = defaultdict(list)
        for index, component in enumerate(components):
            groups[component].append(index)
        keys = sorted(groups)
        if len(keys) < 2:
            return {"estimate": None, "interval": None, "reason": "fewer_than_two_clusters"}
        rng = random.Random(seed)
        values: list[float] = []
        invalid = 0
        for _ in range(replicates):
            sampled = [rng.choice(keys) for _ in keys]
            indices = [index for key in sampled for index in groups[key]]
            y = [labels[i] for i in indices]
            a = metric(y, [left[i] for i in indices])
            b = metric(y, [right[i] for i in indices])
            if a is None or b is None:
                invalid += 1
            else:
                values.append(a - b)
        if not values:
            return {"estimate": None, "interval": None, "invalid_replicates": invalid}
        values.sort()
        def quantile(q: float) -> float:
            return values[min(len(values) - 1, int(q * len(values)))]
        estimate_left = metric(labels, left)
        estimate_right = metric(labels, right)
        return {
            "estimate": None if estimate_left is None or estimate_right is None else estimate_left - estimate_right,
            "interval": [quantile(.025), quantile(.975)], "replicates": replicates,
            "invalid_replicates": invalid, "cluster_count": len(keys),
            'confirmatory_eligible':len(keys)>=20 and invalid/replicates<=.01,
        }


def holm_adjust(p_values):
    ordered=sorted(enumerate(p_values),key=lambda x:x[1])
    adjusted=[0.]*len(p_values);previous=0.
    for rank,(index,p) in enumerate(ordered):
        previous=max(previous,min(1.,(len(p_values)-rank)*p));adjusted[index]=previous
    return adjusted
