import unittest

from astguard.analysis.robustness import (corrupt_feature, delete_edge_groups,
                                          rewire_directed_edges, swap_directed_edges)
from astguard.parsing.dfg import ConservativeDFGExtractor
from astguard.parsing.lexical import lex


class DFGAndRobustnessTests(unittest.TestCase):
    def test_straight_line_dependencies(self):
        extraction = ConservativeDFGExtractor().extract(lex("int f(int x){ int y = x; y = x; return y; }"))
        self.assertEqual(extraction.status,"ok")
        self.assertTrue(extraction.edges)

    def test_control_fails_closed(self):
        extraction = ConservativeDFGExtractor().extract(lex("int f(int x){ if(x) return 1; return 0; }"))
        self.assertEqual(extraction.status,"unsupported_control")
        self.assertEqual(extraction.edges,())

    def test_nested_deletion(self):
        edges=[(i,i+1) for i in range(10)]
        low=set(delete_edge_groups(edges,.2,sample_id="x",relation="dfg",seed=1))
        high=set(delete_edge_groups(edges,.5,sample_id="x",relation="dfg",seed=1))
        self.assertLessEqual(high,low)

    def test_feature_corruption_reprojects_from_lexical_edges(self):
        feature = {
            "sample_id": "x", "lexical_ast_edges": [(0, 1), (1, 0)],
            "lexical_dfg_edges": [(1, 0)], "ast_leaf_to_bpe": {0: [1], 1: [2]},
            "leaf_to_bpe": {0: [1], 1: [2]}, "ast_token_edges": [(1, 2), (2, 1)],
            "dfg_token_edges": [(2, 1)],
            "edge_projection_groups": [
                {"relation": "ast", "projected_pairs": [(1, 2), (2, 1)]},
                {"relation": "dfg", "projected_pairs": [(2, 1)]},
            ],
        }
        changed, diagnostics = corrupt_feature(feature, operation="delete", relation="both", rate=1, seed=1)
        self.assertEqual(changed["ast_token_edges"], [])
        self.assertEqual(changed["dfg_token_edges"], [])
        self.assertEqual(diagnostics["ast"]["achieved_rate"], 1)
        self.assertEqual(diagnostics["dfg"]["achieved_rate"], 1)
        self.assertTrue(feature["ast_token_edges"], "input must remain immutable")

    def test_ast_deletion_operates_on_undirected_groups(self):
        feature = {
            "sample_id":"x","lexical_ast_edges":[(0,1),(1,0),(2,3),(3,2)],
            "lexical_dfg_edges":[],"ast_leaf_to_bpe":{0:[1],1:[2],2:[3],3:[4]},
            "leaf_to_bpe":{},"ast_token_edges":[],"dfg_token_edges":[],"edge_projection_groups":[],
        }
        changed,diagnostics=corrupt_feature(feature,operation="delete",relation="ast",rate=.5,seed=4)
        assert len(changed["lexical_ast_edges"])==2
        assert set(changed["lexical_ast_edges"])=={(b,a) for a,b in changed["lexical_ast_edges"]}
        assert diagnostics["ast"]["achieved_rate"]==.5

    def test_a3_rewiring_uses_successful_swap_budget_and_preserves_degrees(self):
        edges=[(0,1),(2,3),(4,5),(6,7)]
        changed=rewire_directed_edges(edges,sample_id="x",relation="dfg",seed=1001,
                                      successful_swap_factor=1,max_attempt_factor=100)
        self.assertLessEqual(changed["successful_swaps"],changed["successful_swap_goal"])
        self.assertEqual(Counter(a for a,b in edges),Counter(a for a,b in changed["edges"]))
        self.assertEqual(Counter(b for a,b in edges),Counter(b for a,b in changed["edges"]))


if __name__ == "__main__": unittest.main()
from collections import Counter

from astguard.analysis.robustness import swap_symmetric_edges


def test_symmetric_rewiring_preserves_degrees_and_symmetry():
    undirected = {(0, 2), (1, 3), (4, 6), (5, 7)}
    edges = [(a,b) for a,b in undirected] + [(b,a) for a,b in undirected]
    result = swap_symmetric_edges(edges, 1.0, sample_id='x', relation='ast', seed=42)
    before = Counter(a for a,b in edges)
    after = Counter(a for a,b in result['edges'])
    assert before == after
    assert set(result['edges']) == {(b,a) for a,b in result['edges']}
    assert len(result['edges']) == len(edges)
