import os
import shutil
# import json
# import tempfile
# import subprocess
import unittest

from centillion.error import CentillionConfigException
from centillion.config import Config, TMPDIR_NAME

from .context import TempCentillionConfig


class ConfigTest(unittest.TestCase):

    @classmethod
    def setUp(self):
        pass

    @classmethod
    def tearDown(self):
        pass

    def test_config_class_construction(self):
        """
        Test the constructors of the Config class
        """
        temp_config = dict()
        with TempCentillionConfig(temp_config) as temp_config_file:
            # Check that the constructor set the config file properly
            self.assertEqual(Config._CONFIG_FILE, temp_config_file)
            self.assertEqual(Config.get_config_file(), temp_config_file)

    def test_config_class_path_vars(self):
        """
        Test path variables in the Config class
        """
        temp_config = dict()
        with TempCentillionConfig(temp_config) as temp_config_file:
            # get_centillion_root
            centillion_root_dir = os.path.dirname(temp_config_file)
            self.assertEqual(Config.get_centillion_root(), centillion_root_dir)
            # get_centillion_tmpdir
            centillion_temp_dir = os.path.join(centillion_root_dir, TMPDIR_NAME)
            self.assertEqual(Config.get_centillion_tmpdir(), centillion_temp_dir)
            # Accessing the tmpdir location creates it, so verify it was created and clean up
            self.assertTrue(os.path.isdir(centillion_temp_dir))
            shutil.rmtree(centillion_temp_dir)

    '''
    def test_config_class_required_vars(self):
        """
        Check the ability to access required variables in the config file
        """
        test_config = {"hello": "world", "foo": ["bar", "baz", "wuz"]}
        self.write_config(json.dumps(test_config))
        Config(self.path)
        # hello var (str)
        self.assertEqual(Config._CONFIG["hello"], test_config["hello"])
        self.assertEqual(Config.get_required_config_var("hello"), test_config["hello"])
        # foo var (list)
        self.assertEqual(Config._CONFIG["foo"], test_config["foo"])
        self.assertEqual(Config.get_required_config_var("foo"), test_config["foo"])
        # non-existent var
        with self.assertRaises(CentillionConfigException):
            Config.get_required_config_var("error-nonsense-value")
    '''

    def test_config_class_env_vars(self):
        """
        Check the ability to access environment variables in the config file
        """
        temp_config = dict()
        with TempCentillionConfig(temp_config):
            os.environ["FOO"] = "BAR"
            self.assertEqual(Config.get_required_env_var("FOO"), "BAR")
            del os.environ["FOO"]
            with self.assertRaises(CentillionConfigException):
                Config.get_required_env_var("FOO")

    '''
    def test_config_class_get_doctypes(self):
        """
        Check the ability to get a list of active doctypes in the config file
        """
        test_config = {
            "doctypes": [
                {"name": "foo", "doctype": "gdrive_file", "token_path": "credentials.json"},
                {"name": "foo_docx", "doctype": "gdrive_docx", "token_path": "credentials.json"},
                {
                    "name": "foobar",
                    "doctype": "github_issues_prs",
                    "application_token": "XXX",
                    "orgs": ["baz"],
                    "repos": ["foobar/fuzwuz", "foobar/wuznuz"],
                },
            ]
        }
        self.write_config(json.dumps(test_config))
        Config(self.path)
        # Check that doctypes list is returned
        doctypes = ["gdrive_file", "gdrive_docx", "github_issues_prs"]
        self.assertEqual(Config.get_doctypes(), doctypes)
        # Check that doctypes config section is returned
        for d in doctypes:
            name = d["name"]
            config = Config.get_doctypes_config(name)
            self.assertDictEqual(config, d)
        with self.assertRaises(CentillionConfigException):
            Config.get_doctypes_config("non-existent-config")
    '''


if __name__ == "__main__":
    unittest.main()
