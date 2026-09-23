import unittest

from astguard.alignment.byte_spans import ByteSpanAligner, character_offsets_to_bytes
from astguard.alignment.projection import RelationProjector


class AlignmentTests(unittest.TestCase):
    def test_multibyte_conversion_and_partial_leaf(self):
        source = "éname"
        offsets = character_offsets_to_bytes(source, [(0,0),(0,1),(1,5),(0,0)])
        self.assertEqual(offsets[1], (0,2))
        mapping, eligible = ByteSpanAligner().align(offsets, [(0,6)], [True,False,False,True], retained_token_count=2)
        self.assertNotIn(0, eligible)

    def test_projection_excludes_self_and_symmetrizes(self):
        edges, groups = RelationProjector().project([(0,1)], {0:[1,2],1:[2,3]}, symmetric=True)
        self.assertNotIn((2,2), edges)
        self.assertIn((1,3), edges)
        self.assertIn((3,1), edges)


if __name__ == "__main__": unittest.main()

