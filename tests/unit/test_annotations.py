import unittest

from astguard.parsing.annotations import mask_annotation_macros
from astguard.parsing.lexical import lex
from astguard.parsing.lowering import extract_dependencies
from astguard.parsing.trees import select_c_or_cpp

KERNEL = 'static long f(char __user *buf, int n)\n{\n\tint k = n;\n\tk = k + n;\n\treturn k;\n}\n'


class AnnotationMaskingTests(unittest.TestCase):
    def test_masks_identifiers_only_and_preserves_offsets(self):
        source = 'int __init g(void) { const char *s = "__user"; /* __force */ return 0; }'
        masked, ids = mask_annotation_macros(source, lex(source))
        self.assertEqual(len(masked.encode('utf-8')), len(source.encode('utf-8')))
        self.assertNotIn('__init', masked)
        self.assertIn('"__user"', masked)
        self.assertIn('/* __force */', masked)
        self.assertEqual(len(ids), 1)

    def test_offsets_preserved_with_multibyte_text(self):
        source = 'int f(char __user *p) { /* é */ return 0; }'
        masked, _ = mask_annotation_macros(source, lex(source))
        self.assertEqual(len(masked.encode('utf-8')), len(source.encode('utf-8')))
        self.assertEqual(masked.index('é'), source.index('é'))

    def test_none_mode_is_identity(self):
        self.assertEqual(mask_annotation_macros(KERNEL, lex(KERNEL), 'none'), (KERNEL, []))

    def test_rejects_unknown_mode(self):
        with self.assertRaises(ValueError):
            mask_annotation_macros(KERNEL, lex(KERNEL), 'pilot_derived')

    def test_kernel_annotation_parses_and_dependencies_align_to_original_tokens(self):
        tokens = lex(KERNEL)
        self.assertFalse(select_c_or_cpp(KERNEL, 'c').successful)
        masked, ids = mask_annotation_macros(KERNEL, tokens)
        tree = select_c_or_cpp(masked, 'c')
        self.assertTrue(tree.successful)
        extraction = extract_dependencies(masked, tree, tokens)
        self.assertEqual(extraction.status, 'ok')
        self.assertTrue(extraction.edges)
        endpoints = {endpoint for edge in extraction.edges for endpoint in edge}
        self.assertFalse(endpoints.intersection(ids))


if __name__ == '__main__':
    unittest.main()
