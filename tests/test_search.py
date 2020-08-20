import os
import time
import logging
import unittest
import datetime
import tempfile
from whoosh import fields

from centillion.config import Config
from centillion.search import Search
from centillion.doctypes.registry import DoctypeRegistry
from centillion.error import CentillionSearchIndexException

from .context import TempCentillionConfig
from .doctypes.plain import PlainDoctype
from .util_configs import get_plain_config
from .util_searchdocs import get_plain_docs


logger = logging.getLogger(__name__)


class SearchInitIndexTest(unittest.TestCase):
    """
    Test methods that initialize the Search class by creating or opening a search index.
    """

    def test_create_index(self):
        """
        Test the creation of a search index
        """
        doc = get_plain_docs(n=1)[0]

        with self.subTest("Test that search index is created without centillion_index set in the config file"):
            with tempfile.TemporaryDirectory() as td:
                config = get_plain_config()
                config["centillion_root"] = td
                with TempCentillionConfig(config, centillion_root=td):
                    # Populate the search index and verify it exists on disk
                    s = Search()
                    s.add_doc(doc)
                    self.assertEqual(os.path.join(td, "index"), Config.get_centillion_indexdir())
                    self.assertTrue(os.path.exists(Config.get_centillion_indexdir()))

        with self.subTest("Search index is created with centillion_index set in the config file"):
            with tempfile.TemporaryDirectory() as td1:
                with tempfile.TemporaryDirectory(prefix=td1 + "/") as td2:
                    config = get_plain_config()
                    config["centillion_root"] = td1
                    config["centillion_index"] = td2
                    with TempCentillionConfig(config, centillion_root=td1):
                        # Populate search index and verify it exists on disk
                        s = Search()
                        s.add_doc(doc)
                        self.assertEqual(td1, Config.get_centillion_root())
                        self.assertEqual(td2, Config.get_centillion_indexdir())
                        self.assertTrue(os.path.exists(Config.get_centillion_indexdir()))

        with self.subTest("Test search index is created with centillion_index, centillion_root separated"):
            with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
                config = get_plain_config()
                config["centillion_root"] = td1
                config["centillion_index"] = td2
                with TempCentillionConfig(config):
                    s = Search()
                    s.add_doc(doc)
                    self.assertEqual(td1, Config.get_centillion_root())
                    self.assertEqual(td2, Config.get_centillion_indexdir())
                    self.assertTrue(os.path.exists(Config.get_centillion_indexdir()))

    def test_open_index(self):
        """
        Test the opening of an existing search index
        """
        doc = get_plain_docs(n=1)[0]
        doc_id = doc["id"]
        td = tempfile.TemporaryDirectory()

        # Create a search index and populate it
        config = get_plain_config()
        config['centillion_root'] = td.name
        with TempCentillionConfig(config):
            # Populate the search index and verify it exists on disk
            s = Search()
            self.assertEqual(s.get_by_id(doc_id), None)
            s.add_doc(doc)
            self.assertNotEqual(s.get_by_id(doc_id), None)
            self.assertEqual(os.path.join(td.name, "index"), Config.get_centillion_indexdir())
            self.assertTrue(os.path.exists(Config.get_centillion_indexdir()))

        with self.subTest("Open an existing search index on disk"):
            # Open the existing search index
            with TempCentillionConfig(config):
                s2 = Search()
                self.assertNotEqual(s2.get_by_id(doc_id), None)

        # Now add a new, inconsistent doctype to the config file
        with self.subTest("Open an existing search index with modified doctype configuration"):
            pass

        td.cleanup()


