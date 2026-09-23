import json
import subprocess
import sys
import unittest
from pathlib import Path


class SmokeIntegrationTests(unittest.TestCase):
    def test_complete_plumbing_pipeline(self):
        scratch = Path("artifacts/test_runs")
        scratch.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([sys.executable,"scripts/run_smoke_test.py","--output-root",str(scratch)],check=True,text=True,capture_output=True)
        run = Path(json.loads(result.stdout)["run_dir"])
        self.assertTrue((run/"smoke_table.md").is_file())
        self.assertTrue((run/"smoke_figure.svg").is_file())
        self.assertEqual(json.loads((run/"status.json").read_text())["status"],"complete")


if __name__ == "__main__": unittest.main()
