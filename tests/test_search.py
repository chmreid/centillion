import os
import unittest
import typing
import datetime
from unittest import mock
import tempfile
from whoosh.fields import Schema

from centillion.config import Config
from centillion.search import Search
from centillion.doctypes.doctype import Doctype

from . import (
    TempCentillionConfig,
    get_plain_config,
    get_invalid_ghfile_config,
    get_plain_doc,
    get_ghfile_doc,
)


class SearchTest(unittest.TestCase):
    """
    Check the Search class works as intended
    """

    def test_constructor(self):
        """Test the construction of a Search object"""
        with TempCentillionConfig(get_plain_config()) as config_file:
            # We did not specify any doctypes, so the schema
            # should match the common schema exactly.
            s = Search()
            search_schema = s.get_schema()
            common_schema = Schema(**Doctype.get_common_schema())
            self.assertEqual(common_schema, search_schema)

    def test_add_plain_doc(self):
        """Test the ability to add a plain document to the search index"""
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
        with TempCentillionConfig(get_invalid_ghfile_config()) as config_file:
            with mock.patch("centillion.doctypes.github.GithubFileDoctype.validate_credentials"):
                s = Search()

                # Add fake docs to the index
                s.add_doc(get_ghfile_doc(0))
                s.add_doc(get_ghfile_doc(1))
                s.add_doc(get_ghfile_doc(2))
                s.add_doc(get_ghfile_doc(3))

                # Call get_local_map and verify all is ok
                m = s.get_local_map(doctype)
                self.assertGreater(len(m), 0)


if __name__ == "__main__":
    unittest.main()
