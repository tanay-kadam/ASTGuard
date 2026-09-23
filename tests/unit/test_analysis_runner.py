import pytest
from pathlib import Path

from astguard.analysis.aggregate import ResultAggregator
from astguard.analysis.runner import failure_strata, gate_report, pair_report, trapezoidal_area
from astguard.utils.atomic_io import atomic_write_json
from scripts.build_pr_pair_rows import build_rows


def _prediction(sample, label, probability, decision):
    return {"sample_id": sample, "label": label, "probability": probability,
            "logit": probability, "decisions": {"max_f1": decision}}


def test_pair_report_uses_saved_decisions_and_reports_incomplete_pairs():
    predictions = [_prediction("v", 1, .9, True), _prediction("p", 0, .1, False)]
    pairs = [{"pair_id": "one", "vulnerable_id": "v", "patched_id": "p"},
             {"pair_id": "missing", "vulnerable_id": "v", "patched_id": "absent"}]
    report = pair_report(predictions, pairs)
    threshold = next(row for row in report if row["threshold_name"] == "max_f1")
    ranking = next(row for row in report if row["threshold_name"] == "ranking_only")
    assert threshold["PC"] == 1
    assert threshold["incomplete_pair_count"] == 1
    assert ranking["pair_order"] == 1


def test_failure_strata_and_gate_statistics_are_data_derived():
    predictions = [_prediction("a", 1, .8, True), _prediction("b", 0, .2, False)]
    features = [
        {"sample_id": "a", "original_bpe_length": 100, "ast_status": "ok", "dfg_status": "ok",
         "ast_leaf_to_bpe": {"0": [1]}, "leaf_to_bpe": {"0": [1]},
         "lexical_ast_edges": [], "lexical_dfg_edges": []},
        {"sample_id": "b", "original_bpe_length": 200, "ast_status": "ok", "dfg_status": "failed",
         "ast_leaf_to_bpe": {"0": [1]}, "leaf_to_bpe": {"0": [1]},
         "lexical_ast_edges": [], "lexical_dfg_edges": []},
    ]
    strata = failure_strata(predictions, features)
    assert {row["stratum"] for row in strata if row["dimension"] == "length"} == {"<=128", "129-256"}
    gates = gate_report([{"layer": 2, "head": 0, "relation": "ast", "gate": .2, "degree": 0},
                         {"layer": 2, "head": 0, "relation": "ast", "gate": .8, "degree": 1}])
    assert gates[0]["eligible_count"] == 1
    assert gates[0]["mean"] == .8


def test_trapezoidal_area_deduplicates_x_by_averaging():
    result = trapezoidal_area([(0, 1), (.5, .8), (.5, .6), (1, .2)])
    assert result["points"] == [(0.0, 1.0), (0.5, .7), (1.0, .2)]
    assert abs(result["area"] - .65) < 1e-12


def test_aggregator_enforces_identical_populations_and_tracks_file_hashes():
    root=Path(__file__).resolve().parents[1]/"fixtures"
    output=Path(__file__).resolve().parents[2]/"artifacts"/"test"/"aggregate.json"
    left=root/"aggregate_left.json";right=root/"aggregate_right.json"
    result=ResultAggregator().aggregate_predictions([left,right],output)
    assert all(len(row["prediction_hashes"])==1 for row in result)
    with pytest.raises(ValueError,match="populations"):
        ResultAggregator().aggregate_predictions([left,root/"aggregate_bad_population.json"],output)


def test_f3_rows_are_derived_from_predictions_and_registered_pairs():
    root=Path(__file__).resolve().parents[2]/"artifacts"/"test"
    predictions=root/"f3_predictions.json";pairs=root/"f3_pairs.json"
    common={"model_id":"model","seed":42,"split_hash":"split","role":"test"}
    atomic_write_json(predictions,[
        common|{"sample_id":"patched","label":0,"probability":.2,"logit":-1.4},
        common|{"sample_id":"vulnerable","label":1,"probability":.8,"logit":1.4},
    ])
    atomic_write_json(pairs,[{"pair_id":"pair","vulnerable_id":"vulnerable","patched_id":"patched"}])
    pr,margins,provenance=build_rows([predictions],pairs)
    assert pr[0]["model_id"]=="model" and len(pr)==3
    assert margins==[{"model_id":"model","seed":42,"pair_id":"pair","logit_margin":2.8,
                      "correct_order":True,"split_hash":"split","role":"test"}]
    assert provenance["pairs"]["sha256"]
