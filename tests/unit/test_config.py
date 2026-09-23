import dataclasses
import unittest

from astguard.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_inheritance_and_unresolved_guard(self):
        cfg = load_config("configs/models/sequence_only.yaml", allow_unresolved=True)
        self.assertEqual(cfg.model.variant,"sequence_only")
        self.assertEqual(cfg.model.relations,())
        with self.assertRaises(ConfigError):
            load_config("configs/models/sequence_only.yaml")


if __name__ == "__main__": unittest.main()

