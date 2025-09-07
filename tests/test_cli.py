import subprocess
import sys
import unittest


class CLITestCase(unittest.TestCase):
    def test_help_runs(self):
        proc = subprocess.run(
            [sys.executable, "-m", "quickcapture", "--help"], capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("quickcapture", proc.stdout.lower())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
