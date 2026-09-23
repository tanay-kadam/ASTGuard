import json
import random

import pytest

from astguard.analysis.subgroups import subgroup_comparison

SEEDS = [42, 123, 456]


def _population(parsed=160, failed=80):
    features, labels = {}, {}
    for index in range(parsed + failed):
        sample = f"s{index}"
        ok = index < parsed
        features[sample] = {"sample_id": sample, "ast_status": "ok" if ok else "parse_failed",
                            "dfg_status": "ok" if ok and index % 4 else "unsupported",
                            "component_id": f"c{index // 2}", "language_selected": "c" if index % 3 else "cpp"}
        labels[sample] = index % 2
    return features, labels


def _predictions(labels, score):
    return {seed: {s: {"sample_id": s, "label": y, "probability": score(seed, s, y)} for s, y in labels.items()}
            for seed in SEEDS}


def _noise(seed, sample):
    return random.Random(f"{seed}-{sample}").random()


def test_identical_models_give_zero_differences():
    features, labels = _population()
    predictions = _predictions(labels, lambda seed, s, y: _noise(seed, s))
    report = subgroup_comparison(sorted(labels), features, predictions, predictions, replicates=50)
    for entry in report["subgroups"].values():
        assert entry["mean_difference"] == 0
        if entry["inferential_eligible"]:
            assert entry["hierarchical_interval_95"] == [0.0, 0.0]


def test_gain_confined_to_parsed_functions_shows_only_in_parsed_subgroup():
    features, labels = _population()
    left = _predictions(labels, lambda seed, s, y: (0.5 + 0.5 * y) if features[s]["ast_status"] == "ok"
                        else _noise(seed, s))
    right = _predictions(labels, lambda seed, s, y: _noise(seed, s))
    report = subgroup_comparison(sorted(labels), features, left, right, replicates=100)
    parsed, failed = report["subgroups"]["S_parsed"], report["subgroups"]["S_failed"]
    assert parsed["inferential_eligible"] and parsed["mean_difference"] > 0.3
    assert parsed["hierarchical_interval_95"][0] > 0
    assert failed["mean_difference"] == 0
    assert parsed["count"] + failed["count"] == report["population"]


def test_small_subgroup_is_descriptive_only():
    features, labels = _population(parsed=200, failed=20)
    predictions = _predictions(labels, lambda seed, s, y: _noise(seed, s))
    report = subgroup_comparison(sorted(labels), features, predictions, predictions, replicates=50)
    failed = report["subgroups"]["S_failed"]
    assert failed["positives"] < 30 and not failed["inferential_eligible"]
    assert failed["hierarchical_interval_95"] is None and failed["seed_t_interval_95"] is None


def test_requires_two_seeds_and_complete_features():
    features, labels = _population()
    one = {42: _predictions(labels, lambda seed, s, y: y)[42]}
    with pytest.raises(ValueError):
        subgroup_comparison(sorted(labels), features, one, one)
    predictions = _predictions(labels, lambda seed, s, y: y)
    del features["s0"]
    with pytest.raises(ValueError):
        subgroup_comparison(sorted(labels), features, predictions, predictions)


def test_cli_writes_secondary_descriptive_report(tmp_path):
    from scripts.subgroup_analysis import main
    features, labels = _population()
    left = _predictions(labels, lambda seed, s, y: _noise(seed, s))
    paths = {}
    for side in ("left", "right"):
        paths[side] = []
        for seed in SEEDS:
            path = tmp_path / f"{side}-{seed}.json"
            path.write_text(json.dumps([row | {"seed": seed} for row in left[seed].values()]), encoding="utf-8")
            paths[side].append(str(path))
    feature_path = tmp_path / "features.jsonl"
    feature_path.write_text("\n".join(json.dumps(row) for row in features.values()), encoding="utf-8")
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps([{"name": "astguard_vs_sequence", **paths}]), encoding="utf-8")
    output = tmp_path / "subgroups.json"
    main(["--plan", str(plan), "--features", str(feature_path), "--replicates", "20", "--output", str(output)])
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["role"] == "secondary_descriptive" and report["protocol_revision"] == "R1"
    text = json.dumps(report)
    assert "p_value" not in text and "holm" not in text and "_p\"" not in text
