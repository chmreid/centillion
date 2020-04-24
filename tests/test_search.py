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

from . import TempCentillionConfig


def get_plain_config() -> typing.Dict[str, typing.Any]:
    """
    Create a simple configuration file that tests can use.
    - We don't set centillion root because the TempCentillionConfig
      context manager will do that for us
    - We don't set centillion indexdir because by default it is at
      $centillion_root/index
    """
    return {
        "doctypes": [],
    }


def get_plain_doc(ix: int) -> typing.Dict[str, typing.Any]:
    """Return a document that only sets fields in the common schema"""
    return dict(
        id = "https://github.com/charlesreid1/centillion-search-demo",
        kind = "foobar",
        created_time = datetime.datetime.now(),
        modified_time = datetime.datetime.now(),
        indexed_time = datetime.datetime.now(),
        name = f"file_{ix}.dat",
    )


def get_ghfile_config():
    """
    Create a Github file configuration file that tests can use.
    """
    return {
        "doctypes": [{
            "name": "centillion-test-search-get-local-map",
            "doctype": "github_file",
            "access_token": "invalid-access-token",
            "repos": [
                "charlesreid1/centillion-search-demo"
            ]
        }]
    }


def get_ghfile_doc(ix: int) -> typing.Dict[str, typing.Any]:
    """Return a document that only sets fields in the Github file schema"""
    return dict(
        id = "https://github.com/charlesreid1/centillion-search-demo",
        kind = "github_file",
        created_time = datetime.datetime.now(),
        modified_time = datetime.datetime.now(),
        #indexed_time = datetime.datetime.now(),
        name = f"file_{ix}.dat",
        file_name = f"file_{ix}.dat",
        file_url = f"https://github.com/charlesreid1/centillion-search-demo/tree/master/file_{ix}.dat",
        repo_path = f"file_{ix}.dat",
        github_user = "charlesreid1",
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
        with TempCentillionConfig(get_ghfile_config()) as config_file:
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
