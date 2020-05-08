import time
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
    get_plain_docs,
    get_ghfile_doc
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

    def test_search_add_doc(self):
        """
        Test the add_doc functionality of the Search class.

        This method tests these Search class methods:
        - add_doc
        - get_local_map
        - get_by_id
        """
        doctype = "plain"
        doctype_cls = DoctypeRegistry.REGISTRY[doctype]
        docs = get_plain_docs()

        with TempCentillionConfig(get_plain_config()):
            s = Search()

            with self.subTest("Test add_doc method of Search class"):
                for doc in docs:
                    s.add_doc(doc)
                    doctype_cls.register_document(doc)

            with self.subTest("Test get_by_id method of Search class"):
                # Access each document using get_by_id
                for doc in docs:
                    doc_id = doc['id']
                    search_ix_doc = s.get_by_id(doc_id)
                    # Check the search index is not just returning the id field
                    self.assertTrue(len(search_ix_doc.keys()) > 1)
                    # Check each field in the original document is in search index document
                    for k in doc.keys():
                        self.assertEqual(doc[k], search_ix_doc[k])

            with self.subTest("Test get_local_map method of Search class"):
                loc_map = s.get_local_map(doctype)
                # Check type/size of resulting map
                self.assertEqual(type(loc_map), type({}))
                self.assertGreater(len(loc_map), 0)
                # Check the types of the key, value pairs
                for k, v in loc_map.items():
                    self.assertEqual(type(k), str)
                    self.assertEqual(type(v), datetime.datetime)
                # Check that each document added to the search index is in the local_map
                for doc in docs:
                    doc_id = doc['id']
                    self.assertIn(doc_id, loc_map.keys())

    def test_search_update_docs(self):
        """
        Test the abiltiy to add, then update, a document

        This method tests these Search class methods:
        - add_doc
        - update_docs
        """
        doctype = "plain"
        doctype_cls = DoctypeRegistry.REGISTRY[doctype]
        docs = get_plain_docs()
        with TempCentillionConfig(get_plain_config()):
            s = Search()

            with self.subTest("Test add_doc method of Search class"):
                for doc in docs:
                    s.add_doc(doc)
                    doctype_cls.register_document(doc)

            with self.subTest("Test update_docs method of Search class"):
                # To update a document, we need to update the
                # document in the "remote", which in this case
                # is the PlainDoctype class's document_registry variable.
                #
                # Then we get the local and remote lists,
                # and pass them to update_docs to update
                # any documents that need updating.

                # New dummy name of one of the documents
                dummy_name = 'centillion-test-search-file-dingbat.dat'

                # Doc id of document we will modify
                doc_id = doctype_cls.document_registry[-1]['id']

                # First, get the search index document and check it is the old version
                search_ix_doc = s.get_by_id(doc_id)
                self.assertNotEqual(search_ix_doc['name'], dummy_name)

                time.sleep(1)

                # Now pop the doc from the PlainDoctype registry, modify it, and put it back
                doc = doctype_cls.document_registry.pop()
                doc_id = doc['id']
                doc['name'] = dummy_name
                doc['modified_time'] = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(minutes=10)
                doctype_cls.document_registry.append(doc)

                # Now call the update_docs method of the Search class
                to_update = {doc_id}
                remote_map = doctype_cls.get_remote_map()
                local_map = s.get_local_map(doctype)
                s.update_docs(to_update, remote_map, local_map, doctype_cls)

                time.sleep(1)

                # Get the search index document and ensure it was updated
                search_ix_doc = s.get_by_id(doc_id)
                self.assertEqual(search_ix_doc['name'], dummy_name)

    def test_crud_plain_doc(self):
        """
        Test the ability to create/read/update/delete a plain document (a doc whose schema is the common schema)
        in a centillion search index.
        """
        doctype = "plain"
        # doctype_cls = DoctypeRegistry.REGISTRY[doctype]
        docs = get_plain_docs()
        fname = 'centillion-test-search-file-dingbat.dat'

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
                doc = docs.pop()
                doc['name'] = fname
                loc_map = s.get_local_map(doctype)
                self.assertGreater(len(loc_map), 0)
                # do a query for name field, dingbat
                # assert results length greater than 0

            with self.subTest("Test DELETE plain docs"):
                doc_ids = [doc['id'] for doc in docs]
                s.delete_docs(doc_ids)

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
