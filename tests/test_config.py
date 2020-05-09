import os
import unittest

from centillion.error import CentillionConfigException
from centillion.config import Config, TMPDIR_NAME

from .context import TempCentillionConfig


logger = logging.getLogger(__name__)


def get_config_multiple_doctypes():
    doctype_list = [
        "gdrive_docx",
        "gdrive_file",
        "github_issues_prs",
    ]
    doctype_list.sort()
    doctype_config = {
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
    return doctype_list, doctype_config


class ConfigTest(unittest.TestCase):

    def test_config_class_construction(self):
        """
        Test the constructors of the Config class
        """
        # Use an empty configuration dict
        with TempCentillionConfig(dict()) as temp_config_file:
            # Check that the constructor set the config file properly
            self.assertEqual(Config._CONFIG_FILE, temp_config_file)
            # Check the get_config_file() method works
            self.assertEqual(Config.get_config_file(), temp_config_file)

    def test_config_class_path_vars(self):
        """
        Test configuration variables related to paths and directories
        - root directory
        - temporary directory
        - index directory
        """
        # To test out defaults, we use an empty configuration
        root_dir = None
        indx_dir = None
        temp_dir = None
        with TempCentillionConfig(dict()) as temp_config_file:
            # centillion root:
            # this must already exist beforehand
            # (handled here by the TempCentillionConfig context manager)
            root_dir = os.path.dirname(temp_config_file)
            self.assertEqual(Config.get_centillion_root(), root_dir)

            # centillion index dir:
            # accessing the variable should create the directory
            indx_dir = os.path.join(root_dir, 'index')
            self.assertFalse(os.path.isdir(indx_dir))
            self.assertEqual(Config.get_centillion_indexdir(), indx_dir)
            self.assertTrue(os.path.isdir(indx_dir))

            # centillion temp dir:
            # accessing the variable should create the directory
            temp_dir = os.path.join(root_dir, TMPDIR_NAME)
            self.assertFalse(os.path.isdir(temp_dir))
            self.assertEqual(Config.get_centillion_tmpdir(), temp_dir)
            self.assertTrue(os.path.isdir(temp_dir))

        # Once we close the temporary config context, those directories should be gone
        self.assertFalse(os.path.isdir(root_dir))

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
        Check the ability to access environment variables in the Config class
        """
        temp_config = dict()
        with TempCentillionConfig(temp_config):
            var = "CENTILLION_TEST_FOO"
            os.environ[var] = "BAR"
            self.assertEqual(Config.get_required_env_var(var), "BAR")
            del os.environ[var]
            with self.assertRaises(CentillionConfigException):
                Config.get_required_env_var(var)

    def test_config_class_get_doctypes(self):
        """
        Check the ability to get a list of active doctypes in the config file
        """
        doctypes, temp_config = get_config_multiple_doctypes()
        with TempCentillionConfig(temp_config):
            config_doctypes = Config.get_doctypes()
            self.assertEqual(doctypes, config_doctypes)

    def test_config_class_get_doctype_configs(self):
        """
        Check the abiltiy to get the configuration section for a particular doctype
        """
        doctypes, temp_config = get_config_multiple_doctypes()
        with TempCentillionConfig(temp_config):
            for doctype_config_entry in temp_config['doctypes']:
                name = doctype_config_entry['name']
                doctype_config = Config.get_doctype_config(name)
                self.assertEqual(doctype_config_entry, doctype_config)


if __name__ == "__main__":
    unittest.main()
