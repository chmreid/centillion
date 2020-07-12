import unittest
import typing
import logging

from centillion.config import Config
from centillion.error import CentillionConfigException
from centillion.doctypes.doctype import Doctype
from centillion.doctypes.gdrive import (
    GDriveBaseDoctype,
    GDriveFileDoctype,
    GDriveDocxDoctype,
    get_gdrive_service,
)

from .decorators import integration_test, standalone_test
from .mixins import IntegrationTestMixin, ConstructorTestMixin, SchemaTestMixin, RemoteListTestMixin


logger = logging.getLogger(__name__)

# List of Github doctypes (excluding base type)
# (Integration tests should include one credential per doctype in this list in config file)
GDRIVE_DOCTYPES = ["gdrive_file", "gdrive_docx"]


class FindTokenPathTest(unittest.TestCase):
    pass


class GetGDriveServiceTest(IntegrationTestMixin):
    """
    Test the get_gdrive_service() method with valid and invalid credentials.
    """

    @integration_test
    def test_get_gdrive_service(self):
        """Test the get_gdrive_service() with valid (integration test) credentials"""
        doctypes_names_map = Config.get_doctypes_names_map()
        names = []
        # Collect names of credentials that correspond to GDrive doctypes
        for doctype, nameslist in doctypes_names_map.items():
            if doctype in GDRIVE_DOCTYPES:
                names.append(*nameslist)
        # Now create a GDrive service for each credential
        for name in names:
            conf = Config.get_doctype_config(name)
            token_path = conf["token_path"]
            get_gdrive_service(token_path)

    @standalone_test
    def test_get_gdrive_service_invalid_credentials(self):
        """Test the get_gdrive_service() with invalid (standalone test) credentials"""
        doctypes_names_map = Config.get_doctypes_names_map()
        names = []
        # Collect names of credentials that correspond to GDrive doctypes
        for doctype, nameslist in doctypes_names_map.items():
            if doctype in GDRIVE_DOCTYPES:
                names.append(*nameslist)
        # Now assert that creating a GDrive service for any will fail
        for name in names:
            conf = Config.get_doctype_config(name)
            token_path = conf["token_path"]
            with self.assertRaises(CentillionConfigException):
                get_gdrive_service(token_path)


class GDriveDoctypeTest(
    IntegrationTestMixin, ConstructorTestMixin, SchemaTestMixin, RemoteListTestMixin
):
    """
    Test Google Drive doctypes.
    """

    def test_doctype_names(self):
        """Test the doctype attribute of each GDrive doctype"""
        self.assertEqual(GDriveBaseDoctype.doctype, "gdrive_base")
        self.assertEqual(GDriveFileDoctype.doctype, "gdrive_file")
        self.assertEqual(GDriveDocxDoctype.doctype, "gdrive_docx")

    def test_consistent_schemas(self):
        """Test that all GDrive document type schemas are consistent with one another"""
        self.check_consistent_schemas(GDRIVE_DOCTYPES)

    def test_gdrive_base_doctype(self):
        """Test the GDriveBaseDoctype constructor, mocking the Google Drive API creation/credentials validation step"""
        # Just call the constructor of GDriveBaseDoctype
        pass

    @integration_test
    def test_gdrive_doctype_constructors(self):
        """Test the constructor of each GDrive doctype with (real) integration credentials"""
        doctypes_names_map = Config.get_doctypes_names_map()
        self.check_doctype_constructors(GDRIVE_DOCTYPES, doctypes_names_map)

    @integration_test
    def test_gdrive_doctype_constructors_invalid_params(self):
        # Check that invalid inputs to constructor will not work
        registry = Doctype.get_registry()
        doctypes_names_map = Config.get_doctypes_names_map()
        for doctype, names in doctypes_names_map.items():
            if doctype in GDRIVE_DOCTYPES:
                junkargs = ['foo', 'bar', 1000000]
                junkkwargs = {'a': 10, 'b': 20}
                doctype_cls = registry[doctype]
                with self.assertRaises(TypeError):
                    # TypeError due to junk inputs
                    doctype_cls(*junkargs, **junkkwargs)

    def test_render_search_result(self):
        # Mock whoosh search result
        # extends dict so you can do ['asdf']
        pass

    def test_render_search_result_invalid(self):
        # Test invalid inputs to render search result
        pass

    def test_get_jinja_template(self):
        """Test the Jinja template returned by each Github doctype"""
        # Turn a list of doctype labels into a list of doctype classes
        doctype_classes = self._get_gdrive_doctype_classes()
        required_strings = ['<div class="url">', '<div class="markdown-body">']
        for required_string in required_strings:
            for DoctypeCls in doctype_classes:
                self.assertIn(required_string, DoctypeCls.get_jinja_template())

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
    def test_get_remote_map(self):
        doctypes_names_map = Config.get_doctypes_names_map()
        self.check_doctype_remote_map(GDRIVE_DOCTYPES, doctypes_names_map)

    @integration_test
    def test_gdrive_files_get_by_id(self):
        """Test the get_by_id methods for GDrive files"""
        this_doctype = "gdrive_file"

        # Get a doctype class instance using real credentials
        doctypes_names_map = Config.get_doctypes_names_map()
        names = doctypes_names_map[this_doctype]
        name = names[0]
        doctype = GDriveFileDoctype(name)

        # Test a real file
        file_id = "1MB-IgywX9YZVw2fIib_fzvUagUkt1o4c"
        doctype.get_by_id(file_id)

    @integration_test
    def test_gdrive_docx_get_by_id(self):
        """Test the get_by_id methods for GDrive docx documents"""
        this_doctype = "gdrive_docx"

        # Get a doctype class instance using real credentials
        doctypes_names_map = Config.get_doctypes_names_map()
        names = doctypes_names_map[this_doctype]
        name = names[0]
        doctype = GDriveFileDoctype(name)

        # Test a real file
        docx_id = "1pjk3c79lBN3pTW1kNHvwlYR8_24g7Zdhu4efbt-b7c8"
        doctype.get_by_id(docx_id)

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
