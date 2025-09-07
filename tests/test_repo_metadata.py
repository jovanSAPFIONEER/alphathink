import importlib
import unittest


class RepoMetadataTest(unittest.TestCase):
    def test_entry_points_exist(self):
        # Validate CLI entry points import
        importlib.import_module("quickcapture.cli")
        importlib.import_module("alpha_evolve.cli")

    def test_versions_import(self):
        importlib.import_module("quickcapture.version")
        importlib.import_module("alpha_evolve.version")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()