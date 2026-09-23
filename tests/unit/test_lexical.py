import unittest

from astguard.parsing.lexical import char_to_byte_map, lex, lexical_fingerprint


class LexicalTests(unittest.TestCase):
    def test_comments_and_whitespace_removed_but_strings_preserved(self):
        left, values = lexical_fingerprint('char *s = "a b"; /* comment */ return s;')
        right, _ = lexical_fingerprint('char*s="a b";return s; // later')
        self.assertEqual(left, right)
        self.assertIn('string:"a b"', values)

    def test_utf8_byte_offsets(self):
        tokens = lex('char *s="é";')
        string = next(token for token in tokens if token.kind == "string")
        self.assertGreater(string.end_byte - string.start_byte, string.end_char - string.start_char)
        self.assertEqual(char_to_byte_map("é"), [0, 2])


if __name__ == "__main__": unittest.main()