class SearchCrudTest(unittest.TestCase):
    """
    Test methods of the Search class that perform CRUD operations on the search index.
    """

    def test_constructor(self):
        """Test the construction of a Search object"""
        with TempCentillionConfig(get_plain_config()):
            Search()

    def test_search_add_docs(self):
        """
        Test the add_doc functionality of the Search class.

        This method tests these Search class methods:
        - add_doc
        - add_docs
        """
        docs = get_plain_docs()

        with self.subTest("Test add_doc method of Search class"):
            with TempCentillionConfig(get_plain_config()):
                s = Search()

                # Call add_doc on each doc (passes doc directly)
                for doc in docs:
                    PlainDoctype.register_document(doc)
                    s.add_doc(doc)

                # Ensure added
                for doc in docs:
                    search_ix_doc = s.get_by_id(doc["id"])
                    self.assertEqual(search_ix_doc["name"], doc["name"])

        with self.subTest("Test add_doc method of Search class"):
            with TempCentillionConfig(get_plain_config()):
                s = Search()

                # Call add_docs on all doc ids (uses docs from doctype get by id)
                for doc in docs:
                    PlainDoctype.register_document(doc)
                doc_ids = [d["id"] for d in docs]
                s.add_docs(doc_ids, PlainDoctype(""))

                # Ensure added
                for doc in docs:
                    search_ix_doc = s.get_by_id(doc["id"])
                    # TODO improve
                    self.assertEqual(search_ix_doc["name"], doc["name"])

    def test_search_update_docs(self):
        """
        Test the ability to add, then update, a plain document

        This method tests these Search class methods:
        - add_doc
        - update_docs
        """
        docs = get_plain_docs()

        def _rename_doc_in_remote(doc_id, new_name):
            # Utility function to rename a document in the PlainDoctype "remote" (a dict in memory)

            # Check that the document we're about to update doesn't have the new name
            search_ix_doc = s.get_by_id(doc_id)
            self.assertNotEqual(search_ix_doc["name"], new_name)

            # Modify the document in the "remote" (the PlainDoctype class)
            doc = PlainDoctype.document_registry[doc_id]
            doc["name"] = new_name
            doc["modified_time"] = datetime.datetime.now().replace(
                microsecond=0
            ) + datetime.timedelta(minutes=10)

            # Re-register the updated document
            PlainDoctype.register_document(doc)

        with TempCentillionConfig(get_plain_config()):
            s = Search()

            # Add docs (already tested)
            for doc in docs:
                PlainDoctype.register_document(doc)
                s.add_doc(doc)
            doc_id = docs[0]["id"]
            to_update = {doc_id}

            with self.subTest("Testing update_docs with remote_map argument"):
                # Update/rename doc in remote
                new_name = 'centillion-test-search-file-dingbat.dat'
                _rename_doc_in_remote(doc_id, new_name)

                # Update local search index passing remote_map
                remote_map = PlainDoctype.get_remote_map()
                s.update_docs(to_update, PlainDoctype(""), remote_map)

                # Get the search index document and ensure it was updated
                search_ix_doc = s.get_by_id(doc_id)
                self.assertEqual(search_ix_doc["name"], new_name)

            time.sleep(1)

            with self.subTest("Testing update_docs without remote_map argument"):
                # Update/rename doc in remote
                new_name2 = 'centillion-test-search-file-dingbat-2.dat'
                _rename_doc_in_remote(doc_id, new_name2)

                # Update local search index without remote_map
                s.update_docs(to_update, PlainDoctype(""))

                # Get the search index document and ensure it was updated
                search_ix_doc2 = s.get_by_id(doc_id)
                self.assertEqual(search_ix_doc2["name"], new_name2)

    def test_search_delete_docs(self):
        """
        Test the ability to add, then delete, a plain document

        This method tests these Search class methods;
        - add_doc
        - delete_docs
        """
        docs = get_plain_docs()
        doc_ids_list = [d["id"] for d in docs]
        doc_ids_set = {d["id"] for d in docs}

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
        with TempCentillionConfig(get_plain_config()):
            s = Search()

            # Add each doc to search index, and register it with PlainDoctype
            docs = get_plain_docs()
            for doc in docs:
                s.add_doc(doc)
                PlainDoctype.register_document(doc)

            # Access each document using get_by_id
            for doc in docs:
                doc_id = doc["id"]
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
        docs = get_plain_docs()

        with TempCentillionConfig(get_plain_config()):
            s = Search()

            for doc in docs:
                s.add_doc(doc)
                PlainDoctype.register_document(doc)

            loc_map = s.get_local_map(PlainDoctype.doctype)
            # Check type/size of resulting map
            self.assertEqual(type(loc_map), type({}))
            self.assertGreater(len(loc_map), 0)
            # Check the types of the key, value pairs
            for k, v in loc_map.items():
                self.assertEqual(type(k), str)
                self.assertEqual(type(v), datetime.datetime)
            # Check that each document added to the search index is in the local_map
            for doc in docs:
                doc_id = doc["id"]
                self.assertIn(doc_id, loc_map.keys())


class SearchSchemaTest(unittest.TestCase):
    """
    Test methods of the Search class related to the schema
    """

    class MismatchedSchemas1(metaclass=DoctypeRegistry):
        """Barebones doctype class that defines a schema inconsistent with sister object"""

        doctype = "mismatched-1"
        schema = dict(
            matched_field=fields.TEXT(stored=True), mismatched_field=fields.TEXT(stored=True)
        )

    class MismatchedSchemas2(metaclass=DoctypeRegistry):
        """Barebones doctype class that defines a schema inconsistent with sister object"""

        doctype = "mismatched-2"
        schema = dict(
            matched_field=fields.TEXT(stored=True), mismatched_field=fields.DATETIME(stored=True)
        )

    def test_constructor_mismatched(self):
        """Test the construction of a Search object"""
        temp_config = {
            "doctypes": [
                {
                    "name": "centillion-test-search-constructor-mismatched-1",
                    "doctype": "mismatched-1",
                },
                {
                    "name": "centillion-test-search-constructor-mismatched-2",
                    "doctype": "mismatched-2",
                },
            ]
        }

        with TempCentillionConfig(temp_config):
            with self.assertRaises(CentillionSearchIndexException):
                Search()


if __name__ == "__main__":
    unittest.main()
