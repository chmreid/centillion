import unittest
import datetime
from unittest import mock
from whoosh.fields import Schema

# from centillion.config import Config
from centillion.search import Search
from centillion.doctypes.doctype import Doctype
from centillion.doctypes.registry import DoctypeRegistry

from .context import TempCentillionConfig
from .doctypes.plain import PlainDoctype
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

    def test_search_add_docs(self):
        """
        Test the add_doc functionality of the Search class.

        This method tests these Search class methods:
        - add_doc
        - add_docs
        - get_local_map
        - get_by_id
        """
        doctype = "plain"
        docs = get_plain_docs()

        with self.subTest("Test add_doc method of Search class"):
            with TempCentillionConfig(get_plain_config()):
                name = "centillion-test-search-add-doc"
                s = Search()

                # Register each doc, then add it to the search index
                for doc in docs:
                    PlainDoctype.register_document(doc)
                    s.add_doc(doc)

                # Ensure added
                for doc in docs:
                    search_ix_doc = s.get_by_id(doc['id'])
                    self.assertEqual(search_ix_doc['name'], doc['name'])

        with self.subTest("Test add_doc method of Search class"):
            with TempCentillionConfig(get_plain_config()):
                doctype_name = "centillion-test-search-add-docs"
                s = Search()
                doctype_instance = DoctypeRegistry.REGISTRY[doctype](doctype_name)

                # Register each doc to create a remote list
                for doc in docs:
                    PlainDoctype.register_document(doc)
                doc_ids = [d['id'] for d in docs]
                s.add_docs(doc_ids, doctype_instance)

                # Ensure added
                for doc in docs:
                    search_ix_doc = s.get_by_id(doc['id'])
                    self.assertEqual(search_ix_doc['name'], doc['name'])


    def test_search_update_docs(self):
        """
        Test the ability to add, then update, a plain document

        This method tests these Search class methods:
        - add_doc
        - update_docs
        """
        doctype = "plain"
        name = "centillion-test-search-add-doc"
        doctype_instance = DoctypeRegistry.REGISTRY[doctype](name)
        docs = get_plain_docs()

        with TempCentillionConfig(get_plain_config()):
            s = Search()

            # Add docs (already tested)
            for doc in docs:
                s.add_doc(doc)
                PlainDoctype.register_document(doc)

            # To update a document, we need to update the
            # document in the "remote", which in this case
            # is the PlainDoctype class's document_registry variable.
            #
            # Then we get the local and remote lists,
            # and pass them to update_docs to update
            # any documents that need updating.

            # New dummy name for one of the documents
            dummy_name = 'centillion-test-search-file-dingbat.dat'

            # Doc id of document we will modify
            doc_id = docs[0]['id']

            # First, get the search index document and check it is the old version
            # Adding the document above ensures the document will be in the search index.
            search_ix_doc = s.get_by_id(doc_id)
            self.assertNotEqual(search_ix_doc['name'], dummy_name)

            # Modify the document in the "remote" (the PlainDoctype class)
            doc = PlainDoctype.document_registry[doc_id]
            doc['name'] = dummy_name
            doc['modified_time'] = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(minutes=10)

            # Re-register the updated document
            PlainDoctype.register_document(doc)

            # Call the update_docs method of the Search class to update the document in the search index
            to_update = {doc_id}
            remote_map = PlainDoctype.get_remote_map()
            s.update_docs(to_update, doctype_instance, remote_map)

            # Get the search index document and ensure it was updated
            search_ix_doc = s.get_by_id(doc_id)
            self.assertEqual(search_ix_doc['name'], dummy_name)

    def test_search_delete_docs(self):
        """
        Test the ability to add, then delete, a plain document

        This method tests these Search class methods;
        - add_doc
        - delete_docs
        """
        doctype = "plain"
        name = "centillion-test-search-add-doc"
        doctype_instance = DoctypeRegistry.REGISTRY[doctype](name)
        docs = get_plain_docs()
        doc_ids_list = [d['id'] for d in docs]
        doc_ids_set = {d['id'] for d in docs}

        with TempCentillionConfig(get_plain_config()):
            s = Search()

            with self.subTest("Test delete_docs with list"):
                for doc in docs:
                    s.add_doc(doc)
                    PlainDoctype.register_document(doc)

                # Ensure added
                for doc_id in doc_ids_list:
                    self.assertNotEqual(s.get_by_id(doc_id), None)

                # Test delete as list
                s.delete_docs(doc_ids_list)

                # Ensure deleted
                for doc_id in doc_ids_list:
                    self.assertEqual(s.get_by_id(doc_id), None)

            with self.subTest("Test delete_docs with set"):
                for doc in docs:
                    s.add_doc(doc)
                    PlainDoctype.register_document(doc)

                # Ensure added
                for doc_id in doc_ids_list:
                    self.assertNotEqual(s.get_by_id(doc_id), None)

                # Test delete as set
                s.delete_docs(doc_ids_set)

                # Ensure deleted
                for doc_id in doc_ids_list:
                    self.assertEqual(s.get_by_id(doc_id), None)

            with self.subTest("Test delete_doc with individual IDs"):
                for doc in docs:
                    s.add_doc(doc)
                    PlainDoctype.register_document(doc)

                # Ensure added
                for doc_id in doc_ids_list:
                    self.assertNotEqual(s.get_by_id(doc_id), None)

                # Test delete using individual IDs
                for doc_id in doc_ids_list:
                    s.delete_doc(doc_id)

                # Ensure deleted
                for doc_id in doc_ids_list:
                    self.assertEqual(s.get_by_id(doc_id), None)

    def test_get_by_id(self):
        """
        Test the get_by_id method of the Search class.
        """
        doctype = "plain"
        name = "centillion-test-search-get-by-id"
        doctype_instance = DoctypeRegistry.REGISTRY[doctype](name)
        docs = get_plain_docs()

        with TempCentillionConfig(get_plain_config()):
            s = Search()

            for doc in docs:
                s.add_doc(doc)
                doctype_instance.register_document(doc)

            # Access each document using get_by_id
            for doc in docs:
                doc_id = doc['id']
                search_ix_doc = s.get_by_id(doc_id)
                # Check the search index is not just returning the id field
                self.assertTrue(len(search_ix_doc.keys()) > 1)
                # Check each field in the original document is in search index document
                for k in doc.keys():
                    self.assertEqual(doc[k], search_ix_doc[k])

    def test_local_map(self):
        """
        Test the get_local_map method of the Search class.
        """
        doctype = "plain"
        name = "centillion-test-search-local-map"
        doctype_instance = DoctypeRegistry.REGISTRY[doctype](name)
        docs = get_plain_docs()

        with TempCentillionConfig(get_plain_config()):
            s = Search()

            for doc in docs:
                s.add_doc(doc)
                doctype_instance.register_document(doc)

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


if __name__ == "__main__":
    unittest.main()
