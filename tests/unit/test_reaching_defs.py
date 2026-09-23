import unittest

from astguard.parsing.cfg import Event, StructuredCFG
from astguard.parsing.reaching_defs import ReachingDefinitions


class ReachingDefinitionTests(unittest.TestCase):
    def test_branch_union_and_direction(self):
        events = {0:Event(0,"noop",None,None),1:Event(1,"write","x",10),2:Event(2,"write","x",20),3:Event(3,"read","x",30)}
        cfg = StructuredCFG(events,{0:{1,2},1:{3},2:{3},3:set()},0)
        result = ReachingDefinitions().solve(cfg)
        self.assertEqual(result.dependency_edges, [(30,10),(30,20)])

    def test_loop_converges(self):
        events = {0:Event(0,"write","x",1),1:Event(1,"read","x",2),2:Event(2,"write","x",3,rhs_reads=(2,))}
        cfg = StructuredCFG(events,{0:{1},1:{2},2:{1}},0)
        result = ReachingDefinitions().solve(cfg)
        self.assertIn((2,1),result.dependency_edges)
        self.assertIn((2,3),result.dependency_edges)
        self.assertIn((3,2),result.dependency_edges)


if __name__ == "__main__": unittest.main()

