import unittest

from centillion.config import Config
from centillion.doctypes.gdrive import (
    GDriveBaseDoctype,
    GDriveFileDoctype,
    GDriveDocxDoctype,
    get_gdrive_service
)

from .decorators import standalone_test, integration_test
from .mixins import SchemaTestMixin


# List of Github doctypes (excluding base type)
# (Integration tests should include one credential per doctype in this list in config file)
GDRIVE_DOCTYPES = ["gdrive_file", "gdrive_docx"]


@integration_test
class GetGDriveServiceTest(unittest.TestCase):
    """
    Test the get_gdrive_service() method
    """

    def test_get_gdrive_service(self):
        # Note: integration test decorator will set the config file to real values
        doctypes_names_map = Config.get_doctypes_names_map()
        names = []
        # Collect names of credentials that correspond to GDrive doctypes
        for doctype, nameslist in doctypes_names_map.items():
            if doctype in GDRIVE_DOCTYPES:
                names.append(*nameslist)
        # Now create a GDrive service for each credential
        for name in names:
            conf = Config.get_doctype_config(name)
            token_path = conf['token_path']
            get_gdrive_service(token_path)


@standalone_test
class GDriveDoctypeStandaloneTest(SchemaTestMixin):
    """
    Test some basic standalone methods of GDrive doctype classes
    """

    @classmethod
    def setUpClass(cls):
        # Get list of doctypes actually in config file
        cls.doctypes_names_map = Config.get_doctypes_names_map()

    def test_doctypes(self):
        self.assertEqual(GDriveBaseDoctype.doctype, "gdrive_base")
        self.assertEqual(GDriveFileDoctype.doctype, "gdrive_file")
        self.assertEqual(GDriveDocxDoctype.doctype, "gdrive_docx")

    def test_consistent_schemas(self):
        """Test that all GDrive document type schemas are consistent with one another"""
        self._check_consistent_schemas(GDRIVE_DOCTYPES)


@integration_test
class GDriveDoctypeIntegrationTest(unittest.TestCase):
    pass
