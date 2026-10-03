import pytest

from astguard.data.graph_donors import GraphDonorDataset, length_matched_donors, transplant_graph


def _row(sample_id, length, edges):
    return {"sample_id": sample_id, "input_ids": [0] + [5] * (length - 2) + [2],
            "attention_mask": [True] * length,
            "special_tokens_mask": [True] + [False] * (length - 2) + [True], "label": 0,
            "edge_projection_groups": [{"relation": "ast", "projected_pairs": [list(pair) for pair in edges]}],
            "ast_token_edges": [list(pair) for pair in edges], "dfg_token_edges": []}


def test_donors_are_length_matched_derangements():
    lengths = [10, 10, 10, 20, 20, 30, 30, 30, 30]
    donors, stats = length_matched_donors(lengths, seed=42)
    assert all(d != i for i, d in enumerate(donors))
    assert sorted(donors) == list(range(len(lengths)))
    assert all(lengths[i] == lengths[d] for i, d in enumerate(donors))
    assert stats["exact_length_fraction"] == 1.0
    assert donors == length_matched_donors(lengths, seed=42)[0]


def test_singleton_lengths_merge_into_neighbouring_bucket():
    lengths = [5, 6, 6, 7, 9]
    donors, stats = length_matched_donors(lengths, seed=1)
    assert all(d != i for i, d in enumerate(donors))
    assert sorted(donors) == list(range(len(lengths)))
    assert stats["exact_length_matches"] < len(lengths)


def test_single_example_is_rejected():
    with pytest.raises(ValueError):
        length_matched_donors([8], seed=0)


def test_transplant_keeps_recipient_tokens_and_drops_invalid_edges():
    recipient = _row("r", 6, [(1, 2)])
    donor = _row("d", 8, [(1, 2), (3, 4), (4, 5), (5, 6)])
    row = transplant_graph(recipient, donor)
    assert row["sample_id"] == "r" and row["input_ids"] == recipient["input_ids"]
    assert row["ast_token_edges"] == [[1, 2], [3, 4]]
    assert row["edge_projection_groups"][0]["projected_pairs"] == [[1, 2], [3, 4]]
    assert recipient["ast_token_edges"] == [[1, 2]]


def test_dataset_view_feeds_structural_collator():
    pytest.importorskip("torch")
    from astguard.data.collate import StructuralCollator
    rows = [_row("a", 6, [(1, 2)]), _row("b", 6, [(3, 4)]), _row("c", 8, [(5, 6)]), _row("d", 8, [(1, 6)])]
    view = GraphDonorDataset(rows, [len(r["input_ids"]) for r in rows], seed=7)
    items = [view[i] for i in range(len(view))]
    for i, item in enumerate(items):
        assert item["sample_id"] == rows[i]["sample_id"]
        assert item["ast_token_edges"] == rows[view.donors[i]]["ast_token_edges"]
    batch = StructuralCollator()(items)
    assert batch["relation_masks"].sum().item() == 4
