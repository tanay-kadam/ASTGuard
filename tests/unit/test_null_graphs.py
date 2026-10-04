from collections import Counter

from astguard.data.collate import StructuralCollator
from astguard.data.null_graphs import MatchedNullGraphDataset, matched_null_graph


def _row():
    ast = [(1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3),
           (4, 5), (5, 4), (5, 6), (6, 5), (6, 1), (1, 6)]
    dfg = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)]
    return {"sample_id":"x","input_ids":[0,5,6,7,8,9,10,2],
            "attention_mask":[True] * 8,
            "special_tokens_mask":[True] + [False] * 6 + [True],
            "label":1,"ast_token_edges":[list(e) for e in ast],
            "dfg_token_edges":[list(e) for e in dfg]}


def _degrees(edges):
    return Counter(b for a,b in edges), Counter(a for a,b in edges)


def test_matched_nulls_preserve_degrees_and_are_deterministic():
    row = _row()
    draws = [matched_null_graph(row,seed=9,draw=i,position_blocks=1) for i in range(8)]
    assert draws[0] == matched_null_graph(row,seed=9,draw=0,position_blocks=1)
    assert any(any(detail["changed_fraction"] > 0 for detail in diagnostics)
               for _, diagnostics in draws)
    for graph, _ in draws:
        for relation in ("ast","dfg"):
            original = [tuple(e) for e in row[f"{relation}_token_edges"]]
            changed = [tuple(e) for e in graph[f"{relation}_token_edges"]]
            assert _degrees(changed) == _degrees(original)
            assert all(a not in {0,7} and b not in {0,7} for a,b in changed)


def test_dataset_and_collator_supply_multiple_null_masks():
    rows = [_row(), {**_row(), "sample_id":"y", "label":0}]
    view = MatchedNullGraphDataset(rows,seed=42,samples=3,position_blocks=1)
    batch = StructuralCollator()([view[0],view[1]])
    assert batch["relation_masks"].shape == (2,2,8,8)
    assert batch["null_relation_masks"].shape == (2,3,2,8,8)
    assert batch["null_graph_change_fractions"].shape == (2,3,2)
