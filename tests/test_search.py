import unittest
from unittest import mock
from whoosh.fields import Schema

# from centillion.config import Config
from centillion.search import Search
from centillion.doctypes.doctype import Doctype

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

    def test_add_plain_doc(self):
        """Test the ability to add a plain document to the search index"""
        with TempCentillionConfig(get_plain_config()):
            # Common schema
            # s = Search()
            docs = [get_plain_doc(j) for j in range(4)]
            self.assertTrue(len(docs) > 0)

        # assert doc not in search index
        # add doc to search index
        # assert doc is in search index
        pass

    def test_delete_plain_doc(self):
        # (add doc to search index)
        # assert doc is in search index
        # delete doc to search index
        # assert doc not in search index
        pass

    def test_get_local_map(self):
        """Test the get_local_map method of the Search class"""
        doctype = "github_file"

        # Create a Search object
        with TempCentillionConfig(get_invalid_ghfile_config()):
            with mock.patch("centillion.doctypes.github.GithubFileDoctype.validate_credentials"):
                s = Search()

                # Add fake docs to the index
                docs = [get_ghfile_doc(j) for j in range(4)]
                for doc in docs:
                    s.add_doc(doc)

                # Call get_local_map and verify all is ok
                loc_map = s.get_local_map(doctype)
                self.assertGreater(len(loc_map), 0)
                for map_key, map_value in loc_map.items():
                    self.assertEqual(type(map_key), str)


if __name__ == "__main__":
    unittest.main()
