from __future__ import annotations

import random

from scripts.generate_topology_positive_control import generate_split, validate_rows


def test_positive_control_is_paired_balanced_degree_matched_and_split_disjoint():
    seen = set()
    rng = random.Random(20261006)
    train = generate_split("train", 8, rng, seen)
    tune = generate_split("tune", 4, rng, seen)
    validate_rows(train, tune)
    assert len(train) == 16
    assert len(tune) == 8
    assert {row["label"] for row in train} == {0, 1}


def test_sequence_inputs_are_identical_within_opposite_label_pairs():
    rows = generate_split("train", 3, random.Random(7), set())
    for index in range(0, len(rows), 2):
        left, right = rows[index:index + 2]
        assert left["input_ids"] == right["input_ids"]
        assert {left["label"], right["label"]} == {0, 1}
        assert left["ast_token_edges"] != right["ast_token_edges"]

