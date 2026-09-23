import unittest

from astguard.data.audit import LeakageAuditor
from astguard.data.schema import make_sample
from astguard.data.splits import SplitBuilder, component_fraction


def sample(index, split, source, **metadata):
    return make_sample(dataset="x", release="1", original_split=split, source=source, label=index % 2,
                       original_row_index=index, original_id=str(index), **metadata)


class AuditSplitTests(unittest.TestCase):
    def test_clone_and_metadata_components(self):
        rows = [sample(0,"train","int f(){ return 0; }"), sample(1,"test","int f ( ) { /*x*/ return 0 ; }"),
                sample(2,"train","int g(){return 1;}",cve_ids=["CVE-X"]), sample(3,"valid","int h(){return 2;}",cve_ids=["CVE-X"]),
                sample(4,"train","int z(){return 9;}")]
        components, evidence = LeakageAuditor().build_components(rows)
        self.assertEqual(components[rows[0].sample_id], components[rows[1].sample_id])
        self.assertEqual(components[rows[2].sample_id], components[rows[3].sample_id])
        manifest = SplitBuilder().freeze(rows, components, evidence)
        roles = dict(zip(manifest.ordered_sample_ids, manifest.roles))
        self.assertEqual(roles[rows[1].sample_id], "test")
        self.assertNotIn(rows[0].sample_id, roles)
        self.assertNotIn(rows[2].sample_id, roles)

    def test_missing_metadata_does_not_group(self):
        rows = [sample(0,"train","int a;"), sample(1,"train","int b;")]
        components, _ = LeakageAuditor().build_components(rows)
        self.assertNotEqual(components[rows[0].sample_id], components[rows[1].sample_id])

    def test_fraction_is_nested(self):
        components = [f"c{i}" for i in range(100)]
        low = {x for x in components if component_fraction(x,.1)}
        high = {x for x in components if component_fraction(x,.5)}
        self.assertLessEqual(low, high)

    def test_transfer_excludes_every_primevul_split(self):
        prime = make_sample(dataset='primevul', release='original', original_split='test',
                            source='int f(){return 1;}', label=1, original_row_index=0)
        shared = make_sample(dataset='diversevul', release='standalone', original_split='transfer',
                             source='int f(){return 1;}', label=0, original_row_index=0)
        independent = make_sample(dataset='diversevul', release='standalone', original_split='transfer',
                                  source='int g(){return 2;}', label=1, original_row_index=1)
        rows = [prime, shared, independent]
        components, evidence = LeakageAuditor().build_components(rows)
        manifest = SplitBuilder().freeze(rows, components, evidence, view='D_transfer')
        self.assertEqual(manifest.roles, ['transfer'])
        self.assertEqual(manifest.ordered_sample_ids, [independent.sample_id])
        self.assertEqual(manifest.exclusion_reasons[shared.sample_id], 'component_intersects_any_primevul_split')

    def test_project_partition_keeps_project_together(self):
        rows = [sample(0,'train','int a(){return 1;}',project_id='foo'),
                sample(1,'test','int b(){return 2;}',project_id='foo'),
                sample(2,'valid','int c(){return 3;}',project_id=None)]
        components, evidence = LeakageAuditor().build_components(rows)
        manifest = SplitBuilder().freeze(rows, components, evidence, view='P_project')
        self.assertEqual(len(manifest.roles), 2)
        self.assertEqual(len(set(manifest.roles)), 1)
        self.assertEqual(manifest.exclusion_reasons[rows[2].sample_id], 'unknown_project')

    def test_cross_dataset_project_commit_link_without_repo_url(self):
        first = make_sample(dataset='primevul', release='original', original_split='train',
                            source='int first(){return 1;}', label=1, original_row_index=0,
                            project_id='Linux', commit_id='ABC123')
        second = make_sample(dataset='diversevul', release='standalone', original_split='transfer',
                             source='int second(){return 2;}', label=0, original_row_index=0,
                             project_id='linux', commit_id='abc123')
        components, evidence = LeakageAuditor().build_components([first, second])
        self.assertEqual(components[first.sample_id], components[second.sample_id])
        self.assertTrue(any(item.kind == 'repository_commit' for item in evidence))


if __name__ == "__main__": unittest.main()
