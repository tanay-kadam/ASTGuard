"""Candidate completeness matters: compare the optimized join to brute force."""
import random

from astguard.data.audit import _UnionFind
from scripts.seven_day_holdout import near_clone_join, lexical_job


def partitions(uf, ids):
    return {frozenset(other for other in ids if uf.find(other) == uf.find(sid)) for sid in ids}


def test_prefix_join_matches_brute_force_including_transitive_clones():
    rng = random.Random(123)
    info = {}
    for i in range(150):
        base = set(range((i//15)*120, (i//15)*120+100))
        values = frozenset(base-set(rng.sample(sorted(base), rng.randrange(10))))
        info[str(i)] = (105, values)
    a = _UnionFind(info); b = _UnionFind(info)
    near_clone_join(info, a)
    ids = sorted(info)
    for i, left in enumerate(ids):
        for right in ids[:i]:
            _, x = info[left]; _, y = info[right]
            if len(x & y)/len(x | y) >= .9:
                b.union(left, right)
    assert partitions(a, ids) == partitions(b, ids)


def test_fallback_does_not_collapse_unsupported_sources():
    a = lexical_job('int f(){ return \u2603; }')
    b = lexical_job('int f(){ return \u2602; }')
    assert a[3] and b[3] and a[0] != b[0]


def test_comments_do_not_change_lexical_identity():
    a = lexical_job('int f(){ return 1; }')
    b = lexical_job('int /* comment */ f(){\n return 1; }')
    assert a[:3] == b[:3]
