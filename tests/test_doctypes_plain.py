import unittest
import datetime

# from centillion.config import Config
# from centillion.doctypes.registry import DoctypeRegistry
from centillion.doctypes.doctype import Doctype

from .doctypes.plain import PlainDoctype
from .context import TempCentillionConfig
from .util_searchdocs import get_plain_docs
from .util_configs import get_plain_config


class PlainDoctypeTest(unittest.TestCase):
    """
    Test the plain doctype, which is inteded for use in tests
    """
    doctype = 'plain'

    def test_doctype_name(self):
        self.assertEqual(PlainDoctype.doctype, self.doctype)

    def test_schema(self):
        """Check to make sure the PlainDoctype class uses the common_schema"""
        self.assertEqual(PlainDoctype.common_schema, Doctype.common_schema)
        # PlainDoctype uses the common schema, so its schema (extra fields beyond common schema) should be {}
        self.assertEqual(PlainDoctype.schema, {})

    def test_plain_doctype_constructors(self):
        """Check to make sure the constructor does not raise any errors"""
        name = "centillion-test-doctypes-tests-plain-doctype-name"
        PlainDoctype(name)

    def test_register_documents(self):
        docs = get_plain_docs()
        for doc in docs:
            PlainDoctype.register_document(doc)
        self.assertEqual(len(docs), len(PlainDoctype.document_registry.keys()))
        # Check that individual fields are equal
        for ok_doc, (_, check_doc) in zip(docs, PlainDoctype.document_registry.items()):
            for key in ok_doc.keys():
                self.assertEqual(ok_doc[key], check_doc[key])

    def test_get_remote_map(self):
        remote_map = PlainDoctype.get_remote_map()
        for k, v in remote_map.items():
            self.assertEqual(type(k), str)
            self.assertEqual(type(v), datetime.datetime)

    def test_get_by_id(self):
        docs = get_plain_docs()
        with TempCentillionConfig(get_plain_config()):

            # Add each doc
            for doc in docs:
                PlainDoctype.register_document(doc)
            self.assertEqual(len(docs), len(PlainDoctype.document_registry.keys()))

            # Check that the doc returned by get_by_id() is the same
            for local_doc in docs:
                doc_id = local_doc['id']
                remote_doc = PlainDoctype.get_by_id(doc_id)
                self.assertEqual(local_doc.keys(), remote_doc.keys())
                for local_key, remote_key in zip(local_doc.keys(), remote_doc.keys()):
                    self.assertEqual(local_doc[local_key], remote_doc[remote_key])
                # self.assertDictEqual(local_doc, PlainDoctype.get_by_id(doc_id))
