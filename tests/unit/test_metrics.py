import math
import unittest

from astguard.evaluation.metrics import average_precision, evaluate_scores
from astguard.evaluation.pairs import evaluate_pairs
from astguard.evaluation.thresholds import ThresholdSelector


class MetricTests(unittest.TestCase):
    def test_known_ap_and_ties(self):
        self.assertAlmostEqual(average_precision([1,0,1],[.9,.8,.7]), (1 + 2/3)/2)
        self.assertAlmostEqual(average_precision([1,0],[.5,.5]), .5)
        self.assertIsNone(average_precision([0,0],[.2,.1]))

    def test_threshold_fit_only_cal_and_infinity(self):
        selector = ThresholdSelector()
        with self.assertRaises(ValueError):
            selector.fit(["a","b"],[0,1],[.1,.9],role="test",checkpoint_hash="x")
        result = selector.fit(["a","b","c","d"],[0,0,1,1],[.8,.7,.6,.5],role="cal",checkpoint_hash="x")
        self.assertIn("fpr_0.005", result)
        self.assertEqual(result["fpr_0.005"].threshold, "+infinity")

    def test_pair_outcomes_sum(self):
        result = evaluate_pairs([{"pair_id":"p","vulnerable_score":.8,"patched_score":.2}],.5)
        self.assertEqual(result["PC"],1)
        self.assertAlmostEqual(sum(result[x] for x in ("PC","PV","PB","PR")),1)


if __name__ == "__main__": unittest.main()

