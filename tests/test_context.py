import os
import unittest

from .context import TempCentillionConfig


logger = logging.getLogger(__name__)


def get_simple_config():
    return {
        "doctypes": [],
    }


class TestTempCentillionConfig(unittest.TestCase):
    """
    Test the temporary centillion config context manager
    """
    def test_context_createonce(self):
        cnfg = get_simple_config()
        cnfg_file = None
        cnfg_dir = None
        with TempCentillionConfig(cnfg) as cnfg_file:
            cnfg_dir = os.path.dirname(cnfg_file)
            self.assertTrue(os.path.exists(cnfg_file))
            self.assertTrue(os.path.isdir(cnfg_dir))
        self.assertFalse(os.path.exists(cnfg_file))
        self.assertFalse(os.path.isdir(os.path.dirname(cnfg_file)))

    def test_context_createmany(self):
        cnfg = get_simple_config()
        cnfg_file = None
        cnfg_dir = None
        for i in range(3):
            with TempCentillionConfig(cnfg) as cnfg_file:
                cnfg_dir = os.path.dirname(cnfg_file)
                self.assertTrue(os.path.exists(cnfg_file))
                self.assertTrue(os.path.isdir(cnfg_dir))
            self.assertFalse(os.path.exists(cnfg_file))
            self.assertFalse(os.path.isdir(os.path.dirname(cnfg_file)))


if __name__ == "__main__":
    unittest.main()
