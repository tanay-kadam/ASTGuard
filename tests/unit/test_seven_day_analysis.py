import numpy as np
import pytest
from sklearn.metrics import average_precision_score
from scripts.seven_day_analysis import sorted_ap_inputs, weighted_ap, paired_analysis


def test_weighted_ap_equals_expanded_cluster_resample_with_ties_and_zero_weights():
    rng = np.random.default_rng(42)
    for _ in range(20):
        labels = np.array([0, 1]*20)
        scores = rng.integers(0, 5, 40)
        weights = rng.integers(0, 4, 40)
        indices = np.repeat(np.arange(40), weights)
        assert weighted_ap(sorted_ap_inputs(labels, scores), weights) == pytest.approx(
            average_precision_score(labels[indices], scores[indices]), abs=1e-12)


def test_paired_identical_predictions_have_zero_intervals():
    y = [0, 1]*20
    values = {seed: [.2, .8]*20 for seed in [42, 123, 456, 789, 2026]}
    result = paired_analysis(y, values, values, [str(i//2) for i in range(40)], replicates=30)
    assert result['mean_difference'] == 0
    assert result['component_interval_95'] == [0, 0]
    assert result['seed_t_interval_95'] == [0, 0]
    assert not result['all_positive_mean_at_least_0_02']
