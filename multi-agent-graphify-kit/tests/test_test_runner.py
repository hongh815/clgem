import subprocess
import sys
import unittest
from pathlib import Path


class TestRunnerTests(unittest.TestCase):
    def test_local_runner_adds_src_path_and_runs_selected_tests(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(root / "scripts" / "run_tests.py"), "--pattern", "test_contracts.py"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = result.stdout + result.stderr
        self.assertRegex(output, r"Ran [1-9][0-9]* tests")
        self.assertIn("test_task_accepts_review_tree_hash", output)


if __name__ == "__main__":
    unittest.main()
