import unittest
import typing

from centillion.config import Config
from centillion.doctypes.doctype import Doctype
from centillion.doctypes.gdrive import (
    GDriveBaseDoctype,
    GDriveFileDoctype,
    GDriveDocxDoctype,
    get_gdrive_service
)

from .decorators import standalone_test, integration_test
from .mixins import (ConstructorTestMixin, SchemaTestMixin, RemoteListTestMixin)


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


class GDriveDoctypeTest(ConstructorTestMixin, SchemaTestMixin, RemoteListTestMixin):
    """
    Test Google Drive doctypes.
    """

    @standalone_test
    def test_doctypes(self):
        """Test the doctype attribute of each GDrive doctype"""
        self.assertEqual(GDriveBaseDoctype.doctype, "gdrive_base")
        self.assertEqual(GDriveFileDoctype.doctype, "gdrive_file")
        self.assertEqual(GDriveDocxDoctype.doctype, "gdrive_docx")

    @standalone_test
    def test_consistent_schemas(self):
        """Test that all GDrive document type schemas are consistent with one another"""
        self.check_consistent_schemas(GDRIVE_DOCTYPES)

    @standalone_test
    def test_gdrive_base_doctype(self):
        """Test the GDriveBaseDoctype constructor, mocking the Google Drive API creation/credentials validation step"""
        # with mock.patch("centillion.doctypes.github.Github") as gh:
        #     GithubBaseDoctype(name)
        pass

    @integration_test
    def test_gdrive_doctype_constructors(self):
        """Test the constructor of each GDrive doctype with (real) integration credentials"""
        doctypes_names_map = Config.get_doctypes_names_map()
        for doctype, names in doctypes_names_map.items():
            if doctype in GDRIVE_DOCTYPES:
                GDriveBaseDoctype(name)

    @standalone_test
    def test_render_search_result(self):
        # Mock whoosh search result
        # extends dict so you can do ['asdf']
        pass

    @standalone_test
    def test_get_jinja_template(self):
        """Test the Jinja template returned by each Github doctype"""
        # Turn a list of doctype labels into a list of doctype classes
        doctype_classes = self._get_gdrive_doctype_classes()
        required_strings = ['<div class="url">', '<div class="markdown-body">']
        for required_string in required_strings:
            for DoctypeCls in doctype_classes:
                self.assertIn(required_string, DoctypeCls.get_jinja_template())

    @standalone_test
    def test_render_matches_jinja(self):
        """
        Confirm that the SearchResult object resulting from render_search_result is consistent
        with the variables used in the Jinja template.
        """
        # Create a doctype instance for each registered doctype
        # Get the jinja2schema from that doctype
        # Use jinja2schema to extract jinja variables used in template
        # For each attribute of search_result,
        # Check that SearchResult has that attribute
        pass

    @integration_test
    def test_get_remote_list(self):
        doctypes_names_map = Config.get_doctypes_names_map()
        registry = Doctype.get_registry()

        for doctype, names in doctypes_names_map.items():
            name = names[0]
            DoctypeCls = registry[doctype]
            dt = DoctypeCls(name)
            remote_list = dt.get_remote_list()
            self.assertTrue(len(remote_list) > 0)

    @integration_test
    def test_gdrive_file(self):
        """Test the get_by_id (and get_schema) methods for the GDrive file doctype"""
        # Get a doc id, and look it up
        pass

    @integration_test
    def test_gdrive_docx(self):
        """Test the get_by_id (and get_schema) methods for the GDrive docx doctype"""
        # Get a doc id, and look it up
        pass

    def _get_gdrive_doctype_classes(self) -> typing.List[typing.Any]:
        """
        Given a list of strings of doctype classes, turn those into
        references to the actual class using the Doctype Registry.
        """
        doctype_classes = []
        registry = Doctype.get_registry()
        for doctype in GDRIVE_DOCTYPES:
            doctype_classes.append(registry[doctype])
        return doctype_classes
