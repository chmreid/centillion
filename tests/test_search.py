import unittest
import datetime
from unittest import mock
from whoosh.fields import Schema

# from centillion.config import Config
from centillion.search import Search
from centillion.doctypes.doctype import Doctype
from centillion.doctypes.registry import DoctypeRegistry

from .context import TempCentillionConfig
from .util_configs import (
    get_plain_config,
    get_invalid_ghfile_config,
)
from .util_searchdocs import (
    get_plain_doc,
    get_ghfile_doc,
)


class SearchTest(unittest.TestCase):
    """
    Check the Search class works as intended
    """

    def test_constructor(self):
        """Test the construction of a Search object"""
        with TempCentillionConfig(get_plain_config()):
            # We did not specify any doctypes, so the schema
            # should match the common schema exactly.
            s = Search()
            # Returns the schema stored in the search index
            search_schema = s.get_schema()
            # Returns the schema common to all doctypes (common schema)
            common_schema = Schema(**Doctype.get_common_schema())
            # These should be equal, since get_plain_config() does not specify any doctypes
            self.assertEqual(common_schema, search_schema)

    def test_crud_plain_doc(self):
        """
        Test the ability to create/read/update/delete a plain document (a doc whose schema is the common schema)
        in a centillion search index.
        """
        doctype = "plain"
        doctype_cls = DoctypeRegistry.REGISTRY['plain']

        docs = []
        for j in range(1, 5):
            doc = get_plain_doc(j)
            doctype_cls.register_document(doc)

        docs = [get_plain_doc(j) for j in range(4)]

        # Temp config file context manager must wrap all subtests
        with TempCentillionConfig(get_plain_config()):
            s = Search()

            with self.subTest("Test CREATE plain docs"):
                # Common schema
                for doc in docs:
                    s.add_doc(doc)

            with self.subTest("Test READ plain docs"):
                # Call get_local_map and verify all is ok
                loc_map = s.get_local_map(doctype)
                self.assertGreater(len(loc_map), 0)
                for map_key, map_val in loc_map.items():
                    self.assertEqual(type(map_key), str)
                    self.assertEqual(type(map_val), datetime.datetime)

            with self.subTest("Test UPDATE plain docs"):
                pass

            with self.subTest("Test DELETE plain docs"):
                pass

    def test_get_local_map(self):
        """Test the get_local_map method of the Search class"""
        doctype = "github_file"
        docs = [get_ghfile_doc(j) for j in range(4)]

        # Create a Search object
        with TempCentillionConfig(get_invalid_ghfile_config()):
            with mock.patch("centillion.doctypes.github.GithubFileDoctype.validate_credentials"):
                s = Search()

                # Add fake docs to the index
                for doc in docs:
                    s.add_doc(doc)

                # Call get_local_map and verify all is ok
                loc_map = s.get_local_map(doctype)
                self.assertGreater(len(loc_map), 0)
                for map_key, map_val in loc_map.items():
                    self.assertEqual(type(map_key), str)
                    self.assertEqual(type(map_val), datetime.datetime)


if __name__ == "__main__":
    unittest.main()
